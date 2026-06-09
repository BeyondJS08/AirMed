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
