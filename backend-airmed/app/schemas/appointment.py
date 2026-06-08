from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AppointmentBase(BaseModel):
    start_time: datetime
    end_time: datetime
    notes: str | None = None
    is_virtual: bool = False
    location: str | None = None


class AppointmentCreate(AppointmentBase):
    professional_id: int
    patient_id: int


class AppointmentUpdate(AppointmentBase):
    status: str | None = None


class AppointmentOut(AppointmentBase):
    id: int
    status: str
    google_event_id: str | None = None

    model_config = ConfigDict(from_attributes=True)
