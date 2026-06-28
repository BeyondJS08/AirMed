from datetime import datetime

from pydantic import BaseModel


class ProfessionalIntegrationOut(BaseModel):
    id: int
    professional_id: int
    provider: str
    google_email: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
