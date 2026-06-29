import enum
from pydantic import BaseModel


class IntentName(str, enum.Enum):
    schedule = "schedule"
    reschedule = "reschedule"
    cancel = "cancel"
    query = "query"
    unknown = "unknown"


class Entities(BaseModel):
    date: str | None = None
    time: str | None = None
    service: str | None = None
    professional: str | None = None
    appointment_id: int | None = None
    modality: str | None = None


class IntentResult(BaseModel):
    intent: IntentName
    entities: Entities
    confidence: float
