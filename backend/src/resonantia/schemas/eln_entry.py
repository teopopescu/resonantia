"""Pydantic schemas for ELN entries."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ELNEntryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content_markdown: str | None = None
    summary: str | None = None
    experiment_id: uuid.UUID | None = None
    author_id: str | None = None
    embedded_figures: list[dict[str, Any]] | None = None
    linked_references: dict[str, Any] | None = None
    tags: list[str] | None = None


class ELNEntryUpdate(BaseModel):
    title: str | None = None
    content_markdown: str | None = None
    summary: str | None = None
    embedded_figures: list[dict[str, Any]] | None = None
    linked_references: dict[str, Any] | None = None
    tags: list[str] | None = None


class ELNEntrySubmit(BaseModel):
    """Body for submitting an ELN entry (makes it immutable)."""
    pass


class ELNAutoGenerate(BaseModel):
    experiment_id: uuid.UUID
    author_id: str | None = None


class AppendixCreate(BaseModel):
    content_markdown: str = Field(..., min_length=1)
    author_id: str | None = None


class AppendixResponse(BaseModel):
    id: uuid.UUID
    eln_entry_id: uuid.UUID
    content_markdown: str
    author_id: str | None
    appendix_number: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ELNEntryResponse(BaseModel):
    id: uuid.UUID
    title: str
    entry_number: str
    content_markdown: str | None
    summary: str | None
    status: str
    version: int
    experiment_id: uuid.UUID | None
    author_id: str | None
    embedded_figures: list[dict[str, Any]] | None
    linked_references: dict[str, Any] | None
    tags: list[str] | None
    appendices: list[AppendixResponse] = []
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ELNEntryListResponse(BaseModel):
    id: uuid.UUID
    title: str
    entry_number: str
    status: str
    experiment_id: uuid.UUID | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
