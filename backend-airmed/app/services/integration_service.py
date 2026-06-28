from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.integration import ProfessionalIntegration


def get_integration(
    db: Session,
    professional_id: int,
    provider: str = "google_calendar",
) -> ProfessionalIntegration | None:
    return (
        db.query(ProfessionalIntegration)
        .filter(
            ProfessionalIntegration.professional_id == professional_id,
            ProfessionalIntegration.provider == provider,
        )
        .first()
    )


def upsert_integration(
    db: Session,
    professional_id: int,
    provider: str,
    access_token: str,
    refresh_token: str,
    token_expires_at: datetime,
    google_email: str | None = None,
) -> ProfessionalIntegration:
    existing = get_integration(db, professional_id, provider)
    if existing:
        existing.access_token = access_token
        existing.refresh_token = refresh_token
        existing.token_expires_at = token_expires_at
        if google_email is not None:
            existing.google_email = google_email
    else:
        existing = ProfessionalIntegration(
            professional_id=professional_id,
            provider=provider,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            google_email=google_email,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def delete_integration(
    db: Session,
    professional_id: int,
    provider: str = "google_calendar",
) -> None:
    integration = get_integration(db, professional_id, provider)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )
    db.delete(integration)
    db.commit()


def get_or_none(
    db: Session,
    professional_id: int,
    provider: str = "google_calendar",
) -> ProfessionalIntegration | None:
    return get_integration(db, professional_id, provider)
