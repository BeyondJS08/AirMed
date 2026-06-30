"""Tests for Telegram bot service."""
from unittest.mock import patch

from app.schemas.bot import BotReply, Button
from app.services.telegram_bot_service import parse_update, send_callback_answer, send_message, set_webhook


def test_parse_message_update():
    payload = {
        "message": {
            "chat": {"id": 12345},
            "text": "Hola",
        }
    }
    chat_id, text, callback_data, callback_query_id = parse_update(payload)
    assert chat_id == 12345
    assert text == "Hola"
    assert callback_data is None
    assert callback_query_id is None


def test_parse_callback_update():
    payload = {
        "callback_query": {
            "id": "q1",
            "message": {"chat": {"id": 12345}},
            "data": "confirm_slot:0",
        }
    }
    chat_id, text, callback_data, callback_query_id = parse_update(payload)
    assert chat_id == 12345
    assert text is None
    assert callback_data == "confirm_slot:0"
    assert callback_query_id == "q1"


def test_send_message():
    reply = BotReply(text="Hello")
    with patch("app.services.telegram_bot_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None
        result = send_message(12345, reply)
    assert result is True


def test_send_callback_answer():
    with patch("app.services.telegram_bot_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None
        result = send_callback_answer("q1", text="OK")
    assert result is True


def test_set_webhook():
    with patch("app.services.telegram_bot_service.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        result = set_webhook("https://example.com/webhook")
    assert result is True


def test_webhook_secret_verification(client):
    from app.core.config import settings
    original_secret = settings.TELEGRAM_WEBHOOK_SECRET
    settings.TELEGRAM_WEBHOOK_SECRET = "super-secret"
    try:
        payload = {"message": {"chat": {"id": 12345}, "text": "Hola"}}
        resp = client.post(
            "/api/v1/bots/telegram/webhook",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
        )
        assert resp.status_code == 403
    finally:
        settings.TELEGRAM_WEBHOOK_SECRET = original_secret


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
