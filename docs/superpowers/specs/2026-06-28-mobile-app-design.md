# Mobile App (Expo) — Layer 3 Design

## Overview

Patient and professional mobile application built with Expo + expo-router. Shares the existing FastAPI backend — no separate mobile API or database. Mirrors the web frontend feature set with native patterns.

## Auth

- **Credentials login**: email/password form → `POST /auth/login` → JWT stored in `expo-secure-store`
- **Google login**: `expo-auth-session` → browser popup → backend OAuth callback → JWT stored same way
- **Token refresh**: API interceptor detects 401, calls `POST /auth/refresh`, retries. Refresh failure clears store and redirects to login
- **Route protection**: root `_layout.tsx` checks auth store before rendering child routes
- No backend changes required — all auth endpoints already exist

## Project Structure

```
mobile-airmed/
├── app/                      # expo-router file-based routes
│   ├── _layout.tsx           # Root layout (auth guard)
│   ├── index.tsx             # Login screen
│   ├── (patient)/
│   │   ├── _layout.tsx       # Patient tab navigator
│   │   ├── appointments.tsx  # List upcoming/past appointments
│   │   ├── book.tsx          # 3-step booking flow
│   │   └── profile.tsx       # Patient profile
│   └── (professional)/
│       ├── _layout.tsx       # Professional tab navigator
│       ├── appointments.tsx  # Manage appointments (confirm/complete/cancel)
│       ├── availability.tsx  # Weekly availability editor
│       ├── services.tsx      # Service CRUD
│       └── integrations.tsx  # Google Calendar link status
├── components/
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── SlotPicker.tsx
│   └── AppointmentCard.tsx
├── api/
│   └── client.ts             # fetch wrapper with auth interceptor
├── hooks/
│   ├── useAuth.ts            # login, logout, token management
│   ├── useAppointments.ts    # React Query hooks
│   ├── useProfessionals.ts
│   ├── useServices.ts
│   └── useAvailability.ts
├── services/
│   ├── auth.ts               # login/register/refresh API calls
│   ├── appointments.ts
│   ├── professionals.ts
│   ├── services.ts
│   └── availability.ts
├── stores/
│   └── authStore.ts          # Zustand store for auth state
├── types/
│   └── index.ts              # TypeScript types matching backend schemas
├── tests/
│   ├── components/
│   └── hooks/
├── app.json
├── tsconfig.json
└── package.json
```

## Screen Map

### Patient
| Screen | Route | Description |
|--------|-------|-------------|
| Appointments | `/appointments` | Upcoming/past tabs, cancel action |
| Book | `/book` | 3-step: professional → service → slot → confirm |
| Profile | `/profile` | Name, email, logout |

### Professional
| Screen | Route | Description |
|--------|-------|-------------|
| Appointments | `/appointments` | List, confirm, complete, cancel |
| Availability | `/availability` | Day-of-week → time range editor |
| Services | `/services` | Add/remove services with duration + price |
| Integration | `/integrations` | Google Calendar link status + link button |

## API Layer

- `api/client.ts` wraps `fetch` with:
  - `Authorization: Bearer <token>` header from `expo-secure-store`
  - 401 detection → refresh token → retry
  - JSON parsing + error normalization
- `services/*.ts` call the client with typed request/response
- `hooks/*.ts` use `@tanstack/react-query` to wrap service functions

## State Management

- **Zustand** for auth state (current user, tokens, loading state)
- **React Query** for all server state with cache invalidation
- No navigation state library — expo-router handles routing

## Testing

- Jest + `@testing-library/react-native` for component/hook tests
- MSW for API mocking in tests
- Test files colocated in `tests/` matching source structure

## Scaffold Steps

1. `npx create-expo-app@latest mobile-airmed --template blank-typescript`
2. Install dependencies: `expo-router`, `@tanstack/react-query`, `zustand`, `expo-secure-store`, `expo-auth-session`, `jest`, `@testing-library/react-native`
3. Configure expo-router in `app.json`
4. Create directory structure from project map above
5. Implement files in order: types → api client → services → stores → hooks → components → screens → layouts

## Out of Scope (Deferred)

- Push notifications (depends on messaging layer)
- Offline support
- Deep linking
- Admin panel
- Animations and custom transitions
- E2E tests (Detox/Maestro)
