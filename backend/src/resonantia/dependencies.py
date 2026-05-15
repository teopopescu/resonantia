"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import HTTPException, Request

from resonantia.config import get_settings
from resonantia.models.request_context import RequestContext


async def get_org_context(request: Request) -> str:
    """Compatibility wrapper for legacy routes."""
    ctx = await get_request_context(request)
    return ctx.org_id


async def get_request_context(request: Request) -> RequestContext:
    """Verify the Clerk session token and return the application context."""
    settings = get_settings()

    if settings.demo_mode and not settings.clerk_secret_key:
        return RequestContext(
            user_id=request.headers.get("X-User-Id", "demo_user"),
            org_id=request.headers.get("X-Org-Id", "org_demo"),
            roles=_roles_from_header(request.headers.get("X-Org-Role")) or ["org:admin"],
            request_id=getattr(request.state, "request_id", None),
        )

    try:
        from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
    except ImportError as exc:  # pragma: no cover - dependency checked in CI lockfile
        raise HTTPException(status_code=500, detail="Clerk backend SDK is not installed") from exc

    if not settings.clerk_secret_key:
        raise HTTPException(status_code=500, detail="Clerk auth is not configured")

    try:
        state = authenticate_request(
            request,
            AuthenticateRequestOptions(
                secret_key=settings.clerk_secret_key,
                jwt_key=settings.clerk_jwt_key or None,
                authorized_parties=settings.clerk_authorized_parties or None,
                accepts_token=["session_token"],
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

    if not state.is_signed_in:
        reason = getattr(state, "reason", "Unauthenticated")
        raise HTTPException(status_code=401, detail=str(reason))

    payload = dict(state.payload or {})
    user_id = str(payload.get("sub") or "")
    org_id = str(payload.get("org_id") or payload.get("orgId") or payload.get("o", {}).get("id") or "")
    if not user_id or not org_id:
        raise HTTPException(status_code=401, detail="Authenticated session is missing user or organization claims")

    roles = _extract_roles(payload)
    permissions = payload.get("org_permissions") or payload.get("permissions") or []
    if isinstance(permissions, str):
        permissions = [permissions]

    return RequestContext(
        user_id=user_id,
        org_id=org_id,
        roles=roles,
        permissions=[str(p) for p in permissions],
        request_id=getattr(request.state, "request_id", None),
    )


def _extract_roles(payload: dict) -> list[str]:
    roles: list[str] = []
    raw_role = payload.get("org_role") or payload.get("role")
    if raw_role:
        roles.append(str(raw_role))
    raw_roles = payload.get("roles") or []
    if isinstance(raw_roles, str):
        raw_roles = [raw_roles]
    roles.extend(str(role) for role in raw_roles)
    return [role if role.startswith("org:") else f"org:{role}" for role in roles] or ["org:viewer"]


def _roles_from_header(value: str | None) -> list[str]:
    if not value:
        return []
    return [role.strip() if role.strip().startswith("org:") else f"org:{role.strip()}"
            for role in value.split(",") if role.strip()]
