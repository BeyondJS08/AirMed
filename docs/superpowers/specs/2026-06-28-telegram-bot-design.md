# Telegram Bot — Layer 4D Design

## Overview

A Telegram bot that lets patients book, reschedule, cancel, and query appointments using natural-language Spanish messages. Built on a shared `bot_conversation_service` (reusable for future WhatsApp) with a `telegram_bot_service` adapter for Telegram-specific API communication. LLM (4B) handles NLU; Redis handles session state.

## Architecture

```
Telegram ──webhook──▶ telegram_bot_service ──▶ bot_conversation_service ──▶ interpret_message (4B)
    ▲                      │                           │                      Appointment service (1C)
    │                      │                           │                      Availability service (1B)
    │                      │                           │                      Google Calendar service (4A)
    │                      │                           │
    │                      │                    Redis (session store)
    │                      │
    └── reply ◀───────────┘
```

### Components

| Component | File | Responsibility |
|---|---|---|
| `bot_conversation_service` | `app/services/bot_conversation_service.py` | State machine. Coordinates LLM → availability → appointment. Redis-backed session. Returns `BotReply`. |
| `telegram_bot_service` | `app/services/telegram_bot_service.py` | Telegram API client (send/receive). Webhook parsing. Markdown formatting. |
| Bot schemas | `app/schemas/bot.py` | `BotReply`, `Button`, `SessionState` Pydantic models. |
| Webhook endpoint | `app/api/v1/endpoints/bots.py` | `POST /api/v1/bots/telegram/webhook`. Verifies HMAC, delegates to services. |

## Data Model

### BotReply (output contract)

```python
class Button(BaseModel):
    text: str
    callback_data: str

class BotReply(BaseModel):
    text: str
    buttons: list[list[Button]] = []
    parse_mode: str | None = None   # "MarkdownV2" | None
```

### Session State (Redis)

Key: `bot:session:{chat_id}`
TTL: 1800 seconds (30 min)
Value: JSON hash with fields:
```json
{
  "state": "idle",
  "intent": "schedule",
  "entities": {"date": "2026-06-29", "time": "15:00"},
  "proposed_slots": ["2026-06-29T15:00", "2026-06-29T16:00", "2026-06-30T09:00"],
  "selected_slot": null,
  "appointment_id": null,
  "professional_id": null,
  "updated_at": "2026-06-28T12:00:00Z"
}
```

## Conversation State Machine

```
IDLE
  │
  ├── schedule ──────────────▶ AWAITING_CONFIRMATION ── confirm ──▶ BOOKING ──▶ IDLE
  │     (LLM → avail →          (user picks slot)        (create appt)
  │      propose slots)
  │
  ├── cancel ────────────────▶ CANCEL_CONFIRMING ────── confirm ──▶ CANCELLING ──▶ IDLE
  │     (LLM → find appt)       (user confirms yes/no)    (cancel appt)
  │
  ├── reschedule ────────────▶ RESCHEDULE_CONFIRMING ── confirm ──▶ RESCHEDULING ──▶ IDLE
  │     (LLM → find appt        (user picks new slot)     (update appt)
  │      → avail → propose)
  │
  ├── query ──────────────────▶ IDLE (immediate reply with appointment list)
  │
  └── unknown ────────────────▶ IDLE (immediate "No entendí")
```

### State Transitions

**IDLE → AWAITING_CONFIRMATION** (`schedule`):
1. LLM extracts intent=schedule + entities (date/time/service)
2. Call `availability_service` to find slots
3. Build `BotReply` with "Tengo estos horarios disponibles:" + inline keyboard buttons for each slot
4. Save session with `proposed_slots` in Redis

**IDLE → CANCEL_CONFIRMING** (`cancel`):
1. LLM extracts intent=cancel + optional `appointment_id` or date
2. Search appointments for the patient
3. If found: build `BotReply` with "¿Confirmas la cancelación?" + Sí/No buttons
4. If not found: reply "No encontré ninguna cita" → stay IDLE

**IDLE → RESCHEDULE_CONFIRMING** (`reschedule`):
1. LLM extracts intent=reschedule + old date + new date/time
2. Find existing appointment
3. Query availability for new slot
4. Propose new slot(s) with inline keyboard

**AWAITING_CONFIRMATION → BOOKING** (user clicks slot button):
1. Parse `callback_data: "confirm_slot:{index}"`
2. Call `appointment_service.create_appointment()` with professional/patient/service from session
3. Call `google_calendar_service.ensure_sync()` (background)
4. Reply "Cita agendada para el {date} a las {time}"
5. Clear session → IDLE

**Any state → IDLE on timeout/invalid callback**:
1. If session expired (TTL): reply "Tu sesión ha expirado. Envíame un nuevo mensaje."
2. If invalid callback: reply "Opción no válida. Intenta de nuevo."

## Service Interface

### bot_conversation_service.py

```python
def process_message(
    chat_id: int,
    text: str | None,
    callback_data: str | None,
    professional_id: int,
    patient_id: int,
) -> BotReply:
    ...
```

- `chat_id`: Telegram chat ID
- `text`: message text (None for callback queries)
- `callback_data`: inline button data (None for text messages)
- `professional_id` / `patient_id`: resolved from session or provided by caller

### telegram_bot_service.py

```python
def set_webhook(url: str) -> bool: ...
def send_message(chat_id: int, reply: BotReply) -> bool: ...
def send_callback_answer(callback_query_id: str, text: str | None = None) -> bool: ...
def parse_update(payload: dict) -> tuple[int, str | None, str | None]: ...
```

## Webhook Endpoint

**`POST /api/v1/bots/telegram/webhook`**

- Accepts raw JSON from Telegram
- `telegram_bot_service.parse_update()` extracts `chat_id`, `text`, `callback_data`
- Calls `bot_conversation_service.process_message()`
- Calls `telegram_bot_service.send_message()` with the `BotReply`
- Returns `200 OK` (always — Telegram retries on non-200)

**Webhook registration**: at startup or via `/setWebhook` on deploy:
```
https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://example.com/api/v1/bots/telegram/webhook
```

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `None` | Required for bot to function. Set in `.env`. |
| `BOT_SESSION_TTL` | `1800` | Seconds until conversation session expires. |

**+ existing Redis config** (`REDIS_URL`) — already required for session storage.

## Error Handling

| Scenario | Behavior |
|---|---|
| LLM failure | Reply "Lo siento, no pude procesar tu mensaje. Intenta de nuevo." Stay in same state. |
| Booking failure | Reply "Hubo un error al agendar. Intenta de nuevo." Stay in same state. |
| No availability | Reply "No tengo disponibilidad para esa fecha/hora." Stay IDLE or propose alternatives. |
| Appointment not found | Reply "No encontré ninguna cita con esos datos." → IDLE. |
| Redis unavailable | Reply "Servicio temporalmente no disponible." → IDLE. |
| Telegram API error | Log warning, no retry. |
| Invalid callback | Reply "Opción no válida." Stay in same state. |

## Dev Setup

1. Create Telegram bot via [@BotFather](https://t.me/botfather) → get token
2. Set `TELEGRAM_BOT_TOKEN` in `.env`
3. Run ngrok: `ngrok http 8000`
4. Register webhook: `curl https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://{ngrok}.ngrok.io/api/v1/bots/telegram/webhook`
5. Start talking to the bot

## Testing

### Unit Tests

**conversation_service:**
- `test_flow_schedule` — full schedule flow: message → LLM → availability → propose → confirm → book
- `test_flow_cancel` — cancel flow with confirmation
- `test_flow_reschedule` — reschedule flow with new slot selection
- `test_flow_query` — immediate reply with appointment list
- `test_flow_unknown` — "No entendí" reply
- `test_flow_llm_failure` — LLM returns None → graceful fallback
- `test_flow_no_availability` — no slots found → friendly reply
- `test_session_expiry` — expired TTL → reset
- `test_invalid_callback` — bad callback data → error reply

**telegram_service:**
- `test_parse_message` — extract chat_id + text from Telegram update
- `test_parse_callback` — extract chat_id + callback_data from Telegram callback query
- `test_send_message` — mock Telegram API, verify request payload
- `test_webhook_registration` — verify `/setWebhook` call
- `test_send_callback_answer` — acknowledge callback query

### Integration

- End-to-end via `TestClient`: POST to webhook endpoint → verify response
- Mock Telegram API at `api.telegram.org`

### Dependencies

- `httpx` (already in requirements) — for Telegram API calls
- Redis — for session storage (already configured)
