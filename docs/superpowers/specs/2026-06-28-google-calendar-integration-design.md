# Google Calendar Integration — Layer 4A Design

## Overview

Each professional links their own Google Calendar via OAuth 2.0 consent flow. On appointment create/update/cancel the system automatically syncs the corresponding Google Calendar event. Token refresh is handled transparently.

## Data Model

### New: ProfessionalIntegration

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer, PK, auto-increment | |
| `professional_id` | Integer, FK → users.id, unique, not null | One row per pro |
| `provider` | String(50), not null | `"google_calendar"` |
| `access_token` | Text, not null | Encrypted at rest |
| `refresh_token` | Text, not null | Encrypted at rest |
| `token_expires_at` | DateTime, not null | |
| `google_email` | String(255) | Linked Google account |
| `created_at` | DateTime, server default | |
| `updated_at` | DateTime, on update | |

### Existing: appointments.google_event_id

Already present on the Appointment model (Text, nullable). Set after successful Google Calendar event creation. Null until first sync.

## OAuth Flow

### Endpoints

**`GET /api/v1/integrations/google/auth`** — requires authentication, professional role

1. Generates a random `state` parameter (stored in session/cookie for CSRF protection)
2. Redirects to Google's OAuth consent URL with:
   - Scopes: `https://www.googleapis.com/auth/calendar.events`
   - Access type: `offline` (to receive refresh_token)
   - Response type: `code`
3. Returns 302 redirect

**`GET /api/v1/integrations/google/callback`**

1. Validates `state` parameter
2. Exchanges `code` for `access_token` + `refresh_token` via Google's token endpoint
3. Upserts `ProfessionalIntegration` row for the current professional
4. Redirects to frontend success page (e.g., `/dashboard/integrations?google=connected`)

### Token Refresh

Before every Google Calendar API call, the service checks `token_expires_at`. If expired or within 5 minutes:
1. POST to `https://oauth2.googleapis.com/token` with `refresh_token` and `client_id`/`client_secret`
2. Update `access_token` and `token_expires_at` in DB
3. If refresh fails (revoked token) → set a `stale` flag on `ProfessionalIntegration`, surface to frontend, skip sync

## Sync Strategy

### google_calendar_service.py

```python
def create_event(db, appointment, professional_integration) -> str
def update_event(db, appointment, professional_integration) -> None
def delete_event(db, appointment, professional_integration) -> None
def ensure_sync(db, operation, appointment) -> None  # orchestrator
```

### Event Payload

- **Title**: `"{service_name} — {patient_name}"`
- **Description**: includes professional notes, patient name, appointment ID
- **Start/end**: from `appointment.start_time` / `appointment.end_time` (in event timezone using professional's timezone)
- **Virtual (`is_virtual=True`)**: Google Meet link auto-added via `conferenceData`
- **In-person**: `appointment.location` (set during booking) included as event `location`
- **Reminders**: 30-minute email + 10-minute popup default

### Trigger Points (in appointment_service.py)

All via `BackgroundTasks` after DB commit:

| Appointment action | Sync operation |
|-------------------|----------------|
| `create` → `scheduled` | `create_event` |
| `confirm` → `confirmed` | `create_event` (if no `google_event_id`) or `update_event` |
| `cancel` → `cancelled` | `delete_event` |
| Professional reschedules | `update_event` (future) |

### Error Handling

- Failures are logged at `ERROR` level with the exception and appointment ID
- The appointment transaction is already committed — never rolled back due to Google API failure
- No automatic retry in v1
- Professional's integration marked `stale` if token refresh fails

### Configuration

New settings in `app/core/config.py`:

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CLIENT_ID` | Already exists |
| `GOOGLE_CLIENT_SECRET` | Already exists |
| `GOOGLE_REDIRECT_URI` | New: full callback URL, e.g. `https://api.airmed.app/v1/integrations/google/callback` |
| `GOOGLE_CALENDAR_ENABLED` | New: feature flag, default True |

## Testing

### Unit Tests (`tests/test_google_calendar.py`)
- `test_create_event_ok` — mocked Google API response, verifies `google_event_id` set
- `test_update_event_ok` — mocked update, verifies no error
- `test_delete_event_ok` — mocked delete, verifies no error
- `test_token_refresh_before_api_call` — mock the refresh endpoint then verify subsequent API call uses new token
- `test_token_refresh_failure_marks_stale` — refresh returns 400, integration marked stale, sync skipped
- `test_api_failure_does_not_rollback` — API throws, appointment still committed
- `test_virtual_event_includes_meet` — conferenceData in payload
- `test_in_person_event_includes_location` — address in payload

### Integration Tests (`tests/test_integrations.py`)
- `test_auth_endpoint_redirects_to_google` — 302 with correct URL
- `test_callback_exchanges_code_and_stores_tokens` — mocked token endpoint
- `test_callback_validates_state` — wrong state returns 400
- `test_sync_without_integration_returns_skip` — professional not linked, sync skipped gracefully
- `test_create_appointment_triggers_background_sync` — verify `BackgroundTasks.add_task` called
- `test_cancel_appointment_triggers_delete_sync` — same for cancel

No real Google API calls — all mocked via `httpx.MockTransport`.

## Files to Create

| File | Purpose |
|------|---------|
| `app/models/integration.py` | `ProfessionalIntegration` model |
| `app/schemas/integration.py` | Pydantic schemas |
| `app/services/google_calendar_service.py` | Calendar CRUD + token refresh |
| `app/services/integration_service.py` | Integration CRUD + OAuth token exchange |
| `app/api/v1/endpoints/integrations.py` | OAuth endpoints |
| `tests/test_google_calendar.py` | Unit tests |
| `tests/test_integrations.py` | Integration tests |

## Files to Modify

| File | Change |
|------|--------|
| `app/models/__init__.py` | Add Integration import |
| `app/core/config.py` | Add `GOOGLE_REDIRECT_URI`, `GOOGLE_CALENDAR_ENABLED` |
| `app/api/v1/__init__.py` | Add integrations router |
| `app/services/appointment_service.py` | Add BackgroundTasks param + sync call |
| `app/schemas/appointment.py` | No changes needed (`google_event_id` already exposed) |
