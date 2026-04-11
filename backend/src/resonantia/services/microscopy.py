"""Microscopy image handling: upload, thumbnail generation, montage."""

from __future__ import annotations

import math
import os
import uuid
from pathlib import Path
from typing import Any

from PIL import Image

from resonantia.config import get_settings


def _ensure_dirs() -> tuple[Path, Path]:
    settings = get_settings()
    img_dir = Path(settings.microscopy_dir)
    thumb_dir = img_dir / "thumbnails"
    img_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir.mkdir(parents=True, exist_ok=True)
    return img_dir, thumb_dir


async def save_image(
    file_bytes: bytes,
    filename: str,
) -> tuple[str, str]:
    """Persist an uploaded image and generate a thumbnail.

    Returns (image_path, thumbnail_path) relative to the upload root.
    """
    img_dir, thumb_dir = _ensure_dirs()
    settings = get_settings()

    ext = Path(filename).suffix or ".png"
    uid = uuid.uuid4().hex
    image_name = f"{uid}{ext}"
    thumb_name = f"{uid}_thumb.png"

    image_path = img_dir / image_name
    thumb_path = thumb_dir / thumb_name

    # Write original
    image_path.write_bytes(file_bytes)

    # Generate thumbnail
    try:
        with Image.open(image_path) as im:
            im.thumbnail(settings.thumbnail_size)
            im.save(thumb_path, format="PNG")
    except Exception:
        # If thumbnail fails, copy original as fallback
        thumb_path.write_bytes(file_bytes)

    return str(image_path), str(thumb_path)


async def generate_montage(
    image_paths: list[str],
    columns: int = 4,
) -> str:
    """Stitch multiple images into a single montage and return its path."""
    images = [Image.open(p) for p in image_paths]
    if not images:
        raise ValueError("No images provided for montage")

    # Assume uniform size; resize all to first image dims
    w, h = images[0].size
    rows = math.ceil(len(images) / columns)

    montage = Image.new("RGB", (w * columns, h * rows), color=(0, 0, 0))
    for idx, im in enumerate(images):
        r, c = divmod(idx, columns)
        im_resized = im.resize((w, h))
        montage.paste(im_resized, (c * w, r * h))

    img_dir, _ = _ensure_dirs()
    out_path = img_dir / f"montage_{uuid.uuid4().hex}.png"
    montage.save(out_path, format="PNG")

    for im in images:
        im.close()

    return str(out_path)
