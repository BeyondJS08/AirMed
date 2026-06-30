"""Tests for bot conversation service."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.schemas.bot import BotReply
from app.services.bot_conversation_service import (
    SessionState,
    clear_session,
    get_session,
    process_message,
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


def test_process_message_schedule_starts_confirmation(test_user, test_professional):
    intent_result = {
        "intent": "schedule",
        "entities": {"date": "2026-07-15", "time": "10:00", "service": "consulta"},
        "confidence": 0.9,
    }
    with (
        patch("app.services.bot_conversation_service.interpret_message", return_value=intent_result),
        patch("app.services.bot_conversation_service.get_available_slots") as mock_avail,
        patch("app.services.bot_conversation_service.save_session") as mock_save,
        patch("app.services.bot_conversation_service.get_session", return_value=None),
    ):
        mock_avail.return_value = [
            {"start_time": "2026-07-15T10:00:00", "end_time": "2026-07-15T11:00:00"},
        ]
        reply = process_message(12345, "Quiero una cita el martes a las 10", None, test_user)

    assert isinstance(reply, BotReply)
    assert len(reply.buttons) > 0
    mock_save.assert_called_once()


def test_process_message_confirm_slot_creates_appointment(test_user, test_professional):
    session = {
        "state": SessionState.awaiting_confirmation.value,
        "intent": "schedule",
        "entities": {"date": "2026-07-15", "time": "10:00", "service": "consulta"},
        "proposed_slots": [{"start_time": "2026-07-15T10:00:00", "end_time": "2026-07-15T11:00:00"}],
        "professional_id": test_professional.id,
    }
    with (
        patch("app.services.bot_conversation_service.get_session", return_value=session),
        patch("app.services.bot_conversation_service.create_appointment") as mock_create,
        patch("app.services.bot_conversation_service.clear_session") as mock_clear,
    ):
        mock_create.return_value = MagicMock(id=1)
        reply = process_message(12345, None, "confirm_slot:0", test_user)

    assert "agendada" in reply.text.lower() or "confirmada" in reply.text.lower()
    mock_create.assert_called_once()
    mock_clear.assert_called_once()


def test_process_message_cancel_flow(test_user, test_professional):
    intent_result = {
        "intent": "cancel",
        "entities": {"appointment_id": 1},
        "confidence": 0.85,
    }
    with (
        patch("app.services.bot_conversation_service.interpret_message", return_value=intent_result),
        patch("app.services.bot_conversation_service.get_appointment") as mock_get,
        patch("app.services.bot_conversation_service.save_session") as mock_save,
        patch("app.services.bot_conversation_service.get_session", return_value=None),
    ):
        mock_get.return_value = MagicMock(id=1, start_time=datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc))
        reply = process_message(12345, "Cancelar mi cita", None, test_user)

    assert "cancelar" in reply.text.lower() or "confirm" in reply.text.lower()
    mock_save.assert_called_once()


def test_process_message_query_flow(test_user):
    intent_result = {"intent": "query", "entities": {}, "confidence": 0.7}
    with (
        patch("app.services.bot_conversation_service.interpret_message", return_value=intent_result),
        patch("app.services.bot_conversation_service.get_appointments") as mock_list,
        patch("app.services.bot_conversation_service.get_session", return_value=None),
    ):
        mock_list.return_value = [MagicMock(id=1, start_time=datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc))]
        reply = process_message(12345, "Mis citas", None, test_user)

    assert reply.text


def test_process_message_unknown(test_user):
    intent_result = {"intent": "unknown", "entities": {}, "confidence": 0.1}
    with (
        patch("app.services.bot_conversation_service.interpret_message", return_value=intent_result),
        patch("app.services.bot_conversation_service.get_session", return_value=None),
    ):
        reply = process_message(12345, "Hola", None, test_user)

    assert "no entend" in reply.text.lower()
