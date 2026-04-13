"""Shared FastAPI dependencies."""

from fastapi import Request


async def get_org_context(request: Request) -> str:
    """Extract org_id from X-Org-Id header."""
    return request.headers.get("X-Org-Id", "org_default")
