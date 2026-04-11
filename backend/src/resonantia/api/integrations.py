"""Integration configuration and eLabFTW sync endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.config import get_settings
from resonantia.db.session import get_db

router = APIRouter()


# --- Schemas ---

class IntegrationConfigResponse(BaseModel):
    elabftw_url: str
    elabftw_api_key_set: bool  # masked — never expose the actual key


class IntegrationConfigUpdate(BaseModel):
    elabftw_url: str | None = None
    elabftw_api_key: str | None = None


class ConnectionTestResponse(BaseModel):
    status: str
    message: str
    details: dict | None = None


# --- Endpoints ---

@router.get("/config", response_model=IntegrationConfigResponse)
async def get_integration_config() -> dict:
    settings = get_settings()
    return {
        "elabftw_url": settings.elabftw_url,
        "elabftw_api_key_set": bool(settings.elabftw_api_key),
    }


@router.post("/config", response_model=IntegrationConfigResponse)
async def update_integration_config(body: IntegrationConfigUpdate) -> dict:
    """Update integration settings.

    Note: In production this would persist to a config store / database.
    For the demo, settings are read from environment variables and this
    endpoint validates but does not persist changes across restarts.
    """
    settings = get_settings()
    if body.elabftw_url is not None:
        settings.elabftw_url = body.elabftw_url
    if body.elabftw_api_key is not None:
        settings.elabftw_api_key = body.elabftw_api_key
    return {
        "elabftw_url": settings.elabftw_url,
        "elabftw_api_key_set": bool(settings.elabftw_api_key),
    }


@router.post("/elabftw/test", response_model=ConnectionTestResponse)
async def test_elabftw_connection() -> dict:
    """Test the eLabFTW connection with current credentials."""
    settings = get_settings()
    if not settings.elabftw_url or not settings.elabftw_api_key:
        return {
            "status": "error",
            "message": "eLabFTW is not configured. Set elabftw_url and elabftw_api_key first.",
            "details": None,
        }
    try:
        from resonantia.services.integrations.elabftw import ELabFTWClient

        client = ELabFTWClient()
        info = await client.test_connection()
        return {
            "status": "ok",
            "message": "Successfully connected to eLabFTW",
            "details": info,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection failed: {str(e)}",
            "details": None,
        }


@router.post("/elabftw/push/{eln_entry_id}", response_model=ConnectionTestResponse)
async def push_to_elabftw(
    eln_entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Push an ELN entry to eLabFTW."""
    try:
        from resonantia.services.integrations.elabftw import push_eln_entry

        result = await push_eln_entry(str(eln_entry_id))
        return {
            "status": "ok",
            "message": f"Successfully pushed entry to eLabFTW",
            "details": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        return {
            "status": "error",
            "message": f"Push failed: {str(e)}",
            "details": None,
        }
