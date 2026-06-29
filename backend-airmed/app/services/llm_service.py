import logging
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.schemas.llm import IntentResult

logger = logging.getLogger(__name__)


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
        '- modality: "virtual" o "in_person"\n\n'
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


def health_check() -> bool:
    try:
        resp = httpx.get(f"{settings.LLM_BASE_URL}/health", timeout=5.0)
        resp.raise_for_status()
        return True
    except Exception:
        return False
