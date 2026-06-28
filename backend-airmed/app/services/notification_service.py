from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.notification import Notification, NotificationChannel, NotificationStatus


def create_notification(
    db: Session,
    *,
    user_id: int,
    channel: NotificationChannel = NotificationChannel.email,
    subject: str | None = None,
    message: str,
    appointment_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        channel=channel,
        status=NotificationStatus.pending,
        subject=subject,
        message=message,
        appointment_id=appointment_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def list_notifications(
    db: Session,
    user_id: int,
    status: NotificationStatus | None = None,
    limit: int = 50,
) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if status:
        query = query.filter(Notification.status == status)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


def get_notification(db: Session, notification_id: int) -> Notification | None:
    return db.query(Notification).filter(Notification.id == notification_id).first()


def mark_sent(db: Session, notification_id: int) -> Notification | None:
    notification = get_notification(db, notification_id)
    if notification:
        notification.status = NotificationStatus.sent
        notification.sent_at = datetime.now(timezone.utc)
        db.commit()
    return notification


def mark_failed(db: Session, notification_id: int, error: str) -> Notification | None:
    notification = get_notification(db, notification_id)
    if notification:
        notification.status = NotificationStatus.failed
        notification.error = error
        db.commit()
    return notification


def mark_read(db: Session, notification_id: int) -> Notification | None:
    notification = get_notification(db, notification_id)
    if notification:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
    return notification


def notify_appointment_status(db: Session, appointment: Appointment) -> list[Notification]:
    status_map = {
        "scheduled": ("Appointment Booked", "Your appointment has been scheduled."),
        "confirmed": ("Appointment Confirmed", "Your appointment has been confirmed."),
        "completed": ("Appointment Completed", "Your appointment has been completed."),
        "cancelled": ("Appointment Cancelled", "Your appointment has been cancelled."),
    }
    subject, message = status_map.get(appointment.status, ("Notification", "Your appointment has been updated."))
    notifs = []
    for user_id in (appointment.patient_id, appointment.professional_id):
        n = create_notification(
            db,
            user_id=user_id,
            channel=NotificationChannel.email,
            subject=subject,
            message=message,
            appointment_id=appointment.id,
        )
        notifs.append(n)
    return notifs
