from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    id: int
    appointment_id: int | None = None
    user_id: int
    channel: str
    status: str
    subject: str | None = None
    message: str
    error: str | None = None
    created_at: datetime
    sent_at: datetime | None = None
    read_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
