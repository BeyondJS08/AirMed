# On-Premise LLM Integration — Layer 4B Design

## Overview

A stateless NLU service that parses natural-language messages (Spanish) sent by patients via WhatsApp/Telegram into structured intents with extracted entities. Built on gemma-4-E2B running via llama.cpp, accessed through its OpenAI-compatible HTTP API with JSON schema-constrained output.

## Architecture

```
[Bot 4C/4D] ──text──▶ [llm_service.interpret_message()] ──HTTP──▶ [llama-server]
                              │                                            │
                              |                                     JSON schema-constrained
                              ▼                                            │
                       IntentResult ◀──────────────────────────────────────┘
                              │
                              ▼
                       [Bot handles DB lookup, replies]
```

### Components

- `app/services/llm_service.py` — HTTP client + parse + fallback. Single public function
- `app/schemas/llm.py` — `IntentResult` Pydantic schema (also serialized to JSON schema for llama.cpp)
- `app/core/config.py` — `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT`, `LLM_ENABLED`, `LLM_TEMPERATURE`
- `docker-compose.yml` — adds `llm` service (llama.cpp server + model volume)

### Scope Boundaries (in vs. out)

| In scope (4B) | Out of scope (4C/4D) |
|---|---|
| Parsing one message → structured intent | Conversation state machine |
| Entity extraction (date, time, service, etc.) | Multi-turn context |
| Confidence scoring | DB lookups |
| Structured output via JSON schema | Bot reply generation |
| Graceful fallback to `None` | Sending messages back |

## Data Model

### IntentResult Schema

```python
class IntentName(str, enum.Enum):
    schedule = "schedule"
    reschedule = "reschedule"
    cancel = "cancel"
    query = "query"
    unknown = "unknown"

class Entities(BaseModel):
    date: str | None = None        # ISO date "2026-06-29"
    time: str | None = None        # "15:00"
    service: str | None = None     # e.g. "limpieza dental"
    professional: str | None = None
    appointment_id: int | None = None
    modality: str | None = None    # "virtual" | "in_person"

class IntentResult(BaseModel):
    intent: IntentName
    entities: Entities
    confidence: float              # 0.0-1.0, model self-report
```

`IntentResult.model_json_schema()` is passed to llama.cpp as the `response_format` parameter, constraining output to valid JSON matching this shape.

## Service Interface

```python
def interpret_message(text: str) -> IntentResult | None
```

- **Input**: raw message text from patient (Spanish)
- **Output**: `IntentResult` on success, `None` on failure/timeout/disability
- **Sync function** — called from async bot endpoints via `run_in_executor` or FastAPI's sync-to-async bridge
- **All failure modes return `None`** — bot handles graceful "I didn't understand" fallback

### Implementation Details

1. Check `settings.LLM_ENABLED` — return `None` immediately if `False`
2. POST to `{LLM_BASE_URL}/chat/completions` with:
   - `model`: `LLM_MODEL` (default `gemma-4-E2B`)
   - `messages`: system prompt (Spanish, few-shot, current date/time injected) + user message
   - `response_format`: JSON schema constrained to `IntentResult`
   - `temperature`: `LLM_TEMPERATURE` (default `0.1`)
3. Parse response → `IntentResult.model_validate_json(content)`
4. On any exception (HTTP error, timeout, JSON parse, schema validation) → log warning, return `None`

## Prompt Design

### System Prompt (Spanish)

```
Eres un asistente médico. Analiza el mensaje del paciente y devuelve
un JSON con la intención y las entidades extraídas.

Fecha actual: {current_date}
Hora actual: {current_time}

Intenciones válidas: schedule, reschedule, cancel, query, unknown.

Entidades:
- date: fecha en formato ISO (YYYY-MM-DD)
- time: hora en formato 24h (HH:MM)
- service: nombre del servicio solicitado
- professional: nombre o especialidad del profesional
- appointment_id: ID numérico de cita existente (solo cancel/reschedule)
- modality: "virtual" o "in_person"

Ejemplos:
Usuario: "Quiero una cita mañana a las 3pm con el dentista"
→ {"intent":"schedule","entities":{"date":"2026-06-29","time":"15:00","service":"dentista"},"confidence":0.9}

Usuario: "Necesito cancelar mi cita del viernes"
→ {"intent":"cancel","entities":{"date":"2026-06-29"},"confidence":0.85}

Usuario: "Tengo consulta el lunes, hay que cambiarla para el martes a las 10"
→ {"intent":"reschedule","entities":{"date":"2026-06-29","time":"10:00"},"confidence":0.8}

Usuario: "Hola, buenos días"
→ {"intent":"unknown","entities":{},"confidence":0.1}

Responde solo con JSON válido.
```

`current_date`/`current_time` are server UTC. The bot layer converts to user timezone before comparing.

## Docker Setup

```yaml
services:
  # ... existing db, backend, etc.
  llm:
    image: ghcr.io/ggerganov/llama.cpp:server
    ports:
      - "8080:8080"
    volumes:
      - ./models:/models
    command: -m /models/gemma-4-E2B.gguf --host 0.0.0.0 --port 8080 --json-schema
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: ["gpu"]   # optional
```

- Model file (`gemma-4-E2B.gguf`) downloaded separately to `./models/` (gitignored)
- `--json-schema` flag enables structured output
- Backend connects via `LLM_BASE_URL=http://llm:8080/v1` (Docker) or `http://localhost:8080/v1` (local)

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:8080/v1` | llama.cpp server base URL |
| `LLM_MODEL` | `gemma-4-E2B` | Model name passed in API calls |
| `LLM_TIMEOUT` | `30.0` | Max seconds per request |
| `LLM_ENABLED` | `False` | Opt-in; flip true when server is up |
| `LLM_TEMPERATURE` | `0.1` | Low for deterministic-ish output |

## Failure Modes

| Scenario | Behavior |
|---|---|
| `LLM_ENABLED=false` | `interpret_message` returns `None` immediately |
| Timeout > 30s | Log warning, return `None` |
| HTTP error (4xx/5xx) | Log warning, return `None` |
| Malformed JSON response | Log warning, return `None` |
| Schema validation fails | Log warning, return `None` |
| Connection refused | Log warning, return `None` |

No retry logic — 30s timeout is already long. Fail fast, let bot reply gracefully.

## Testing

### Unit Tests (mocked HTTP via `respx`)

| Test | Case |
|---|---|
| `test_interpret_schedule` | "Quiero una cita mañana a las 3pm" → schedule + entities |
| `test_interpret_cancel` | Cancel intent with date |
| `test_interpret_reschedule` | Reschedule with two dates |
| `test_interpret_query` | Query intent |
| `test_interpret_unknown_greeting` | "Hola" → unknown |
| `test_llm_disabled` | `LLM_ENABLED=false` → `None` |
| `test_timeout` | HTTP timeout → `None` |
| `test_malformed_json` | Server returns garbage → `None` |
| `test_schema_violation` | Missing required fields → `None` |
| `test_prompt_includes_date` | System prompt builder injects current date |
| `test_health_check` | `/health` probe returns True/False |

### Golden Integration Suite (`tests/golden_messages.json`)

~10 hand-crafted Spanish messages with expected `IntentResult` objects. Runs against a live llama-server only when `LLM_BASE_URL` is explicitly set, marked with `@pytest.mark.integration`.
