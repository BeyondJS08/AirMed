from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate


def create_appointment(db: Session, appointment: AppointmentCreate) -> Appointment:
    pass


def list_appointments(db: Session) -> list[Appointment]:
    pass
