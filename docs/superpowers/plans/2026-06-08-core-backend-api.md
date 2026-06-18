# Core Backend API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the complete FastAPI backend with JWT auth, Google OAuth, user management, and service CRUD.

**Architecture:** FastAPI + SQLAlchemy + PostgreSQL with JWT access/refresh tokens and Google OAuth. Test infrastructure uses SQLite in-memory for CI.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL, python-jose, google-auth, passlib, pytest

---

## File Structure

### New files to create:
- `backend-airmed/app/models/service.py` — Service model (professional_id, name, description, duration_minutes, price)
- `backend-airmed/app/models/refresh_token.py` — RefreshToken model (token_hash, user_id, expires_at, revoked, created_at)
- `backend-airmed/app/schemas/token.py` — TokenResponse, TokenRefresh schemas
- `backend-airmed/app/schemas/auth.py` — GoogleAuthRequest, LoginRequest schemas
- `backend-airmed/app/schemas/service.py` — ServiceBase, ServiceCreate, ServiceUpdate, ServiceOut
- `backend-airmed/app/api/deps.py` — get_current_user, get_current_professional dependencies
- `backend-airmed/app/services/auth_service.py` — Auth business logic (register, login, google auth, refresh)
- `backend-airmed/app/services/service_service.py` — Service CRUD
- `backend-airmed/tests/test_auth.py` — Auth endpoint tests
- `backend-airmed/tests/test_users.py` — User endpoint tests
- `backend-airmed/tests/test_services.py` — Service CRUD tests

### Files to modify:
- `backend-airmed/app/models/user.py` — Add phone_number column
- `backend-airmed/app/models/__init__.py` — Import all 5 models
- `backend-airmed/app/schemas/user.py` — Add phone_number to UserBase, UserOut
- `backend-airmed/app/core/config.py` — Add JWT settings (JWT_SECRET, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, GOOGLE_CLIENT_ID)
- `backend-airmed/app/core/security.py` — Add create_access_token, create_refresh_token, decode_access_token functions
- `backend-airmed/app/services/user_service.py` — Implement create_user, get_user_by_email, get_user_by_id, get_user_by_google_id
- `backend-airmed/app/api/v1/endpoints/auth.py` — Rewrite with real register, login, google, refresh handlers
- `backend-airmed/app/api/v1/endpoints/users.py` — Rewrite with real /me handler
- `backend-airmed/app/api/v1/__init__.py` — Add services router
- `backend-airmed/tests/conftest.py` — Add SQLite in-memory test DB fixture, create test user fixture

---

### Task 1: Update config with JWT settings

**Files:**
- Modify: `backend-airmed/app/core/config.py`

- [ ] **Step 1: Add JWT and Google settings to Settings class**

Read the current config:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    REDIS_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
```

Replace with:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    REDIS_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/core/config.py
git commit -m "feat: add JWT and Google OAuth settings"
```

---

### Task 2: Add JWT token functions to security

**Files:**
- Modify: `backend-airmed/app/core/security.py`

- [ ] **Step 1: Add JWT creation and verification functions**

Current content:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

Replace with:
```python
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> str:
    return secrets.token_hex(64)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/core/security.py
git commit -m "feat: add JWT token creation, hashing, and verification"
```

---

### Task 3: Update User model - add phone_number

**Files:**
- Modify: `backend-airmed/app/models/user.py`

- [ ] **Step 1: Add phone_number column**

Current:
```python
from sqlalchemy import Column, Integer, String, Boolean
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_professional = Column(Boolean, default=False)
    google_id = Column(String, unique=True, nullable=True)
```

Replace with:
```python
from sqlalchemy import Column, Integer, String, Boolean
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_professional = Column(Boolean, default=False)
    google_id = Column(String, unique=True, nullable=True)
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/models/user.py
git commit -m "feat: add phone_number to User model"
```

---

### Task 4: Create Service model

**Files:**
- Create: `backend-airmed/app/models/service.py`

- [ ] **Step 1: Write the Service model**

```python
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from app.db.base import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/models/service.py
git commit -m "feat: add Service model"
```

---

### Task 5: Create RefreshToken model

**Files:**
- Create: `backend-airmed/app/models/refresh_token.py`

- [ ] **Step 1: Write the RefreshToken model**

```python
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/models/refresh_token.py
git commit -m "feat: add RefreshToken model"
```

---

### Task 6: Import all models in __init__.py

**Files:**
- Modify: `backend-airmed/app/models/__init__.py`

- [ ] **Step 1: Import all models for Alembic auto-detection**

```python
from app.models.user import User
from app.models.appointment import Appointment
from app.models.availability import Availability
from app.models.service import Service
from app.models.refresh_token import RefreshToken
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/models/__init__.py
git commit -m "feat: import all models for Alembic"
```

---

### Task 7: Update User schemas

**Files:**
- Modify: `backend-airmed/app/schemas/user.py`

- [ ] **Step 1: Add phone_number to UserBase and adjust UserCreate**

Current:
```python
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str | None = None


class UserUpdate(UserBase):
    pass


class UserOut(UserBase):
    id: int
    is_active: bool
    is_professional: bool

    model_config = ConfigDict(from_attributes=True)
```

Replace with:
```python
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    phone_number: str | None = None


class UserCreate(UserBase):
    password: str | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone_number: str | None = None


class UserOut(UserBase):
    id: int
    is_active: bool
    is_professional: bool
    google_id: str | None = None

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/schemas/user.py
git commit -m "feat: add phone_number to user schemas"
```

---

### Task 8: Create Token schemas

**Files:**
- Create: `backend-airmed/app/schemas/token.py`

- [ ] **Step 1: Write token schemas**

```python
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/schemas/token.py
git commit -m "feat: add token schemas"
```

---

### Task 9: Create Auth schemas

**Files:**
- Create: `backend-airmed/app/schemas/auth.py`

- [ ] **Step 1: Write auth request schemas**

```python
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/schemas/auth.py
git commit -m "feat: add auth request schemas"
```

---

### Task 10: Create Service schemas

**Files:**
- Create: `backend-airmed/app/schemas/service.py`

- [ ] **Step 1: Write Service schemas**

```python
from pydantic import BaseModel, ConfigDict


class ServiceBase(BaseModel):
    name: str
    description: str | None = None
    duration_minutes: int
    price: float | None = None


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    duration_minutes: int | None = None
    price: float | None = None


class ServiceOut(ServiceBase):
    id: int
    professional_id: int

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/schemas/service.py
git commit -m "feat: add Service schemas"
```

---

### Task 11: Create shared dependencies (deps.py)

**Files:**
- Create: `backend-airmed/app/api/deps.py`

- [ ] **Step 1: Write shared dependency functions**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def get_current_professional(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_professional:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professional access required",
        )
    return current_user
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/api/deps.py
git commit -m "feat: add auth dependencies (get_current_user, get_current_professional)"
```

---

### Task 12: Implement User service

**Files:**
- Modify: `backend-airmed/app/services/user_service.py`

- [ ] **Step 1: Implement user CRUD operations**

Current:
```python
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, user: UserCreate) -> User:
    pass


def get_user_by_email(db: Session, email: str) -> User | None:
    pass
```

Replace with:
```python
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        hashed_password=get_password_hash(user.password) if user.password else None,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_google_user(
    db: Session, email: str, full_name: str | None, google_id: str
) -> User:
    db_user = User(
        email=email,
        full_name=full_name,
        google_id=google_id,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_google_id(db: Session, google_id: str) -> User | None:
    return db.query(User).filter(User.google_id == google_id).first()
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/services/user_service.py
git commit -m "feat: implement user service with email and Google auth support"
```

---

### Task 13: Implement Auth service

**Files:**
- Create: `backend-airmed/app/services/auth_service.py`

- [ ] **Step 1: Write the auth service**

```python
from datetime import datetime, timedelta, timezone

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import (
    create_google_user,
    create_user,
    get_user_by_email,
    get_user_by_google_id,
)


class AuthResult:
    def __init__(self, access_token: str, refresh_token: str, user: User):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user = user


def _create_token_pair(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(user.id)
    raw_refresh = create_refresh_token()
    token_hash = hash_refresh_token(raw_refresh)
    db_token = RefreshToken(
        token_hash=token_hash,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_token)
    db.commit()
    return access_token, raw_refresh


def register_user(db: Session, user_data: UserCreate) -> AuthResult:
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise ValueError("Email already registered")
    user = create_user(db, user_data)
    access_token, raw_refresh = _create_token_pair(db, user)
    return AuthResult(access_token, raw_refresh, user)


def login_user(db: Session, email: str, password: str) -> AuthResult:
    user = get_user_by_email(db, email)
    if not user or not user.hashed_password:
        raise ValueError("Invalid email or password")
    if not verify_password(password, user.hashed_password):
        raise ValueError("Invalid email or password")
    access_token, raw_refresh = _create_token_pair(db, user)
    return AuthResult(access_token, raw_refresh, user)


def google_auth(db: Session, token: str) -> AuthResult:
    try:
        info = id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise ValueError("Invalid Google token")

    google_id = info["sub"]
    email = info.get("email", "")
    name = info.get("name")

    user = get_user_by_google_id(db, google_id)
    if not user:
        user = get_user_by_email(db, email)
        if user:
            user.google_id = google_id
            db.commit()
            db.refresh(user)
        else:
            user = create_google_user(db, email, name, google_id)

    access_token, raw_refresh = _create_token_pair(db, user)
    return AuthResult(access_token, raw_refresh, user)


def refresh_access_token(db: Session, raw_refresh: str) -> AuthResult:
    token_hash = hash_refresh_token(raw_refresh)
    stored = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )
    if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
        raise ValueError("Invalid or expired refresh token")

    stored.revoked = True
    db.flush()

    user = db.query(User).filter(User.id == stored.user_id).first()
    if not user or not user.is_active:
        raise ValueError("User not found or inactive")

    access_token, new_raw_refresh = _create_token_pair(db, user)
    return AuthResult(access_token, new_raw_refresh, user)
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/services/auth_service.py
git commit -m "feat: implement auth service with register, login, Google OAuth, and token refresh"
```

---

### Task 14: Implement Service service

**Files:**
- Create: `backend-airmed/app/services/service_service.py`

- [ ] **Step 1: Write the Service CRUD service**

```python
from sqlalchemy.orm import Session

from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate


def create_service(
    db: Session, service: ServiceCreate, professional_id: int
) -> Service:
    db_service = Service(
        professional_id=professional_id,
        name=service.name,
        description=service.description,
        duration_minutes=service.duration_minutes,
        price=service.price,
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


def list_services(db: Session, professional_id: int | None = None) -> list[Service]:
    query = db.query(Service)
    if professional_id is not None:
        query = query.filter(Service.professional_id == professional_id)
    return query.all()


def get_service(db: Session, service_id: int) -> Service | None:
    return db.query(Service).filter(Service.id == service_id).first()


def update_service(
    db: Session, db_service: Service, update: ServiceUpdate
) -> Service:
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_service, field, value)
    db.commit()
    db.refresh(db_service)
    return db_service


def delete_service(db: Session, db_service: Service) -> None:
    db.delete(db_service)
    db.commit()
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/services/service_service.py
git commit -m "feat: implement service CRUD"
```

---

### Task 15: Rewrite Auth endpoints with real logic

**Files:**
- Modify: `backend-airmed/app/api/v1/endpoints/auth.py`

- [ ] **Step 1: Replace stub with full auth implementation**

Replace the entire file with:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import GoogleAuthRequest, LoginRequest
from app.schemas.token import TokenRefresh, TokenResponse
from app.schemas.user import UserCreate
from app.services.auth_service import (
    google_auth,
    login_user,
    refresh_access_token,
    register_user,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        result = register_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = login_user(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post("/google", response_model=TokenResponse)
async def google(body: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        result = google_auth(db, body.id_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: TokenRefresh, db: Session = Depends(get_db)):
    try:
        result = refresh_access_token(db, body.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/api/v1/endpoints/auth.py
git commit -m "feat: implement auth endpoints (register, login, google, refresh)"
```

---

### Task 16: Rewrite Users endpoint

**Files:**
- Modify: `backend-airmed/app/api/v1/endpoints/users.py`

- [ ] **Step 1: Replace stub with real /me handler**

Current:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_current_user(db: Session = Depends(get_db)):
    pass
```

Replace with:
```python
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/api/v1/endpoints/users.py
git commit -m "feat: implement GET /users/me endpoint"
```

---

### Task 17: Create Services endpoints

**Files:**
- Create: `backend-airmed/app/api/v1/endpoints/services.py`

- [ ] **Step 1: Write services CRUD endpoints**

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_professional, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate
from app.services.service_service import (
    create_service,
    delete_service,
    get_service,
    list_services,
    update_service,
)

router = APIRouter()


@router.get("/", response_model=list[ServiceOut])
async def list_all_services(
    professional_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list_services(db, professional_id)


@router.post("/", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
async def create_new_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_professional),
):
    return create_service(db, service, current_user.id)


@router.get("/{service_id}", response_model=ServiceOut)
async def get_service_by_id(
    service_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    db_service = get_service(db, service_id)
    if not db_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return db_service


@router.put("/{service_id}", response_model=ServiceOut)
async def update_service_by_id(
    service_id: int,
    update: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_professional),
):
    db_service = get_service(db, service_id)
    if not db_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if db_service.professional_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your service")
    return update_service(db, db_service, update)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_by_id(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_professional),
):
    db_service = get_service(db, service_id)
    if not db_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if db_service.professional_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your service")
    delete_service(db, db_service)
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/api/v1/endpoints/services.py
git commit -m "feat: implement services CRUD endpoints"
```

---

### Task 18: Update router aggregator

**Files:**
- Modify: `backend-airmed/app/api/v1/__init__.py`

- [ ] **Step 1: Add services router**

Current:
```python
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, appointments

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
```

Replace with:
```python
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, appointments, services

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/app/api/v1/__init__.py
git commit -m "feat: register services router"
```

---

### Task 19: Improve test infrastructure

**Files:**
- Modify: `backend-airmed/tests/conftest.py`

- [ ] **Step 1: Add SQLite in-memory test database and fixtures**

Current:
```python
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
```

Replace with:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.core.security import get_password_hash

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("password123"),
        is_professional=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_professional(db_session):
    user = User(
        email="professional@example.com",
        full_name="Dr. Professional",
        hashed_password=get_password_hash("password123"),
        is_professional=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_token(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def professional_token(client, test_professional):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "professional@example.com", "password": "password123"},
    )
    return response.json()["access_token"]
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/tests/conftest.py
git commit -m "test: add SQLite test database and fixtures"
```

---

### Task 20: Write Auth endpoint tests

**Files:**
- Create: `backend-airmed/tests/test_auth.py`

- [ ] **Step 1: Write test file with auth test cases**

```python
def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "secure123", "full_name": "New User"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "secure123"},
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "secure123"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_password(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401


def test_refresh_token_success(client, test_user):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_revoked_after_use(client, test_user):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 401


def test_refresh_invalid_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalidtoken123"},
    )
    assert response.status_code == 401


def test_access_protected_endpoint_without_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_access_protected_endpoint_with_valid_token(client, test_user):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/tests/test_auth.py
git commit -m "test: add auth endpoint tests"
```

---

### Task 21: Write User endpoint tests

**Files:**
- Create: `backend-airmed/tests/test_users.py`

- [ ] **Step 1: Write user endpoint tests**

```python
def test_get_me_authenticated(client, user_token):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "google_id" in data


def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalidtoken123"},
    )
    assert response.status_code == 401
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/tests/test_users.py
git commit -m "test: add user endpoint tests"
```

---

### Task 22: Write Service CRUD tests

**Files:**
- Create: `backend-airmed/tests/test_services.py`

- [ ] **Step 1: Write service test cases**

```python
def test_create_service_as_professional(client, professional_token):
    response = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={
            "name": "General Checkup",
            "description": "A standard medical checkup",
            "duration_minutes": 30,
            "price": 150.0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "General Checkup"
    assert data["duration_minutes"] == 30
    assert data["price"] == 150.0
    assert "id" in data


def test_create_service_as_non_professional(client, user_token):
    response = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "name": "Checkup",
            "duration_minutes": 30,
        },
    )
    assert response.status_code == 403


def test_create_service_unauthenticated(client):
    response = client.post(
        "/api/v1/services/",
        json={"name": "Checkup", "duration_minutes": 30},
    )
    assert response.status_code == 401


def test_list_services(client, professional_token):
    client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    response = client.get(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_service_by_id(client, professional_token):
    create_resp = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    service_id = create_resp.json()["id"]

    response = client.get(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Checkup"


def test_get_service_not_found(client, professional_token):
    response = client.get(
        "/api/v1/services/9999",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 404


def test_update_service_by_owner(client, professional_token):
    create_resp = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    service_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Extended Checkup", "duration_minutes": 45},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Extended Checkup"
    assert response.json()["duration_minutes"] == 45


def test_update_service_not_owner(client, professional_token, user_token):
    create_resp = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    service_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"name": "Hacked"},
    )
    assert response.status_code == 403


def test_delete_service_by_owner(client, professional_token):
    create_resp = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    service_id = create_resp.json()["id"]

    response = client.delete(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 204


def test_delete_service_not_owner(client, professional_token, user_token):
    create_resp = client.post(
        "/api/v1/services/",
        headers={"Authorization": f"Bearer {professional_token}"},
        json={"name": "Checkup", "duration_minutes": 30},
    )
    service_id = create_resp.json()["id"]

    response = client.delete(
        f"/api/v1/services/{service_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Commit**

```bash
git add backend-airmed/tests/test_services.py
git commit -m "test: add service CRUD tests"
```

---

### Task 23: Run all tests and fix any failures

**Files:**
- No file changes — verification step

- [ ] **Step 1: Run tests**

Run: `cd backend-airmed && python -m pytest tests/ -v`
Expected: All tests PASS

If any tests fail, fix the implementation code or test code, then re-run until all pass.

- [ ] **Step 2: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve test failures"
```

---

### Task 24: Generate initial Alembic migration

**Files:**
- Modify: `backend-airmed/alembic/env.py`
- Create: `backend-airmed/alembic/versions/0001_initial_migration.py`

- [ ] **Step 1: Add model imports to alembic/env.py for autodetection**

Current (around line 8-9):
```python
from app.core.config import settings
from app.db.base import Base
```

Replace with:
```python
from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401 - Import all models to populate Base.metadata
```

- [ ] **Step 2: Generate autogenerated migration**

Ensure a database is accessible (Docker PostgreSQL) or set DATABASE_URL to point to a running instance, then:

```bash
cd backend-airmed
alembic revision --autogenerate -m "Initial migration"
```

- [ ] **Step 3: Review the generated migration and upgrade**

```bash
alembic upgrade head
```

Expected: All tables created (users, appointments, availabilities, services, refresh_tokens)

- [ ] **Step 4: Commit**

```bash
git add alembic/env.py alembic/versions/
git commit -m "feat: add initial database migration"
```
