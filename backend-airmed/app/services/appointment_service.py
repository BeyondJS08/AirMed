import logging
from datetime import date, datetime, time, timedelta, timezone

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.appointment import Appointment
from app.models.availability import Availability
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.google_calendar_service import ensure_sync
from app.services.notification_service import notify_appointment_status

logger = logging.getLogger(__name__)


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "scheduled": {"confirmed", "cancelled"},
    "confirmed": {"completed", "cancelled"},
    "completed": {"cancelled"},
}


def _sync_appointment(operation: str, appointment_id: int) -> None:
    db = SessionLocal()
    try:
        appointment = (
            db.query(Appointment).filter(Appointment.id == appointment_id).first()
        )
        if appointment:
            ensure_sync(db, operation, appointment)
    except Exception:
        logger.exception(
            "Background calendar sync failed for appointment %s", appointment_id
        )
    finally:
        db.close()


def _schedule_sync(background_tasks: BackgroundTasks | None, operation: str, appointment: Appointment) -> None:
    if background_tasks is None:
        return
    background_tasks.add_task(_sync_appointment, operation, appointment.id)


def _validate_slot_available(
    db: Session,
    professional_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_id: int | None = None,
) -> None:
    prof = db.query(User).filter(User.id == professional_id, User.is_active == True).first()
    if not prof:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Professional not found or inactive")

    target_day = start_time.date().weekday()
    windows = (
        db.query(Availability)
        .filter(
            Availability.professional_id == professional_id,
            Availability.day_of_week == target_day,
            Availability.is_active == True,
        )
        .all()
    )
    if not windows:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Professional has no availability on this date")

    appt_start_t = start_time.time()
    appt_end_t = end_time.time()
    fits_in_window = False
    for window in windows:
        if window.start_time <= appt_start_t and window.end_time >= appt_end_t:
            fits_in_window = True
            break
    if not fits_in_window:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Appointment does not fit within professional's availability window")

    query = db.query(Appointment).filter(
        Appointment.professional_id == professional_id,
        Appointment.status != "cancelled",
        Appointment.start_time < end_time,
        Appointment.end_time > start_time,
    )
    if exclude_id is not None:
        query = query.filter(Appointment.id != exclude_id)
    conflict = query.first()
    if conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Time slot conflicts with an existing appointment")


def _validate_transition(current_user: User, appointment: Appointment, new_status: str) -> None:
    allowed = ALLOWED_TRANSITIONS.get(appointment.status)
    if not allowed or new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Cannot transition from '{appointment.status}' to '{new_status}'",
        )
    is_professional = current_user.id == appointment.professional_id
    is_patient = current_user.id == appointment.patient_id
    if new_status == "confirmed" and not is_professional:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the professional can confirm appointments")
    if not is_professional and not is_patient:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")


def create_appointment(
    db: Session,
    data: AppointmentCreate,
    current_user: User,
    background_tasks: BackgroundTasks | None = None,
) -> Appointment:
    _validate_slot_available(db, data.professional_id, data.start_time, data.end_time)
    appt = Appointment(
        professional_id=data.professional_id,
        patient_id=current_user.id,
        start_time=data.start_time,
        end_time=data.end_time,
        notes=data.notes,
        is_virtual=data.is_virtual,
        location=data.location,
        status="scheduled",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    notify_appointment_status(db, appt)
    _schedule_sync(background_tasks, "create", appt)
    return appt


def get_appointments(
    db: Session,
    current_user: User,
    status_filter: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Appointment]:
    query = db.query(Appointment).filter(
        (Appointment.patient_id == current_user.id) | (Appointment.professional_id == current_user.id)
    )
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    if date_from:
        query = query.filter(Appointment.start_time >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        query = query.filter(Appointment.start_time <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))
    query = query.order_by(Appointment.start_time.asc())
    return query.all()


def get_appointment(db: Session, appointment_id: int) -> Appointment | None:
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()


def update_appointment(
    db: Session,
    appointment: Appointment,
    data: AppointmentUpdate,
    current_user: User,
    background_tasks: BackgroundTasks | None = None,
) -> Appointment:
    if data.status is not None:
        _validate_transition(current_user, appointment, data.status)
    if data.notes is not None:
        appointment.notes = data.notes
    times_changed = data.start_time is not None or data.end_time is not None
    if times_changed:
        start_time = data.start_time if data.start_time is not None else appointment.start_time
        end_time = data.end_time if data.end_time is not None else appointment.end_time
        _validate_slot_available(db, appointment.professional_id, start_time, end_time, exclude_id=appointment.id)
        appointment.start_time = start_time
        appointment.end_time = end_time
    if data.status is not None:
        appointment.status = data.status
    db.commit()
    db.refresh(appointment)
    if data.status is not None and data.status in ("confirmed", "completed", "cancelled"):
        notify_appointment_status(db, appointment)
    if data.status is not None:
        if data.status == "cancelled":
            _schedule_sync(background_tasks, "delete", appointment)
        elif data.status in ("scheduled", "confirmed"):
            operation = "create" if not appointment.google_event_id else "update"
            _schedule_sync(background_tasks, operation, appointment)
    elif times_changed:
        operation = "create" if not appointment.google_event_id else "update"
        _schedule_sync(background_tasks, operation, appointment)
    return appointment
