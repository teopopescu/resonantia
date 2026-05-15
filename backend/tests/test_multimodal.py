"""Tests for the multimodal user-content builder."""

from __future__ import annotations

import base64
import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.file_upload import FileUpload
from resonantia.services import multimodal
from resonantia.services.storage import LocalStorage
from tests.conftest import _test_session_factory

pytestmark = pytest.mark.asyncio


@pytest.fixture
def fake_file_store(tmp_path, monkeypatch, db_session):
    """Point multimodal DB and storage lookups at the test fixtures."""
    from resonantia.services import storage as storage_module

    monkeypatch.setattr(multimodal, "async_session_factory", _test_session_factory)
    monkeypatch.setattr(storage_module, "_storage_instance", LocalStorage(str(tmp_path)))
    return tmp_path


async def _add_file(
    db_session: AsyncSession,
    tmp_path: Path,
    *,
    content_type: str,
    data: bytes,
    filename: str = "test.png",
    org_id: str = "org_test",
    inline: bool = True,
) -> str:
    file_id = uuid.uuid4()
    storage_path = f"files/{file_id}{Path(filename).suffix}"
    path = tmp_path / storage_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    db_session.add(
        FileUpload(
            id=file_id,
            org_id=org_id,
            uploaded_by="test-user",
            filename=filename,
            content_type=content_type,
            size_bytes=len(data),
            storage_path=storage_path,
            storage_backend="local",
            content_bytes=data if inline else None,
        )
    )
    await db_session.commit()
    return str(file_id)


async def test_plain_message_with_no_images_returns_str(fake_file_store):
    out = await multimodal.build_user_content(
        "hello, what's the lot of anti-GFP?", org_id="org_test",
    )
    assert isinstance(out, str)
    assert out == "hello, what's the lot of anti-GFP?"


async def test_message_with_csv_attachment_only_returns_str(fake_file_store, db_session):
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="text/csv", data=b"a,b\n1,2", filename="data.csv",
    )
    msg = f"[file:data.csv](http://x/api/v1/files/{file_id}/download){{size:7B}}\nplease analyse"
    out = await multimodal.build_user_content(msg, org_id="org_test")
    assert isinstance(out, str)
    assert out == msg


async def test_message_with_unknown_file_id_returns_plain_string(fake_file_store):
    msg = f"[file:ghost.png](http://x/api/v1/files/{uuid.uuid4()}/download)"
    out = await multimodal.build_user_content(msg, org_id="org_test")
    assert isinstance(out, str)


async def test_message_with_inline_image_returns_blocks(fake_file_store, db_session):
    raw = b"\x89PNG\r\n\x1a\nfake-png-bytes"
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=raw, filename="well-A1.png",
    )

    msg = (
        "here is the well image:\n"
        f"[file:well-A1.png](http://x/api/v1/files/{file_id}/download){{size:24B}}"
    )
    out = await multimodal.build_user_content(msg, org_id="org_test")

    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0]["type"] == "text"
    assert out[0]["text"] == msg
    assert out[1]["type"] == "image_url"
    expected_b64 = base64.b64encode(raw).decode("ascii")
    assert out[1]["image_url"]["url"] == f"data:image/png;base64,{expected_b64}"


async def test_explicit_attachments_field_works_without_inline_marker(fake_file_store, db_session):
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="image/jpeg", data=b"jpeg-bytes", filename="snap.jpg",
    )

    out = await multimodal.build_user_content(
        "what do you see?", attachments=[file_id], org_id="org_test",
    )
    assert isinstance(out, list)
    assert len(out) == 2
    assert out[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


async def test_multiple_images_each_become_a_block(fake_file_store, db_session):
    i1 = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=b"a", filename="a.png",
    )
    i2 = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=b"b", filename="b.png",
    )
    msg = (
        "compare these:\n"
        f"[file:a.png](http://x/api/v1/files/{i1}/download)\n"
        f"[file:b.png](http://x/api/v1/files/{i2}/download)"
    )
    out = await multimodal.build_user_content(msg, org_id="org_test")
    assert isinstance(out, list)
    image_blocks = [b for b in out if b["type"] == "image_url"]
    assert len(image_blocks) == 2


async def test_inline_marker_and_explicit_attachments_dedupe(fake_file_store, db_session):
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=b"x", filename="d.png",
    )
    msg = f"[file:d.png](http://x/api/v1/files/{file_id}/download)"
    out = await multimodal.build_user_content(
        msg, attachments=[file_id], org_id="org_test",
    )
    assert isinstance(out, list)
    image_blocks = [b for b in out if b["type"] == "image_url"]
    assert len(image_blocks) == 1


async def test_oversized_image_is_skipped(fake_file_store, db_session, monkeypatch):
    monkeypatch.setattr(multimodal, "MAX_IMAGE_BYTES", 10)
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=b"x" * 100, filename="huge.png",
    )
    msg = f"[file:huge.png](http://x/api/v1/files/{file_id}/download)"
    out = await multimodal.build_user_content(msg, org_id="org_test")
    assert isinstance(out, str)
    assert out == msg


async def test_image_missing_from_storage_is_skipped(fake_file_store, db_session):
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=b"x", filename="gone.png", inline=False,
    )
    for path in fake_file_store.rglob("*"):
        if path.is_file():
            path.unlink()
    msg = f"[file:gone.png](http://x/api/v1/files/{file_id}/download)"
    out = await multimodal.build_user_content(msg, org_id="org_test")
    assert isinstance(out, str)


async def test_non_image_mime_in_attachments_is_ignored(fake_file_store, db_session):
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="application/pdf", data=b"%PDF-1.4", filename="report.pdf",
    )
    out = await multimodal.build_user_content(
        "summarize this report", attachments=[file_id], org_id="org_test",
    )
    assert isinstance(out, str)


async def test_cross_tenant_file_id_is_not_encoded(fake_file_store, db_session):
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=b"\x89PNG-secret",
        filename="secret.png", org_id="org_alpha",
    )

    out = await multimodal.build_user_content(
        "what do you see?", attachments=[file_id], org_id="org_beta",
    )
    assert isinstance(out, str), "Cross-tenant file leaked into vision content blocks"


async def test_cross_tenant_inline_marker_is_not_encoded(fake_file_store, db_session):
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=b"\x89PNG-secret",
        filename="x.png", org_id="org_alpha",
    )
    msg = f"[file:x.png](http://x/api/v1/files/{file_id}/download)"
    out = await multimodal.build_user_content(msg, org_id="org_beta")
    assert isinstance(out, str)


async def test_owner_org_can_access_its_own_file(fake_file_store, db_session):
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=b"\x89PNG-mine",
        filename="m.png", org_id="org_alpha",
    )
    out = await multimodal.build_user_content(
        "what's in here?", attachments=[file_id], org_id="org_alpha",
    )
    assert isinstance(out, list)


async def test_too_many_images_per_turn_capped(fake_file_store, db_session, monkeypatch):
    monkeypatch.setattr(multimodal, "MAX_IMAGES_PER_TURN", 2)
    file_ids = [
        await _add_file(
            db_session, fake_file_store,
            content_type="image/png", data=b"x", filename=f"f{i}.png",
        )
        for i in range(5)
    ]
    out = await multimodal.build_user_content(
        "compare", attachments=file_ids, org_id="org_test",
    )
    assert isinstance(out, list)
    image_blocks = [b for b in out if b["type"] == "image_url"]
    assert len(image_blocks) == 2


async def test_total_bytes_cap_stops_encoding(fake_file_store, db_session, monkeypatch):
    monkeypatch.setattr(multimodal, "MAX_TOTAL_IMAGE_BYTES", 10)
    monkeypatch.setattr(multimodal, "MAX_IMAGE_BYTES", 100)
    i1 = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=b"x" * 8, filename="a.png",
    )
    i2 = await _add_file(
        db_session, fake_file_store,
        content_type="image/png", data=b"x" * 8, filename="b.png",
    )
    out = await multimodal.build_user_content(
        "compare", attachments=[i1, i2], org_id="org_test",
    )
    image_blocks = [b for b in out if b["type"] == "image_url"]
    assert len(image_blocks) == 1


async def test_svg_mime_is_rejected(fake_file_store, db_session):
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="image/svg+xml", data=b"<svg/>", filename="x.svg",
    )
    out = await multimodal.build_user_content(
        "see this", attachments=[file_id], org_id="org_test",
    )
    assert isinstance(out, str)


async def test_gif_mime_is_rejected(fake_file_store, db_session):
    file_id = await _add_file(
        db_session, fake_file_store,
        content_type="image/gif", data=b"GIF89a", filename="x.gif",
    )
    out = await multimodal.build_user_content(
        "see this", attachments=[file_id], org_id="org_test",
    )
    assert isinstance(out, str)


async def test_is_image_true_only_for_strict_mimes():
    assert multimodal._is_image("image/png")
    assert multimodal._is_image("image/jpeg")
    assert multimodal._is_image("image/webp")
    assert multimodal._is_image("image/png; charset=utf-8")


async def test_is_image_false_for_excluded_mimes():
    assert not multimodal._is_image("image/jpg")
    assert not multimodal._is_image("image/gif")
    assert not multimodal._is_image("image/svg+xml")
    assert not multimodal._is_image("image/tiff")
    assert not multimodal._is_image("text/csv")
    assert not multimodal._is_image("application/pdf")
    assert not multimodal._is_image(None)
    assert not multimodal._is_image("")


async def test_file_id_from_url_extracts_correctly():
    assert multimodal._file_id_from_url(
        "http://x.com/api/v1/files/abc-123/download"
    ) == "abc-123"
    assert multimodal._file_id_from_url("/api/v1/files/xyz/download") == "xyz"
    assert multimodal._file_id_from_url("http://x.com/other/path") is None
