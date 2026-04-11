"""User profile model storing onboarding data."""
from __future__ import annotations

from sqlalchemy import String, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from resonantia.models.base import Base, UUIDPrimaryKey, TimestampMixin


class UserProfile(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "user_profiles"

    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)  # scientist, lab_manager, bioinformatician, other
    focus_areas: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # ["plate_assays", "microscopy", "qpcr", "sample_management"]
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
