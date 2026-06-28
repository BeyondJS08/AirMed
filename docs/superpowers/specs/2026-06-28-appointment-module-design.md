# Layer 1C — Appointment Booking Module Design

## Overview

The Appointment module enables patients to book time slots with healthcare professionals and manage the appointment lifecycle. It builds on the Availability module (Layer 1B) to validate slot availability.

## Data Model

### Existing `Appointment` table

No schema changes needed. Current columns:

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `professional_id` | FK → users.id | |
| `patient_id` | FK → users.id | |
| `start_time` | DateTime | tz-aware |
| `end_time` | DateTime | tz-aware |
| `status` | String(50) | `scheduled` / `confirmed` / `completed` / `cancelled` |
| `notes` | Text | nullable |
| `is_virtual` | Boolean | default false |
| `location` | String | nullable, in-person address |
| `google_event_id` | String | nullable, future use |

### Status Flow

```
scheduled ──→ confirmed ──→ completed
     │                      │
     └──→ cancelled ←───────┘
```

- **Patient can:** create (→ scheduled), cancel own appointment (→ cancelled)
- **Professional can:** confirm (→ confirmed), complete (→ completed), cancel (→ cancelled) any of their appointments
- **No backward transitions:** confirmed → scheduled, completed → confirmed, cancelled → anything

## Schema Changes

### `AppointmentCreate` (updated)

Remove `patient_id` — it is derived from the authenticated user server-side.

```python
class AppointmentCreate(BaseModel):
    professional_id: int
    start_time: datetime
    end_time: datetime
    notes: str | None = None
    is_virtual: bool = False
    location: str | None = None
```

Validation rules added:
- `end_time > start_time`
- `start_time` and `end_time` must be in the future

### `AppointmentUpdate` (replaced)

Remove all fields except `status` and `notes`. Partial update for status transitions.

```python
class AppointmentUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
```

Backend validates allowed status transitions.

### `AppointmentOut` (unchanged)

```python
class AppointmentOut(BaseModel):
    id: int
    professional_id: int
    patient_id: int
    start_time: datetime
    end_time: datetime
    status: str
    notes: str | None
    is_virtual: bool
    location: str | None
    google_event_id: str | None
```

## Endpoints

All endpoints require authentication (`get_current_user`).

### `POST /api/v1/appointments/` — Book an appointment

- Auth: any authenticated user
- If current user is a professional → they are the professional (overrides `professional_id`)
- If current user is a patient → `patient_id` = current user
- If current user is a professional and also wants to specify a patient → they can optionally provide `patient_id` (query param or body field). For simplicity in this layer: if current user is professional, `patient_id` defaults to current user. Future: add `patient_id` field that professionals can set.

**Validation (server-side):**
1. Professional exists and is active
2. `end_time > start_time`, both in future
3. No overlapping appointment for same professional at that time
4. Appointment fits within professional's availability windows (from the Availability module)

- Returns `201` + `AppointmentOut`

### `GET /api/v1/appointments/` — List appointments

- Auth: any authenticated user
- Returns appointments where user is either patient OR professional
- Query params:
  - `status` (optional): filter by status
  - `date_from` (optional): filter appointments on or after this date
  - `date_to` (optional): filter appointments on or before this date
- Returns `list[AppointmentOut]`

### `GET /api/v1/appointments/{id}` — Get single appointment

- Auth: any authenticated user
- Must be the patient or professional of the appointment (403 otherwise)
- Returns `AppointmentOut`

### `PATCH /api/v1/appointments/{id}` — Update appointment status/notes

- Auth: any authenticated user
- Must be the patient or professional of the appointment (403 otherwise)
- Validates status transitions:
  - Patient: only `scheduled` → `cancelled`
  - Professional: `scheduled` → `confirmed` / `cancelled`, `confirmed` → `completed` / `cancelled`, `completed` → `cancelled`
- Returns `AppointmentOut`

### `DELETE /api/v1/appointments/{id}` — Cancel appointment

- Convenience endpoint for `PATCH` with status `cancelled`
- Auth: patient or professional of the appointment
- Returns `204`

## Service Layer

### `app/services/appointment_service.py`

Functions:
- `create_appointment(db, data, current_user)` — validates availability, creates appointment
- `get_appointments(db, current_user, status, date_from, date_to)` — filtered list
- `get_appointment(db, appointment_id)` — single lookup
- `update_appointment(db, appointment, data, current_user)` — status transition validation
- `_validate_slot_available(db, professional_id, start_time, end_time)` — availability check using the Availability module's windows, plus conflict check against existing appointments
- `_validate_transition(current_user, appointment, new_status)` — status transition rules

## Test Plan

| Test | Scenario |
|------|----------|
| `test_book_appointment_ok` | Patient books within availability → 201 |
| `test_book_appointment_no_availability` | No availability windows → 422 |
| `test_book_appointment_clash` | Existing appointment → 409 |
| `test_book_appointment_past` | start_time in the past → 422 |
| `test_book_appointment_end_before_start` | end < start → 422 |
| `test_book_appointment_unauthenticated` | No token → 401 |
| `test_list_appointments_as_patient` | Patient sees own appointments |
| `test_list_appointments_as_professional` | Professional sees theirs |
| `test_list_appointments_filter_status` | Filter by status works |
| `test_get_appointment_ok` | Fetch by ID works |
| `test_get_appointment_not_found` | 404 |
| `test_get_appointment_not_owner` | Neither patient nor professional → 403 |
| `test_cancel_appointment_as_patient` | Patient cancels → 204 |
| `test_cancel_appointment_as_professional` | Professional cancels → 204 |
| `test_cancel_others_appointment` | Unrelated user → 403 |
| `test_confirm_appointment_as_patient` | Patient tries to confirm → 403 |
| `test_confirm_appointment_as_professional` | Professional confirms → status = confirmed |
| `test_complete_appointment` | Professional completes → status = completed |

## Files to Create/Modify

| Action | File |
|--------|------|
| Modify | `app/schemas/appointment.py` — update Create/Update schemas |
| Modify | `app/services/appointment_service.py` — full implementation |
| Modify | `app/api/v1/endpoints/appointments.py` — full endpoints |
| Create | `tests/test_appointment.py` |
| Commit | All the above |
