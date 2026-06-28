# Execution Plan: Layer 1B — Availability Module

**Spec:** `docs/superpowers/specs/2026-06-28-availability-module-design.md`
**Branch:** `main` (no branch switch — working directly)
**Test command:** `./.venv/bin/python -m pytest tests/ -v --tb=short`
**TDD:** Write test before implementation code.

---

## Task 1 — Add timezone to User model + Alembic migration

**Files:**
- `app/models/user.py` — add `timezone = Column(String(50), default="America/Sao_Paulo")`
- Generate migration: `alembic revision --autogenerate -m "add timezone to users"`
- Review, then `alembic upgrade head`
- Verify: check table schema in psql

**TDD?** No test needed for a schema-only change.

---

## Task 2 — Create availability schemas

**File:** `app/schemas/availability.py`

Classes:
- `AvailabilityBase(day_of_week: int, start_time: time, end_time: time, is_active: bool = True)`
- `AvailabilityCreate(AvailabilityBase)`
- `AvailabilityUpdate(day_of_week: int | None, start_time: time | None, end_time: time | None, is_active: bool | None)`
- `AvailabilityOut(AvailabilityBase, id: int, professional_id: int)` with `model_config = ConfigDict(from_attributes=True)`
- `AvailableSlotOut(start_time: datetime, end_time: datetime)`

**TDD?** No test needed for schemas.

---

## Task 3 — Write availability tests (TDD)

**File:** `tests/test_availability.py`

Write tests first (they will fail until implementation exists):

1. `test_create_availability_ok` — professional creates window → 201
2. `test_create_availability_not_professional` — patient user → 403
3. `test_create_availability_unauthenticated` — no token → 401
4. `test_create_availability_overlap` — overlapping window → 409 (or 400)
5. `test_create_availability_invalid_day` — day_of_week=7 → 422
6. `test_create_availability_end_before_start` — end < start → 422
7. `test_list_availability` — returns owner's windows
8. `test_list_availability_other_professional` — logged as A, returns A's windows (not B's, not empty)
9. `test_update_availability_ok` — owner updates → 200
10. `test_update_availability_not_owner` — non-owner → 403
11. `test_update_availability_overlap` — update causes overlap → 409
12. `test_delete_availability_ok` — owner deletes → 204
13. `test_delete_availability_not_owner` — non-owner → 403
14. `test_available_slots_basic` — one window, no appointments → full range
15. `test_available_slots_with_appointment` — appointment blocks part → two ranges
16. `test_available_slots_no_window` — professional has no windows → empty
17. `test_available_slots_with_service_duration` — 30min slots → 30-min intervals
18. `test_available_slots_multiple_windows` — two windows with gap → both

**Fixtures needed:** Two professional users with tokens (for owner/non-owner tests).

---

## Task 4 — Implement availability service + endpoints

**File:** `app/services/availability_service.py`

Functions:
- `create_availability(db, professional_id, data)` — overlap check, insert, return
- `get_availabilities(db, professional_id)` — list all
- `get_availability(db, availability_id)` — single by ID
- `update_availability(db, availability_id, professional_id, data)` — owner check, overlap check, update
- `delete_availability(db, availability_id, professional_id)` — owner check, delete
- `get_available_slots(db, professional_id, date, service_id=None)` — algorithm per spec
- `_overlaps(existing, new_start, new_end)` — helper: returns True if start/end overlaps any existing window on same day_of_week

**File:** `app/api/v1/endpoints/availability.py`

Dependency: `get_current_professional` (from `app.api.deps`)

Endpoints:
- `GET /availability/` — `availabilities = service.get_availabilities(db, professional.id)`
- `POST /availability/` — `service.create_availability(db, professional.id, data)`, 201
- `PUT /availability/{id}` — `service.update_availability(db, id, professional.id, data)`
- `DELETE /availability/{id}` — `service.delete_availability(db, id, professional.id)`, 204
- `GET /availability/available-slots` — public, takes `professional_id`, `date`, optional `service_id`

Wire in `app/api/v1/__init__.py`.

---

## Task 5 — Run all tests, final review, commit

- Run all 25 prior tests + 18 new availability tests = 43 total
- Fix any failures
- Final commit with all Layer 1B files

---

## Rollback Plan

If tests fail and cannot be fixed quickly:
- `git checkout -- tests/ app/services/ app/api/v1/endpoints/availability.py`
- Review, re-attack
