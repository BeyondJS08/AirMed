# AirMed Stages 1+2 Development Roadmap

> **Meta-spec:** This document is the master roadmap for Stages 1 (Analysis/Design) and 2 (Development/Integration) of the AirMed project. Each sub-project listed here gets its own spec and detailed implementation plan, following the per-sub-project rhythm defined below. Stage 1 design work is distributed into each sub-project's brainstorm/spec phase — not done as a separate upfront phase.

**Created:** 2026-06-28
**Status:** Approved
**Current state:** Backend auth fully implemented; services CRUD implemented but not wired into router; appointments/availability are stubs; frontend is greenfield; mobile directory deleted (uncommitted); no Alembic migrations; minimal tests.

---

## Locked Decisions

| Decision | Value |
|----------|-------|
| Sequencing strategy | Layer-by-layer completion |
| Mobile architecture | Shared backend — mobile is a client of the existing FastAPI + Postgres (not a separate API/DB) |
| Security/Infrastructure | Deferred to Stage 4; Stage 4 plan must explicitly satisfy all security evaluation criteria |
| Mobile utility criterion | Ignored — mobile may mirror the web patient panel |
| Frontend state management | React Query (server state) + Zustand (UI state) |
| LLM hosting | llama.cpp for Gemma-4-E2B (on-premise/edge) |
| Test database | Postgres-only (no SQLite) — local Postgres via docker-compose for unit + integration tests |
| Production database | Supabase Postgres (free plan) — managed Postgres instance |
| Supabase Auth | NOT used — backend has custom JWT auth (already implemented in Layer 1A) |
| Mobile directory | Commit deletion; fresh Expo scaffold in Layer 3 |

---

## Database Strategy

### Production: Supabase Postgres (free plan)
- **App connection:** Supabase connection pooler (Supavisor, port 6543) — supports connection pooling for the FastAPI backend.
- **Migrations:** Supabase direct connection (port 5432) — Alembic requires session-level features not available through pgBouncer/Supavisor.
- **SSL:** Supabase requires SSL on all connections — partially satisfies the "SSL certificate" security criterion.
- **Limitations (free plan):** 500MB storage, 1 project, pauses after 1 week inactivity. Keep active with a cron job or regular access.
- **Not used:** Supabase Auth, Supabase REST API (PostgREST), Supabase Realtime, Supabase Storage. Supabase is purely the managed Postgres provider.

### Local development & testing: Postgres in docker-compose
- `docker-compose.yml` includes a `db` service (postgres:16-alpine) for local dev and test execution.
- Tests run against this local Postgres — fast, isolated, no Supabase connection limits.
- The `airmed_test` database is created automatically (or via a setup script) for test isolation.
- Connection string for local: `postgresql://airmed:airmed@localhost:5432/airmed_test`
- Connection string for Supabase: stored in `.env` as `DATABASE_URL` (pooler) and `DATABASE_URL_DIRECT` (for Alembic).

### Environment variables (backend)
```
# Local dev / testing
DATABASE_URL=postgresql://airmed:airmed@localhost:5432/airmed

# Supabase production (pooler for app)
DATABASE_URL=postgresql+psycopg2://postgres.[project]:[password]@aws-0-[region].pooler.supabase.com:6542/postgres

# Supabase production (direct for Alembic)
DATABASE_URL_DIRECT=postgresql+psycopg2://postgres.[project]:[password]@aws-0-[region].supabase.com:5432/postgres
```

---

## Evaluation Criteria Tracking

### Mobile (satisfied in Layer 3)
- [ ] Professional design and aesthetics
- [ ] 100% functional across multiple devices (iOS + Android)
- [ ] Clear and understandable mobile navigation for any user
- [ ] Mandatory data validation in all interfaces that send data to the database
- [ ] Mobile app works with at least its own API and its respective database (shared backend = its API)
- [ ] Web application, API, and database hosted on cloud service (Stage 4 deployment)

### Security (satisfied in Stage 4 — deferred but tracked)
- [ ] Demonstrate hashing (bcrypt — already in Layer 1) and encryption methods
- [ ] At least two servers: one public (web/mobile-facing) + one private (DB/LLM/internal)
- [ ] System monitoring (e.g., Prometheus + Grafana)
- [ ] Firewall implementation + monitoring
- [ ] API protection with JWT (already achieved in Layer 1A — document it)
- [ ] SSL certificate for the platform (Supabase connections require SSL; full SSL for web frontend in Stage 4)
- [ ] Load balancer (Nginx/HAProxy/cloud LB) in front of stateless backend
- [ ] Cloud hosting for web app, API, and database (Supabase = DB; web + API on cloud in Stage 4)

---

## Roadmap Overview

```
Layer 0: Cleanup & Foundation
   │
   ▼
Layer 1: Backend complete  (Postgres-only tests, Supabase prod)
   1A → 1B → 1C → 1D → 1E
   │
   ▼
Layer 2: Web Frontend  (React Query + Zustand)
   2A → 2B → 2C → 2D → 2E
   │
   ▼
Layer 3: Mobile  (fresh Expo; patient-facing, mirrors web)
   │
   ▼
Layer 4: Integrations  (llama.cpp for LLM)
   4A → 4B → 4C → 4D
   │
   ▼
[Stage 4: Security & Deployment — PENDING but criteria-anchored]
```

---

## Layer 0 — Cleanup & Foundation

*No separate spec — mechanical fixes bundled into one short plan.*

| # | Task | Why |
|---|------|-----|
| 0.1 | Wire `services` router into `app/api/v1/__init__.py` | Blocks all service endpoints (1-line fix) |
| 0.2 | Commit deletion of `mobile-airmed/` | Clean working tree; fresh scaffold in Layer 3 |
| 0.3 | Clean corrupted root `.env` (contains stray GitHub Actions YAML) | File holds YAML, not env vars |
| 0.4 | Fix `.gitignore` (add `node_modules/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.next/`) | Build artifacts leaking into working tree |
| 0.5 | Fix CI: remove mobile job, add `DATABASE_URL` to backend job | CI currently fails on import |
| 0.6 | Update `docker-compose.yml` to add `airmed_test` database for tests | Postgres-only test strategy needs isolated test DB |
| 0.7 | Update `.env.example` files with Supabase connection string patterns | Document Supabase as production DB |

**Definition of done:** `pytest` passes locally, CI passes on push, working tree clean, all existing service endpoints reachable, docker-compose provides a working local Postgres for dev + tests.

---

## Layer 1 — Backend Complete

### 1A: Finish Core Backend API *(spec + plan exist — tasks 18–24 of `2026-06-08-core-backend-api.md`)*
- Test infrastructure: Postgres test DB (local docker-compose `airmed_test`), fixtures (`client`, `db_session`, `auth_headers`, `test_user`, `test_professional`).
- `test_auth.py`: register, login, google auth, refresh, token rotation, revocation.
- `test_users.py`: `/users/me` happy path + unauthenticated.
- `test_services.py`: CRUD + owner checks + 403 for non-professionals.
- Run full suite, fix failures.
- Generate initial Alembic migration (`alembic revision --autogenerate`); verify `alembic upgrade head` on fresh Postgres.
- **Done:** all existing endpoints tested, migration committed.

### 1B: Availability Module *(new spec + plan)*
- **Design:** availability data model (weekly recurring windows vs. date exceptions, or both), timezone handling, conflict detection rules.
- `Availability` service: CRUD + `is_slot_available(professional_id, start, end)`.
- Endpoints: `GET/POST/PUT/DELETE /api/v1/availability/` (professional-scoped via `get_current_professional`).
- Schemas, Postgres tests, Alembic migration increment.
- **Done:** professional can CRUD availability; overlap detection works.

### 1C: Appointments Module *(new spec + plan)*
- **Design:** appointment state machine (requested → confirmed → completed / cancelled / rescheduled), booking validation against availability (1B), cancellation policy, virtual vs. in-person.
- Replace `pass` stubs: `create_appointment`, `list_appointments` (filters: professional/patient/status/date), `cancel_appointment`, `reschedule_appointment`.
- Endpoints: `POST/GET/PUT/DELETE /api/v1/appointments/`.
- Permission checks: patient sees own, professional sees own.
- Tests, migration.
- **Done:** full appointment lifecycle; no double-booking.

### 1D: Notifications Management *(new spec + plan)*
- **Design:** `Notification` entity (channel: email/WhatsApp/Telegram, status: pending/sent/failed, payload, appointment FK). *Automated dispatch is Stage 3 — out of scope here.*
- Model + service (`create_notification`, `list_notifications`, `mark_sent`) + endpoints.
- Tests, migration.
- **Done:** notifications tracked; ready for Stage 3 automation.

### 1E: Backend Hardening *(new spec + plan)*
- Coverage audit (pytest-cov ~85%).
- Integration tests against real Postgres via docker-compose.
- OpenAPI schema validation / contract tests.
- Input validation review (Pydantic strict modes).
- Migration sequence verified from empty DB → full schema.
- Ensure backend is stateless (supports horizontal scaling for Stage 4 load balancer).
- **Done:** backend complete, tested, production-shaped.

---

## Layer 2 — Web Frontend Complete

### 2A: Auth UI + Token Handling *(new spec + plan)*
- **Design:** auth flow (login/register/Google), token storage (httpOnly cookie via backend endpoint vs. localStorage + refresh), route protection, redirect-after-login.
- Pages: `/login`, `/register`, Google sign-in button.
- `lib/api.ts`: auth header injection, 401 → refresh → retry, redirect to login.
- shadcn installs: `input`, `form`, `card`, `label`.
- Route groups: `(auth)` vs. `(dashboard)`.
- Tests: auth flow with mocked API.
- **Done:** user can register, log in, log out; protected routes redirect; tokens refresh.

### 2B: UI Component Foundation *(new spec + plan)*
- **Design:** component inventory, layout primitives, navigation shell.
- Install shadcn: `dialog`, `table`, `calendar`, `date-picker`, `select`, `tabs`, `toast`, `badge`, `avatar`, `dropdown-menu`, `separator`, `sheet`.
- Layout shell: top nav, sidebar, responsive container.
- **Done:** all components for 2C/2D installed and composable.

### 2C: Professional Panel *(new spec + plan)*
- **Design:** dashboard IA — availability calendar, appointments, services, patient roster.
- Pages: `/dashboard`, `/dashboard/availability`, `/dashboard/appointments`, `/dashboard/services`.
- React Query for server state; Zustand for UI state (filters, selected slot).
- Availability weekly grid (1B), appointments list with status + cancel/reschedule (1C), services CRUD table.
- **Done:** professional manages their practice from web.

### 2D: Patient Panel *(new spec + plan)*
- **Design:** patient UX — discover → service → slot → confirm; history.
- Pages: `/appointments/new`, `/appointments`, `/p/[professional-id]`.
- Slot picker: conflict-free slots from availability + existing appointments.
- Booking confirmation, cancel.
- **Done:** patient books/views/cancels end-to-end via web.

### 2E: Frontend Hardening *(new spec + plan)*
- Test framework: Vitest + React Testing Library; Playwright for E2E.
- Coverage for auth, booking, professional CRUD.
- Error boundaries, loading/empty states, failed-fetch handling.
- Accessibility audit (WCAG 2.1 AA per `.docs/ui`).
- Performance pass (Lighthouse).
- **Done:** frontend complete, tested, accessible.

---

## Layer 3 — Mobile Complete

### 3A: Mobile App *(new spec + plan — may split into 3A/3B/3C after design)*
- **Design:** fresh Expo scaffold (file-based routing per AGENTS.md structure), patient-only scope (mirrors web 2D), auth (Google Sign-In via Expo Auth Session + SecureStore token persistence), push notifications (Expo Notifications — required for Stage 3), API client pointing to shared backend.
- Pages: auth, appointment booking (slot picker), appointment list, cancel.
- Data validation on all forms (evaluation criterion).
- Cross-device testing (iOS + Android simulators).
- Tests: Jest + React Native Testing Library.
- **Done:** patient installs, logs in, books, views, cancels; push token registered.

---

## Layer 4 — Integrations Complete

### 4A: Google Calendar Integration *(new spec + plan)*
- **Design:** OAuth scopes (`calendar.events`), per-professional calendar linking, event payload (virtual link vs. office address), reminder defaults, sync strategy.
- `google_calendar_service.py`: `create_event`, `update_event`, `delete_event`.
- Store `google_event_id` on Appointment (field exists).
- Endpoint: `POST /api/v1/integrations/google/connect` + callback.
- Background task on appointment create/update/cancel.
- Tests with mocked Calendar API.
- **Done:** booking creates Calendar event; reschedule/cancel syncs.

### 4B: On-Prem LLM *(new spec + plan)*
- **Design:** Gemma-4-E2B via llama.cpp, inference server (Docker), intent schema (schedule/reschedule/cancel/query), entity extraction (date/time/service/professional), prompt design (Spanish), JSON response format, latency budget, fallback.
- `llm_service.py`: `interpret_message(text) → IntentResult`.
- Few-shot examples; golden test set.
- Local inference server + health check.
- **Done:** natural-language messages parse to structured intents.

### 4C: WhatsApp Bot *(new spec + plan)*
- **Design:** WhatsApp Business API webhook, conversation state machine, session store (Redis), templates, opt-in/out, fallback.
- Webhook: `POST /api/v1/bots/whatsapp/webhook`.
- Flow: msg → LLM (4B) → availability (1B) → propose slot → confirm → appointment (1C) → Calendar (4A) → reply.
- Tests with mocked WhatsApp + LLM.
- **Done:** patient books via WhatsApp end-to-end.

### 4D: Telegram Bot *(new spec + plan)*
- **Design:** Telegram Bot API, shared conversation engine with 4C (refactor to `bot_conversation_service`).
- Webhook: `POST /api/v1/bots/telegram/webhook`.
- Tests.
- **Done:** patient books via Telegram end-to-end.

---

## [PENDING] Stage 4 — Security & Deployment

*Deferred per decision, but the Stage 4 plan must explicitly satisfy each security evaluation criterion. Tracked here as a checklist:*

- [ ] Demonstrate hashing (bcrypt — already in Layer 1) and encryption methods
- [ ] At least two servers: one public (web/mobile-facing) + one private (DB/LLM/internal)
- [ ] System monitoring (e.g., Prometheus + Grafana)
- [ ] Firewall implementation + monitoring
- [ ] API protection with JWT (already achieved in Layer 1A — document it)
- [ ] SSL certificate for the platform (Supabase connections already require SSL; full SSL via Let's Encrypt/cloud in Stage 4)
- [ ] Load balancer (Nginx/HAProxy/cloud LB) in front of stateless backend
- [ ] Cloud hosting for web app, API, and database (Supabase = DB already; web + API deployed to cloud in Stage 4)

---

## Per-Sub-Project Rhythm

Each sub-project (except Layer 0 and 1A which already has its spec/plan) follows this cycle:

1. **Brainstorm** — clarify requirements, propose approaches, present design sections, get approval.
2. **Write spec** → `docs/superpowers/specs/YYYY-MM-DD-<name>-design.md`, commit.
3. **Self-review spec** — fix placeholders/contradictions; user review gate.
4. **Write plan** → `docs/superpowers/plans/YYYY-MM-DD-<name>.md`, TDD bite-sized tasks, commit.
5. **Execute** — subagent-driven (recommended) or inline; verify before each commit.

Stage 1 design work (requirements, DB schema, UI/UX, flow design) is distributed into steps 1–2 of each sub-project — not done as a separate upfront phase.

---

## Existing Work Absorbed

| Existing artifact | Status | Disposition |
|-------------------|--------|-------------|
| `docs/superpowers/specs/2026-06-08-core-backend-api-design.md` | Spec for sub-project 1 | Retained; Layer 1A implements it |
| `docs/superpowers/plans/2026-06-08-core-backend-api.md` | 24-task plan, ~75% done (tasks 1–17 complete, 18–24 pending) | Resumed in Layer 1A; tasks 18–24 adapted to Postgres-only test infra |
| Backend auth (register/login/google/refresh) | Fully implemented | Tested in Layer 1A |
| Backend services CRUD | Implemented but not wired | Wired in Layer 0.1, tested in Layer 1A |
| Backend appointments/availability | Stubs | Implemented in Layer 1B/1C |
| Frontend (placeholder page + button) | Greenfield | Built in Layer 2 |
| Mobile directory | Deleted (uncommitted) | Deletion committed in Layer 0.2; fresh scaffold in Layer 3 |
| Alembic | Configured, no migrations | First migration generated in Layer 1A |
| Tests | Only health check | Full coverage in Layer 1A + 1E |
