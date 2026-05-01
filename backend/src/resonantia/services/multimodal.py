"""Build multimodal user messages for the agent.

The frontend uploads attachments through ``/api/v1/files/upload`` and
inlines them into chat text as ``[file:NAME](DOWNLOAD_URL){size:...}``.
For images, the LLM never sees the bytes unless we explicitly include
them as vision content blocks.

This module:
1. Parses a chat message for ``[file:...](URL)`` markers (and accepts a
   parallel ``attachments`` field for direct file IDs).
2. Resolves each reference against the in-process file registry, with
   org_id ownership enforcement so a chat in tenant A cannot reference
   a file uploaded by tenant B.
3. For image MIME types, reads the file and base64-encodes it into a
   ``data:`` URL — the only path that works regardless of whether the
   API is publicly reachable from the LLM provider.
4. Returns either a plain ``str`` (no images) or a structured list of
   OpenAI / Anthropic-compatible content blocks.

Non-image attachments (CSV, PDF, TXT) are NOT inlined as bytes —
those are read separately via the ``read_file_contents`` agent tool
since they need to be parsed, not just looked at.

Network fetch is forbidden in this module: image bytes are read from
the configured upload directory, never from a user-supplied URL.
"""

from __future__ import annotations

import base64
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

# --- Caps ---------------------------------------------------------------
# Per-image cap. Anthropic and OpenAI fail nastily on >20MB image payloads
# and base64 expands by ~4/3, so we keep raw images well under that.
MAX_IMAGE_BYTES = 5 * 1024 * 1024
# Max number of images encoded into a single chat turn. A user message
# attaching 20 images at the per-image cap would push ~133MB of base64
# into one LLM request body — refuse.
MAX_IMAGES_PER_TURN = 5
# Total decoded bytes across all images in a turn.
MAX_TOTAL_IMAGE_BYTES = 15 * 1024 * 1024

# --- MIME -----------------------------------------------------------------
# Strict equality — no prefix matching. Excludes:
#   - image/svg+xml: SVG can carry script and breaks the data-URL safety story
#   - image/tiff:    not supported by either OpenAI or Anthropic vision
#   - image/jpg:     non-canonical; browsers send image/jpeg
#   - image/gif:     polyglot risk + low value for lab imagery
ALLOWED_IMAGE_MIMES = frozenset({"image/png", "image/jpeg", "image/webp"})

# Matches the frontend's exact rendering: [file:NAME](URL){size:...}
# Note: the URL captured here is used ONLY to extract the file_id; we
# never make a network request against it.
_FILE_REF_RE = re.compile(r"\[file:[^\]]+\]\((?P<url>[^)]+)\)(?:\{[^}]*\})?")
_FILE_ID_FROM_URL_RE = re.compile(r"/api/v1/files/(?P<file_id>[^/]+)/download")


def _is_image(content_type: str | None) -> bool:
    if not content_type:
        return False
    ct = content_type.lower().split(";")[0].strip()
    return ct in ALLOWED_IMAGE_MIMES


def _file_id_from_url(url: str) -> str | None:
    match = _FILE_ID_FROM_URL_RE.search(url)
    return match.group("file_id") if match else None


def _resolve_file_meta(file_id: str, org_id: str) -> dict[str, Any] | None:
    """Look up a file in the in-process registry, scoped by org_id.

    Imported lazily so this module doesn't pull the FastAPI router at
    import time (and so tests can monkeypatch the registry).
    """
    from resonantia.api.files import _file_registry

    meta = _file_registry.get(file_id)
    if meta is None:
        return None
    if meta.get("org_id") != org_id:
        # Cross-tenant access attempt. Log it (anonymized) so the
        # security team has a signal, then act as if the file does
        # not exist.
        logger.warning(
            "Cross-tenant file access blocked: file %s belongs to org "
            "%r, requester is org %r",
            file_id, meta.get("org_id"), org_id,
        )
        return None
    return meta


def _safe_path(file_id: str, ext: str) -> str | None:
    """Re-derive the on-disk path from upload_dir + file_id, never trust
    a stored_path field. Returns None if the resolved path escapes the
    configured upload directory."""
    from resonantia.config import get_settings

    settings = get_settings()
    upload_dir = os.path.realpath(os.path.join(settings.upload_dir, "files"))
    candidate = os.path.realpath(os.path.join(upload_dir, f"{file_id}{ext}"))
    if os.path.commonpath([upload_dir, candidate]) != upload_dir:
        return None
    return candidate


def _encode_image(meta: dict[str, Any]) -> tuple[dict[str, Any] | None, int]:
    """Read + base64 a single image file. Returns (block, bytes_read).
    block is None if the file is missing / too large / outside upload_dir.
    """
    file_id = meta.get("id")
    if not file_id:
        return None, 0
    raw_ext = os.path.splitext(meta.get("filename") or "")[1]
    # Validate stored_path against the safe-derived path. If they differ
    # (legacy upload before the path-traversal fix) we fall back to the
    # safe-derived path and refuse to read anywhere else.
    safe_path = _safe_path(file_id, raw_ext)
    if safe_path is None or not os.path.exists(safe_path):
        # Try the registry's stored_path as a fallback, but only if it
        # still resolves under upload_dir.
        stored = meta.get("stored_path")
        if not stored:
            return None, 0
        from resonantia.config import get_settings

        upload_dir = os.path.realpath(
            os.path.join(get_settings().upload_dir, "files")
        )
        stored_real = os.path.realpath(stored)
        if os.path.commonpath([upload_dir, stored_real]) != upload_dir:
            logger.warning("File %s stored_path escapes upload_dir", file_id)
            return None, 0
        safe_path = stored_real
        if not os.path.exists(safe_path):
            return None, 0

    size = os.path.getsize(safe_path)
    if size > MAX_IMAGE_BYTES:
        logger.warning(
            "Image %s skipped: %d bytes > MAX_IMAGE_BYTES (%d)",
            file_id, size, MAX_IMAGE_BYTES,
        )
        return None, 0

    with open(safe_path, "rb") as fp:
        raw = fp.read()
    encoded = base64.b64encode(raw).decode("ascii")
    mime = (meta.get("content_type") or "image/png").split(";")[0].strip()
    if mime not in ALLOWED_IMAGE_MIMES:
        return None, 0
    block = {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{encoded}"},
    }
    return block, size


def _collect_image_file_ids(
    message: str,
    explicit_file_ids: list[str] | None,
    org_id: str,
) -> list[str]:
    """Return the set of file IDs referenced in this turn that are
    images and belong to ``org_id``."""
    file_ids: list[str] = []
    seen: set[str] = set()

    for match in _FILE_REF_RE.finditer(message):
        url = match.group("url")
        fid = _file_id_from_url(url)
        if fid and fid not in seen:
            file_ids.append(fid)
            seen.add(fid)

    for fid in explicit_file_ids or []:
        if fid and fid not in seen:
            file_ids.append(fid)
            seen.add(fid)

    image_ids: list[str] = []
    for fid in file_ids:
        meta = _resolve_file_meta(fid, org_id)
        if not meta:
            continue
        if _is_image(meta.get("content_type")):
            image_ids.append(fid)

    return image_ids


def build_user_content(
    message: str,
    *,
    attachments: list[str] | None = None,
    org_id: str = "org_default",
) -> str | list[dict[str, Any]]:
    """Return the value to put in ``messages[N].content`` for a user turn.

    - If no images are referenced (or all fail to load), returns the
      plain string. Preserves the legacy single-agent code path so
      non-multimodal turns are byte-identical.
    - If one or more images are present, returns a list of content
      blocks: a single ``{"type": "text", ...}`` block followed by
      each image as ``{"type": "image_url", ...}``.

    OpenAI's chat completions API accepts both shapes. Anthropic
    accepts the same shape via LiteLLM's translation, or via ``image``
    blocks natively. We emit the OpenAI shape since that's what the
    current backend uses.
    """
    image_ids = _collect_image_file_ids(message, attachments, org_id)
    if not image_ids:
        return message

    if len(image_ids) > MAX_IMAGES_PER_TURN:
        logger.warning(
            "Capping images per turn: %d requested, %d max",
            len(image_ids), MAX_IMAGES_PER_TURN,
        )
        image_ids = image_ids[:MAX_IMAGES_PER_TURN]

    blocks: list[dict[str, Any]] = [{"type": "text", "text": message}]
    total_bytes = 0
    for fid in image_ids:
        meta = _resolve_file_meta(fid, org_id)
        if meta is None:
            continue
        block, size = _encode_image(meta)
        if block is None:
            continue
        if total_bytes + size > MAX_TOTAL_IMAGE_BYTES:
            logger.warning(
                "Hit total-image-bytes cap (%d) at file %s; remaining "
                "images for this turn dropped",
                MAX_TOTAL_IMAGE_BYTES, fid,
            )
            break
        total_bytes += size
        blocks.append(block)

    # If every image failed to load, fall back to the plain string —
    # better than dropping the user's text.
    if len(blocks) == 1:
        return message
    return blocks
