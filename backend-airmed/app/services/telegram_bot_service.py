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
