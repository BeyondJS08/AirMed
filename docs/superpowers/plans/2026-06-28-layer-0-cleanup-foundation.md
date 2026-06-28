# Layer 0: Cleanup & Foundation Implementation Plan

> **For agentic workers:** Simple mechanical plan — sequential inline execution recommended. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix blocking infrastructure and configuration issues before resuming feature development.

**Scope:** Router wiring, environment cleanup, gitignore, CI fix, docker-compose test database setup, env.example updates for Supabase.

**Tech Stack:** FastAPI, PostgreSQL/PostGIS, Docker Compose, GitHub Actions

---

## Files to Modify

| File | Change | Responsibility |
|------|--------|----------------|
| `backend-airmed/app/api/v1/__init__.py` | Add `services` router import + include_router call | Router wiring |
| `.env` (gitignored) | Clear corrupted YAML content | Environment cleanup |
| `.env.example` | Add Supabase connection patterns (pooler + direct) | Documentation |
| `backend-airmed/.env.example` | Add `DATABASE_URL_DIRECT` for Alembic | Documentation |
| `.gitignore` | Add missing entries (node_modules, .venv, __pycache__, etc.) | Repo hygiene |
| `.github/workflows/ci.yml` | Remove mobile job; add Postgres service container to backend job | CI fix |
| `docker-compose.yml` | Add Postgres init script for `airmed_test` database | Test infrastructure |
| `backend-airmed/db/init.sql` | Create SQL script to initialize `airmed_test` database | Test infrastructure |

---

### Task 1: Wire services router

**Files:**
- Modify: `backend-airmed/app/api/v1/__init__.py`

- [ ] **Step 1: Edit `__init__.py` to include the services router**

Add the `services` module to the imports and register it on the API router:

From:
```python
from app.api.v1.endpoints import auth, users, appointments

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
```

To:
```python
from app.api.v1.endpoints import auth, users, services, appointments

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
```

- [ ] **Step 2: Verify the router loads correctly**

Run: `python -c "from app.api.v1 import api_router; print(f'Routes: {len(api_router.routes)}')"`

Expected: prints "Routes: N" where N includes service endpoints (register, login, google auth, refresh, users/me, service CRUD, appointment stubs).

- [ ] **Step 3: Verify services endpoints are reachable**

Start the backend with `uvicorn app.main:app --reload` (if Postgres is running) or just import-check:

Run: `python -c "from app.api.v1.endpoints.services import router; print(f'Service routes: {[r.path for r in router.routes]}')"`

Expected: prints `['/services/', '/services/', '/services/{id}', '/services/{id}', '/services/{id}']`

Workdir: `backend-airmed`

---

### Task 2: Clean corrupted .env and update .env.example files

**Files:**
- Modify: `.env` (gitignored, local)
- Modify: `.env.example`
- Modify: `backend-airmed/.env.example`

- [ ] **Step 1: Clear corrupted .env and write local dev config**

The `.env` file currently contains a fragment of GitHub Actions YAML. Since it's gitignored, clear it and write proper local development variables:

From (YAML fragment):
```yaml
  backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./backend-airmed
    steps:
      ...
```

To (local dev config):
```env
# Backend
DATABASE_URL=postgresql://user:password@localhost:5432/airmed
DATABASE_URL_DIRECT=postgresql://user:password@localhost:5432/airmed
SECRET_KEY=dev-secret-key-change-in-production
REDIS_URL=redis://localhost:6379/0
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 2: Update root .env.example with Supabase connection patterns**

From:
```env
# Backend
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Mobile
API_URL=http://localhost:8000
```

To:
```env
# Backend
DATABASE_URL=postgresql+psycopg2://postgres.[project]:[password]@aws-0-[region].pooler.supabase.com:6542/postgres
DATABASE_URL_DIRECT=postgresql+psycopg2://postgres.[project]:[password]@aws-0-[region].supabase.com:5432/postgres
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
REDIS_URL=redis://redis:6379/0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id

# Mobile
API_URL=http://localhost:8000
```

- [ ] **Step 3: Update backend-airmed/.env.example with DATABASE_URL_DIRECT**

From:
```env
DATABASE_URL=postgresql://user:password@db:5432/airmed
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
REDIS_URL=redis://redis:6379/0
```

To:
```env
# App connection (use Supabase pooler with `+psycopg2` in production; local Postgres in dev)
DATABASE_URL=postgresql://user:password@db:5432/airmed
# Direct connection (for Alembic migrations — bypasses pgBouncer/Supavisor)
DATABASE_URL_DIRECT=postgresql://user:password@db:5432/airmed
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
REDIS_URL=redis://redis:6379/0
```

---

### Task 3: Fix .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add missing build/artifact entries**

From:
```gitignore
# Environment
.env
.env.example
.docs

# OS
.DS_Store
```

To:
```gitignore
# Environment
.env
.env.example
.docs

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.pytest_cache/

# Node
node_modules/
.next/

# OS
.DS_Store

# IDE (local only)
.vscode/
```

---

### Task 4: Fix CI workflow

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Remove mobile job and add Postgres service container to backend job**

From (current CI):
```yaml
jobs:
  backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./backend-airmed
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend-airmed
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: corepack enable && pnpm install
      - run: pnpm run build

  mobile:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./mobile-airmed
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: corepack enable && pnpm install
      - run: pnpm run lint
```

To:
```yaml
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: user
          POSTGRES_PASSWORD: password
          POSTGRES_DB: airmed_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    defaults:
      run:
        working-directory: ./backend-airmed
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest
        env:
          DATABASE_URL: postgresql://user:password@localhost:5432/airmed_test

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend-airmed
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: corepack enable && pnpm install
      - run: pnpm run build
```

- [ ] **Step 2: Verify CI workflow YAML is valid**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('Valid YAML')"`

Expected: prints "Valid YAML". If `yaml` not installed, skip or install with `pip install pyyaml`.

---

### Task 5: Update docker-compose with airmed_test database

**Files:**
- Create: `backend-airmed/db/init.sql`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Create database init SQL script**

Create `backend-airmed/db/init.sql`:
```sql
-- Create test database (created alongside the main 'airmed' database)
SELECT 'CREATE DATABASE airmed_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airmed_test')\gexec
```

This uses `\gexec` to conditionally create the database — it runs the SELECT and executes the result only if the condition is true.

- [ ] **Step 2: Mount init script in docker-compose**

Add the init script volume to the `db` service in `docker-compose.yml`. From:
```yaml
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: airmed
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

To:
```yaml
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: airmed
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend-airmed/db/init.sql:/docker-entrypoint-initdb.d/init.sql
```

---

### Task 6: Commit

- [ ] **Step 1: Stage and commit all changes**

```bash
git add backend-airmed/app/api/v1/__init__.py \
        .env \
        .env.example \
        backend-airmed/.env.example \
        .gitignore \
        .github/workflows/ci.yml \
        docker-compose.yml \
        backend-airmed/db/init.sql

git commit -m "chore(layer-0): cleanup and foundation fixes

- Wire services router into app/api/v1/__init__.py (was missing)
- Clear corrupted .env (contained stray CI YAML) and add local dev config
- Update .env.example files with Supabase connection patterns (pooler + direct)
- Fix .gitignore to exclude build artifacts (node_modules, .venv, __pycache__, etc.)
- Fix CI: remove mobile job (directory deleted), add Postgres service container to backend job
- Add backend-airmed/db/init.sql and mount in docker-compose for airmed_test DB"
```

---
