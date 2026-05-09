# SPEC: Org Admin + Basic Roles

**ID:** P3.3
**Phase:** 3 — Design Partner Hardening
**Branch:** `feat/org-admin-roles`
**Priority:** P2
**Effort:** 4 days
**Dependencies:** Phase 0 complete

---

## Problem Statement

Currently all org members have identical permissions. Labs need at minimum: an admin who manages the org, members who do lab work, and viewers who can see results but not modify data.

---

## Scope

### In Scope
- 3 roles only: admin, member, viewer (not full RBAC)
- Permission middleware on API routes
- Clerk org metadata → backend role mapping
- Settings page: org members with role display

### Out of Scope
- Custom roles
- Per-entity permissions
- Role hierarchy beyond 3 levels
- SAML/SSO (deferred)

---

## Architecture

### Role Permissions

| Permission | Admin | Member | Viewer |
|-----------|-------|--------|--------|
| Read all data | Yes | Yes | Yes |
| Create/edit samples, plates, experiments | Yes | Yes | No |
| Create/edit ELN entries | Yes | Yes | No |
| Submit ELN entries | Yes | Yes | No |
| Use agent chat | Yes | Yes | Yes (read-only tools) |
| Manage org members | Yes | No | No |
| Change org settings | Yes | No | No |
| View audit log | Yes | Yes | Yes |
| Export data | Yes | Yes | No |

### Permission Check

```python
# backend/src/resonantia/api/dependencies.py

async def require_role(min_role: str):
    async def check(org_context: OrgContext = Depends(get_org_context)):
        member = await get_org_member(org_context.org_id, org_context.user_id)
        if not has_permission(member.role, min_role):
            raise HTTPException(403, "Insufficient permissions")
        return org_context
    return check

# Usage:
@router.post("/samples", dependencies=[Depends(require_role("member"))])
async def create_sample(...): ...
```

---

## Acceptance Criteria

- [ ] 3 roles defined: admin, member, viewer
- [ ] Viewer cannot create/modify/delete any data — API returns 403
- [ ] Member can CRUD all lab data
- [ ] Admin can manage org members and settings
- [ ] Clerk org membership maps to backend role
- [ ] Settings page shows org members with their roles
- [ ] Admin can change member roles in settings UI
- [ ] All mutating API endpoints check for minimum required role
- [ ] Test: viewer attempts create sample → 403
- [ ] Test: member creates sample → 200
