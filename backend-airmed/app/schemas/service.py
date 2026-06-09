from pydantic import BaseModel, ConfigDict


class ServiceBase(BaseModel):
    name: str
    description: str | None = None
    duration_minutes: int
    price: float | None = None


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    duration_minutes: int | None = None
    price: float | None = None


class ServiceOut(ServiceBase):
    id: int
    professional_id: int

    model_config = ConfigDict(from_attributes=True)
