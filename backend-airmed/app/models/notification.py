import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, Index

from app.db.base import Base


class NotificationChannel(str, enum.Enum):
    email = "email"
    whatsapp = "whatsapp"
    telegram = "telegram"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False, default=NotificationChannel.email)
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.pending)
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)


    __table_args__ = (
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_appointment", "appointment_id"),
    )
