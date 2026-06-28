"""Tests for google_calendar_service.py."""
import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.models.appointment import Appointment
from app.models.integration import ProfessionalIntegration
from app.services.google_calendar_service import (
    _ensure_valid_token,
    create_event,
    delete_event,
    ensure_sync,
    update_event,
)
from app.services.integration_service import upsert_integration

MOCK_TOKEN_RESPONSE = {"access_token": "new_at", "expires_in": 3600}
MOCK_EVENT_RESPONSE = {
    "id": "google_event_123",
    "htmlLink": "https://calendar.google.com/event?eid=abc",
}


def _make_appointment(db_session, professional_id, patient_id, **overrides):
    appt = Appointment(
        professional_id=professional_id,
        patient_id=patient_id,
        start_time=datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 7, 15, 11, 0, tzinfo=timezone.utc),
        status="scheduled",
        **overrides,
    )
    db_session.add(appt)
    db_session.commit()
    db_session.refresh(appt)
    return appt


def _setup_integration(db_session, professional_id, expires_at=None):
    if expires_at is None:
        expires_at = datetime(2026, 7, 1, 0, 0, 0)
    return upsert_integration(
        db_session,
        professional_id,
        "google_calendar",
        "at1",
        "rt1",
        expires_at,
    )


def test_refresh_token_when_expired(db_session, test_professional):
    expired = datetime.now(timezone.utc) - timedelta(hours=1)
    _setup_integration(db_session, test_professional.id, expires_at=expired)
    integration = db_session.query(ProfessionalIntegration).first()

    with patch("app.services.google_calendar_service.httpx.Client") as mock_client:
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.post.return_value.status_code = 200
        mock_instance.post.return_value.json.return_value = MOCK_TOKEN_RESPONSE
        _ensure_valid_token(db_session, integration)

    db_session.refresh(integration)
    assert integration.access_token == "new_at"


def test_create_event_sets_google_event_id(db_session, test_professional, test_user):
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.return_value = MOCK_EVENT_RESPONSE
        create_event(db_session, appt, integration)
    db_session.refresh(appt)
    assert appt.google_event_id == "google_event_123"


def test_create_event_virtual_includes_conference_data(
    db_session, test_professional, test_user
):
    appt = _make_appointment(
        db_session, test_professional.id, test_user.id, is_virtual=True
    )
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.return_value = MOCK_EVENT_RESPONSE
        create_event(db_session, appt, integration)
    call_body = mock_call.call_args[0][3]
    assert call_body.get("conferenceData") is not None


def test_create_event_in_person_includes_location(
    db_session, test_professional, test_user
):
    appt = _make_appointment(
        db_session,
        test_professional.id,
        test_user.id,
        location="123 Main St",
    )
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.return_value = MOCK_EVENT_RESPONSE
        create_event(db_session, appt, integration)
    call_body = mock_call.call_args[0][3]
    assert call_body.get("location") == "123 Main St"


def test_update_event_uses_existing_event_id(
    db_session, test_professional, test_user
):
    appt = _make_appointment(
        db_session, test_professional.id, test_user.id, google_event_id="evt_1"
    )
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.return_value = MOCK_EVENT_RESPONSE
        update_event(db_session, appt, integration)
    endpoint = mock_call.call_args[0][1]
    assert "evt_1" in endpoint


def test_update_event_creates_when_no_event_id(
    db_session, test_professional, test_user
):
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.return_value = MOCK_EVENT_RESPONSE
        update_event(db_session, appt, integration)
    db_session.refresh(appt)
    assert appt.google_event_id == "google_event_123"


def test_delete_event_uses_event_id(db_session, test_professional, test_user):
    appt = _make_appointment(
        db_session, test_professional.id, test_user.id, google_event_id="evt_1"
    )
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.return_value = {}
        delete_event(db_session, appt, integration)
    endpoint = mock_call.call_args[0][1]
    assert "evt_1" in endpoint


def test_ensure_sync_skips_when_no_integration(
    db_session, test_professional, test_user
):
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    ensure_sync(db_session, "create", appt)
    assert appt.google_event_id is None


def test_ensure_sync_logs_error_does_not_raise(
    db_session, test_professional, test_user, caplog
):
    caplog.set_level(logging.ERROR)
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    _setup_integration(db_session, test_professional.id)
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        mock_call.side_effect = Exception("Google API down")
        ensure_sync(db_session, "create", appt)
    assert "Google Calendar sync failed" in caplog.text


def test_delete_event_noop_when_no_event_id(
    db_session, test_professional, test_user
):
    appt = _make_appointment(db_session, test_professional.id, test_user.id)
    _setup_integration(db_session, test_professional.id)
    integration = db_session.query(ProfessionalIntegration).first()
    with patch("app.services.google_calendar_service._call_api") as mock_call:
        delete_event(db_session, appt, integration)
    mock_call.assert_not_called()
