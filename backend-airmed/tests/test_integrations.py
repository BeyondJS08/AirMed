"""Tests for integration service and OAuth endpoints."""
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.models.integration import ProfessionalIntegration
from app.services.integration_service import (
    delete_integration,
    get_integration,
    upsert_integration,
)


def test_upsert_creates(db_session, test_professional):
    integration = upsert_integration(
        db_session,
        test_professional.id,
        "google_calendar",
        "at1",
        "rt1",
        datetime(2026, 7, 1, 0, 0, 0),
        google_email="doc@example.com",
    )
    assert integration.professional_id == test_professional.id
    assert integration.provider == "google_calendar"
    assert integration.access_token == "at1"
    assert integration.refresh_token == "rt1"
    assert integration.google_email == "doc@example.com"


def test_upsert_updates_existing(db_session, test_professional):
    upsert_integration(
        db_session,
        test_professional.id,
        "google_calendar",
        "at1",
        "rt1",
        datetime(2026, 7, 1, 0, 0, 0),
    )
    upsert_integration(
        db_session,
        test_professional.id,
        "google_calendar",
        "at2",
        "rt2",
        datetime(2026, 8, 1, 0, 0, 0),
    )
    rows = db_session.query(ProfessionalIntegration).all()
    assert len(rows) == 1
    assert rows[0].access_token == "at2"


def test_get_returns_none_when_missing(db_session, test_professional):
    result = get_integration(db_session, test_professional.id, "google_calendar")
    assert result is None


def test_delete_removes_integration(db_session, test_professional):
    upsert_integration(
        db_session,
        test_professional.id,
        "google_calendar",
        "at1",
        "rt1",
        datetime(2026, 7, 1, 0, 0, 0),
    )
    delete_integration(db_session, test_professional.id, "google_calendar")
    assert get_integration(db_session, test_professional.id, "google_calendar") is None


def test_delete_raises_404_when_missing(db_session, test_professional):
    with pytest.raises(HTTPException) as exc:
        delete_integration(db_session, test_professional.id, "google_calendar")
    assert exc.value.status_code == 404


def test_integration_unique_constraint(db_session, test_professional):
    upsert_integration(
        db_session,
        test_professional.id,
        "google_calendar",
        "at1",
        "rt1",
        datetime(2026, 7, 1, 0, 0, 0),
    )
    with pytest.raises(Exception):
        dup = ProfessionalIntegration(
            professional_id=test_professional.id,
            provider="google_calendar",
            access_token="at2",
            refresh_token="rt2",
            token_expires_at=datetime(2026, 8, 1, 0, 0, 0),
        )
        db_session.add(dup)
        db_session.commit()


# --- API tests ---


def test_google_auth_requires_professional(client, user_token):
    response = client.get(
        "/api/v1/integrations/google/auth",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


def test_google_auth_returns_url(client, professional_token):
    response = client.get(
        "/api/v1/integrations/google/auth",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert data["auth_url"].startswith("https://accounts.google.com/o/oauth2/v2/auth")


def test_google_tokens_missing_code(client, professional_token):
    response = client.post(
        "/api/v1/integrations/google/tokens",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 422


def test_google_tokens_requires_auth(client):
    response = client.post("/api/v1/integrations/google/tokens?code=abc")
    assert response.status_code == 401


def test_google_tokens_exchange_failure(client, professional_token):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = mock_post.return_value
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error": "invalid_grant"}
        response = client.post(
            "/api/v1/integrations/google/tokens?code=bad_code",
            headers={"Authorization": f"Bearer {professional_token}"},
        )
    assert response.status_code == 400
    assert "Failed to exchange" in response.text


def test_google_status_no_integration(client, professional_token):
    response = client.get(
        "/api/v1/integrations/google/status",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 200
    assert response.json() is None


def test_google_status_with_integration(
    client, professional_token, db_session, test_professional
):
    upsert_integration(
        db_session,
        test_professional.id,
        "google_calendar",
        "at1",
        "rt1",
        datetime(2026, 7, 1, 0, 0, 0),
    )
    response = client.get(
        "/api/v1/integrations/google/status",
        headers={"Authorization": f"Bearer {professional_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "google_calendar"
