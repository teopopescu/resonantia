"""FileUpload ORM model — persists file metadata to PostgreSQL."""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from resonantia.models.base import Base, TimestampMixin, UUIDPrimaryKey


class FileUpload(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "file_uploads"

    org_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # For CSVs: { columns: [...], row_count: N, detected_types: {...} }
