from pydantic import BaseModel


class Button(BaseModel):
    text: str
    callback_data: str


class BotReply(BaseModel):
    text: str
    buttons: list[list[Button]] = []
    parse_mode: str | None = None
