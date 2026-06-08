from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from app.db.base import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, default="scheduled")
    notes = Column(Text, nullable=True)
    is_virtual = Column(Boolean, default=False)
    location = Column(String, nullable=True)
    google_event_id = Column(String, nullable=True)
