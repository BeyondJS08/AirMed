from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, model_validator


class AppointmentBase(BaseModel):
    start_time: datetime
    end_time: datetime
    notes: str | None = None
    is_virtual: bool = False
    location: str | None = None


class AppointmentCreate(AppointmentBase):
    professional_id: int

    @model_validator(mode="after")
    def end_must_be_after_start(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self

    @model_validator(mode="after")
    def must_be_in_future(self):
        if self.start_time <= datetime.now(timezone.utc):
            raise ValueError("start_time must be in the future")
        return self


class AppointmentUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    @model_validator(mode="after")
    def end_must_be_after_start(self):
        if self.start_time is not None and self.end_time is not None and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AppointmentOut(AppointmentBase):
    id: int
    professional_id: int
    patient_id: int
    status: str
    google_event_id: str | None = None

    model_config = ConfigDict(from_attributes=True)
