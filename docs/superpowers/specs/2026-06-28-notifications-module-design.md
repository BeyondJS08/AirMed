# Notifications Module Design

## Purpose

Track notification records (email, WhatsApp, Telegram) for patients and professionals. Notifications are created automatically by the appointment service when appointment status changes. Actual dispatch (sending via email/WhatsApp/Telegram APIs) is deferred to Stage 3 — this layer only persists the records.

## Data Model

### Notification

| Column | Type | Notes |
|--------|------|-------|
| `id` | int (PK, autoincrement) | |
| `appointment_id` | int (FK → appointments.id, nullable) | null for system-level notifications |
| `user_id` | int (FK → users.id, NOT NULL) | recipient |
| `channel` | enum(email, whatsapp, telegram) | delivery channel |
| `status` | enum(pending, sent, failed) | default: pending |
| `subject` | str | nullable, e.g. "Appointment Confirmed" |
| `message` | text | body content |
| `error` | text | nullable — stores failure reason when sent fails |
| `created_at` | datetime (timezone-aware, server default) | |
| `sent_at` | datetime (timezone-aware) | nullable — set when dispatch succeeds |
| `read_at` | datetime (timezone-aware) | nullable — set when user reads |

### Enum values

- **Channel**: `email`, `whatsapp`, `telegram`
- **Status**: `pending` → `sent` or `failed`

Indexes: `(user_id, status)`, `(appointment_id)`.

## Service Layer

### Functions

- `create_notification(db, *, user_id, channel, subject, message, appointment_id=None) -> Notification`
- `list_notifications(db, user_id, status=None, limit=50) -> list[Notification]`
- `mark_sent(db, notification_id, sent_at=None) -> Notification`
- `mark_failed(db, notification_id, error) -> Notification`
- `mark_read(db, notification_id) -> Notification`

### Appointment hook

- `notify_appointment_status(db, appointment)` — called after appointment create/cancel:
  - **On book (scheduled):** create pending notification for patient (channel=email, subject="Appointment Booked") and for professional (channel=email, subject="New Appointment")
  - **On cancel (cancelled):** create pending notification for both parties (subject="Appointment Cancelled")
  - Channels default to `email` for now — Stage 3 adds user channel preference

## API Endpoints

All under `/api/v1/notifications/` — auth required (any authenticated user), scoped to current user only.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List own notifications. Query params: `status`, `limit` |
| GET | `/{id}` | Get single notification (must be owner) |
| PUT | `/{id}/read` | Mark notification as read (must be owner) |

No create endpoint — notifications are created internally by `notify_appointment_status`. No update endpoint — status transitions happen via `mark_sent`/`mark_failed` (called by Stage 3 dispatch workers).

## Migration

Alembic revision adding the `notifications` table and enums.

## Tests (~12 tests)

- `test_create_notification` — service creates notification with correct fields
- `test_list_notifications` — list own notifications, scoped
- `test_list_filter_status` — filter by pending/sent/failed
- `test_mark_sent` — status transitions to sent
- `test_mark_failed` — status transitions to failed with error
- `test_mark_read` — read_at is set
- `test_hook_on_book` — booking appointment creates 2 notifications (patient + professional)
- `test_hook_on_cancel` — cancelling creates 2 notification
- `test_get_own_notification` — can get own
- `test_get_other_notification` — 403 for another user's notification
- `test_mark_read_other` — 403
- `test_unauthenticated` — 401

## Future (Stage 3)

- Dispatch workers: email (SMTP), WhatsApp (Business API), Telegram (Bot API)
- User channel preferences
- Notification templates
- Batch dispatch, retry logic
