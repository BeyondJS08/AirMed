# Google Calendar Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow professionals to link their Google Calendar via OAuth and auto-sync appointments as calendar events.

**Architecture:** Each professional authenticates with Google OAuth 2.0 (`calendar.events` scope). Tokens stored in a new `ProfessionalIntegration` table. A `google_calendar_service.py` wraps the Google Calendar v3 API (create/update/delete events). Appointment service calls calendar sync via `BackgroundTasks` after DB commit. All Google API calls mocked in tests.

**Tech Stack:** FastAPI, SQLAlchemy, httpx, Google Calendar v3 API, alembic

---

### File Structure

**Create:**
- `app/models/integration.py` — ProfessionalIntegration model
- `app/schemas/integration.py` — Pydantic schemas
- `app/services/integration_service.py` — Integration CRUD
- `app/services/google_calendar_service.py` — Google Calendar API CRUD + token refresh
- `app/api/v1/endpoints/integrations.py` — OAuth endpoints (GET auth + POST tokens)
- `tests/test_google_calendar.py` — Unit tests for calendar sync service
- `tests/test_integrations.py` — API tests for endpoints & service

**Modify:**
- `app/models/__init__.py` — Add ProfessionalIntegration import
- `app/core/config.py` — Add GOOGLE_REDIRECT_URI, GOOGLE_CALENDAR_ENABLED
- `app/api/v1/__init__.py` — Add integrations router
- `app/services/appointment_service.py` — Accept BackgroundTasks, call sync fn

---

### Task 1: Config, Model, Schema

**Files:**
- Create: `app/models/integration.py`
- Create: `app/schemas/integration.py`
- Modify: `app/models/__init__.py`
- Modify: `app/core/config.py`

- [ ] **Step 1: Add config vars in `app/core/config.py`**

```python
# After REDIS_URL: str | None = None, add:
    GOOGLE_REDIRECT_URI: str | None = None
    GOOGLE_CALENDAR_ENABLED: bool = True
```

- [ ] **Step 2: Create the model `app/models/integration.py`**

```python
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class ProfessionalIntegration(Base):
    __tablename__ = "professional_integrations"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    provider = Column(String(50), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime, nullable=False)
    google_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
```

- [ ] **Step 3: Register model in `app/models/__init__.py`**

```python
# Add line:
from app.models.integration import ProfessionalIntegration
```

- [ ] **Step 4: Create the schema `app/schemas/integration.py`**

```python
from datetime import datetime

from pydantic import BaseModel


class ProfessionalIntegrationOut(BaseModel):
    id: int
    professional_id: int
    provider: str
    google_email: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Verify model fields**

Run: `python -c "from app.models.integration import ProfessionalIntegration; print([c.name for c in ProfessionalIntegration.__table__.columns])"`
Expected: no import error, columns printed

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: add ProfessionalIntegration model, schema, config"
```

---

### Task 2: Alembic Migration

**Files:**
- Create: `alembic/versions/xxxx_add_professional_integrations_table.py`

- [ ] **Step 1: Generate migration**

```bash
alembic revision --autogenerate -m "add professional_integrations table"
```

- [ ] **Step 2: Review generated file, then apply**

```bash
alembic upgrade head
```

- [ ] **Step 3: Verify**

```bash
psql -h localhost -U postgres -d airmed_test -c "\dt professional_integrations"
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add professional_integrations migration"
```

---

### Task 3: Integration Service

**Files:**
- Create: `app/services/integration_service.py`

- [ ] **Step 1: Write service `app/services/integration_service.py`**

```python
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.integration import ProfessionalIntegration


def get_integration(
    db: Session,
    professional_id: int,
    provider: str = "google_calendar",
) -> ProfessionalIntegration | None:
    return db.query(ProfessionalIntegration).filter(
        ProfessionalIntegration.professional_id == professional_id,
        ProfessionalIntegration.provider == provider,
    ).first()


def upsert_integration(
    db: Session,
    professional_id: int,
    provider: str,
    access_token: str,
    refresh_token: str,
    token_expires_at: datetime,
    google_email: str | None = None,
) -> ProfessionalIntegration:
    existing = get_integration(db, professional_id, provider)
    if existing:
        existing.access_token = access_token
        existing.refresh_token = refresh_token
        existing.token_expires_at = token_expires_at
        if google_email is not None:
            existing.google_email = google_email
    else:
        existing = ProfessionalIntegration(
            professional_id=professional_id,
            provider=provider,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            google_email=google_email,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def delete_integration(db: Session, professional_id: int, provider: str = "google_calendar") -> None:
    integration = get_integration(db, professional_id, provider)
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    db.delete(integration)
    db.commit()


def get_or_none(db: Session, professional_id: int, provider: str = "google_calendar") -> ProfessionalIntegration | None:
    return get_integration(db, professional_id, provider)
```

- [ ] **Step 2: Test the service inline**

Run: `python -c "from app.services.integration_service import get_integration, upsert_integration, delete_integration; print('OK')"`
Expected: OK (no import errors)

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: add integration CRUD service"
```

---

### Task 4: Google Calendar Sync Service

**Files:**
- Create: `app/services/google_calendar_service.py`

- [ ] **Step 1: Write `app/services/google_calendar_service.py`**

```python
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.integration import ProfessionalIntegration
from app.services.integration_service import get_integration, upsert_integration

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"


def _refresh_access_token(integration: ProfessionalIntegration) -> dict:
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": integration.refresh_token,
        "grant_type": "refresh_token",
    }
    with httpx.Client() as client:
        resp = client.post(GOOGLE_TOKEN_URL, data=payload)
        if resp.status_code != 200:
            logger.error("Token refresh failed: %s %s", resp.status_code, resp.text)
            raise RuntimeError("Failed to refresh Google token")
        return resp.json()


def _ensure_valid_token(db: Session, integration: ProfessionalIntegration) -> None:
    now = datetime.now(timezone.utc)
    expires = (
        integration.token_expires_at.replace(tzinfo=timezone.utc)
        if integration.token_expires_at.tzinfo is None
        else integration.token_expires_at
    )
    if expires - now > timedelta(minutes=5):
        return
    token_data = _refresh_access_token(integration)
    new_expiry = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
    upsert_integration(
        db,
        professional_id=integration.professional_id,
        provider=integration.provider,
        access_token=token_data["access_token"],
        refresh_token=integration.refresh_token,
        token_expires_at=new_expiry,
    )
    integration.access_token = token_data["access_token"]
    integration.token_expires_at = new_expiry


def _call_api(method: str, endpoint: str, access_token: str, body: dict | None = None) -> dict:
    url = f"{GOOGLE_CALENDAR_API}/{endpoint}"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    with httpx.Client() as client:
        resp = client.request(method, url, headers=headers, json=body)
        if resp.status_code >= 400:
            logger.error("Google Calendar API error: %s %s", resp.status_code, resp.text)
            resp.raise_for_status()
        return resp.json() if resp.text else {}


def _build_event_body(appointment: Appointment) -> dict:
    patient_name = "Patient"
    if appointment.patient and appointment.patient.full_name:
        patient_name = appointment.patient.full_name
    service_name = "Appointment"
    if appointment.service and appointment.service.name:
        service_name = appointment.service.name

    body = {
        "summary": f"{service_name} — {patient_name}",
        "description": f"Appointment #{appointment.id}\nPatient: {patient_name}",
        "start": {"dateTime": appointment.start_time.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": appointment.end_time.isoformat(), "timeZone": "UTC"},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 30},
                {"method": "popup", "minutes": 10},
            ],
        },
    }
    if appointment.is_virtual:
        body["conferenceData"] = {
            "createRequest": {
                "requestId": f"airmed-{appointment.id}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }
    elif appointment.location:
        body["location"] = appointment.location
    return body


def create_event(db: Session, appointment: Appointment, integration: ProfessionalIntegration) -> None:
    _ensure_valid_token(db, integration)
    body = _build_event_body(appointment)
    conference_data_version = 1 if appointment.is_virtual else 0
    endpoint = f"calendars/primary/events?conferenceDataVersion={conference_data_version}"
    result = _call_api("POST", endpoint, integration.access_token, body)
    appointment.google_event_id = result["id"]
    db.commit()


def update_event(db: Session, appointment: Appointment, integration: ProfessionalIntegration) -> None:
    if not appointment.google_event_id:
        create_event(db, appointment, integration)
        return
    _ensure_valid_token(db, integration)
    body = _build_event_body(appointment)
    endpoint = f"calendars/primary/events/{appointment.google_event_id}"
    _call_api("PATCH", endpoint, integration.access_token, body)


def delete_event(db: Session, appointment: Appointment, integration: ProfessionalIntegration) -> None:
    if not appointment.google_event_id:
        return
    _ensure_valid_token(db, integration)
    endpoint = f"calendars/primary/events/{appointment.google_event_id}"
    _call_api("DELETE", endpoint, integration.access_token)


OPERATION_MAP = {
    "create": create_event,
    "update": update_event,
    "delete": delete_event,
}


def ensure_sync(db: Session, operation: str, appointment: Appointment) -> None:
    if not settings.GOOGLE_CALENDAR_ENABLED:
        return
    integration = get_integration(db, appointment.professional_id, "google_calendar")
    if not integration:
        return
    func = OPERATION_MAP.get(operation)
    if not func:
        return
    try:
        func(db, appointment, integration)
    except Exception:
        logger.exception("Google Calendar sync failed for appointment %s (operation=%s)", appointment.id, operation)
```

- [ ] **Step 2: Verify imports**

Run: `python -c "from app.services.google_calendar_service import ensure_sync, create_event, update_event, delete_event; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: add Google Calendar sync service"
```

---

### Task 5: OAuth Endpoints + Router Registration

**Files:**
- Create: `app/api/v1/endpoints/integrations.py`
- Modify: `app/api/v1/__init__.py`

**Design note:** OAuth flow uses two backend endpoints. The frontend calls `/auth` to get the Google consent URL, opens it in a popup, Google redirects to `GOOGLE_REDIRECT_URI` (a frontend page), frontend extracts the `code` and calls `/tokens` to exchange it server-side. No state management needed — the final token exchange is authenticated.

- [ ] **Step 1: Create `app/api/v1/endpoints/integrations.py`**

```python
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_professional
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.integration import ProfessionalIntegrationOut
from app.services.integration_service import get_integration, upsert_integration

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


@router.get("/google/auth")
async def google_auth(
    professional: User = Depends(get_current_professional),
):
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return {"auth_url": auth_url}


@router.post("/google/tokens")
async def google_exchange_tokens(
    code: str = Query(),
    db: Session = Depends(get_db),
    professional: User = Depends(get_current_professional),
):
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")

    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code",
            )

    token_data = resp.json()
    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        existing = get_integration(db, professional.id, "google_calendar")
        if existing and existing.refresh_token:
            refresh_token = existing.refresh_token

    from datetime import datetime, timedelta, timezone

    upsert_integration(
        db,
        professional_id=professional.id,
        provider="google_calendar",
        access_token=token_data["access_token"],
        refresh_token=refresh_token,
        token_expires_at=datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600)),
        google_email=token_data.get("email"),
    )

    return {"status": "connected"}


@router.get("/google/status", response_model=ProfessionalIntegrationOut | None)
async def google_status(
    db: Session = Depends(get_db),
    professional: User = Depends(get_current_professional),
):
    return get_integration(db, professional.id, "google_calendar")
```

- [ ] **Step 2: Register router in `app/api/v1/__init__.py`**

```python
# Add import:
from app.api.v1.endpoints import integrations

# Add line before closing:
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
```

- [ ] **Step 3: Verify imports**

Run: `python -c "from app.api.v1.endpoints.integrations import router; print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add OAuth endpoints for Google Calendar"
```

---

### Task 6: Wire Sync into Appointment Service

**Files:**
- Modify: `app/services/appointment_service.py`
- Modify: `app/api/v1/endpoints/appointments.py`

- [ ] **Step 1: Add BackgroundTasks import to appointment service**

```python
# At top of app/services/appointment_service.py, add import:
from fastapi import BackgroundTasks
```

- [ ] **Step 2: Add sync call in create_appointment after db.refresh**

```python
# After db.refresh(appt) and before return appt:
from app.services.google_calendar_service import ensure_sync
background_tasks.add_task(ensure_sync, db, "create", appt)
```

Function signature changes to accept `background_tasks: BackgroundTasks`:

```python
def create_appointment(
    db: Session,
    data: AppointmentCreate,
    current_user: User,
    background_tasks: BackgroundTasks,
) -> Appointment:
```

- [ ] **Step 3: Add sync call in update_appointment after commit**

```python
# Inside update_appointment, after db.refresh(appointment) and before return:
from app.services.google_calendar_service import ensure_sync
if data.status is not None:
    if data.status == "cancelled":
        background_tasks.add_task(ensure_sync, db, "delete", appointment)
    elif appointment.status in ("scheduled", "confirmed"):
        background_tasks.add_task(ensure_sync, db, "create" if not appointment.google_event_id else "update", appointment)
```

Function signature changes to accept `background_tasks: BackgroundTasks`:

```python
def update_appointment(
    db: Session,
    appointment: Appointment,
    data: AppointmentUpdate,
    current_user: User,
    background_tasks: BackgroundTasks,
) -> Appointment:
```

- [ ] **Step 4: Update endpoints to pass BackgroundTasks**

```python
# In app/api/v1/endpoints/appointments.py, add import:
from fastapi import BackgroundTasks

# Update endpoint signatures:
async def create_new_appointment(
    data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_appointment(db, data, current_user, background_tasks)

async def update_appointment_by_id(
    appointment_id: int,
    data: AppointmentUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ...
    return update_appointment(db, appt, data, current_user, background_tasks)
```

- [ ] **Step 5: Verify existing tests still pass**

Run: `pytest tests/test_appointment.py -v --tb=short`
Expected: All PASS (may need to update test helpers that call these functions directly)

- [ ] **Step 6: Fix test helpers if needed**

Tests call `create_appointment(db, data, current_user)` directly — need to add `BackgroundTasks()` default parameter:

```python
# In tests, either:
from fastapi import BackgroundTasks
create_appointment(db, data, user, BackgroundTasks())

# Or make background_tasks optional in the service:
def create_appointment(
    db: Session,
    data: AppointmentCreate,
    current_user: User,
    background_tasks: BackgroundTasks | None = None,
) -> Appointment:
```

Use the optional approach for backward compatibility.

- [ ] **Step 7: Run all existing tests**

Run: `pytest tests/ -v --tb=short`
Expected: All 99 PASS

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: wire Google Calendar sync into appointment service"
```

---

### Task 7: Tests

**Files:**
- Create: `tests/test_google_calendar.py` (9 tests)
- Create: `tests/test_integrations.py` (6 service tests + 6 API tests)

- [ ] **Step 1: Write tests for integration service in `tests/test_integrations.py`**

```python
"""Tests for integration service and OAuth endpoints."""
from datetime import datetime

import pytest
from fastapi import HTTPException

from app.models.integration import ProfessionalIntegration
from app.services.integration_service import (
    get_integration,
    upsert_integration,
    delete_integration,
)


def test_upsert_creates(db_session, test_professional):
    integration = upsert_integration(
        db_session, test_professional.id, "google_calendar",
        "at1", "rt1", datetime(2026, 7, 1, 0, 0, 0),
        google_email="doc@example.com",
    )
    assert integration.professional_id == test_professional.id
    assert integration.provider == "google_calendar"
    assert integration.access_token == "at1"
    assert integration.refresh_token == "rt1"
    assert integration.google_email == "doc@example.com"


def test_upsert_updates_existing(db_session, test_professional):
    upsert_integration(db_session, test_professional.id, "google_calendar", "at1", "rt1", datetime(2026, 7, 1, 0, 0, 0))
    upsert_integration(db_session, test_professional.id, "google_calendar", "at2", "rt2", datetime(2026, 8, 1, 0, 0, 0))
    rows = db_session.query(ProfessionalIntegration).all()
    assert len(rows) == 1
    assert rows[0].access_token == "at2"


def test_get_returns_none_when_missing(db_session, test_professional):
    result = get_integration(db_session, test_professional.id, "google_calendar")
    assert result is None


def test_delete_removes_integration(db_session, test_professional):
    upsert_integration(db_session, test_professional.id, "google_calendar", "at1", "rt1", datetime(2026, 7, 1, 0, 0, 0))
    delete_integration(db_session, test_professional.id, "google_calendar")
    assert get_integration(db_session, test_professional.id, "google_calendar") is None


def test_delete_raises_404_when_missing(db_session, test_professional):
    with pytest.raises(HTTPException) as exc:
        delete_integration(db_session, test_professional.id, "google_calendar")
    assert exc.value.status_code == 404


def test_integration_unique_constraint(db_session, test_professional):
    upsert_integration(db_session, test_professional.id, "google_calendar", "at1", "rt1", datetime(2026, 7, 1, 0, 0, 0))
    with pytest.raises(Exception):
        dup = ProfessionalIntegration(
            professional_id=test_professional.id,
            provider="google_calendar",
            access_token="at2",
            refresh_token="rt2",
            token_expires_at=datetime(2026, 8, 1, 0, 0, 0),
        )
        db_session.add(dup)
        db_session.commit()
```

- [ ] **Step 2: Write calendar service tests in `tests/test_google_calendar.py`**

```python
"""Tests for google_calendar_service.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.models.appointment import Appointment
from app.models.integration import ProfessionalIntegration
from app.services.integration_service import upsert_integration
from app.services.google_calendar_service import (
    _ensure_valid_token,
    create_event,
    update_event,
    delete_event,
    ensure_sync,
)

MOCK_TOKEN_RESPONSE = {"access_token": "new_at", "expires_in": 3600}
MOCK_EVENT_RESPONSE = {"id": "google_event_123", "htmlLink": "https://calendar.google.com/event?eid=abc"}


def _make_appointment(db_session, professional_id, patient_id):
    appt = Appointment(
        professional_id=professional_id,
        patient_id=patient_id,
        start_time=datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 7, 15, 11, 0, tzinfo=timezone.utc),
        status="scheduled",
    )
    db_session.add(appt)
    db_session.commit()
    db_session.refresh(appt)
    return appt


def _setup_integration(db_session, professional_id: int):
    return upsert_integration(
        db_session, professional_id, "google_calendar",
        "at1", "rt1", datetime(2026, 7, 1, 0, 0, 0),
    )


def test_refresh_token_when_expired(db_session, test_professional):
    expired = datetime.utcnow() - timedelta(hours=1)
    upsert_integration(db_session, test_professional.id, "google_calendar", "old_at", "rt1", expired)
    integration = db_session.query(ProfessionalIntegration).first()

    with patch("app.services.google_calendar_service.httpx.Client") as mock_client:
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.post.return_value.status_code = 200
        mock_instance.post.return_value.json.return_value = MOCK_TOKEN_RESPONSE
        _ensure_valid_token(db_session, integration)

    db_session.refresh(integration)
    assert integration.access_token == "new_at"


def test_create_event_sets_google_event_id(db_session, test_professional, test_user):
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.return_value = MOCK_EVENT_RESPONSE
        create_event(db_session, appt, integration)
    db_session.refresh(appt)
    assert appt.google_event_id == "google_event_123"


def test_create_event_virtual_includes_conference_data(db_session, test_professional, test_user):
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    appt.is_virtual = True
    db_session.commit()
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.return_value = MOCK_EVENT_RESPONSE
        create_event(db_session, appt, integration)
    call_body = mock_call.call_args[1]["body"]
    assert call_body.get("conferenceData") is not None


def test_update_event_uses_existing_event_id(db_session, test_professional, test_user):
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    appt.google_event_id = "evt_1"
    db_session.commit()
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.return_value = MOCK_EVENT_RESPONSE
        update_event(db_session, appt, integration)
    endpoint = mock_call.call_args[0][0]
    assert "evt_1" in endpoint


def test_delete_event_uses_event_id(db_session, test_professional, test_user):
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    appt.google_event_id = "evt_1"
    db_session.commit()
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.return_value = {}
        delete_event(db_session, appt, integration)
    endpoint = mock_call.call_args[0][0]
    assert "evt_1" in endpoint


def test_ensure_sync_skips_when_no_integration(db_session, test_professional, test_user):
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    ensure_sync(db_session, "create", appt)
    assert appt.google_event_id is None


def test_ensure_sync_logs_error_does_not_raise(db_session, test_professional, test_user, caplog):
    import logging
    caplog.set_level(logging.ERROR)
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    _setup_integration(db_session, test_professional.id)
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.side_effect = Exception("Google API down")
        ensure_sync(db_session, "create", appt)
    assert "Google Calendar sync failed" in caplog.text


def test_delete_event_noop_when_no_event_id(db_session, test_professional, test_user):
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        delete_event(db_session, appt, integration)
    mock_call.assert_not_called()
```

- [ ] **Step 3: Write API endpoint tests — append to `tests/test_integrations.py`**

```python
# --- API tests ---


def test_google_auth_requires_professional(client, user_token):
    response = client.get(
        "/api/v1/integrations/google/auth",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


def test_google_auth_returns_url(client, professional_token):
    response = client.get(
        "/api/v1/integrations/google/auth",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert data["auth_url"].startswith("https://accounts.google.com/o/oauth2/v2/auth")


def test_google_tokens_missing_code(client, professional_token):
    response = client.post(
        "/api/v1/integrations/google/tokens",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 422  # missing query param


def test_google_tokens_requires_auth(client):
    response = client.post("/api/v1/integrations/google/tokens?code=abc")
    assert response.status_code == 403


def test_google_tokens_exchange_failure(client, professional_token):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = mock_post.return_value
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error": "invalid_grant"}
        response = client.post(
            "/api/v1/integrations/google/tokens?code=bad_code",
            headers={"Authorization": f"Bearer {professional_token}"},
        )
    assert response.status_code == 400
    assert "Failed to exchange" in response.text


def test_google_status_no_integration(client, professional_token):
    response = client.get(
        "/api/v1/integrations/google/status",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 200
    assert response.json() is None


def test_google_status_with_integration(client, professional_token, db_session, test_professional):
    from datetime import datetime
    upsert_integration(db_session, test_professional.id, "google_calendar", "at1", "rt1", datetime(2026, 7, 1, 0, 0, 0))
    response = client.get(
        "/api/v1/integrations/google/status",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "google_calendar"
```

- [ ] **Step 4: Conftest confirm**

Existing fixtures (`db_session`, `test_user`, `test_professional`, `user_token`, `professional_token`, `client`) cover all test needs. No new fixtures required.

- [ ] **Step 5: Run all tests**

Run: `pytest tests/ -v --tb=short`
Expected: all PASS (new total: 99 + 6 service + 9 calendar + 7 API = ~121)

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: add tests for Google Calendar integration"
```

---

### Task 8: Final Verification

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

- [ ] **Step 2: Verify alembic history**

```bash
alembic history
```

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A && git commit -m "fix: address test/verification issues"
```

- [ ] **Step 4: Update anchored summary**

Document the completed layer in the anchored summary.
