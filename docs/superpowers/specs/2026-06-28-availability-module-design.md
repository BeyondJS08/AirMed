# Layer 1B — Availability Module Design

## Overview

The Availability module allows healthcare professionals to define their weekly recurring availability windows. The system computes concrete available time slots by subtracting booked appointments from these windows. This is a core dependency for the appointment booking flow (Layer 2).

## Data Model

### Existing `Availability` table (keep, no schema changes)

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | auto |
| `professional_id` | FK → users.id | |
| `day_of_week` | Integer | 0=Monday, 6=Sunday |
| `start_time` | Time | wall-clock, no tz (interpreted in professional's timezone) |
| `end_time` | Time | wall-clock, no tz |
| `is_active` | Boolean | default `true`, allows soft-disable |

No date-specific overrides in this layer. Future: `AvailabilityOverride` (date, start, end, reason).

### New column on `User`

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| `timezone` | String(50) | `"America/Sao_Paulo"` | IANA tz name for the professional |

## Schema Layers

### `app/schemas/availability.py`

```python
class AvailabilityBase(BaseModel):
    day_of_week: int          # 0-6
    start_time: time          # "HH:MM"
    end_time: time            # "HH:MM", must be after start_time
    is_active: bool = True

class AvailabilityCreate(AvailabilityBase):
    pass

class AvailabilityUpdate(BaseModel):
    day_of_week: int | None = None
    start_time: time | None = None
    end_time: time | None = None
    is_active: bool | None = None

class AvailabilityOut(AvailabilityBase):
    id: int
    professional_id: int
```

### `app/schemas/availability.py` — Available slots

```python
class AvailableSlotOut(BaseModel):
    start_time: datetime    # ISO datetime (tz-aware)
    end_time: datetime      # ISO datetime (tz-aware)
```

## Endpoints

All availability endpoints are scoped to the **authenticated professional** (`get_current_professional` dependency).

### `GET /api/v1/availability/`
List all availability windows for the authenticated professional.
- Returns `list[AvailabilityOut]`
- Active and inactive windows both returned (client decides how to render)

### `POST /api/v1/availability/`
Create a new weekly availability window.
- Body: `AvailabilityCreate`
- Validates: `day_of_week` in 0-6, `end_time > start_time`, no overlap with existing windows for same professional + day_of_week
- Returns `201` + `AvailabilityOut`

### `PUT /api/v1/availability/{id}`
Update an existing window. Owner-only (403 if not owner).
- Body: `AvailabilityUpdate` (partial)
- Returns `AvailabilityOut`
- Overlap check re-applied if day/time changes

### `DELETE /api/v1/availability/{id}`
Soft-delete (set `is_active = False`), or hard-delete. Owner-only.
- Returns `204`

### `GET /api/v1/availability/available-slots?professional_id=X&date=YYYY-MM-DD&service_id=X`
**(Public)** Get concrete available time slots for a specific date.
- Query params:
  - `professional_id` (required)
  - `date` (required, `YYYY-MM-DD`)
  - `service_id` (optional, filters by service duration)
- Algorithm:
  1. Resolve `day_of_week` from the given date
  2. Load active windows for that professional + day_of_week
  3. Load booked appointments for that professional on that date (status != cancelled)
  4. For each window, subtract overlapping appointments → list of open ranges
  5. If `service_id` provided, further split ranges into slots matching the service's `duration_minutes`
- Returns `list[AvailableSlotOut]`
- No auth required (patients need to see slots before booking)

## Validation Rules

- `day_of_week` must be 0-6
- `end_time` must be after `start_time`
- Overlap: two windows for the same professional + day_of_week may not overlap (but may abut: window A 09:00-12:00, window B 12:00-14:00 is OK)
- No timezone conversion in the API — the professional's timezone field is metadata; the system assumes wall-clock times are in that timezone

## Test Plan

| Test | Scenario |
|------|----------|
| `test_create_availability_ok` | Professional creates a valid window → 201 |
| `test_create_availability_not_professional` | Non-professional → 403 |
| `test_create_availability_unauthenticated` | No token → 401 |
| `test_create_availability_overlap` | Overlapping window → 409 |
| `test_create_availability_invalid_day` | day_of_week out of range → 422 |
| `test_create_availability_end_before_start` | end_time < start_time → 422 |
| `test_list_availability` | List returns owner's windows |
| `test_list_availability_other_professional` | Logged in as A, lists A's windows only |
| `test_update_availability_ok` | Owner updates → 200 |
| `test_update_availability_not_owner` | Non-owner → 403 |
| `test_update_availability_overlap` | Update causes overlap → 409 |
| `test_delete_availability_ok` | Owner deletes → 204 |
| `test_delete_availability_not_owner` | Non-owner → 403 |
| `test_available_slots_basic` | Date with one window, no appointments → returns full range |
| `test_available_slots_with_appointment` | Appointment at 10:00-10:30 → two ranges returned |
| `test_available_slots_no_window` | Professional has no availability that day → empty |
| `test_available_slots_with_service_duration` | Service=60min, window 09-17 → slots at :00 marks |
| `test_available_slots_multiple_windows` | Two windows with gap → both ranges returned |

## Non-Goals (for this layer)

- Date-specific overrides / vacation blocks
- Recurring appointments
- Recurring availability exceptions (e.g., "every 2nd Thursday off")
- Calendar sync (Layer 5)

## Files to Create/Modify

| Action | File |
|--------|------|
| Modify | `app/models/user.py` — add `timezone` column |
| Create | `app/schemas/availability.py` |
| Create | `app/services/availability_service.py` |
| Create | `app/api/v1/endpoints/availability.py` |
| Modify | `app/api/v1/__init__.py` — include availability router |
| Create | `tests/test_availability.py` |
| Generate | Alembic migration for timezone column |
| Commit | All the above |
