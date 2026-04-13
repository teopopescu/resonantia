# Feature Requests, A/B Testing, Org API Keys & Graceful Degradation — Plan

---

## 1. Feature Request Notifications

### Options Evaluated

| Service | Free Tier | Cost After | Complexity |
|---|---|---|---|
| **AWS SES** | 3,000 emails/month (12 months) | $0.10/1,000 emails | Low — already on AWS |
| **Resend** | 3,000 emails/month (forever) | $20/month for 50K | Low — simple REST API |
| **SendGrid** | 100 emails/day | $20/month for 50K | Medium |

### Recommendation: AWS SES

We're already deploying on AWS. SES is practically free ($0.0001/email), no separate account needed, and works directly from the backend. For the volume we'll have (maybe 10-50 feature requests/month), cost is negligible.

### Implementation

**Backend:**
- New model: `FeatureRequest` (id, name, email, role, description, priority, org_id, status, created_at)
- `POST /api/v1/feature-requests` — validates input, saves to DB, sends email via SES (boto3)
- `GET /api/v1/feature-requests` — admin-only listing
- Config: `aws_ses_sender_email`, `feature_request_notify_email`

**Frontend:**
- Update `/feature-request/page.tsx` to POST to backend
- Show loading state while submitting, error state if fails

**Email format:** Simple HTML with feature details, priority badge, requester info. Uses Resonantia branding.

### Effort: Half day

---

## 2. A/B Testing — Feature Flags per Organization

### Options Evaluated

| Tool | Type | A/B Testing | Org Targeting | SDK (Python + React) | Self-Hosted | Cost |
|---|---|---|---|---|---|---|
| **GrowthBook** | Open source | Full (Bayesian, CUPED, Sequential) | Yes (attributes) | Python + React/Next.js | Docker Compose | Free (MIT) |
| **Unleash** | Open source | Basic (gradual rollout) | Enterprise only | Python + React | Docker + Postgres | Free (Apache-2.0), Enterprise paid |
| **Flipt** | Open source | No | No | Go, limited others | Single binary | Free, Pro $200/month |
| **AWS AppConfig** | Managed | Gradual rollout only | Not natively | Python (boto3) | N/A (managed) | Pay-per-retrieval |
| **Custom DB table** | DIY | No | Yes (by design) | N/A | N/A | Free |

### Recommendation: GrowthBook

**Why GrowthBook over the alternatives:**

1. **Full A/B testing with statistical analysis** — Bayesian engine, CUPED variance reduction, sequential testing, SRM checks. Unleash only does basic rollouts. Flipt has no A/B testing. AppConfig only does gradual deploys.

2. **Organization-level targeting** — supports custom attributes (we pass `org_id` as an attribute), so we can enable features per org. Unleash needs Enterprise for this.

3. **React + Next.js SDK** — first-class `@growthbook/growthbook-react` with `useFeatureIsOn()` hook. Works with our SSR/CSR hybrid.

4. **Python SDK** — `growthbook` Python package for backend feature checks (guard API endpoints too, not just UI).

5. **Self-hosted via Docker** — runs alongside our stack. No external dependency. MIT licensed.

6. **Experiment analytics** — connects to our PostgreSQL for experiment results. We can measure whether a feature flag change actually improved outcomes.

### Architecture

```
┌─────────────────────────────────────────────┐
│              GrowthBook Server               │
│         (Docker container in our stack)       │
│                                               │
│  Dashboard: http://localhost:3100             │
│  API: http://growthbook:3100/api              │
│                                               │
│  Features:                                    │
│    voice_mode: ON for org_resonantia_team     │
│    benchling_integration: OFF (coming soon)   │
│    eln_pdf_export: ON for all                 │
│    gpt4o_mini: ON for org_pfizer (cost test)  │
│                                               │
│  Experiments:                                 │
│    "IC50 display format" — A: table, B: chart │
│    "Voice VAD threshold" — A: 1.5s, B: 2.0s  │
└─────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌─────────────────┐
│  Backend (Python) │      │ Frontend (React) │
│  from growthbook  │      │ @growthbook/     │
│  import GrowthBook│      │ growthbook-react │
│                   │      │                  │
│  gb.is_on("voice")│      │ useFeatureIsOn() │
│  gb.get_value(    │      │ useFeatureValue() │
│    "model",       │      │                  │
│    "gpt-4o"       │      │ <IfFeatureEnabled│
│  )                │      │   feature="voice" │
│                   │      │ >                 │
└─────────────────┘      └─────────────────┘
```

### Docker Setup

Add to docker-compose.yml:

```yaml
growthbook:
  image: growthbook/growthbook:latest
  ports:
    - "3100:3000"
    - "3101:3100"  # API
  environment:
    MONGODB_URI: mongodb://growthbook-mongo:27017/growthbook
    APP_ORIGIN: http://localhost:3100
    API_HOST: http://localhost:3101
  depends_on:
    - growthbook-mongo

growthbook-mongo:
  image: mongo:7
  volumes:
    - growthbook_mongo_data:/data/db
```

### Feature Flags We'd Create

| Flag | Type | Default | Description |
|---|---|---|---|
| `voice_mode` | Boolean | ON | Voice mode in chat |
| `eln_notebook` | Boolean | ON | ELN tab |
| `protocol_builder` | Boolean | ON | Protocols tab |
| `eln_pdf_export` | Boolean | ON | PDF export from ELN |
| `benchling_integration` | Boolean | OFF | Benchling card in settings |
| `dotmatics_integration` | Boolean | OFF | Dotmatics card in settings |
| `file_analysis` | Boolean | ON | Agent reads uploaded files |
| `llm_model` | String | "gpt-4o" | Which model to use per org |
| `vad_silence_threshold` | Number | 1500 | VAD silence duration in ms |

### Frontend Integration

```typescript
// In _app or layout:
import { GrowthBook, GrowthBookProvider } from "@growthbook/growthbook-react";

const gb = new GrowthBook({
  apiHost: "http://localhost:3101",
  clientKey: "sdk-xxx",
  attributes: {
    org_id: activeOrgId,
    user_id: clerkUserId,
  },
});

// In components:
import { useFeatureIsOn } from "@growthbook/growthbook-react";

function ChatToolbar() {
  const voiceEnabled = useFeatureIsOn("voice_mode");
  return (
    <>
      {voiceEnabled && <MicButton />}
    </>
  );
}
```

### Backend Integration

```python
# In agent.py or any service:
from growthbook import GrowthBook

gb = GrowthBook(
    api_host="http://growthbook:3100",
    client_key="sdk-xxx",
)
gb.set_attributes({"org_id": org_id, "user_id": clerk_user_id})

model = gb.get_feature_value("llm_model", "gpt-4o")
client = AsyncOpenAI(api_key=settings.openai_api_key)
response = await client.chat.completions.create(model=model, ...)
```

### Files to create/modify
- `docker-compose.yml` — add GrowthBook + MongoDB containers
- `backend/pyproject.toml` — add `growthbook` Python SDK
- `frontend/package.json` — add `@growthbook/growthbook-react`
- `frontend/src/app/lab/layout.tsx` — GrowthBookProvider wrapper
- `backend/src/resonantia/services/feature_flags.py` — Python GrowthBook client
- All feature components — wrap in `useFeatureIsOn()` checks

### Effort: 1-2 days

---

## 3. Organization-Level OpenAI API Keys with Platform Key Access Control

### Problem
- Clients should be able to use their own OpenAI API keys (for cost allocation and data residency)
- Resonantia admins must control which orgs can use the Resonantia platform key vs which must bring their own
- Default: new orgs must bring their own key. Resonantia admins manually grant platform key access for internal team, design partners, or free trials.

### Data Model

```
org_api_config table:
- id (UUID PK)
- org_id (String, unique, indexed)
- platform_key_allowed (Boolean, default False)   ← admin-controlled: can this org use our key?
- own_key_encrypted (String, nullable)             ← org's own OpenAI key (Fernet encrypted)
- model_override (String, nullable)                ← org can choose gpt-4o vs gpt-4o-mini
- created_at, updated_at
```

### Three States per Organization

| `platform_key_allowed` | Own key set | Behaviour |
|---|---|---|
| `True` | No | Uses Resonantia platform key — we pay (internal team, design partners, free trials) |
| `True` | Yes | Uses org's key — they pay. Falls back to platform key if theirs fails |
| `False` | No | **AI chat disabled** — "Add your OpenAI API key in Settings to enable AI features." All non-AI features still work. |
| `False` | Yes | Uses org's key — they pay. No fallback to platform key |

### Who Controls What

| Setting | Controlled by | How |
|---|---|---|
| `platform_key_allowed` | Resonantia admin only | Admin API (`PUT /api/v1/admin/orgs/{org_id}/platform-key`) or direct DB |
| `own_key_encrypted` | Org admin (client) | Settings page UI |
| `model_override` | Org admin (client) | Settings page UI |

Clients **never see** the `platform_key_allowed` toggle. They only see whether AI is available or whether they need to add a key.

### Encryption

```python
from cryptography.fernet import Fernet
from resonantia.config import get_settings

def encrypt(plaintext: str) -> str:
    f = Fernet(get_settings().encryption_key.encode())
    return f.encrypt(plaintext.encode()).decode()

def decrypt(ciphertext: str) -> str:
    f = Fernet(get_settings().encryption_key.encode())
    return f.decrypt(ciphertext.encode()).decode()
```

Config: `encryption_key: str = ""` — set via `ENCRYPTION_KEY` env var, generated with `Fernet.generate_key()`.

### API

**Client-facing (org admins):**
```
GET    /api/v1/settings/api-keys           — check if org has key (masked: sk-...xxxx) + whether platform key is available
POST   /api/v1/settings/api-keys           — set/update org's own OpenAI key
DELETE /api/v1/settings/api-keys           — remove org key (falls back to platform key if allowed, otherwise disables AI)
POST   /api/v1/settings/api-keys/test      — test the key with a minimal OpenAI call
```

**Admin-only (Resonantia team):**
```
GET    /api/v1/admin/orgs                          — list all orgs with their key status
PUT    /api/v1/admin/orgs/{org_id}/platform-key    — enable/disable platform key access for an org
```

### Agent Integration

```python
async def _get_client_for_org(org_id: str) -> tuple[AsyncOpenAI | None, str]:
    """Get OpenAI client for an org. Returns (client, source)."""
    config = await get_org_api_config(org_id)
    
    # Priority 1: org's own key
    if config and config.own_key_encrypted:
        try:
            key = decrypt(config.own_key_encrypted)
            model = config.model_override or get_settings().llm_model
            return AsyncOpenAI(api_key=key), model
        except Exception:
            pass  # key invalid, try fallback
    
    # Priority 2: platform key (only if allowed)
    if config and config.platform_key_allowed:
        settings = get_settings()
        if settings.openai_api_key:
            return AsyncOpenAI(api_key=settings.openai_api_key), settings.llm_model
    
    # Priority 3: platform key allowed by default for unconfigured orgs? No.
    # New orgs must bring their own key unless admin grants platform access.
    return None, ""
```

In `agent.py chat()`:
```python
client, model = await _get_client_for_org(org_id)
if client is None:
    return {
        "message": "AI chat requires an OpenAI API key. Add yours in Settings → API Configuration.\n\n"
                   "All other features (plate mapping, samples, protocols, processing) work without it.",
        "conversation_id": cid,
        "error_type": "no_api_key",
    }
```

### Settings UI — What the Client Sees

**Case 1: `platform_key_allowed = False`, no own key (default for new orgs)**
```
┌─────────────────────────────────────────────────┐
│ API Configuration                                │
│                                                   │
│ ⚠ AI chat requires an OpenAI API key.            │
│   Add your key below to enable the chat           │
│   assistant and voice mode.                       │
│                                                   │
│ OpenAI API Key: [________________________] [Save] │
│ Model: [gpt-4o            ▼]                      │
│ [Test Connection]                                  │
│                                                   │
│ ℹ All other features (plates, samples,            │
│   protocols) work without an API key.             │
└─────────────────────────────────────────────────┘
```

**Case 2: `platform_key_allowed = True`, no own key (internal/partner orgs)**
```
┌─────────────────────────────────────────────────┐
│ API Configuration                                │
│                                                   │
│ ✓ Using Resonantia platform AI                    │
│                                                   │
│ Optionally add your own OpenAI API key            │
│ for dedicated capacity:                           │
│                                                   │
│ OpenAI API Key: [________________________] [Save] │
│ Model: [gpt-4o            ▼]                      │
│ [Test Connection]                                  │
│                                                   │
│ ℹ Using your own key means OpenAI bills your      │
│   account directly. Remove to use platform key.   │
└─────────────────────────────────────────────────┘
```

**Case 3: Own key set (regardless of platform_key_allowed)**
```
┌─────────────────────────────────────────────────┐
│ API Configuration                                │
│                                                   │
│ ✓ Connected — using your API key                  │
│                                                   │
│ OpenAI API Key: sk-Cknz...T3Bl  [Change] [Remove]│
│ Model: gpt-4o ▼                                   │
│ [Test Connection] ✓ Valid                          │
│                                                   │
│ ℹ OpenAI bills your account directly.             │
│   Remove to use the Resonantia platform key.      │
└─────────────────────────────────────────────────┘
```

### Default for New Organizations

| Org Type | `platform_key_allowed` | Rationale |
|---|---|---|
| Resonantia Internal Team | `True` | Internal testing |
| Design partner (free pilot) | `True` | We subsidise to get feedback |
| Free trial org | `True` (time-limited) | 7-day trial, then must add own key |
| Paying customer | `False` | They bring their own key, we don't pay for their AI usage |

### Voice Mode Integration

The same client resolution applies to voice:
```python
# In voice.py:
client, model = await _get_client_for_org(org_id)
if client is None:
    raise HTTPException(400, "OpenAI API key required for voice mode. Add in Settings.")

# Use client for both Whisper STT and TTS
transcription = await client.audio.transcriptions.create(model="whisper-1", file=f)
tts_response = await client.audio.speech.create(model="tts-1", voice="nova", input=text)
```

### Files to create/modify
- `backend/src/resonantia/models/org_api_config.py` — new model
- `backend/src/resonantia/services/encryption.py` — Fernet encrypt/decrypt
- `backend/src/resonantia/services/org_keys.py` — get_org_api_config, get_client_for_org
- `backend/src/resonantia/api/settings_api.py` — client-facing key management
- `backend/src/resonantia/api/admin.py` — admin-only org management
- `backend/src/resonantia/api/router.py` — register both routers
- `backend/src/resonantia/services/agent.py` — use org-specific client
- `backend/src/resonantia/api/voice.py` — use org-specific client for STT/TTS
- `backend/src/resonantia/config.py` — add encryption_key
- `backend/pyproject.toml` — add `cryptography`
- `frontend/src/app/lab/settings/page.tsx` — add API Configuration section with all 3 states

### Effort: 1-2 days

---

## 4. Graceful Degradation

### Error Handling in Agent

```python
import asyncio
from openai import RateLimitError, APIError, AuthenticationError, APIConnectionError

MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 8]  # exponential backoff

for attempt in range(MAX_RETRIES):
    try:
        response = await client.chat.completions.create(**kwargs)
        break
    except RateLimitError:
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(RETRY_DELAYS[attempt])
            continue
        return degraded_response("rate_limit",
            "The AI service is temporarily busy. All lab tools still work — "
            "try again in a minute, or use the sidebar tabs directly.")
    except APIError as e:
        if "insufficient_quota" in str(e):
            return degraded_response("quota_exhausted",
                "OpenAI API quota exhausted. You can:\n"
                "- Wait for quota to reset\n"
                "- Add your own API key in Settings\n\n"
                "All lab tools (plates, samples, processing) still work.")
        raise
    except AuthenticationError:
        return degraded_response("auth_error",
            "Invalid API key. Check Settings → API Configuration.")
    except APIConnectionError:
        return degraded_response("connection_error",
            "Cannot reach the AI service. Check your internet connection.")
```

### Response Format

```python
def degraded_response(error_type: str, message: str) -> dict:
    return {
        "message": message,
        "conversation_id": cid,
        "tool_calls": None,
        "error_type": error_type,  # frontend uses this for specific UI
    }
```

### Frontend Error UI

| Error Type | Banner Color | Message | Action |
|---|---|---|---|
| `rate_limit` | Amber | "AI is busy — retrying..." | Auto-retry countdown |
| `quota_exhausted` | Red | "AI quota exhausted" | Link to Settings → API Keys |
| `auth_error` | Red | "Invalid API key" | Link to Settings → API Keys |
| `connection_error` | Amber | "Connection error" | Retry button |

Key principle: the banner says **"All lab tools still work"** and highlights the sidebar tabs.

For voice mode: if a quota/auth error occurs, exit voice mode automatically and show the error in the chat.

### Effort: Half day

---

## Implementation Order

```
Phase 1 (Day 1):
├── Graceful degradation — retry logic + error UI (high impact, small effort)
└── Feature request notifications — AWS SES + DB storage (quick win)

Phase 2 (Days 2-3):
├── GrowthBook setup — Docker container, SDKs, initial flags
├── Wrap existing features in flag checks
└── Test: enable voice_mode for one org, disable for another

Phase 3 (Days 3-4):
├── Org-level API keys — encrypted storage, Settings UI
├── Agent uses org-specific client
└── Test: org uses own key, platform key as fallback
```

---

## Updated Architecture

```
docker-compose.yml services:

Infrastructure:
  postgres          — Primary database
  redis             — Tool registry, caching
  temporal          — Workflow orchestration
  temporal-ui       — Workflow monitoring
  temporal-postgres — Temporal database

Application:
  backend           — FastAPI API server
  temporal-worker   — Temporal workflow worker
  frontend          — Next.js application

New:
  growthbook        — Feature flags + A/B testing dashboard
  growthbook-mongo  — GrowthBook data store

Total: 10 containers
```

---

## Cost Summary

| Service | Free Tier | Ongoing Cost |
|---|---|---|
| AWS SES | 3,000 emails/month (12 months) | $0.10/1,000 emails |
| GrowthBook | Free (self-hosted, MIT) | $0 (just Docker resources) |
| Fernet encryption | Built into Python `cryptography` | $0 |
| OpenAI retry logic | N/A | $0 |
| **Total** | **$0** | **~$0.01/month** |
