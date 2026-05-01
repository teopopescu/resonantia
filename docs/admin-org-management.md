# Organization Management — Admin Guide

## Overview

Resonantia Lab uses organization-based multi-tenancy. Each client company gets their own organization with completely isolated data. Only Resonantia admins can create organizations — users can only be invited to existing ones.

## How It Works

```
Resonantia Admin creates org "Pfizer Screening" in Clerk Dashboard
    │
    ├── Invites first user (e.g. john@pfizer.com)
    │     └── John signs up → joins "Pfizer Screening" → sees only Pfizer data
    │
    └── John invites colleagues via /invite page
          └── Colleagues join same org → same isolated data
```

All data (samples, plates, experiments, ELN entries, protocols, conversations) is scoped by `org_id`. Users in "Pfizer Screening" cannot see data from "Novartis Discovery" and vice versa.

## Creating a New Organization

### Step 1: Create the organization in Clerk Dashboard

1. Go to https://dashboard.clerk.com
2. Navigate to **Organizations** in the left sidebar
3. Click **Create Organization**
4. Enter the organization name (e.g. "Pfizer Screening", "Smith Lab")
5. Note the **Organization ID** (e.g. `org_2abc123xyz`) — this becomes the `org_id` for data isolation

### Step 2: Invite the first user

Option A — Via Clerk Dashboard:
1. Open the newly created organization
2. Go to **Members** → **Invite**
3. Enter the user's email address
4. They'll receive an invitation email and join the org on sign-up

Option B — Via Resonantia Lab:
1. Sign in as an admin user who belongs to the organization
2. Go to the **Invite** page (sidebar → UserPlus icon)
3. Enter the user's email
4. They'll receive a branded Resonantia invitation email

### Step 3: User onboarding

When the invited user signs up:
1. They're automatically added to the organization
2. They see the onboarding flow (Welcome → Role → Focus Areas → Feature Tour)
3. After onboarding, they land in the lab with access to their org's data only
4. The database is seeded with demo data for their org on first access

## User Permissions Within an Organization

| Role | Can Invite Others | Can See Data | Can Modify Data |
|---|---|---|---|
| Admin (first user) | Yes | Yes | Yes |
| Member | Yes | Yes | Yes |

All members of an organization have equal access to that org's data. Role-based access control (admin vs. viewer) can be added later via Clerk's role system.

## Data Isolation

Every database table has an `org_id` column:

| Table | Isolated |
|---|---|
| `samples` | Yes — each org has its own reagent inventory |
| `plate_maps` | Yes — plate designs are org-specific |
| `experiments` | Yes — experiment results are org-specific |
| `eln_entries` | Yes — notebook entries are org-specific |
| `protocols` | Yes — protocols are org-specific |
| `conversations` | Yes — chat history is org-specific |
| `microscopy_images` | Yes — imaging data is org-specific |
| `user_profiles` | Yes — onboarding data is org-specific |

The `X-Org-Id` header is sent with every API request. The backend filters all queries by this value.

## Switching Between Organizations

If a user belongs to multiple organizations (e.g. a consultant):
- Clerk's `<OrganizationSwitcher />` component handles the UI (future)
- Switching orgs changes the `X-Org-Id` header on all API calls
- The user sees a completely different dataset

## Monitoring Organizations

### Via Clerk Dashboard
- See all organizations, their members, and invitation status
- Remove users from organizations
- Delete organizations

### Via Resonantia Backend
```bash
# List all samples for a specific org
curl -H "X-Org-Id: org_2abc123" http://localhost:8000/api/v1/samples/

# List conversations for a user in an org
curl -H "X-Org-Id: org_2abc123" "http://localhost:8000/api/v1/chat/conversations?clerk_user_id=user_xyz"
```

## Testing with "Resonantia Team"

For internal testing, seed data uses `org_id = "org_resonantia_team"`. To test:

1. Ensure your Clerk organization ID is known
2. Set it in the frontend (it's read from `useOrganization()`) 
3. Or test via curl with `-H "X-Org-Id: org_resonantia_team"`

If Clerk Organizations is not enabled yet, the system falls back to `org_id = "org_default"` — all users share the same data space.
