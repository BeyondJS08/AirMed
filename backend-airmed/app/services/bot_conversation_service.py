import enum
import json
import logging
from datetime import datetime, timezone

from app.core.config import settings

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
