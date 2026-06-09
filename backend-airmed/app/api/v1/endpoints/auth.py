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
