"""eLabFTW integration client.

Supports pushing ELN entries to eLabFTW and pulling experiments back.
Requires elabftw_url and elabftw_api_key to be configured in Settings.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from resonantia.config import get_settings

logger = logging.getLogger(__name__)


class ELabFTWClient:
    """Thin wrapper around the eLabFTW REST API v2."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.elabftw_url).rstrip("/")
        self.api_key = api_key or settings.elabftw_api_key
        if not self.base_url or not self.api_key:
            raise ValueError(
                "eLabFTW integration is not configured. Set elabftw_url and elabftw_api_key."
            )
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    async def test_connection(self) -> dict[str, Any]:
        """Test the connection to eLabFTW by fetching the API info."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{self.base_url}/api/v2/info",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def push_experiment(
        self,
        title: str,
        body_html: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create an experiment in eLabFTW."""
        payload: dict[str, Any] = {
            "title": title,
            "body": body_html,
        }
        if tags:
            payload["tags"] = tags

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/api/v2/experiments",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def pull_experiment(self, experiment_id: int) -> dict[str, Any]:
        """Pull an experiment from eLabFTW."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{self.base_url}/api/v2/experiments/{experiment_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()


async def push_eln_entry(
    entry_id: str,
    elabftw_url: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Push a Resonantia ELN entry to eLabFTW."""
    from resonantia.db.session import async_session_factory
    from resonantia.models.eln_entry import ELNEntry

    async with async_session_factory() as session:
        import uuid as _uuid
        entry = await session.get(ELNEntry, _uuid.UUID(entry_id))
        if not entry:
            raise ValueError(f"ELN entry {entry_id} not found")

        # Convert markdown to HTML
        try:
            import markdown
            body_html = markdown.markdown(
                entry.content_markdown or "",
                extensions=["tables", "fenced_code"],
            )
        except ImportError:
            body_html = f"<pre>{entry.content_markdown or ''}</pre>"

        client = ELabFTWClient(base_url=elabftw_url, api_key=api_key)
        result = await client.push_experiment(
            title=f"[{entry.entry_number}] {entry.title}",
            body_html=body_html,
            tags=entry.tags,
        )
        logger.info("Pushed ELN entry %s to eLabFTW", entry.entry_number)
        return result


async def pull_from_elabftw(
    elabftw_url: str | None = None,
    api_key: str | None = None,
    experiment_id: int = 0,
) -> dict[str, Any]:
    """Pull an experiment from eLabFTW and return it as a dict suitable for creating an ELN entry."""
    client = ELabFTWClient(base_url=elabftw_url, api_key=api_key)
    data = await client.pull_experiment(experiment_id)

    return {
        "title": data.get("title", "Imported from eLabFTW"),
        "content_markdown": data.get("body", ""),
        "tags": data.get("tags", []),
        "source": "elabftw",
        "elabftw_id": experiment_id,
    }
