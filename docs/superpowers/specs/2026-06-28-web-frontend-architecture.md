# Layer 6 — Web Frontend Architecture

## Overview

The AirMed web frontend is a Next.js 16 App Router application with Tailwind v4, shadcn/ui, and Radix UI primitives. It serves patients, healthcare professionals, and administrators through role-based dashboards.

## Current State

The scaffold includes:
- Next.js 16.2.6 + React 19.2.4 + Tailwind v4 + shadcn/ui (`radix-luma` style, `mist` base, Tabler icons)
- `Button` component, `ThemeProvider`, `globals.css` with OKLCH theme vars, dark mode toggle (press `d`)
- `lib/api.ts` — bare `apiFetch` wrapper (no auth token management)
- `services/auth.ts`, `services/appointments.ts` — service stubs
- `types/index.ts` — User, Appointment, Availability interfaces
- Empty `stores/`, `hooks/`, `features/`, `tests/` directories

## Missing Dependencies

These must be installed in Layer 6A:
- `@tanstack/react-query` (server state)
- `zustand` (UI state — auth, theme)
- `react-hook-form` + `zod` + `@hookform/resolvers` (forms)
- `date-fns` (date formatting/manipulation)

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth token storage | `localStorage` + Zustand store | Access token stored in localStorage, loaded into Zustand on mount. Backend JWT is short-lived (15min) with refresh token. |
| State: server | React Query (`@tanstack/react-query` v5) | Caching, dedup, refetching for API data (appointments, availabilities, services) |
| State: client | Zustand | Auth state (user, token), UI state (sidebar, modals). Simple, no boilerplate. |
| Forms | react-hook-form + zod | Validation on both client and server schemas |
| Routing pattern | Route groups for roles | `(auth)` for login/register, `(patient)` for patient dashboard, `(professional)` for professional dashboard |
| Protected routes | Layout-level auth check | Middleware or layout redirects to login if no token |
| API client | Enhanced `apiFetch` with auth header injection | Attaches `Authorization: Bearer <token>` from Zustand store, handles 401 → refresh → retry |
| Server vs Client | Pages default server, "use client" where needed | Data fetching via React Query in client components, forms, interactivity |

## Route Structure

```
/(auth)/                # Unauthenticated — login, register
  login/page.tsx
  register/page.tsx

/(patient)/             # Patient dashboard (requires auth)
  layout.tsx            #   ← auth guard + sidebar
  page.tsx              #   upcoming appointments
  appointments/
    page.tsx            #   all appointments
    book/
      page.tsx          #   booking flow (select prof → service → slot → confirm)

/(professional)/        # Professional dashboard (requires auth)
  layout.tsx            #   ← auth guard + is_professional check + sidebar
  page.tsx              #   overview / upcoming appointments
  appointments/
    page.tsx            #   manage appointments
  availability/
    page.tsx            #   manage weekly windows

/api/                   # (backend handled separately)
```

## Data Flow

```
User Action → Client Component → React Query mutation → apiFetch → Backend
                                    ↓
                                React Query cache (refetch/invalidate)
                                    ↓
                                UI re-renders
```

Auth flow:
```
Login → POST /auth/login → access_token + refresh_token → Zustand auth store → apiFetch intercepts 401 → POST /auth/refresh → retry
```

## Sub-Layer Breakdown

### Layer 6A: Foundation & Auth
**Depends on:** Nothing (but must not break existing scaffold)

1. Install missing deps (`@tanstack/react-query`, `zustand`, `react-hook-form`, `zod`, `@hookform/resolvers`, `date-fns`)
2. Create Zustand auth store (token, user, login/logout/refresh actions)
3. Enhance `apiFetch` to inject auth header and handle 401 → refresh → retry
4. Create React Query provider (`QueryClientProvider` in root layout)
5. Build Login page (email + password form, zod validation, redirect based on role)
6. Build Register page (email + password + full_name form, redirect to login)
7. Create auth guard layout (redirect to /login if no token)
8. Create `(patient)` layout with sidebar/nav
9. Create `(professional)` layout with sidebar/nav
10. Wire up `apiFetch` for all existing services (auth, appointments)

### Layer 6B: Patient Dashboard
**Depends on:** 6A

1. Appointments list page (upcoming + past with filters)
2. Book appointment flow (multi-step: select professional → select service → date/time picker → confirm)
3. Appointment detail view (with cancel action, status badge)
4. Profile page (view/edit personal info)

### Layer 6C: Professional Dashboard
**Depends on:** 6A

1. Appointment management page (list, confirm, complete, cancel)
2. Availability management page (CRUD weekly time windows)
3. Service management page (CRUD offered services)
4. Overview page (upcoming appointments summary, stats)

### Layer 6D: Polish & Testing
**Depends on:** 6B, 6C

1. Add loading states (skeleton components, Suspense boundaries)
2. Toast notifications for success/error feedback
3. Responsive layout optimization
4. Error boundaries per page
5. Test setup (Vitest + React Testing Library)
6. Service function tests
7. Auth flow integration tests

## Implementation Priority

Build in this order: **6A → 6B → 6C → 6D**.

Each sub-layer writes its own tests. Layer 6D adds polish and remaining test coverage.

## Files to Create (Layer 6A)

| Action | File |
|--------|------|
| Install | `@tanstack/react-query`, `zustand`, `react-hook-form`, `zod`, `@hookform/resolvers`, `date-fns` |
| Create | `stores/auth-store.ts` |
| Create | `hooks/use-auth.ts` |
| Create | `hooks/use-api.ts` |
| Modify | `lib/api.ts` (auth injection + refresh) |
| Create | `providers/query-provider.tsx` |
| Create | `providers/auth-provider.tsx` |
| Modify | `app/layout.tsx` (add providers) |
| Create | `app/(auth)/login/page.tsx` |
| Create | `app/(auth)/register/page.tsx` |
| Create | `app/(auth)/layout.tsx` |
| Create | `app/(patient)/layout.tsx` |
| Create | `app/(patient)/page.tsx` |
| Create | `app/(professional)/layout.tsx` |
| Create | `app/(professional)/page.tsx` |
| Create | `components/sidebar.tsx` |
| Test | `services/auth.ts` (enhance) |
