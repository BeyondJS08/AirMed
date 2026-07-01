"""Tests for bot conversation service."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.schemas.bot import BotReply, SessionState
from app.schemas.llm import Entities, IntentName, IntentResult
from app.services.bot_conversation_service import (
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
    intent_result = IntentResult(
        intent=IntentName.schedule,
        entities=Entities(date="2026-07-15", time="10:00", service="consulta"),
        confidence=0.9,
    )
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
    intent_result = IntentResult(
        intent=IntentName.cancel,
        entities=Entities(appointment_id=1),
        confidence=0.85,
    )
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
    intent_result = IntentResult(intent=IntentName.query, entities=Entities(), confidence=0.7)
    with (
        patch("app.services.bot_conversation_service.interpret_message", return_value=intent_result),
        patch("app.services.bot_conversation_service.get_appointments") as mock_list,
        patch("app.services.bot_conversation_service.get_session", return_value=None),
    ):
        mock_list.return_value = [MagicMock(id=1, start_time=datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc))]
        reply = process_message(12345, "Mis citas", None, test_user)

    assert reply.text


def test_process_message_unknown(test_user):
    intent_result = IntentResult(intent=IntentName.unknown, entities=Entities(), confidence=0.1)
    with (
        patch("app.services.bot_conversation_service.interpret_message", return_value=intent_result),
        patch("app.services.bot_conversation_service.get_session", return_value=None),
    ):
        reply = process_message(12345, "Hola", None, test_user)

    assert "no entend" in reply.text.lower()


def test_flow_llm_failure(test_user):
    with (
        patch("app.services.bot_conversation_service.interpret_message", return_value=None),
        patch("app.services.bot_conversation_service.get_session", return_value=None),
    ):
        reply = process_message(12345, "Quiero cita", None, test_user)
    assert "no pude procesar" in reply.text.lower()


def test_flow_no_availability(test_user):
    intent_result = IntentResult(
        intent=IntentName.schedule,
        entities=Entities(date="2026-07-15", time="10:00"),
        confidence=0.9,
    )
    with (
        patch("app.services.bot_conversation_service.interpret_message", return_value=intent_result),
        patch("app.services.bot_conversation_service.get_available_slots", return_value=[]),
        patch("app.services.bot_conversation_service.get_session", return_value=None),
    ):
        reply = process_message(12345, "Quiero cita", None, test_user)
    assert "disponibilidad" in reply.text.lower() or "disponible" in reply.text.lower()


def test_session_expiry(test_user):
    with patch("app.services.bot_conversation_service.get_session", return_value=None):
        reply = process_message(12345, None, "confirm_slot:0", test_user)
    assert "expirado" in reply.text.lower()


def test_invalid_callback(test_user):
    session = {"state": SessionState.awaiting_confirmation.value}
    with patch("app.services.bot_conversation_service.get_session", return_value=session):
        reply = process_message(12345, None, "unknown_callback", test_user)
    assert "no válida" in reply.text.lower()


def test_reschedule_flow(test_user, test_professional):
    intent_result = IntentResult(
        intent=IntentName.reschedule,
        entities=Entities(date="2026-07-20"),
        confidence=0.9,
    )
    existing_appointment = MagicMock(id=1, professional_id=test_professional.id)
    proposed_slots = [
        {"start_time": "2026-07-20T10:00:00", "end_time": "2026-07-20T11:00:00"},
    ]
    with (
        patch("app.services.bot_conversation_service.interpret_message", return_value=intent_result),
        patch("app.services.bot_conversation_service.get_appointments", return_value=[existing_appointment]),
        patch("app.services.bot_conversation_service.get_available_slots", return_value=proposed_slots),
        patch("app.services.bot_conversation_service.save_session") as mock_save,
        patch("app.services.bot_conversation_service.get_session", return_value=None),
    ):
        reply = process_message(12345, "Reprogramar mi cita", None, test_user)
    assert reply.buttons
    assert "reschedule_slot:0" in reply.buttons[0][0].callback_data
    mock_save.assert_called_once()
    saved_session = mock_save.call_args[0][1]
    assert saved_session["state"] == SessionState.reschedule_confirming.value

    session = {
        "state": SessionState.reschedule_confirming.value,
        "appointment_id": 1,
        "proposed_slots": proposed_slots,
    }
    background_tasks = MagicMock()
    with (
        patch("app.services.bot_conversation_service.get_session", return_value=session),
        patch("app.services.bot_conversation_service.get_appointment", return_value=existing_appointment),
        patch("app.services.bot_conversation_service.update_appointment") as mock_update,
        patch("app.services.bot_conversation_service.clear_session") as mock_clear,
    ):
        reply = process_message(12345, None, "reschedule_slot:0", test_user, background_tasks=background_tasks)
    assert "reprogramada" in reply.text.lower()
    mock_update.assert_called_once()
    assert mock_update.call_args.kwargs.get("background_tasks") is background_tasks
    mock_clear.assert_called_once()


def test_callback_state_mismatch_clears_session(test_user):
    session = {"state": SessionState.idle.value}
    with (
        patch("app.services.bot_conversation_service.get_session", return_value=session),
        patch("app.services.bot_conversation_service.clear_session") as mock_clear,
    ):
        reply = process_message(12345, None, "confirm_slot:0", test_user)
    assert "no válida" in reply.text.lower()
    mock_clear.assert_called_once()

    session = {"state": SessionState.awaiting_confirmation.value}
    with (
        patch("app.services.bot_conversation_service.get_session", return_value=session),
        patch("app.services.bot_conversation_service.clear_session") as mock_clear,
    ):
        reply = process_message(12345, None, "reschedule_slot:0", test_user)
    assert "no válida" in reply.text.lower()
    mock_clear.assert_called_once()

    session = {"state": SessionState.awaiting_confirmation.value}
    with (
        patch("app.services.bot_conversation_service.get_session", return_value=session),
        patch("app.services.bot_conversation_service.clear_session") as mock_clear,
    ):
        reply = process_message(12345, None, "cancel_yes", test_user)
    assert "no válida" in reply.text.lower()
    mock_clear.assert_called_once()


def test_text_override_during_pending_session(test_user):
    session = {"state": SessionState.awaiting_confirmation.value}
    with (
        patch("app.services.bot_conversation_service.get_session", return_value=session),
        patch("app.services.bot_conversation_service.clear_session") as mock_clear,
    ):
        reply = process_message(12345, "cancelar", None, test_user)
    assert "acción cancelada" in reply.text.lower()
    mock_clear.assert_called_once()

    with (
        patch("app.services.bot_conversation_service.get_session", return_value=session),
        patch("app.services.bot_conversation_service.interpret_message") as mock_llm,
    ):
        reply = process_message(12345, "quiero otra cosa", None, test_user)
    assert "pendiente" in reply.text.lower()
    mock_llm.assert_not_called()


def test_schedule_filters_past_slots(test_user, test_professional):
    now = datetime.now(timezone.utc)
    past_slot = {
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": now.isoformat(),
    }
    future_start = now + timedelta(days=1)
    future_slot = {
        "start_time": future_start.isoformat(),
        "end_time": (future_start + timedelta(hours=1)).isoformat(),
    }
    intent_result = IntentResult(
        intent=IntentName.schedule,
        entities=Entities(date=future_start.date().isoformat()),
        confidence=0.9,
    )
    with (
        patch("app.services.bot_conversation_service.interpret_message", return_value=intent_result),
        patch("app.services.bot_conversation_service.get_available_slots", return_value=[past_slot, future_slot]),
        patch("app.services.bot_conversation_service.save_session") as mock_save,
        patch("app.services.bot_conversation_service.get_session", return_value=None),
    ):
        reply = process_message(12345, "Quiero cita mañana", None, test_user)

    assert len(reply.buttons) == 1
    saved_session = mock_save.call_args[0][1]
    assert len(saved_session["proposed_slots"]) == 1
