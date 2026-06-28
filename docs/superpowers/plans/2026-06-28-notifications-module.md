# Notifications Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Backend model, service, API, and tests for tracking notification records (email/WhatsApp/Telegram), auto-created on appointment status changes.

**Architecture:** Add a `Notification` SQLAlchemy model + enum columns, service layer with CRUD + status transitions, scoped endpoints, and a hook called by the appointment service on book/cancel. Dispatch is deferred to Stage 3.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic (enum type via SQLAlchemy `Enum`), pytest

---

## File Structure

- Create: `backend-airmed/app/models/notification.py` — `Notification` model
- Create: `backend-airmed/app/schemas/notification.py` — `NotificationOut`, `NotificationListParams`
- Create: `backend-airmed/app/services/notification_service.py` — all business logic
- Create: `backend-airmed/app/api/v1/endpoints/notifications.py` — list/get/mark-read endpoints
- Create: `backend-airmed/tests/test_notifications.py` — ~12 tests
- Modify: `backend-airmed/app/db/base.py` — import Notification model
- Modify: `backend-airmed/app/api/v1/__init__.py` — wire router
- Modify: `backend-airmed/app/services/appointment_service.py` — hook notification creation on book/cancel
- Alembic: generate + verify migration

---

### Task 1: Notification Model

**Files:**
- Create: `backend-airmed/app/models/notification.py`
- Modify: `backend-airmed/app/db/base.py`

- [ ] **Step 1: Create the model file**

```python
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class NotificationChannel(str, enum.Enum):
    email = "email"
    whatsapp = "whatsapp"
    telegram = "telegram"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False, default=NotificationChannel.email)
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.pending)
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    appointment = relationship("Appointment", backref="notifications")
    user = relationship("User", backref="notifications")

    __table_args__ = (
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_appointment", "appointment_id"),
    )
```

- [ ] **Step 2: Import model in base.py**

Read `backend-airmed/app/db/base.py` and add import line:

```python
from app.models.notification import Notification  # noqa
```

- [ ] **Step 3: Run test import check**

```bash
cd backend-airmed && ./.venv/bin/python -c "from app.models.notification import Notification; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend-airmed/app/models/notification.py backend-airmed/app/db/base.py
git commit -m "feat: add Notification model"
```

---

### Task 2: Pydantic Schemas

**Files:**
- Create: `backend-airmed/app/schemas/notification.py`

- [ ] **Step 1: Create the schemas file**

```python
from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    appointment_id: int | None = None
    user_id: int
    channel: str
    status: str
    subject: str | None = None
    message: str
    error: str | None = None
    created_at: datetime
    sent_at: datetime | None = None
    read_at: datetime | None = None

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Verify import**

```bash
cd backend-airmed && ./.venv/bin/python -c "from app.schemas.notification import NotificationOut; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend-airmed/app/schemas/notification.py
git commit -m "feat: add NotificationOut schema"
```

---

### Task 3: Notification Service

**Files:**
- Create: `backend-airmed/app/services/notification_service.py`

- [ ] **Step 1: Create the service with all CRUD functions**

```python
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationChannel, NotificationStatus


def create_notification(
    db: Session,
    *,
    user_id: int,
    channel: NotificationChannel = NotificationChannel.email,
    subject: str | None = None,
    message: str,
    appointment_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        channel=channel,
        status=NotificationStatus.pending,
        subject=subject,
        message=message,
        appointment_id=appointment_id,
    )
    db.add(notification)
    db.flush()
    return notification


def list_notifications(
    db: Session,
    user_id: int,
    status: NotificationStatus | None = None,
    limit: int = 50,
) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if status:
        query = query.filter(Notification.status == status)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


def get_notification(db: Session, notification_id: int) -> Notification | None:
    return db.query(Notification).filter(Notification.id == notification_id).first()


def mark_sent(db: Session, notification_id: int) -> Notification | None:
    notification = get_notification(db, notification_id)
    if notification:
        notification.status = NotificationStatus.sent
        notification.sent_at = datetime.now(timezone.utc)
    return notification


def mark_failed(db: Session, notification_id: int, error: str) -> Notification | None:
    notification = get_notification(db, notification_id)
    if notification:
        notification.status = NotificationStatus.failed
        notification.error = error
    return notification


def mark_read(db: Session, notification_id: int) -> Notification | None:
    notification = get_notification(db, notification_id)
    if notification:
        notification.read_at = datetime.now(timezone.utc)
    return notification
```

- [ ] **Step 2: Verify import**

```bash
cd backend-airmed && ./.venv/bin/python -c "from app.services.notification_service import create_notification; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend-airmed/app/services/notification_service.py
git commit -m "feat: add notification service"
```

---

### Task 4: Appointment Hook — Auto-Create Notifications

**Files:**
- Modify: `backend-airmed/app/services/appointment_service.py`
- Modify: `backend-airmed/app/services/notification_service.py` (add `notify_appointment_status`)

- [ ] **Step 1: Add the hook function to notification_service.py**

Append to `backend-airmed/app/services/notification_service.py`:

```python
from app.models.appointment import Appointment


def notify_appointment_status(db: Session, appointment: Appointment) -> list[Notification]:
    status_map = {
        "scheduled": ("Appointment Booked", "Your appointment has been scheduled."),
        "cancelled": ("Appointment Cancelled", "Your appointment has been cancelled."),
    }
    subject, message = status_map.get(appointment.status, ("Notification", "Your appointment has been updated."))
    notifs = []
    for user_id in (appointment.patient_id, appointment.professional_id):
        n = create_notification(
            db,
            user_id=user_id,
            channel=NotificationChannel.email,
            subject=subject,
            message=message,
            appointment_id=appointment.id,
        )
        notifs.append(n)
    return notifs
```

- [ ] **Step 2: Read appointment_service.py to find the create/cancel functions**

```bash
cd backend-airmed && cat app/services/appointment_service.py
```

- [ ] **Step 3: Add the hook call in create_appointment (after db.flush) and cancel_appointment (after status change)**

Import and call `notify_appointment_status`:

```python
from app.services.notification_service import notify_appointment_status
```

Add after the line where appointment is created/status changed:

```python
notify_appointment_status(db, appointment)
```

For example in `create_appointment`, add after `db.flush()`. In `cancel_appointment`, add after `appointment.status = "cancelled"` + `db.flush()`.

- [ ] **Step 4: Run existing tests to verify nothing broke**

```bash
cd backend-airmed && ./.venv/bin/python -m pytest tests/ -v --tb=short
```

All 74 tests must still pass.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: auto-create notifications on appointment book/cancel"
```

---

### Task 5: API Endpoints

**Files:**
- Create: `backend-airmed/app/api/v1/endpoints/notifications.py`
- Modify: `backend-airmed/app/api/v1/__init__.py`

- [ ] **Step 1: Create the router**

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.notification import NotificationStatus
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services import notification_service as ns

router = APIRouter()


@router.get("/", response_model=list[NotificationOut])
async def list_notifications(
    status: NotificationStatus | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ns.list_notifications(db, current_user.id, status=status, limit=limit)


@router.get("/{notification_id}", response_model=NotificationOut)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = ns.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your notification")
    return notification


@router.put("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = ns.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your notification")
    updated = ns.mark_read(db, notification_id)
    return updated
```

- [ ] **Step 2: Wire the router**

Read `backend-airmed/app/api/v1/__init__.py` and add router:

```python
from app.api.v1.endpoints.notifications import router as notifications_router
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
```

- [ ] **Step 3: Verify the app starts**

```bash
cd backend-airmed && ./.venv/bin/python -c "from app.main import app; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add notifications API endpoints"
```

---

### Task 6: Alembic Migration

**Files:**
- Generate: new migration revision

- [ ] **Step 1: Generate migration**

```bash
cd backend-airmed && ./.venv/bin/alembic revision --autogenerate -m "add notifications table"
```

- [ ] **Step 2: Review migration SQL**

```bash
cd backend-airmed && cat alembic/versions/*_add_notifications_table.py
```

Verify it creates the `notifications` table with correct columns, enums, FKs, and indexes.

- [ ] **Step 3: Run migration on test DB**

```bash
cd backend-airmed && ./.venv/bin/alembic upgrade head
```

- [ ] **Step 4: Verify tables**

```bash
cd backend-airmed && ./.venv/bin/python -c "
from app.db.session import SessionLocal
db = SessionLocal()
tables = [row[0] for row in db.execute('SELECT table_name FROM information_schema.tables WHERE table_schema=\\'public\\'').all()]
print(tables)
db.close()
"
```

Confirm `notifications` is listed.

- [ ] **Step 5: Commit**

```bash
git add alembic/versions/
git commit -m "feat: add notifications table migration"
```

---

### Task 7: Tests

**Files:**
- Create: `backend-airmed/tests/test_notifications.py`

- [ ] **Step 1: Write the test file**

```python
from datetime import datetime, timezone

from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.services.notification_service import (
    create_notification,
    get_notification,
    list_notifications,
    mark_failed,
    mark_read,
    mark_sent,
    notify_appointment_status,
)
from app.models.appointment import Appointment


def test_create_notification(db_session):
    user_id = 1
    n = create_notification(db_session, user_id=user_id, channel=NotificationChannel.email, subject="Test", message="Hello")
    assert n.user_id == user_id
    assert n.channel == NotificationChannel.email
    assert n.status == NotificationStatus.pending
    assert n.subject == "Test"
    assert n.message == "Hello"
    assert n.appointment_id is None


def test_list_notifications(db_session, test_user):
    u = test_user
    for i in range(3):
        create_notification(db_session, user_id=u.id, message=f"msg{i}")
    db_session.commit()
    notifs = list_notifications(db_session, u.id)
    assert len(notifs) == 3


def test_list_notifications_filter_status(db_session, test_user):
    u = test_user
    n = create_notification(db_session, user_id=u.id, message="pending")
    db_session.commit()
    mark_sent(db_session, n.id)
    db_session.commit()
    pending = list_notifications(db_session, u.id, status=NotificationStatus.pending)
    assert len(pending) == 0
    sent = list_notifications(db_session, u.id, status=NotificationStatus.sent)
    assert len(sent) == 1


def test_list_notifications_scoped(db_session, test_user):
    u1 = test_user
    u2_id = 9999
    create_notification(db_session, user_id=u1.id, message="mine")
    create_notification(db_session, user_id=u2_id, message="not mine")
    db_session.commit()
    notifs = list_notifications(db_session, u1.id)
    assert len(notifs) == 1


def test_mark_sent(db_session, test_user):
    u = test_user
    n = create_notification(db_session, user_id=u.id, message="x")
    db_session.commit()
    updated = mark_sent(db_session, n.id)
    assert updated.status == NotificationStatus.sent
    assert updated.sent_at is not None


def test_mark_failed(db_session, test_user):
    u = test_user
    n = create_notification(db_session, user_id=u.id, message="x")
    db_session.commit()
    updated = mark_failed(db_session, n.id, "SMTP error")
    assert updated.status == NotificationStatus.failed
    assert updated.error == "SMTP error"


def test_mark_read(db_session, test_user):
    u = test_user
    n = create_notification(db_session, user_id=u.id, message="x")
    db_session.commit()
    updated = mark_read(db_session, n.id)
    assert updated.read_at is not None


def test_hook_on_book_creates_two_notifications(db_session):
    from app.models.user import User
    from app.core.security import get_password_hash

    patient = User(email="pat@t.com", full_name="Patient", hashed_password=get_password_hash("p"), is_professional=False, is_active=True)
    pro = User(email="pro@t.com", full_name="Pro", hashed_password=get_password_hash("p"), is_professional=True, is_active=True)
    db_session.add_all([patient, pro])
    db_session.commit()

    appt = Appointment(professional_id=pro.id, patient_id=patient.id, start_time=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc), end_time=datetime(2026, 7, 1, 11, 0, tzinfo=timezone.utc), status="scheduled")
    db_session.add(appt)
    db_session.flush()

    notifs = notify_appointment_status(db_session, appt)
    assert len(notifs) == 2
    assert {n.user_id for n in notifs} == {patient.id, pro.id}
    assert all(n.status == NotificationStatus.pending for n in notifs)
    assert all(n.appointment_id == appt.id for n in notifs)


def test_hook_on_cancel_creates_two_notifications(db_session):
    from app.models.user import User
    from app.core.security import get_password_hash

    patient = User(email="pat2@t.com", full_name="Patient", hashed_password=get_password_hash("p"), is_professional=False, is_active=True)
    pro = User(email="pro2@t.com", full_name="Pro", hashed_password=get_password_hash("p"), is_professional=True, is_active=True)
    db_session.add_all([patient, pro])
    db_session.commit()

    appt = Appointment(professional_id=pro.id, patient_id=patient.id, start_time=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc), end_time=datetime(2026, 7, 1, 11, 0, tzinfo=timezone.utc), status="cancelled")
    db_session.add(appt)
    db_session.flush()

    notifs = notify_appointment_status(db_session, appt)
    assert len(notifs) == 2
    assert all(n.subject == "Appointment Cancelled" for n in notifs)


def test_get_notification_returns_none_for_missing(db_session):
    assert get_notification(db_session, 9999) is None


# API tests


def test_list_notifications_api(client, user_token, db_session, test_user):
    create_notification(db_session, user_id=test_user.id, message="hello")
    db_session.commit()
    resp = client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["message"] == "hello"


def test_list_notifications_api_unauthenticated(client):
    resp = client.get("/api/v1/notifications/")
    assert resp.status_code == 401


def test_get_notification_api_forbidden(client, user_token, db_session):
    n = create_notification(db_session, user_id=9999, message="secret")
    db_session.commit()
    resp = client.get(f"/api/v1/notifications/{n.id}", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


def test_mark_read_api(client, user_token, db_session, test_user):
    n = create_notification(db_session, user_id=test_user.id, message="readme")
    db_session.commit()
    resp = client.put(f"/api/v1/notifications/{n.id}/read", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert resp.json()["read_at"] is not None


def test_mark_read_api_forbidden(client, user_token, db_session):
    n = create_notification(db_session, user_id=9999, message="notmine")
    db_session.commit()
    resp = client.put(f"/api/v1/notifications/{n.id}/read", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403
```

- [ ] **Step 2: Run the test file**

```bash
cd backend-airmed && ./.venv/bin/python -m pytest tests/test_notifications.py -v --tb=short
```

Expected: ~15 tests all passing.

- [ ] **Step 3: Run full test suite to verify no regressions**

```bash
cd backend-airmed && ./.venv/bin/python -m pytest tests/ -v --tb=short
```

All 89 tests should pass.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add notification service tests and API tests"
```

---

### Task 8: Final Verification

- [ ] **Step 1: Full test suite**

```bash
cd backend-airmed && ./.venv/bin/python -m pytest tests/ -v --tb=short
```

- [ ] **Step 2: Commit any remaining changes**

```bash
git add -A && git commit -m "chore: finalize notifications module"
```
