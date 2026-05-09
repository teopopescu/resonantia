"""Tests for the multimodal user-content builder.

These exercise the parser + image encoder using a temp file registry,
without touching FastAPI or the LLM provider.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import pytest

from resonantia.services import multimodal


@pytest.fixture
def fake_registry(tmp_path, monkeypatch):
    """Replace ``api.files._file_registry`` with a clean dict and point
    upload_dir at tmp_path so the multimodal helper's path-canonicalization
    accepts the test files."""
    from resonantia.api import files as files_module
    from resonantia.config import get_settings

    registry: dict = {}
    monkeypatch.setattr(files_module, "_file_registry", registry)

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path), raising=False)
    return registry, tmp_path


def _add_file(
    registry,
    tmp_path: Path,
    file_id: str,
    *,
    content_type: str,
    data: bytes,
    filename: str = "test.png",
    org_id: str = "org_test",
) -> dict:
    """Add a file directly to the in-memory registry, mirroring the
    production layout: files live under upload_dir/files/<file_id><ext>."""
    files_subdir = tmp_path / "files"
    files_subdir.mkdir(exist_ok=True)
    ext = os.path.splitext(filename)[1]
    path = files_subdir / f"{file_id}{ext}"
    path.write_bytes(data)
    meta = {
        "id": file_id,
        "filename": filename,
        "size": len(data),
        "content_type": content_type,
        "uploaded_at": "2026-05-01T00:00:00Z",
        "download_url": f"/api/v1/files/{file_id}/download",
        "stored_path": str(path),
        "org_id": org_id,
    }
    registry[file_id] = meta
    return meta


# ---------------------------------------------------------------------------
# build_user_content — text-only paths
# ---------------------------------------------------------------------------

def test_plain_message_with_no_images_returns_str():
    out = multimodal.build_user_content(
        "hello, what's the lot of anti-GFP?", org_id="org_test",
    )
    assert isinstance(out, str)
    assert out == "hello, what's the lot of anti-GFP?"


def test_message_with_csv_attachment_only_returns_str(fake_registry):
    """CSV files are referenced by URL but not encoded as vision blocks."""
    registry, tmp = fake_registry
    _add_file(registry, tmp, "csv-1", content_type="text/csv",
              data=b"a,b\n1,2", filename="data.csv")
    msg = "[file:data.csv](http://x/api/v1/files/csv-1/download){size:7B}\nplease analyse"
    out = multimodal.build_user_content(msg, org_id="org_test")
    assert isinstance(out, str)
    assert out == msg


def test_message_with_unknown_file_id_returns_plain_string(fake_registry):
    msg = "[file:ghost.png](http://x/api/v1/files/missing/download)"
    out = multimodal.build_user_content(msg, org_id="org_test")
    assert isinstance(out, str)


# ---------------------------------------------------------------------------
# build_user_content — image paths
# ---------------------------------------------------------------------------

def test_message_with_inline_image_returns_blocks(fake_registry):
    registry, tmp = fake_registry
    raw = b"\x89PNG\r\n\x1a\nfake-png-bytes"
    _add_file(registry, tmp, "img-1", content_type="image/png",
              data=raw, filename="well-A1.png")

    msg = ("here is the well image:\n"
           "[file:well-A1.png](http://x/api/v1/files/img-1/download){size:24B}")
    out = multimodal.build_user_content(msg, org_id="org_test")

    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0]["type"] == "text"
    assert out[0]["text"] == msg
    assert out[1]["type"] == "image_url"
    expected_b64 = base64.b64encode(raw).decode("ascii")
    assert out[1]["image_url"]["url"] == f"data:image/png;base64,{expected_b64}"


def test_explicit_attachments_field_works_without_inline_marker(fake_registry):
    registry, tmp = fake_registry
    _add_file(registry, tmp, "img-2", content_type="image/jpeg",
              data=b"jpeg-bytes", filename="snap.jpg")

    out = multimodal.build_user_content(
        "what do you see?", attachments=["img-2"], org_id="org_test",
    )
    assert isinstance(out, list)
    assert len(out) == 2
    assert out[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_multiple_images_each_become_a_block(fake_registry):
    registry, tmp = fake_registry
    _add_file(registry, tmp, "i1", content_type="image/png",
              data=b"a", filename="a.png")
    _add_file(registry, tmp, "i2", content_type="image/png",
              data=b"b", filename="b.png")
    msg = (
        "compare these:\n"
        "[file:a.png](http://x/api/v1/files/i1/download)\n"
        "[file:b.png](http://x/api/v1/files/i2/download)"
    )
    out = multimodal.build_user_content(msg, org_id="org_test")
    assert isinstance(out, list)
    image_blocks = [b for b in out if b["type"] == "image_url"]
    assert len(image_blocks) == 2


def test_inline_marker_and_explicit_attachments_dedupe(fake_registry):
    """If the same file appears inline AND in the attachments list, the
    image is encoded once, not twice."""
    registry, tmp = fake_registry
    _add_file(registry, tmp, "dup", content_type="image/png",
              data=b"x", filename="d.png")
    msg = "[file:d.png](http://x/api/v1/files/dup/download)"
    out = multimodal.build_user_content(
        msg, attachments=["dup"], org_id="org_test",
    )
    assert isinstance(out, list)
    image_blocks = [b for b in out if b["type"] == "image_url"]
    assert len(image_blocks) == 1


def test_oversized_image_is_skipped(fake_registry, monkeypatch):
    """Images larger than MAX_IMAGE_BYTES are dropped, not crashed on."""
    registry, tmp = fake_registry
    monkeypatch.setattr(multimodal, "MAX_IMAGE_BYTES", 10)
    _add_file(registry, tmp, "huge", content_type="image/png",
              data=b"x" * 100, filename="huge.png")
    msg = "[file:huge.png](http://x/api/v1/files/huge/download)"
    out = multimodal.build_user_content(msg, org_id="org_test")
    # Falls back to plain string because the only image was rejected.
    assert isinstance(out, str)
    assert out == msg


def test_image_missing_from_disk_is_skipped(fake_registry):
    registry, tmp = fake_registry
    _add_file(registry, tmp, "gone", content_type="image/png",
              data=b"x", filename="gone.png")
    os.remove(registry["gone"]["stored_path"])
    msg = "[file:gone.png](http://x/api/v1/files/gone/download)"
    out = multimodal.build_user_content(msg, org_id="org_test")
    assert isinstance(out, str)


def test_non_image_mime_in_attachments_is_ignored(fake_registry):
    registry, tmp = fake_registry
    _add_file(registry, tmp, "pdf", content_type="application/pdf",
              data=b"%PDF-1.4", filename="report.pdf")
    out = multimodal.build_user_content(
        "summarize this report", attachments=["pdf"], org_id="org_test",
    )
    assert isinstance(out, str)


# ---------------------------------------------------------------------------
# Tenant isolation — the security boundary
# ---------------------------------------------------------------------------

def test_cross_tenant_file_id_is_not_encoded(fake_registry):
    """Org A uploaded the file. Org B references the file_id in chat.
    The image must NOT reach the LLM."""
    registry, tmp = fake_registry
    _add_file(registry, tmp, "secret-img", content_type="image/png",
              data=b"\x89PNG-secret", filename="secret.png", org_id="org_alpha")

    out = multimodal.build_user_content(
        "what do you see?", attachments=["secret-img"], org_id="org_beta",
    )
    assert isinstance(out, str), (
        "Cross-tenant file leaked into vision content blocks"
    )


def test_cross_tenant_inline_marker_is_not_encoded(fake_registry):
    registry, tmp = fake_registry
    _add_file(registry, tmp, "secret2", content_type="image/png",
              data=b"\x89PNG-secret", filename="x.png", org_id="org_alpha")
    msg = "[file:x.png](http://x/api/v1/files/secret2/download)"
    out = multimodal.build_user_content(msg, org_id="org_beta")
    assert isinstance(out, str)


def test_owner_org_can_access_its_own_file(fake_registry):
    """Sanity check: same-org access still works."""
    registry, tmp = fake_registry
    _add_file(registry, tmp, "mine", content_type="image/png",
              data=b"\x89PNG-mine", filename="m.png", org_id="org_alpha")
    out = multimodal.build_user_content(
        "what's in here?", attachments=["mine"], org_id="org_alpha",
    )
    assert isinstance(out, list)


# ---------------------------------------------------------------------------
# Per-turn caps
# ---------------------------------------------------------------------------

def test_too_many_images_per_turn_capped(fake_registry, monkeypatch):
    """User attaches more images than MAX_IMAGES_PER_TURN; only the cap
    is encoded."""
    registry, tmp = fake_registry
    monkeypatch.setattr(multimodal, "MAX_IMAGES_PER_TURN", 2)
    for i in range(5):
        _add_file(registry, tmp, f"img-{i}", content_type="image/png",
                  data=b"x", filename=f"f{i}.png")
    out = multimodal.build_user_content(
        "compare", attachments=[f"img-{i}" for i in range(5)],
        org_id="org_test",
    )
    assert isinstance(out, list)
    image_blocks = [b for b in out if b["type"] == "image_url"]
    assert len(image_blocks) == 2


def test_total_bytes_cap_stops_encoding(fake_registry, monkeypatch):
    """The total-bytes cap is enforced even if individual images fit."""
    registry, tmp = fake_registry
    monkeypatch.setattr(multimodal, "MAX_TOTAL_IMAGE_BYTES", 10)
    monkeypatch.setattr(multimodal, "MAX_IMAGE_BYTES", 100)
    _add_file(registry, tmp, "i1", content_type="image/png",
              data=b"x" * 8, filename="a.png")
    _add_file(registry, tmp, "i2", content_type="image/png",
              data=b"x" * 8, filename="b.png")
    out = multimodal.build_user_content(
        "compare", attachments=["i1", "i2"], org_id="org_test",
    )
    image_blocks = [b for b in out if b["type"] == "image_url"]
    assert len(image_blocks) == 1


# ---------------------------------------------------------------------------
# MIME tightening
# ---------------------------------------------------------------------------

def test_svg_mime_is_rejected(fake_registry):
    """SVG can carry script — must never be inlined as a data: URL."""
    registry, tmp = fake_registry
    _add_file(registry, tmp, "svg", content_type="image/svg+xml",
              data=b"<svg/>", filename="x.svg")
    out = multimodal.build_user_content(
        "see this", attachments=["svg"], org_id="org_test",
    )
    assert isinstance(out, str)


def test_gif_mime_is_rejected(fake_registry):
    """GIF dropped per the audit (polyglot risk + low value for lab imagery)."""
    registry, tmp = fake_registry
    _add_file(registry, tmp, "gif", content_type="image/gif",
              data=b"GIF89a", filename="x.gif")
    out = multimodal.build_user_content(
        "see this", attachments=["gif"], org_id="org_test",
    )
    assert isinstance(out, str)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def test_is_image_true_only_for_strict_mimes():
    assert multimodal._is_image("image/png")
    assert multimodal._is_image("image/jpeg")
    assert multimodal._is_image("image/webp")
    assert multimodal._is_image("image/png; charset=utf-8")  # split-on-;


def test_is_image_false_for_excluded_mimes():
    assert not multimodal._is_image("image/jpg")  # non-canonical
    assert not multimodal._is_image("image/gif")  # dropped
    assert not multimodal._is_image("image/svg+xml")  # never
    assert not multimodal._is_image("image/tiff")
    assert not multimodal._is_image("text/csv")
    assert not multimodal._is_image("application/pdf")
    assert not multimodal._is_image(None)
    assert not multimodal._is_image("")


def test_file_id_from_url_extracts_correctly():
    assert multimodal._file_id_from_url(
        "http://x.com/api/v1/files/abc-123/download"
    ) == "abc-123"
    assert multimodal._file_id_from_url("/api/v1/files/xyz/download") == "xyz"
    assert multimodal._file_id_from_url("http://x.com/other/path") is None
