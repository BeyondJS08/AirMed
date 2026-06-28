from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfessionalIntegrationOut(BaseModel):
    id: int
    professional_id: int
    provider: str
    google_email: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
