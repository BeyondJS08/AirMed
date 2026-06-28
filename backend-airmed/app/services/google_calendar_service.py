import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.integration import ProfessionalIntegration
from app.models.user import User
from app.services.integration_service import get_integration, upsert_integration

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"


def _refresh_access_token(integration: ProfessionalIntegration) -> dict:
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": integration.refresh_token,
        "grant_type": "refresh_token",
    }
    with httpx.Client() as client:
        resp = client.post(GOOGLE_TOKEN_URL, data=payload)
        if resp.status_code != 200:
            logger.error(
                "Token refresh failed: %s %s",
                resp.status_code,
                resp.text,
            )
            raise RuntimeError("Failed to refresh Google token")
        return resp.json()


def _ensure_valid_token(db: Session, integration: ProfessionalIntegration) -> None:
    now = datetime.now(timezone.utc)
    expires = integration.token_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if expires - now > timedelta(minutes=5):
        return

    token_data = _refresh_access_token(integration)
    new_expiry = datetime.now(timezone.utc) + timedelta(
        seconds=token_data.get("expires_in", 3600)
    )
    upsert_integration(
        db,
        professional_id=integration.professional_id,
        provider=integration.provider,
        access_token=token_data["access_token"],
        refresh_token=integration.refresh_token,
        token_expires_at=new_expiry,
    )
    integration.access_token = token_data["access_token"]
    integration.token_expires_at = new_expiry


def _call_api(
    method: str,
    endpoint: str,
    access_token: str,
    body: dict | None = None,
) -> dict:
    url = f"{GOOGLE_CALENDAR_API}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    with httpx.Client() as client:
        resp = client.request(method, url, headers=headers, json=body)
        if resp.status_code >= 400:
            logger.error(
                "Google Calendar API error: %s %s",
                resp.status_code,
                resp.text,
            )
            resp.raise_for_status()
        return resp.json() if resp.text else {}


def _build_event_body(db: Session, appointment: Appointment) -> dict:
    patient = db.query(User).filter(User.id == appointment.patient_id).first()
    patient_name = patient.full_name if patient and patient.full_name else "Patient"

    description = f"Appointment #{appointment.id}\nPatient: {patient_name}"
    if appointment.notes:
        description += f"\nNotes: {appointment.notes}"

    body = {
        "summary": f"Consulta — {patient_name}",
        "description": description,
        "start": {
            "dateTime": appointment.start_time.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": appointment.end_time.isoformat(),
            "timeZone": "UTC",
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 30},
                {"method": "popup", "minutes": 10},
            ],
        },
    }
    if appointment.is_virtual:
        body["conferenceData"] = {
            "createRequest": {
                "requestId": f"airmed-{appointment.id}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }
    elif appointment.location:
        body["location"] = appointment.location
    return body


def create_event(
    db: Session,
    appointment: Appointment,
    integration: ProfessionalIntegration,
) -> None:
    _ensure_valid_token(db, integration)
    body = _build_event_body(db, appointment)
    conference_data_version = 1 if appointment.is_virtual else 0
    endpoint = f"calendars/primary/events?conferenceDataVersion={conference_data_version}"
    result = _call_api("POST", endpoint, integration.access_token, body)
    appointment.google_event_id = result["id"]
    db.commit()


def update_event(
    db: Session,
    appointment: Appointment,
    integration: ProfessionalIntegration,
) -> None:
    if not appointment.google_event_id:
        create_event(db, appointment, integration)
        return
    _ensure_valid_token(db, integration)
    body = _build_event_body(db, appointment)
    endpoint = f"calendars/primary/events/{appointment.google_event_id}"
    _call_api("PATCH", endpoint, integration.access_token, body)


def delete_event(
    db: Session,
    appointment: Appointment,
    integration: ProfessionalIntegration,
) -> None:
    if not appointment.google_event_id:
        return
    _ensure_valid_token(db, integration)
    endpoint = f"calendars/primary/events/{appointment.google_event_id}"
    _call_api("DELETE", endpoint, integration.access_token)


OPERATION_MAP = {
    "create": create_event,
    "update": update_event,
    "delete": delete_event,
}


def ensure_sync(
    db: Session,
    operation: str,
    appointment: Appointment,
) -> None:
    if not settings.GOOGLE_CALENDAR_ENABLED:
        return
    integration = get_integration(
        db, appointment.professional_id, "google_calendar"
    )
    if not integration:
        return
    func = OPERATION_MAP.get(operation)
    if not func:
        return
    try:
        func(db, appointment, integration)
    except Exception:
        logger.exception(
            "Google Calendar sync failed for appointment %s (operation=%s)",
            appointment.id,
            operation,
        )
