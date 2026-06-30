from unittest.mock import patch
from app.schemas.bot import BotReply, Button
from app.services.linking_service import link_user, resolve_user


def test_bot_reply_schema():
    reply = BotReply(text="Hello")
    assert reply.text == "Hello"
    assert reply.buttons == []
    assert reply.parse_mode is None


def test_button_schema():
    btn = Button(text="Yes", callback_data="yes")
    assert btn.text == "Yes"
    assert btn.callback_data == "yes"


def test_resolve_user_not_linked():
    with patch("app.services.linking_service.redis_client.get") as mock_get:
        mock_get.return_value = None
        user = resolve_user(12345)
    assert user is None


def test_link_user_valid_email(test_user):
    with patch("app.services.linking_service.redis_client.set") as mock_set:
        result = link_user(12345, test_user.email)
    assert result is not None
    assert result.id == test_user.id
    mock_set.assert_called_once()
