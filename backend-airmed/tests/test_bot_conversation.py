"""Tests for bot conversation service."""
from datetime import datetime, timezone
from unittest.mock import patch

from app.services.bot_conversation_service import (
    SessionState,
    clear_session,
    get_session,
    save_session,
)


def test_session_state_enum_values():
    assert SessionState.idle.value == "idle"
    assert SessionState.awaiting_confirmation.value == "awaiting_confirmation"
    assert SessionState.booking.value == "booking"


def test_get_session_missing():
    with patch("app.services.bot_conversation_service.redis_client.get") as mock_get:
        mock_get.return_value = None
        session = get_session(12345)
    assert session is None


def test_save_and_get_session():
    with patch("app.services.bot_conversation_service.redis_client") as mock_redis:
        mock_redis.get.return_value = '{"state": "idle", "updated_at": "2026-06-28T12:00:00Z"}'
        session = get_session(12345)
    assert session is not None
    assert session["state"] == "idle"


def test_clear_session():
    with patch("app.services.bot_conversation_service.redis_client.delete") as mock_delete:
        clear_session(12345)
    mock_delete.assert_called_once_with("bot:session:12345")
