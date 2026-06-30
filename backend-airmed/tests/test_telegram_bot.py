"""Tests for Telegram bot service."""
from unittest.mock import patch

from app.schemas.bot import BotReply, Button
from app.services.telegram_bot_service import parse_update, send_message, set_webhook


def test_parse_message_update():
    payload = {
        "message": {
            "chat": {"id": 12345},
            "text": "Hola",
        }
    }
    chat_id, text, callback_data = parse_update(payload)
    assert chat_id == 12345
    assert text == "Hola"
    assert callback_data is None


def test_parse_callback_update():
    payload = {
        "callback_query": {
            "id": "q1",
            "message": {"chat": {"id": 12345}},
            "data": "confirm_slot:0",
        }
    }
    chat_id, text, callback_data = parse_update(payload)
    assert chat_id == 12345
    assert text is None
    assert callback_data == "confirm_slot:0"


def test_send_message():
    reply = BotReply(text="Hello")
    with patch("app.services.telegram_bot_service.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None
        result = send_message(12345, reply)
    assert result is True


def test_set_webhook():
    with patch("app.services.telegram_bot_service.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        result = set_webhook("https://example.com/webhook")
    assert result is True
