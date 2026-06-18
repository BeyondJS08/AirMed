# Core Backend API Design

> **Part of Sub-project 1:** The complete AirMed system is decomposed into 6 sub-projects. This spec covers the first: Core Backend API.

**Architecture:** FastAPI backend with JWT (access + refresh tokens) and Google OAuth authentication, SQLAlchemy ORM with PostgreSQL, Alembic migrations.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL, python-jose (JWT), google-auth (Google OAuth), passlib/bcrypt (password hashing), pydantic-settings (config)

---

## Database Models

### User (Existing + Additions)
- `id` — Integer, PK
- `email` — String, unique, indexed
- `full_name` — String, nullable
- `hashed_password` — String, nullable
- `phone_number` — String, nullable (NEW)
- `is_active` — Boolean, default true
- `is_professional` — Boolean, default false
- `google_id` — String, unique, nullable

### Appointment (Existing — untouched in this sub-project)
### Availability (Existing — untouched in this sub-project)

### Service (NEW)
- `id` — Integer, PK
- `professional_id` — FK to users.id
- `name` — String, not null
- `description` — Text, nullable
- `duration_minutes` — Integer, not null (how long the appointment lasts)
- `price` — Float, nullable

### RefreshToken (NEW)
- `id` — Integer, PK
- `token_hash` — String, unique, indexed (SHA-256 hash of the refresh token)
- `user_id` — FK to users.id
- `expires_at` — DateTime
- `revoked` — Boolean, default false
- `created_at` — DateTime

---

## Auth Flow

### Email/Password Registration
1. `POST /auth/register` receives `email`, `password`, `full_name`
2. Validate email uniqueness
3. Hash password with bcrypt
4. Create User, generate JWT pair
5. Return `{ access_token, refresh_token, user }`

### Email/Password Login
1. `POST /auth/login` receives `email`, `password`
2. Verify password hash
3. Generate JWT pair
4. Return `{ access_token, refresh_token, user }`

### Google OAuth
1. Frontend/mobile performs Google Sign-In client-side, obtains ID token
2. Posts `{ id_token }` to `POST /auth/google`
3. Backend verifies ID token using `google-auth` library
4. Extract email, name, google_id from verified token
5. Find existing user by google_id or email, or create new
6. Generate JWT pair
7. Return `{ access_token, refresh_token, user }`

### Token Refresh
1. `POST /auth/refresh` receives `{ refresh_token }`
2. Hash the token, look up in refresh_tokens table
3. Verify not expired, not revoked
4. Issue new access + refresh token pair (revoke old refresh token)

### JWT Structure
- Access token: `{ sub: user_id, exp, type: "access" }`, expires in 15 minutes
- Refresh token: random 64-byte hex string (opaque), stored as SHA-256 hash, expires in 7 days

---

## API Endpoints

### Auth (`/api/v1/auth`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | No | Register with email/password |
| POST | `/login` | No | Login with email/password |
| POST | `/google` | No | Login/register with Google ID token |
| POST | `/refresh` | No | Refresh access token |

### Users (`/api/v1/users`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/me` | Yes | Get current user profile |

### Services (`/api/v1/services`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Yes | List services (filter by `professional_id` query param) |
| POST | `/` | Yes | Create service (professional only) |
| GET | `/{id}` | Yes | Get service by ID |
| PUT | `/{id}` | Yes | Update service (owner only) |
| DELETE | `/{id}` | Yes | Delete service (owner only) |

---

## Security

- JWT access tokens: 15-minute expiry, signed with HS256 using SECRET_KEY
- Refresh tokens: opaque random strings, stored as SHA-256 hashes, 7-day expiry
- Google ID token verified via `google-auth` library (checks iss, aud, exp)
- Password hashing with bcrypt via passlib
- CORS already configured in main.py
- Protect professional-only endpoints with a `get_current_professional` dependency

---

## Implementation Notes

- Create `app/api/deps.py` for shared dependencies (get_current_user, get_current_professional)
- All models must be imported in `app/models/__init__.py` for Alembic autodetection
- `Alembic` initial migration will include all 5 models (User, Appointment, Availability, Service, RefreshToken)
- Password field in UserCreate is nullable to allow Google-only users

---

## Out of Scope (Sub-project 1)

- Appointment CRUD endpoints
- Availability CRUD endpoints
- Google Calendar integration
- LLM integration
- WhatsApp/Telegram bots
- Notifications
- Frontend/mobile implementation
