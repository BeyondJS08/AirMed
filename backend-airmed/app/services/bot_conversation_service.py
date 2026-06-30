import enum
import json
import logging
from datetime import date, datetime, timedelta, timezone

from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.schemas.bot import BotReply, Button
from app.services.appointment_service import create_appointment, get_appointment, get_appointments, update_appointment
from app.services.availability_service import get_available_slots
from app.services.llm_service import interpret_message

logger = logging.getLogger(__name__)


try:
    import redis

    redis_client = redis.from_url(
        settings.REDIS_URL or "redis://localhost:6379/0", decode_responses=True
    )
except Exception:
    redis_client = None


class SessionState(str, enum.Enum):
    idle = "idle"
    awaiting_confirmation = "awaiting_confirmation"
    cancel_confirming = "cancel_confirming"
    reschedule_confirming = "reschedule_confirming"
    booking = "booking"
    cancelling = "cancelling"
    rescheduling = "rescheduling"
    linking = "linking"


def _session_key(chat_id: int) -> str:
    return f"bot:session:{chat_id}"


def get_session(chat_id: int) -> dict | None:
    if redis_client is None:
        return None
    try:
        data = redis_client.get(_session_key(chat_id))
        if not data:
            return None
        return json.loads(data)
    except Exception:
        logger.warning("get_session failed", exc_info=True)
        return None


def save_session(chat_id: int, session: dict) -> None:
    if redis_client is None:
        return
    session["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        redis_client.setex(
            _session_key(chat_id),
            settings.BOT_SESSION_TTL,
            json.dumps(session),
        )
    except Exception:
        logger.warning("save_session failed", exc_info=True)


def clear_session(chat_id: int) -> None:
    if redis_client is None:
        return
    try:
        redis_client.delete(_session_key(chat_id))
    except Exception:
        logger.warning("clear_session failed", exc_info=True)


def _build_slot_buttons(slots: list[dict]) -> list[list[Button]]:
    buttons = []
    for i, slot in enumerate(slots):
        start = datetime.fromisoformat(slot["start_time"])
        label = start.strftime("%d/%m %H:%M")
        buttons.append([Button(text=label, callback_data=f"confirm_slot:{i}")])
    return buttons


def _default_professional_id() -> int:
    db = SessionLocal()
    try:
        from app.models.user import User

        pro = db.query(User).filter(User.is_professional == True).first()
        return pro.id if pro else 1
    finally:
        db.close()


def handle_cancel(chat_id: int, user, entities: dict) -> BotReply:
    appointment_id = entities.get("appointment_id")
    db = SessionLocal()
    try:
        appointment = None
        if appointment_id:
            appointment = get_appointment(db, appointment_id)
        if not appointment:
            appointments = get_appointments(db, current_user=user)
            if not appointments:
                return BotReply(text="No encontré citas para cancelar.")
            appointment = appointments[0]

        save_session(chat_id, {
            "state": SessionState.cancel_confirming.value,
            "intent": "cancel",
            "entities": entities,
            "appointment_id": appointment.id,
        })
        return BotReply(
            text=f"¿Confirmas que quieres cancelar la cita del {appointment.start_time.strftime('%d/%m/%Y')} a las {appointment.start_time.strftime('%H:%M')}?",
            buttons=[[Button(text="Sí", callback_data="cancel_yes"), Button(text="No", callback_data="cancel_no")]],
        )
    finally:
        db.close()


def handle_query(user) -> BotReply:
    db = SessionLocal()
    try:
        appointments = get_appointments(db, current_user=user)
        if not appointments:
            return BotReply(text="No tienes citas próximas.")
        lines = ["Tus citas:"]
        for appt in appointments:
            lines.append(f"- {appt.start_time.strftime('%d/%m/%Y %H:%M')} (ID: {appt.id})")
        return BotReply(text="\n".join(lines))
    finally:
        db.close()


def handle_schedule(chat_id: int, user, entities: dict) -> BotReply:
    date_str = entities.get("date")
    if not date_str:
        return BotReply(text="¿Para qué fecha te gustaría agendar? Ejemplo: mañana o 2026-07-15.")

    target_date = date.fromisoformat(date_str)
    professional_id = entities.get("professional_id") or _default_professional_id()

    db = SessionLocal()
    try:
        slots = get_available_slots(db, professional_id=professional_id, target_date=target_date, service_id=None)
    finally:
        db.close()

    if not slots:
        return BotReply(text=f"No tengo disponibilidad para el {date_str}. ¿Quieres intentar otra fecha?")

    session = {
        "state": SessionState.awaiting_confirmation.value,
        "intent": "schedule",
        "entities": entities,
        "proposed_slots": slots,
        "professional_id": professional_id,
    }
    save_session(chat_id, session)

    return BotReply(
        text=f"Tengo estos horarios disponibles para el {date_str}:\nElige uno:",
        buttons=_build_slot_buttons(slots),
    )


def handle_confirm_slot(chat_id: int, user, session: dict, slot_index: int) -> BotReply:
    slots = session.get("proposed_slots", [])
    if slot_index < 0 or slot_index >= len(slots):
        return BotReply(text="Opción no válida. Intenta de nuevo.")

    slot = slots[slot_index]
    start_time = datetime.fromisoformat(slot["start_time"])
    end_time = datetime.fromisoformat(slot["end_time"])
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    professional_id = session.get("professional_id")

    db = SessionLocal()
    try:
        appointment = create_appointment(
            db,
            data=AppointmentCreate(
                professional_id=professional_id,
                start_time=start_time,
                end_time=end_time,
                notes=session.get("entities", {}).get("service", ""),
                is_virtual=(session.get("entities", {}).get("modality") == "virtual"),
            ),
            current_user=user,
            background_tasks=None,
        )
        clear_session(chat_id)
        return BotReply(
            text=f"¡Listo! Tu cita fue agendada para el {start_time.strftime('%d/%m/%Y')} a las {start_time.strftime('%H:%M')}. ID: {appointment.id}"
        )
    except Exception:
        logger.warning("handle_confirm_slot failed", exc_info=True)
        return BotReply(text="Hubo un error al agendar. Intenta de nuevo.")
    finally:
        db.close()


def _intent_value(intent_result) -> str:
    if isinstance(intent_result, dict):
        intent = intent_result.get("intent")
        return intent.value if hasattr(intent, "value") else str(intent)
    return intent_result.intent.value


def _intent_entities(intent_result) -> dict:
    if isinstance(intent_result, dict):
        entities = intent_result.get("entities", {})
        return entities.model_dump(exclude_none=True) if hasattr(entities, "model_dump") else dict(entities)
    return intent_result.entities.model_dump(exclude_none=True)


def process_message(chat_id: int, text: str | None, callback_data: str | None, user) -> BotReply:
    session = get_session(chat_id)

    if callback_data:
        if session is None:
            return BotReply(text="Tu sesión ha expirado. Envíame un nuevo mensaje.")
        if callback_data.startswith("confirm_slot:"):
            try:
                index = int(callback_data.split(":", 1)[1])
            except ValueError:
                return BotReply(text="Opción no válida.")
            return handle_confirm_slot(chat_id, user, session, index)
        if callback_data == "cancel_yes":
            appointment_id = session.get("appointment_id")
            db = SessionLocal()
            try:
                appointment = get_appointment(db, appointment_id)
                if appointment:
                    update_appointment(
                        db,
                        appointment,
                        AppointmentUpdate(status="cancelled"),
                        current_user=user,
                        background_tasks=None,
                    )
                clear_session(chat_id)
                return BotReply(text="Tu cita ha sido cancelada.")
            finally:
                db.close()
        if callback_data == "cancel_no":
            clear_session(chat_id)
            return BotReply(text="Cancelación descartada.")
        return BotReply(text="Opción no válida. Intenta de nuevo.")

    if text is None:
        return BotReply(text="No entendí tu mensaje. Intenta de nuevo.")

    intent_result = interpret_message(text)
    if intent_result is None:
        return BotReply(text="Lo siento, no pude procesar tu mensaje. Intenta de nuevo.")

    entities = _intent_entities(intent_result)
    intent_value = _intent_value(intent_result)
    if intent_value == "schedule":
        return handle_schedule(chat_id, user, entities)
    elif intent_value == "cancel":
        return handle_cancel(chat_id, user, entities)
    elif intent_value == "reschedule":
        return BotReply(text="Función de reprogramación en desarrollo.")
    elif intent_value == "query":
        return handle_query(user)

    return BotReply(text="No entendí. Puedes pedirme agendar, cancelar, reprogramar o consultar citas.")
