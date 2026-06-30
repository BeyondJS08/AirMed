import enum

from pydantic import BaseModel


class SessionState(str, enum.Enum):
    idle = "idle"
    awaiting_confirmation = "awaiting_confirmation"
    cancel_confirming = "cancel_confirming"
    reschedule_confirming = "reschedule_confirming"
    booking = "booking"
    cancelling = "cancelling"
    rescheduling = "rescheduling"
    linking = "linking"


class Button(BaseModel):
    text: str
    callback_data: str


class BotReply(BaseModel):
    text: str
    buttons: list[list[Button]] = []
    parse_mode: str | None = None
