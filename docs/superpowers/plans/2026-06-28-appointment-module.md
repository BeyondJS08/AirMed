# Execution Plan: Layer 1C — Appointment Booking Module

**Spec:** `docs/superpowers/specs/2026-06-28-appointment-module-design.md`
**Test command:** `./.venv/bin/python -m pytest tests/ -v --tb=short`
**TDD:** Write test before implementation code.

---

## Task 1 — Update schemas

**File:** `app/schemas/appointment.py`

- `AppointmentCreate`: remove `patient_id`, add `@model_validator(end_must_be_after_start, must_be_future)`
- `AppointmentUpdate`: replace with `status: str | None, notes: str | None` only
- Keep `AppointmentBase` and `AppointmentOut` as-is

**TDD?** No test needed for schemas.

---

## Task 2 — Write appointment tests (TDD)

**File:** `tests/test_appointment.py`

16 tests covering:
- Book: ok, no availability (422), clash (409), past date (422), end<start (422), unauth (401)
- List: as patient, as professional, filter by status
- Get: by ID (200), not found (404), not owner (403)
- Cancel: as patient (204), as professional (204), unrelated user (403)
- Confirm: patient tries → 403, professional → status=confirmed
- Complete: professional → status=completed

**Fixtures needed:** Reuse existing `test_professional`, `test_user`, `professional_token`, `user_token`. Create availability windows in tests that need them.

---

## Task 3 — Implement appointment service

**File:** `app/services/appointment_service.py`

Functions:
- `create_appointment(db, data, current_user)` — slot validation + create
- `get_appointments(db, current_user, status, date_from, date_to)` — filtered
- `get_appointment(db, appointment_id)` — single
- `update_appointment(db, appointment, data, current_user)` — transition validation
- Helpers: `_validate_slot_available`, `_validate_transition`, `_validate_future`

Slot validation uses `Availability` model directly (reuses the windows + appointments query from Layer 1B).

---

## Task 4 — Implement endpoints

**File:** `app/api/v1/endpoints/appointments.py`

Replace stubs with full implementation:
- `POST /` — `Depends(get_current_user)`, creates appointment
- `GET /` — `Depends(get_current_user)`, list with optional filters
- `GET /{id}` — `Depends(get_current_user)`, single with owner check
- `PATCH /{id}` — `Depends(get_current_user)`, status update with transition validation
- `DELETE /{id}` — `Depends(get_current_user)`, convenience cancel → 204

No router changes needed (already wired in `__init__.py`).

---

## Task 5 — Run all tests, commit

- Run all 51 prior tests + 16 new appointment tests = 67 total
- Fix any failures
- Final commit

## Rollback

```bash
git checkout -- tests/app/schemas/appointment.py app/services/appointment_service.py app/api/v1/endpoints/appointments.py
```
