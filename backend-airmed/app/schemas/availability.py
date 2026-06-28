from datetime import datetime, time
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AvailabilityBase(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    is_active: bool = True


class AvailabilityCreate(AvailabilityBase):
    @model_validator(mode="after")
    def end_must_be_after_start(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AvailabilityUpdate(BaseModel):
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def end_must_be_after_start(self):
        if self.start_time is not None and self.end_time is not None and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AvailabilityOut(AvailabilityBase):
    id: int
    professional_id: int

    model_config = ConfigDict(from_attributes=True)


class AvailableSlotOut(BaseModel):
    start_time: datetime
    end_time: datetime
