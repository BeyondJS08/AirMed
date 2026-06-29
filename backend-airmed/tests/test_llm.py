"""Tests for LLM integration service."""
import json
import os
from datetime import datetime, timezone
from unittest.mock import patch

import httpx
import pytest

from app.core.config import settings
from app.schemas.llm import Entities, IntentName, IntentResult
from app.services.llm_service import build_system_prompt, health_check, interpret_message

# ────────────────────────────────────────────────────────────
# Task 1: Schema + Config
# ────────────────────────────────────────────────────────────


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


# ────────────────────────────────────────────────────────────
# Task 2: build_system_prompt
# ────────────────────────────────────────────────────────────


def test_build_system_prompt_includes_date():
    prompt = build_system_prompt()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert today in prompt


def test_build_system_prompt_includes_spanish():
    prompt = build_system_prompt()
    assert "Eres un asistente médico" in prompt
    assert "Intenciones válidas" in prompt


# ────────────────────────────────────────────────────────────
# Task 3: Happy path tests for interpret_message
# ────────────────────────────────────────────────────────────

MOCK_SCHEDULE_RESPONSE = {
    "choices": [{
        "message": {
            "content": '{"intent":"schedule","entities":{"date":"2026-06-29","time":"15:00","service":"dentista"},"confidence":0.9}'
        }
    }]
}


def test_interpret_schedule_happy_path():
    with (
        patch("app.services.llm_service.settings.LLM_ENABLED", True),
        patch("app.services.llm_service.httpx.post") as mock_post,
    ):
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
    with (
        patch("app.services.llm_service.settings.LLM_ENABLED", True),
        patch("app.services.llm_service.httpx.post") as mock_post,
    ):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_data
        mock_post.return_value.raise_for_status = lambda: None
        result = interpret_message("Hola, buenos días")
    assert result is not None
    assert result.intent.value == "unknown"
    assert result.confidence == 0.1


def test_interpret_cancel():
    mock_data = {
        "choices": [{
            "message": {
                "content": '{"intent":"cancel","entities":{"date":"2026-06-26"},"confidence":0.85}'
            }
        }]
    }
    with (
        patch("app.services.llm_service.settings.LLM_ENABLED", True),
        patch("app.services.llm_service.httpx.post") as mock_post,
    ):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_data
        mock_post.return_value.raise_for_status = lambda: None
        result = interpret_message("Necesito cancelar mi cita del viernes")
    assert result is not None
    assert result.intent.value == "cancel"
    assert result.entities.date == "2026-06-26"
    assert result.confidence == 0.85


def test_interpret_reschedule():
    mock_data = {
        "choices": [{
            "message": {
                "content": '{"intent":"reschedule","entities":{"date":"2026-06-29","time":"10:00"},"confidence":0.8}'
            }
        }]
    }
    with (
        patch("app.services.llm_service.settings.LLM_ENABLED", True),
        patch("app.services.llm_service.httpx.post") as mock_post,
    ):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_data
        mock_post.return_value.raise_for_status = lambda: None
        result = interpret_message("Tengo consulta, hay que cambiarla")
    assert result is not None
    assert result.intent.value == "reschedule"
    assert result.entities.date == "2026-06-29"
    assert result.confidence == 0.8


def test_interpret_query():
    mock_data = {
        "choices": [{
            "message": {
                "content": '{"intent":"query","entities":{},"confidence":0.7}'
            }
        }]
    }
    with (
        patch("app.services.llm_service.settings.LLM_ENABLED", True),
        patch("app.services.llm_service.httpx.post") as mock_post,
    ):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_data
        mock_post.return_value.raise_for_status = lambda: None
        result = interpret_message("Quiero saber mis citas")
    assert result is not None
    assert result.intent.value == "query"
    assert result.confidence == 0.7


# ────────────────────────────────────────────────────────────
# Task 4: Error handling tests
# ────────────────────────────────────────────────────────────


def test_interpret_returns_none_when_disabled():
    with patch("app.services.llm_service.settings.LLM_ENABLED", False):
        result = interpret_message("Quiero una cita")
    assert result is None


def test_interpret_returns_none_on_timeout():
    with patch("app.services.llm_service.settings.LLM_ENABLED", True), patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.side_effect = httpx.TimeoutException("timeout")
        result = interpret_message("Quiero una cita")
    assert result is None


def test_interpret_returns_none_on_http_error():
    with patch("app.services.llm_service.settings.LLM_ENABLED", True), patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 500
        mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 error", request=None, response=mock_post.return_value
        )
        result = interpret_message("Quiero una cita")
    assert result is None


def test_interpret_returns_none_on_malformed_json():
    with patch("app.services.llm_service.settings.LLM_ENABLED", True), patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"choices": [{"message": {"content": "not json"}}]}
        mock_post.return_value.raise_for_status = lambda: None
        result = interpret_message("Quiero una cita")
    assert result is None


def test_interpret_returns_none_on_schema_violation():
    with patch("app.services.llm_service.settings.LLM_ENABLED", True), patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": '{"intent":"invalid","entities":{},"confidence":0.5}'}}]
        }
        mock_post.return_value.raise_for_status = lambda: None
        result = interpret_message("Quiero una cita")
    assert result is None


def test_interpret_returns_none_on_connection_error():
    with patch("app.services.llm_service.settings.LLM_ENABLED", True), patch("app.services.llm_service.httpx.post") as mock_post:
        mock_post.side_effect = httpx.ConnectError("connection refused")
        result = interpret_message("Quiero una cita")
    assert result is None


# ────────────────────────────────────────────────────────────
# Task 5: Health check
# ────────────────────────────────────────────────────────────


def test_health_check_returns_true():
    with patch("app.services.llm_service.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        assert health_check() is True


def test_health_check_returns_false():
    with patch("app.services.llm_service.httpx.get") as mock_get:
        mock_get.side_effect = httpx.ConnectError("refused")
        assert health_check() is False


# ────────────────────────────────────────────────────────────
# Task 6: Golden test set (integration)
# ────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.skipif(not settings.LLM_ENABLED, reason="LLM not enabled")
def test_golden_messages():
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
        for key, val in case["expected"].get("entities", {}).items():
            assert getattr(result.entities, key, None) == val, (
                f"Entity '{key}' mismatch for '{case['text']}': "
                f"expected {val}, got {getattr(result.entities, key, None)}"
            )
