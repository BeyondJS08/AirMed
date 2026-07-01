# On-Premise LLM Integration (Layer 4B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a stateless NLU service that parses Spanish natural-language messages into structured intents + entities via gemma-4-E2B (llama.cpp, JSON schema-constrained output).

**Architecture:** `llm_service.interpret_message(text) → IntentResult | None`. Sync HTTP client calling llama.cpp's OpenAI-compatible `/chat/completions` endpoint. All failures → `None` → bot replies graceful fallback.

**Tech Stack:** FastAPI, httpx, Pydantic (JSON schema), llama.cpp (gemma-4-E2B), pytest + unittest.mock

---

## File Structure

| File | Action | Purpose |
|---|---|---|
| `app/schemas/llm.py` | Create | IntentResult, IntentName, Entities Pydantic models |
| `app/core/config.py` | Modify (lines 14-15) | Add LLM config vars |
| `app/services/llm_service.py` | Create | interpret_message(), build_system_prompt() |
| `tests/test_llm.py` | Create | Unit tests with mocked httpx |
| `tests/golden_messages.json` | Create | 10 hand-crafted Spanish messages + expected intents |
| `docker-compose.yml` | Modify | Add `llm` service |
| `requirements.txt` | Check | httpx already present; no new deps needed |

---

### Task 1: Schema + Config

**Files:**
- Create: `app/schemas/llm.py`
- Modify: `app/core/config.py`
- Test: `tests/test_llm.py` (first test)

- [ ] **Step 1: Write the failing schema/config test**

Add to `tests/test_llm.py`:
```python
"""Tests for LLM integration service."""
from app.core.config import settings
from app.schemas.llm import Entities, IntentName, IntentResult


def test_intent_result_schema():
    result = IntentResult(intent="schedule", entities={}, confidence=0.9)
    assert result.intent == IntentName.schedule
    assert result.confidence == 0.9
    schema = IntentResult.model_json_schema()
    assert "properties" in schema


def test_entities_defaults_are_none():
    entities = Entities()
    assert entities.date is None
    assert entities.time is None
    assert entities.service is None
    assert entities.professional is None
    assert entities.appointment_id is None
    assert entities.modality is None


def test_llm_config_defaults():
    assert hasattr(settings, "LLM_BASE_URL")
    assert hasattr(settings, "LLM_TIMEOUT")
    assert hasattr(settings, "LLM_ENABLED")
    assert hasattr(settings, "LLM_TEMPERATURE")
    assert hasattr(settings, "LLM_MODEL")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_llm.py::test_intent_result_schema tests/test_llm.py::test_entities_defaults_are_none tests/test_llm.py::test_llm_config_defaults -v
```
Expected: FAIL "No module named 'app.schemas.llm'" and "AttributeError: no attribute 'LLM_BASE_URL'"

- [ ] **Step 3: Write minimal schema**

`app/schemas/llm.py`:
```python
import enum

from pydantic import BaseModel


class IntentName(str, enum.Enum):
    schedule = "schedule"
    reschedule = "reschedule"
    cancel = "cancel"
    query = "query"
    unknown = "unknown"


class Entities(BaseModel):
    date: str | None = None
    time: str | None = None
    service: str | None = None
    professional: str | None = None
    appointment_id: int | None = None
    modality: str | None = None


class IntentResult(BaseModel):
    intent: IntentName
    entities: Entities
    confidence: float
```

- [ ] **Step 4: Add config variables**

Modify `app/core/config.py` — add these lines after `GOOGLE_CALENDAR_ENABLED`:
```python
    LLM_BASE_URL: str = "http://localhost:8080/v1"
    LLM_MODEL: str = "gemma-4-E2B"
    LLM_TIMEOUT: float = 30.0
    LLM_ENABLED: bool = False
    LLM_TEMPERATURE: float = 0.1
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_llm.py::test_intent_result_schema tests/test_llm.py::test_entities_defaults_are_none tests/test_llm.py::test_llm_config_defaults -v
```
Expected: 3 PASS

- [ ] **Step 6: Commit**

```bash
git add app/schemas/llm.py app/core/config.py tests/test_llm.py
git commit -m "feat(4b): add LLM intent schema and config"
```

---

### Task 2: Service — build_system_prompt

**Files:**
- Create: `app/services/llm_service.py`
- Modify: `tests/test_llm.py` (add prompt tests)

- [ ] **Step 1: Write failing tests for build_system_prompt**

Add to `tests/test_llm.py`:
```python
from datetime import datetime, timezone
from app.services.llm_service import build_system_prompt


def test_build_system_prompt_includes_date():
    prompt = build_system_prompt()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert today in prompt


def test_build_system_prompt_includes_spanish():
    prompt = build_system_prompt()
    assert "Eres un asistente médico" in prompt
    assert "Intenciones válidas" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_llm.py::test_build_system_prompt_includes_date tests/test_llm.py::test_build_system_prompt_includes_spanish -v
```
Expected: FAIL "No module named 'app.services.llm_service'"

- [ ] **Step 3: Write build_system_prompt**

`app/services/llm_service.py`:
```python
from datetime import datetime, timezone


def build_system_prompt() -> str:
    now = datetime.now(timezone.utc)
    return (
        "Eres un asistente médico. Analiza el mensaje del paciente y devuelve "
        "un JSON con la intención y las entidades extraídas.\n\n"
        f"Fecha actual: {now.strftime('%Y-%m-%d')}\n"
        f"Hora actual: {now.strftime('%H:%M')}\n\n"
        "Intenciones válidas: schedule, reschedule, cancel, query, unknown.\n\n"
        "Entidades:\n"
        "- date: fecha en formato ISO (YYYY-MM-DD)\n"
        "- time: hora en formato 24h (HH:MM)\n"
        "- service: nombre del servicio solicitado\n"
        "- professional: nombre o especialidad del profesional\n"
        "- appointment_id: ID numérico de cita existente (solo cancel/reschedule)\n"
        "- modality: \"virtual\" o \"in_person\"\n\n"
        "Ejemplos:\n"
        'Usuario: "Quiero una cita mañana a las 3pm con el dentista"\n'
        '→ {"intent":"schedule","entities":{"date":"2026-06-29","time":"15:00","service":"dentista"},"confidence":0.9}\n\n'
        'Usuario: "Necesito cancelar mi cita del viernes"\n'
        '→ {"intent":"cancel","entities":{"date":"2026-06-29"},"confidence":0.85}\n\n'
        'Usuario: "Tengo consulta el lunes, hay que cambiarla para el martes a las 10"\n'
        '→ {"intent":"reschedule","entities":{"date":"2026-06-29","time":"10:00"},"confidence":0.8}\n\n'
        'Usuario: "Hola, buenos días"\n'
        '→ {"intent":"unknown","entities":{},"confidence":0.1}\n\n'
        "Responde solo con JSON válido."
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_llm.py::test_build_system_prompt_includes_date tests/test_llm.py::test_build_system_prompt_includes_spanish -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/llm_service.py tests/test_llm.py
git commit -m "feat(4b): add build_system_prompt"
```

---

### Task 3: Service — interpret_message happy path

**Files:**
- Modify: `app/services/llm_service.py` (add interpret_message)
- Modify: `tests/test_llm.py` (add happy path tests)

- [ ] **Step 1: Write failing tests**

Add to `tests/test_llm.py`:
```python
from unittest.mock import patch
from app.schemas.llm import IntentResult
from app.services.llm_service import interpret_message


MOCK_SCHEDULE_RESPONSE = {
    "choices": [{
        "message": {
            "content": '{"intent":"schedule","entities":{"date":"2026-06-29","time":"15:00","service":"dentista"},"confidence":0.9}'
        }
    }]
}


def test_interpret_schedule_happy_path():
    with patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = MOCK_SCHEDULE_RESPONSE
        mock_post.return_value.raise_for_status = lambda: None

        result = interpret_message("Quiero una cita mañana a las 3pm con el dentista")

    assert result is not None
    assert result.intent.value == "schedule"
    assert result.entities.date == "2026-06-29"
    assert result.entities.time == "15:00"
    assert result.entities.service == "dentista"
    assert result.confidence == 0.9


def test_interpret_unknown_greeting():
    mock_data = {
        "choices": [{
            "message": {
                "content": '{"intent":"unknown","entities":{},"confidence":0.1}'
            }
        }]
    }
    with patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_data
        mock_post.return_value.raise_for_status = lambda: None

        result = interpret_message("Hola, buenos días")

    assert result is not None
    assert result.intent.value == "unknown"
    assert result.confidence == 0.1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_llm.py::test_interpret_schedule_happy_path tests/test_llm.py::test_interpret_unknown_greeting -v
```
Expected: FAIL "module 'app.services.llm_service' has no attribute 'interpret_message'"

- [ ] **Step 3: Write interpret_message**

Add to `app/services/llm_service.py`:
```python
import logging

import httpx

from app.core.config import settings
from app.schemas.llm import IntentResult

logger = logging.getLogger(__name__)


def interpret_message(text: str) -> IntentResult | None:
    if not settings.LLM_ENABLED:
        return None
    try:
        resp = httpx.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            json={
                "model": settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user", "content": text},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "IntentResult",
                        "schema": IntentResult.model_json_schema(),
                    },
                },
                "temperature": settings.LLM_TEMPERATURE,
            },
            timeout=settings.LLM_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return IntentResult.model_validate_json(content)
    except Exception:
        logger.warning("LLM interpret_message failed", exc_info=True)
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_llm.py::test_interpret_schedule_happy_path tests/test_llm.py::test_interpret_unknown_greeting -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/llm_service.py tests/test_llm.py
git commit -m "feat(4b): add interpret_message with happy path"
```

---

### Task 4: Service — error handling

**Files:**
- Modify: `tests/test_llm.py` (add error handling tests)

- [ ] **Step 1: Write failing error handling tests**

Add to `tests/test_llm.py`:
```python
def test_interpret_returns_none_when_disabled():
    with patch("app.services.llm_service.settings.LLM_ENABLED", False):
        result = interpret_message("Quiero una cita")
    assert result is None


def test_interpret_returns_none_on_timeout():
    with patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.side_effect = httpx.TimeoutException("timeout")
        result = interpret_message("Quiero una cita")
    assert result is None


def test_interpret_returns_none_on_http_error():
    with patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 500
        mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 error", request=None, response=mock_post.return_value
        )
        result = interpret_message("Quiero una cita")
    assert result is None


def test_interpret_returns_none_on_malformed_json():
    with patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"choices": [{"message": {"content": "not json"}}]}
        mock_post.return_value.raise_for_status = lambda: None
        result = interpret_message("Quiero una cita")
    assert result is None


def test_interpret_returns_none_on_schema_violation():
    with patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": '{"intent":"invalid","entities":{},"confidence":0.5}'}}]
        }
        mock_post.return_value.raise_for_status = lambda: None
        result = interpret_message("Quiero una cita")
    assert result is None


def test_interpret_returns_none_on_connection_error():
    with patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.side_effect = httpx.ConnectError("connection refused")
        result = interpret_message("Quiero una cita")
    assert result is None
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
pytest tests/test_llm.py::test_interpret_returns_none_when_disabled tests/test_llm.py::test_interpret_returns_none_on_timeout tests/test_llm.py::test_interpret_returns_none_on_http_error tests/test_llm.py::test_interpret_returns_none_on_malformed_json tests/test_llm.py::test_interpret_returns_none_on_schema_violation tests/test_llm.py::test_interpret_returns_none_on_connection_error -v
```
Expected: 6 PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_llm.py
git commit -m "feat(4b): error handling tests for interpret_message"
```

---

### Task 5: Docker compose setup + health check

**Files:**
- Modify: `docker-compose.yml`
- Modify: `app/services/llm_service.py` (add health check)
- Modify: `tests/test_llm.py` (add health check test)

- [ ] **Step 1: Write failing health check test**

Add to `tests/test_llm.py`:
```python
def test_health_check_returns_true():
    with patch("app.services.llm_service.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        from app.services.llm_service import health_check
        assert health_check() is True


def test_health_check_returns_false():
    with patch("app.services.llm_service.httpx.get") as mock_get:
        mock_get.side_effect = httpx.ConnectError("refused")
        from app.services.llm_service import health_check
        assert health_check() is False
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_llm.py::test_health_check_returns_true tests/test_llm.py::test_health_check_returns_false -v
```
Expected: FAIL "module 'app.services.llm_service' has no attribute 'health_check'"

- [ ] **Step 3: Write health check**

Add to `app/services/llm_service.py`:
```python
def health_check() -> bool:
    try:
        resp = httpx.get(f"{settings.LLM_BASE_URL}/health", timeout=5.0)
        resp.raise_for_status()
        return True
    except Exception:
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_llm.py::test_health_check_returns_true tests/test_llm.py::test_health_check_returns_false -v
```
Expected: 2 PASS

- [ ] **Step 5: Add LLM service to docker-compose.yml**

Modify `docker-compose.yml` — add before `volumes:` section (after the `frontend:` service):
```yaml
  llm:
    image: ghcr.io/ggerganov/llama.cpp:server
    ports:
      - "8080:8080"
    volumes:
      - ./models:/models
    command: -m /models/gemma-4-E2B.gguf --host 0.0.0.0 --port 8080 --json-schema
```

- [ ] **Step 6: Commit**

```bash
git add app/services/llm_service.py tests/test_llm.py docker-compose.yml
git commit -m "feat(4b): add health check and Docker compose LLM service"
```

---

### Task 6: Golden Test Set

**Files:**
- Create: `tests/golden_messages.json`
- Modify: `tests/test_llm.py` (add integration marker)

- [ ] **Step 1: Write golden messages file**

`tests/golden_messages.json`:
```json
[
  {
    "text": "Quiero una cita mañana a las 3pm con el dentista",
    "expected": {"intent": "schedule", "entities": {"date": "2026-06-29", "time": "15:00", "service": "dentista"}}
  },
  {
    "text": "Necesito cancelar mi cita del viernes",
    "expected": {"intent": "cancel", "entities": {"date": "2026-06-26"}}
  },
  {
    "text": "Tengo consulta el lunes, hay que cambiarla para el martes a las 10",
    "expected": {"intent": "reschedule", "entities": {"date": "2026-06-29", "time": "10:00"}}
  },
  {
    "text": "Hola, buenos días",
    "expected": {"intent": "unknown", "entities": {}}
  },
  {
    "text": "Quiero saber mis citas para esta semana",
    "expected": {"intent": "query", "entities": {}}
  },
  {
    "text": "Agenda una consulta virtual para el jueves a las 11 con la Dra. García",
    "expected": {"intent": "schedule", "entities": {"date": "2026-07-02", "time": "11:00", "professional": "Dra. García", "modality": "virtual"}}
  },
  {
    "text": "Mi cita número 5, quiero cancelarla",
    "expected": {"intent": "cancel", "entities": {"appointment_id": 5}}
  },
  {
    "text": "Cambia mi cita del miércoles 10am al jueves 2pm",
    "expected": {"intent": "reschedule", "entities": {"date": "2026-07-01", "time": "14:00"}}
  },
  {
    "text": "Quiero una limpieza dental el próximo lunes",
    "expected": {"intent": "schedule", "entities": {"date": "2026-07-06", "service": "limpieza dental"}}
  },
  {
    "text": "Necesito una consulta presencial mañana a primera hora",
    "expected": {"intent": "schedule", "entities": {"date": "2026-06-29", "modality": "in_person"}}
  }
]
```

- [ ] **Step 2: Write integration test marker**

Add at bottom of `tests/test_llm.py`:
```python
@pytest.mark.integration
@pytest.mark.skipif(not settings.LLM_ENABLED, reason="LLM not enabled")
def test_golden_messages():
    """Run golden messages against live LLM server."""
    import json
    import os
    golden_path = os.path.join(os.path.dirname(__file__), "golden_messages.json")
    with open(golden_path) as f:
        cases = json.load(f)
    for case in cases:
        result = interpret_message(case["text"])
        assert result is not None, f"Failed on: {case['text']}"
        assert result.intent.value == case["expected"]["intent"], (
            f"Intent mismatch for '{case['text']}': "
            f"expected {case['expected']['intent']}, got {result.intent.value}"
        )
```

- [ ] **Step 3: Verify unit tests still pass**

```bash
pytest tests/test_llm.py -v -m "not integration"
```
Expected: All previous tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/golden_messages.json tests/test_llm.py
git commit -m "feat(4b): add golden test set for LLM integration"
```

---

### Task 7: Run full test suite + final verification

- [ ] **Step 1: Run all unit tests**

```bash
pytest tests/test_llm.py -v -m "not integration"
```
Expected: All tests PASS (count should be ~16 tests)

- [ ] **Step 2: Run full backend test suite**

```bash
pytest -v
```
Expected: All previously passing tests still pass (122 + ~16 = ~138)

- [ ] **Step 3: Type-check if configured**

```bash
pip install -q mypy 2>/dev/null; mypy app/services/llm_service.py app/schemas/llm.py --ignore-missing-imports 2>&1 || true
```
Expected: No type errors (optional, informational)

- [ ] **Step 4: Final commit with all changes**

```bash
git add -A && git status
# Verify only relevant files are staged
```
Expected: Clean git status
