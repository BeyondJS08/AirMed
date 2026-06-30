import json
import logging

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

try:
    import redis

    redis_client = redis.from_url(
        settings.REDIS_URL or "redis://localhost:6379/0", decode_responses=True
    )
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
        redis_client.set(f"bot:link:{chat_id}", json.dumps({"user_id": user.id}))
        return user
    finally:
        db.close()
