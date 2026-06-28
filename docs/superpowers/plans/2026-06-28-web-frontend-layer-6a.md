# Execution Plan: Layer 6A — Frontend Foundation & Auth

**Spec:** `docs/superpowers/specs/2026-06-28-web-frontend-architecture.md`
**Verify:** `npm run build` (must succeed without errors)
**Format:** `npm run format`

---

## Task 1 — Install dependencies

```bash
pnpm add @tanstack/react-query zustand react-hook-form @hookform/resolvers zod date-fns
```

**Check:** `package.json` updated, `pnpm-lock.yaml` updated.

---

## Task 2 — Create Zustand auth store

**File:** `stores/auth-store.ts`

```ts
interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  refreshAuth: () => Promise<void>
  hydrate: () => void  // load from localStorage on mount
}
```

- Tokens stored in Zustand + synced to `localStorage`
- `login` calls API, stores tokens + user
- `refreshAuth` calls refresh endpoint, updates tokens
- `logout` clears everything
- `hydrate` called on app init to restore session

**TDD?** No.

---

## Task 3 — Enhance apiFetch

**File:** `lib/api.ts`

- Accept optional `{ auth?: boolean }` option (default true)
- Read token from Zustand store (via a non-reactive helper to avoid hook rules)
- Inject `Authorization: Bearer <token>` header
- On 401 response, attempt token refresh, retry original request once
- On refresh failure, logout

Implementation note: Since `apiFetch` is called outside React components in service files, import the store's `getState()` method directly (Zustand supports this).

---

## Task 4 — Create providers

**File:** `providers/query-provider.tsx`
- Wraps children in `QueryClientProvider`
- Creates `QueryClient` with sensible defaults (staleTime: 30s, retry: 1)

**File:** `providers/auth-provider.tsx`
- Client component (`"use client"`)
- Calls `hydrate()` on mount to restore session from localStorage
- Provides nothing extra (Zustand is accessed directly via hooks)

---

## Task 5 — Update root layout

**File:** `app/layout.tsx`

Wrap children:
```
QueryClientProvider → AuthProvider → ThemeProvider → children
```

---

## Task 6 — Build login page

**File:** `app/(auth)/login/page.tsx` (client component)

Form fields:
- Email (required, valid email)
- Password (required, min 6 chars)

On success:
- Store auth in Zustand
- Redirect: `/` (which routes to appropriate dashboard based on role)

UI:
- Centered card layout
- Link to register
- Error display for invalid credentials

---

## Task 7 — Build register page

**File:** `app/(auth)/register/page.tsx` (client component)

Form fields:
- Full name (required)
- Email (required, valid email)
- Password (required, min 6 chars)
- Confirm password (must match)
- I am a professional (checkbox, default false)

On success:
- Redirect to login with success message (or auto-login)

---

## Task 8 — Create auth layout

**File:** `app/(auth)/layout.tsx`
- Simple centered layout
- Redirects to / if already authenticated

---

## Task 9 — Create patient layout

**File:** `app/(patient)/layout.tsx`
- Auth guard: redirects to /login if not authenticated
- Sidebar nav: Appointments, Book Appointment, Profile
- Header: user info + logout button

---

## Task 10 — Create professional layout

**File:** `app/(professional)/layout.tsx`
- Auth guard: redirects to /login if not authenticated
- Role guard: redirects to / if not a professional
- Sidebar nav: Appointments, Availability, Services, Overview
- Header: user info + logout button

---

## Task 11 — Create landing pages

**File:** `app/page.tsx` — redirects based on role (patient → /appointments, professional → /professional)

**File:** `app/(patient)/page.tsx` — simple "Your Appointments" placeholder

**File:** `app/(professional)/page.tsx` — simple "Overview" placeholder

---

## Task 12 — Verify

```bash
npm run build
```

Must compile without errors.

---

## Files Summary

| Action | File |
|--------|------|
| Modify | `lib/api.ts` |
| Create | `stores/auth-store.ts` |
| Create | `providers/query-provider.tsx` |
| Create | `providers/auth-provider.tsx` |
| Create | `lib/constants.ts` |
| Modify | `app/layout.tsx` |
| Create | `app/(auth)/layout.tsx` |
| Create | `app/(auth)/login/page.tsx` |
| Create | `app/(auth)/register/page.tsx` |
| Create | `app/(patient)/layout.tsx` |
| Create | `app/(patient)/page.tsx` |
| Create | `app/(professional)/layout.tsx` |
| Create | `app/(professional)/page.tsx` |
| Create | `components/sidebar.tsx` |
| Modify | `app/page.tsx` |
