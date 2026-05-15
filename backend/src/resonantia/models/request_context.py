"""Verified request context derived from Clerk session claims."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RequestContext(BaseModel):
    user_id: str
    org_id: str
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    request_id: str | None = None

    def has_role(self, *roles: str) -> bool:
        normalized = {_normalize_role(role) for role in self.roles}
        return any(_normalize_role(role) in normalized for role in roles)

    def can_write(self) -> bool:
        return self.has_role("org:member", "org:admin", "org:approver")

    def can_approve(self) -> bool:
        return self.has_role("org:admin", "org:approver")


def _normalize_role(role: str) -> str:
    if role.startswith("org:"):
        return role
    return f"org:{role}"
