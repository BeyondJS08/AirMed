# Telegram Bot (Layer 4D) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Telegram bot that lets patients book, reschedule, cancel, and query appointments via natural-language Spanish messages, using a shared conversation engine and Redis-backed session state.

**Architecture:** `telegram_bot_service` handles Telegram API/webhook; `bot_conversation_service` implements a state machine (stored in Redis) that coordinates LLM intent parsing, availability lookup, and appointment CRUD; `linking_service` maps Telegram `chat_id` to `User` records.

**Tech Stack:** FastAPI, httpx, Redis (redis-py), Pydantic, pytest + unittest.mock

---

## File Structure

| File | Action | Purpose |
|---|---|---|
| `app/schemas/bot.py` | Create | `BotReply`, `Button`, `SessionState` Pydantic schemas |
| `app/services/linking_service.py` | Create | `resolve_user(chat_id)` and `link_user(chat_id, email)` |
| `app/services/bot_conversation_service.py` | Create | State machine, `process_message()`, session CRUD |
| `app/services/telegram_bot_service.py` | Create | Telegram API client, webhook parsing |
| `app/api/v1/endpoints/bots.py` | Create | `POST /api/v1/bots/telegram/webhook` endpoint |
| `app/api/v1/__init__.py` | Modify | Register the bots router |
| `app/core/config.py` | Modify | Add `TELEGRAM_BOT_TOKEN`, `BOT_SESSION_TTL` |
| `tests/test_linking.py` | Create | Tests for linking service |
| `tests/test_bot_conversation.py` | Create | Tests for conversation state machine and flows |
| `tests/test_telegram_bot.py` | Create | Tests for Telegram service and webhook endpoint |

---

### Task 1: Schemas + Config + Linking Service

**Files:**
- Create: `app/schemas/bot.py`
- Create: `app/services/linking_service.py`
- Modify: `app/core/config.py`
- Test: `tests/test_linking.py`

- [ ] **Step 1: Write failing tests**

`tests/test_linking.py`:
```python
"""Tests for bot linking service."""
from unittest.mock import patch
from app.schemas.bot import BotReply, Button
from app.services.linking_service import link_user, resolve_user


def test_bot_reply_schema():
    reply = BotReply(text="Hello")
    assert reply.text == "Hello"
    assert reply.buttons == []
    assert reply.parse_mode is None


def test_button_schema():
    btn = Button(text="Yes", callback_data="yes")
    assert btn.text == "Yes"
    assert btn.callback_data == "yes"


def test_resolve_user_not_linked():
    with patch("app.services.linking_service.redis_client.get") as mock_get:
        mock_get.return_value = None
        user = resolve_user(12345)
    assert user is None


def test_link_user_valid_email(test_user):
    with patch("app.services.linking_service.redis_client.set") as mock_set:
        result = link_user(12345, test_user.email)
    assert result is not None
    assert result.id == test_user.id
    mock_set.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_linking.py -v
```
Expected: FAIL "No module named 'app.schemas.bot'" / "No module named 'app.services.linking_service'"

- [ ] **Step 3: Write schemas**

`app/schemas/bot.py`:
```python
from pydantic import BaseModel


class Button(BaseModel):
    text: str
    callback_data: str


class BotReply(BaseModel):
    text: str
    buttons: list[list[Button]] = []
    parse_mode: str | None = None
```

- [ ] **Step 4: Add config vars**

Modify `app/core/config.py` after the LLM settings:
```python
    TELEGRAM_BOT_TOKEN: str | None = None
    BOT_SESSION_TTL: int = 1800
```

- [ ] **Step 5: Write linking service**

`app/services/linking_service.py`:
```python
import json
import logging

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)


try:
    import redis
    redis_client = redis.from_url(settings.REDIS_URL or "redis://localhost:6379/0", decode_responses=True)
except Exception:
    redis_client = None


def resolve_user(chat_id: int) -> User | None:
    if redis_client is None:
        return None
    try:
        data = redis_client.get(f"bot:link:{chat_id}")
        if not data:
            return None
        user_id = json.loads(data).get("user_id")
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
    except Exception:
        logger.warning("resolve_user failed", exc_info=True)
        return None


def link_user(chat_id: int, email: str) -> User | None:
    if redis_client is None:
        return None
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        redis_client.set(
            f"bot:link:{chat_id}",
            json.dumps({"user_id": user.id}),
        )
        return user
    finally:
        db.close()
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_linking.py -v
```
Expected: 4 PASS

- [ ] **Step 7: Commit**

```bash
git add app/schemas/bot.py app/core/config.py app/services/linking_service.py tests/test_linking.py
git commit -m "feat(4d): add bot schemas, config, and chat-to-user linking service"
```

---

### Task 2: Conversation Session Management

**Files:**
- Create: `app/services/bot_conversation_service.py` (session CRUD + state enum)
- Test: `tests/test_bot_conversation.py`

- [ ] **Step 1: Write failing tests**

`tests/test_bot_conversation.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_bot_conversation.py::test_session_state_enum_values tests/test_bot_conversation.py::test_get_session_missing tests/test_bot_conversation.py::test_save_and_get_session tests/test_bot_conversation.py::test_clear_session -v
```
Expected: FAIL "No module named 'app.services.bot_conversation_service'"

- [ ] **Step 3: Write session management code**

`app/services/bot_conversation_service.py`:
```python
import enum
import json
import logging
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger(__name__)


try:
    import redis
    redis_client = redis.from_url(settings.REDIS_URL or "redis://localhost:6379/0", decode_responses=True)
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_bot_conversation.py::test_session_state_enum_values tests/test_bot_conversation.py::test_get_session_missing tests/test_bot_conversation.py::test_save_and_get_session tests/test_bot_conversation.py::test_clear_session -v
```
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/bot_conversation_service.py tests/test_bot_conversation.py
git commit -m "feat(4d): add conversation session management"
```

---

### Task 3: Conversation Flow — Schedule

**Files:**
- Modify: `app/services/bot_conversation_service.py`
- Test: `tests/test_bot_conversation.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_bot_conversation.py`:
```python
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.db.session import SessionLocal
from app.schemas.bot import BotReply
from app.services.bot_conversation_service import process_message, SessionState


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_bot_conversation.py::test_process_message_schedule_starts_confirmation tests/test_bot_conversation.py::test_process_message_confirm_slot_creates_appointment -v
```
Expected: FAIL "module 'app.services.bot_conversation_service' has no attribute 'process_message'"

- [ ] **Step 3: Write conversation service flow**

Add to `app/services/bot_conversation_service.py`:
```python
from datetime import date, datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.schemas.appointment import AppointmentCreate
from app.schemas.bot import BotReply, Button
from app.services.appointment_service import create_appointment
from app.services.availability_service import get_available_slots
from app.services.llm_service import interpret_message


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

    entities = intent_result.entities.model_dump(exclude_none=True)
    if intent_result.intent.value == "schedule":
        return handle_schedule(chat_id, user, entities)
    elif intent_result.intent.value == "cancel":
        return BotReply(text="Función de cancelación en desarrollo.")
    elif intent_result.intent.value == "reschedule":
        return BotReply(text="Función de reprogramación en desarrollo.")
    elif intent_result.intent.value == "query":
        return BotReply(text="Función de consulta en desarrollo.")

    return BotReply(text="No entendí. Puedes pedirme agendar, cancelar, reprogramar o consultar citas.")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_bot_conversation.py::test_process_message_schedule_starts_confirmation tests/test_bot_conversation.py::test_process_message_confirm_slot_creates_appointment -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/bot_conversation_service.py tests/test_bot_conversation.py
git commit -m "feat(4d): add schedule flow in conversation service"
```

---

### Task 4: Conversation Flow — Cancel / Query / Unknown

**Files:**
- Modify: `app/services/bot_conversation_service.py`
- Modify: `tests/test_bot_conversation.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_bot_conversation.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_bot_conversation.py::test_process_message_cancel_flow tests/test_bot_conversation.py::test_process_message_query_flow tests/test_bot_conversation.py::test_process_message_unknown -v
```
Expected: FAIL due to unimplemented functions

- [ ] **Step 3: Implement flows**

Add to `app/services/bot_conversation_service.py`:
```python
from app.schemas.appointment import AppointmentUpdate
from app.services.appointment_service import get_appointment, get_appointments, update_appointment


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
```

Update `process_message` route for cancel/query:
```python
    if intent_result.intent.value == "schedule":
        return handle_schedule(chat_id, user, entities)
    elif intent_result.intent.value == "cancel":
        return handle_cancel(chat_id, user, entities)
    elif intent_result.intent.value == "query":
        return handle_query(user)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_bot_conversation.py -v
```
Expected: All conversation tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/bot_conversation_service.py tests/test_bot_conversation.py
git commit -m "feat(4d): add cancel, query, and unknown conversation flows"
```

---

### Task 5: Telegram Service — API Client + Webhook Parse

**Files:**
- Create: `app/services/telegram_bot_service.py`
- Test: `tests/test_telegram_bot.py`

- [ ] **Step 1: Write failing tests**

`tests/test_telegram_bot.py`:
```python
"""Tests for Telegram bot service."""
from unittest.mock import patch

from app.schemas.bot import BotReply, Button
from app.services.telegram_bot_service import parse_update, send_message, set_webhook


def test_parse_message_update():
    payload = {
        "message": {
            "chat": {"id": 12345},
            "text": "Hola",
        }
    }
    chat_id, text, callback_data = parse_update(payload)
    assert chat_id == 12345
    assert text == "Hola"
    assert callback_data is None


def test_parse_callback_update():
    payload = {
        "callback_query": {
            "id": "q1",
            "message": {"chat": {"id": 12345}},
            "data": "confirm_slot:0",
        }
    }
    chat_id, text, callback_data = parse_update(payload)
    assert chat_id == 12345
    assert text is None
    assert callback_data == "confirm_slot:0"


def test_send_message():
    reply = BotReply(text="Hello")
    with patch("app.services.telegram_bot_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None
        result = send_message(12345, reply)
    assert result is True


def test_set_webhook():
    with patch("app.services.telegram_bot_service.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        result = set_webhook("https://example.com/webhook")
    assert result is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_telegram_bot.py -v
```
Expected: FAIL "No module named 'app.services.telegram_bot_service'"

- [ ] **Step 3: Write Telegram service**

`app/services/telegram_bot_service.py`:
```python
import logging

import httpx

from app.core.config import settings
from app.schemas.bot import BotReply

logger = logging.getLogger(__name__)


API_BASE = "https://api.telegram.org/bot{token}"


def _api(method: str) -> str:
    token = settings.TELEGRAM_BOT_TOKEN
    return f"{API_BASE.format(token=token)}/{method}"


def parse_update(payload: dict) -> tuple[int, str | None, str | None]:
    if "message" in payload:
        chat_id = payload["message"]["chat"]["id"]
        text = payload["message"].get("text")
        return chat_id, text, None
    if "callback_query" in payload:
        chat_id = payload["callback_query"]["message"]["chat"]["id"]
        callback_data = payload["callback_query"].get("data")
        return chat_id, None, callback_data
    raise ValueError("Unknown update type")


def _build_reply_markup(reply: BotReply) -> dict | None:
    if not reply.buttons:
        return None
    return {
        "inline_keyboard": [
            [{"text": btn.text, "callback_data": btn.callback_data} for btn in row]
            for row in reply.buttons
        ]
    }


def send_message(chat_id: int, reply: BotReply) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    payload = {
        "chat_id": chat_id,
        "text": reply.text,
    }
    if reply.parse_mode:
        payload["parse_mode"] = reply.parse_mode
    markup = _build_reply_markup(reply)
    if markup:
        payload["reply_markup"] = markup
    try:
        resp = httpx.post(_api("sendMessage"), json=payload, timeout=10.0)
        resp.raise_for_status()
        return True
    except Exception:
        logger.warning("send_message failed", exc_info=True)
        return False


def set_webhook(url: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    try:
        resp = httpx.get(_api("setWebhook"), params={"url": url}, timeout=10.0)
        resp.raise_for_status()
        return True
    except Exception:
        logger.warning("set_webhook failed", exc_info=True)
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_telegram_bot.py -v
```
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/telegram_bot_service.py tests/test_telegram_bot.py
git commit -m "feat(4d): add Telegram API client and webhook parser"
```

---

### Task 6: Webhook Endpoint + Router Registration

**Files:**
- Create: `app/api/v1/endpoints/bots.py`
- Modify: `app/api/v1/__init__.py`
- Test: `tests/test_telegram_bot.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_telegram_bot.py`:
```python
from unittest.mock import patch


def test_telegram_webhook_endpoint(client):
    payload = {
        "message": {
            "chat": {"id": 12345},
            "text": "Hola",
        }
    }
    with (
        patch("app.api.v1.endpoints.bots.resolve_user", return_value=None),
        patch("app.api.v1.endpoints.bots.send_message") as mock_send,
    ):
        resp = client.post("/api/v1/bots/telegram/webhook", json=payload)
    assert resp.status_code == 200
    mock_send.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_telegram_bot.py::test_telegram_webhook_endpoint -v
```
Expected: FAIL "404" (router not registered) or "No module named 'app.api.v1.endpoints.bots'"

- [ ] **Step 3: Write webhook endpoint**

`app/api/v1/endpoints/bots.py`:
```python
import logging

from fastapi import APIRouter, Body

from app.schemas.bot import BotReply
from app.services.bot_conversation_service import process_message
from app.services.linking_service import link_user, resolve_user
from app.services.telegram_bot_service import parse_update, send_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("/telegram/webhook")
def telegram_webhook(payload: dict = Body(...)):
    try:
        chat_id, text, callback_data = parse_update(payload)
    except (KeyError, ValueError):
        logger.warning("Invalid Telegram update payload", extra={"payload": payload})
        return {"ok": True}

    user = resolve_user(chat_id)

    if user is None and text:
        # Linking flow
        linked = link_user(chat_id, text.strip())
        if linked is None:
            send_message(chat_id, BotReply(text="Bienvenido a AirMed. Para usar este bot, necesito vincular tu cuenta. ¿Cuál es tu email registrado?"))
            return {"ok": True}
        send_message(chat_id, BotReply(text=f"¡Listo, {linked.full_name or linked.email}! Ya puedes agendar, cancelar o consultar citas."))
        return {"ok": True}

    if user is None:
        send_message(chat_id, BotReply(text="Bienvenido a AirMed. ¿Cuál es tu email registrado?"))
        return {"ok": True}

    reply = process_message(chat_id, text, callback_data, user)
    send_message(chat_id, reply)
    return {"ok": True}
```

- [ ] **Step 4: Register router**

Modify `app/api/v1/__init__.py`:
```python
from app.api.v1.endpoints import auth, users, services, appointments, availability, notifications, integrations, bots

api_router.include_router(bots.router)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_telegram_bot.py::test_telegram_webhook_endpoint -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/api/v1/endpoints/bots.py app/api/v1/__init__.py tests/test_telegram_bot.py
git commit -m "feat(4d): add Telegram webhook endpoint and router"
```

---

### Task 7: Final Verification + Cleanup

- [ ] **Step 1: Run all bot tests**

```bash
pytest tests/test_linking.py tests/test_bot_conversation.py tests/test_telegram_bot.py -v
```
Expected: All PASS

- [ ] **Step 2: Run full backend suite**

```bash
pytest -v
```
Expected: All existing tests still pass (140+) with new bot tests passing

- [ ] **Step 3: Add `.env.example` Telegram entries**

Modify `backend-airmed/.env.example` to add at the bottom:
```
# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
BOT_SESSION_TTL=1800
```

- [ ] **Step 4: Final commit**

```bash
git add -A && git commit -m "feat(4d): final cleanup and .env.example updates"
```
