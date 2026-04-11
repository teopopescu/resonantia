"""ELN Entry management endpoints."""

from __future__ import annotations

import io
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.db.session import get_db
from resonantia.models.eln_entry import ELNAppendix, ELNEntry
from resonantia.models.experiment import Experiment
from resonantia.schemas.eln_entry import (
    AppendixCreate,
    AppendixResponse,
    ELNAutoGenerate,
    ELNEntryCreate,
    ELNEntryListResponse,
    ELNEntryResponse,
    ELNEntryUpdate,
)

router = APIRouter()


async def _next_entry_number(db: AsyncSession) -> str:
    """Generate the next sequential ELN entry number."""
    year = datetime.utcnow().year
    prefix = f"ELN-{year}-"
    stmt = (
        select(func.count())
        .select_from(ELNEntry)
        .where(ELNEntry.entry_number.like(f"{prefix}%"))
    )
    count = await db.scalar(stmt) or 0
    return f"{prefix}{count + 1:04d}"


@router.post("/", response_model=ELNEntryResponse, status_code=201)
async def create_eln_entry(
    body: ELNEntryCreate,
    db: AsyncSession = Depends(get_db),
) -> ELNEntry:
    entry_number = await _next_entry_number(db)
    entry = ELNEntry(
        title=body.title,
        entry_number=entry_number,
        content_markdown=body.content_markdown,
        summary=body.summary,
        status="draft",
        experiment_id=body.experiment_id,
        author_id=body.author_id,
        embedded_figures=body.embedded_figures,
        linked_references=body.linked_references,
        tags=body.tags,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


@router.get("/", response_model=list[ELNEntryListResponse])
async def list_eln_entries(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    experiment_id: uuid.UUID | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ELNEntry]:
    stmt = select(ELNEntry).order_by(ELNEntry.created_at.desc())
    if status:
        stmt = stmt.where(ELNEntry.status == status)
    if experiment_id:
        stmt = stmt.where(ELNEntry.experiment_id == experiment_id)
    # Tag filtering via JSON contains is DB-specific; simple approach:
    if tag:
        stmt = stmt.where(ELNEntry.tags.contains([tag]))
    result = await db.execute(stmt.offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get("/{entry_id}", response_model=ELNEntryResponse)
async def get_eln_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ELNEntry:
    entry = await db.get(ELNEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ELN entry not found")
    return entry


@router.patch("/{entry_id}", response_model=ELNEntryResponse)
async def update_eln_entry(
    entry_id: uuid.UUID,
    body: ELNEntryUpdate,
    db: AsyncSession = Depends(get_db),
) -> ELNEntry:
    entry = await db.get(ELNEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ELN entry not found")
    if entry.status == "submitted":
        raise HTTPException(
            status_code=409,
            detail="Cannot edit a submitted entry. Use appendices instead.",
        )
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(entry, k, v)
    await db.flush()
    await db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
async def delete_eln_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    entry = await db.get(ELNEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ELN entry not found")
    if entry.status == "submitted":
        raise HTTPException(status_code=409, detail="Cannot delete a submitted entry")
    await db.delete(entry)


@router.post("/{entry_id}/submit", response_model=ELNEntryResponse)
async def submit_eln_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ELNEntry:
    entry = await db.get(ELNEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ELN entry not found")
    if entry.status == "submitted":
        raise HTTPException(status_code=409, detail="Entry is already submitted")
    entry.status = "submitted"
    await db.flush()
    await db.refresh(entry)
    return entry


@router.post("/{entry_id}/appendix", response_model=AppendixResponse, status_code=201)
async def add_appendix(
    entry_id: uuid.UUID,
    body: AppendixCreate,
    db: AsyncSession = Depends(get_db),
) -> ELNAppendix:
    entry = await db.get(ELNEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ELN entry not found")
    # Count existing appendices
    stmt = (
        select(func.count())
        .select_from(ELNAppendix)
        .where(ELNAppendix.eln_entry_id == entry_id)
    )
    count = await db.scalar(stmt) or 0
    appendix = ELNAppendix(
        eln_entry_id=entry_id,
        content_markdown=body.content_markdown,
        author_id=body.author_id,
        appendix_number=count + 1,
    )
    db.add(appendix)
    await db.flush()
    await db.refresh(appendix)
    return appendix


@router.post("/auto-generate", response_model=ELNEntryResponse, status_code=201)
async def auto_generate_eln_entry(
    body: ELNAutoGenerate,
    db: AsyncSession = Depends(get_db),
) -> ELNEntry:
    """Auto-generate an ELN entry from an experiment's data."""
    exp = await db.get(Experiment, body.experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Build markdown content from experiment data
    sections = []
    sections.append(f"# {exp.name}\n")
    sections.append("## Objective\n")
    sections.append(f"{exp.description or 'No description provided.'}\n")
    sections.append("## Protocol\n")
    sections.append(f"{exp.protocol or 'No protocol specified.'}\n")

    # Include plate map info
    if exp.plate_maps:
        sections.append("## Plate Maps\n")
        for pm in exp.plate_maps:
            well_count = len(pm.well_mappings) if pm.well_mappings else 0
            sections.append(f"- **{pm.name}** ({pm.plate_type}-well): {pm.description or ''} — {well_count} well mappings\n")

    # Include results
    if exp.results:
        sections.append("## Results\n")
        sections.append("| Parameter | Value |")
        sections.append("|-----------|-------|")
        for key, val in exp.results.items():
            sections.append(f"| {key} | {val} |")
        sections.append("")

    sections.append("## Conclusions\n")
    sections.append("*To be completed by the investigator.*\n")

    content = "\n".join(sections)
    summary = f"Auto-generated ELN entry for experiment: {exp.name} (status: {exp.status})"

    entry_number = await _next_entry_number(db)
    entry = ELNEntry(
        title=f"ELN — {exp.name}",
        entry_number=entry_number,
        content_markdown=content,
        summary=summary,
        status="draft",
        experiment_id=body.experiment_id,
        author_id=body.author_id,
        linked_references={"experiments": [str(body.experiment_id)]},
        tags=["auto-generated"],
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


@router.get("/{entry_id}/export/markdown")
async def export_markdown(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    entry = await db.get(ELNEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ELN entry not found")

    md = f"# {entry.title}\n\n"
    md += f"**Entry:** {entry.entry_number}  \n"
    md += f"**Status:** {entry.status}  \n"
    md += f"**Created:** {entry.created_at.isoformat() if entry.created_at else ''}  \n\n"
    md += entry.content_markdown or ""

    if entry.appendices:
        md += "\n\n---\n\n# Appendices\n\n"
        for app in entry.appendices:
            md += f"## Appendix {app.appendix_number}\n\n"
            md += f"{app.content_markdown}\n\n"

    return Response(
        content=md,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{entry.entry_number}.md"'},
    )


@router.get("/{entry_id}/export/pdf")
async def export_pdf(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    entry = await db.get(ELNEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ELN entry not found")

    try:
        import markdown as md_lib
        from weasyprint import HTML as WeasyprintHTML
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PDF export requires 'weasyprint' and 'markdown' packages. Install them with: pip install weasyprint markdown",
        )

    # Convert markdown to HTML
    md_content = entry.content_markdown or ""
    html_body = md_lib.markdown(md_content, extensions=["tables", "fenced_code"])

    # Resonantia branding CSS
    css = """
    @page { size: A4; margin: 2cm; }
    body { font-family: 'Helvetica Neue', Arial, sans-serif; color: #1a1a1a; line-height: 1.6; }
    h1 { color: #d97706; border-bottom: 2px solid #d97706; padding-bottom: 0.3em; }
    h2 { color: #92400e; margin-top: 1.5em; }
    table { border-collapse: collapse; width: 100%; margin: 1em 0; }
    th, td { border: 1px solid #d1d5db; padding: 8px 12px; text-align: left; }
    th { background-color: #fef3c7; color: #92400e; }
    code { background-color: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
    .header { text-align: center; margin-bottom: 2em; border-bottom: 3px solid #d97706; padding-bottom: 1em; }
    .header h1 { border: none; }
    .meta { color: #6b7280; font-size: 0.9em; }
    .footer { text-align: center; color: #9ca3af; font-size: 0.8em; margin-top: 3em; border-top: 1px solid #e5e7eb; padding-top: 0.5em; }
    """

    html = f"""<!DOCTYPE html>
<html><head><style>{css}</style></head><body>
<div class="header">
    <h1>Resonantia Lab Notebook</h1>
    <p class="meta"><strong>{entry.entry_number}</strong> | {entry.title}</p>
    <p class="meta">Author: {entry.author_id or 'Unknown'} | Created: {entry.created_at.strftime('%Y-%m-%d') if entry.created_at else ''} | Status: {entry.status}</p>
</div>
{html_body}
<div class="footer">Generated by Resonantia Lab &mdash; {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</div>
</body></html>"""

    pdf_bytes = WeasyprintHTML(string=html).write_pdf()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{entry.entry_number}.pdf"'},
    )
