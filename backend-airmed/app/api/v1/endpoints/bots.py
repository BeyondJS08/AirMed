import hmac
import logging

from fastapi import APIRouter, BackgroundTasks, Body, Header, HTTPException, Request, status

from app.core.config import settings
from app.schemas.bot import BotReply
from app.services.bot_conversation_service import process_message
from app.services.linking_service import link_user, resolve_user
from app.services.telegram_bot_service import parse_update, send_callback_answer, send_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("/telegram/webhook")
def telegram_webhook(
    request: Request,
    payload: dict = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    x_telegram_bot_api_secret_token: str | None = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    expected = settings.TELEGRAM_WEBHOOK_SECRET or ""
    if not hmac.compare_digest(secret, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    try:
        chat_id, text, callback_data, callback_query_id = parse_update(payload)
    except (KeyError, ValueError):
        logger.warning("Invalid Telegram update payload", extra={"payload": payload})
        return {"ok": True}

    if callback_query_id:
        send_callback_answer(callback_query_id)

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

    reply = process_message(chat_id, text, callback_data, user, background_tasks=background_tasks)
    send_message(chat_id, reply)
    return {"ok": True}
