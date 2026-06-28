from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_professional
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.integration import ProfessionalIntegrationOut
from app.services.integration_service import get_integration, upsert_integration

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


@router.get("/google/auth")
async def google_auth(
    professional: User = Depends(get_current_professional),
):
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return {"auth_url": auth_url}


@router.post("/google/tokens")
async def google_exchange_tokens(
    code: str = Query(),
    db: Session = Depends(get_db),
    professional: User = Depends(get_current_professional),
):
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code",
        )

    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code",
            )

    token_data = resp.json()
    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        existing = get_integration(db, professional.id, "google_calendar")
        if existing and existing.refresh_token:
            refresh_token = existing.refresh_token

    from datetime import datetime, timedelta, timezone

    upsert_integration(
        db,
        professional_id=professional.id,
        provider="google_calendar",
        access_token=token_data["access_token"],
        refresh_token=refresh_token,
        token_expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=token_data.get("expires_in", 3600)),
        google_email=token_data.get("email"),
    )

    return {"status": "connected"}


@router.get("/google/status", response_model=ProfessionalIntegrationOut | None)
async def google_status(
    db: Session = Depends(get_db),
    professional: User = Depends(get_current_professional),
):
    return get_integration(db, professional.id, "google_calendar")
