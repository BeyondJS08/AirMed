from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.availability import Availability
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.user import User
from app.schemas.availability import AvailabilityCreate, AvailabilityUpdate


def _overlaps(existing: Availability, new_start: time, new_end: time) -> bool:
    return existing.start_time < new_end and existing.end_time > new_start


def _validate_no_overlap(
    db: Session,
    professional_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    exclude_id: int | None = None,
) -> None:
    windows = (
        db.query(Availability)
        .filter(
            Availability.professional_id == professional_id,
            Availability.day_of_week == day_of_week,
        )
    )
    if exclude_id is not None:
        windows = windows.filter(Availability.id != exclude_id)

    for existing in windows:
        if _overlaps(existing, start_time, end_time):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Availability window overlaps with an existing window",
            )


def create_availability(
    db: Session,
    professional_id: int,
    data: AvailabilityCreate,
) -> Availability:
    _validate_no_overlap(db, professional_id, data.day_of_week, data.start_time, data.end_time)
    av = Availability(
        professional_id=professional_id,
        day_of_week=data.day_of_week,
        start_time=data.start_time,
        end_time=data.end_time,
        is_active=data.is_active,
    )
    db.add(av)
    db.commit()
    db.refresh(av)
    return av


def get_availabilities(db: Session, professional_id: int) -> list[Availability]:
    return (
        db.query(Availability)
        .filter(Availability.professional_id == professional_id)
        .all()
    )


def get_availability(db: Session, availability_id: int) -> Availability | None:
    return db.query(Availability).filter(Availability.id == availability_id).first()


def update_availability(
    db: Session,
    availability: Availability,
    data: AvailabilityUpdate,
) -> Availability:
    update_data = data.model_dump(exclude_unset=True)
    if "day_of_week" in update_data or "start_time" in update_data or "end_time" in update_data:
        new_day = update_data.get("day_of_week", availability.day_of_week)
        new_start = update_data.get("start_time", availability.start_time)
        new_end = update_data.get("end_time", availability.end_time)
        _validate_no_overlap(db, availability.professional_id, new_day, new_start, new_end, exclude_id=availability.id)

    for field, value in update_data.items():
        setattr(availability, field, value)
    db.commit()
    db.refresh(availability)
    return availability


def delete_availability(db: Session, availability: Availability) -> None:
    db.delete(availability)
    db.commit()


def get_available_slots(
    db: Session,
    professional_id: int,
    target_date: date,
    service_id: int | None = None,
) -> list[dict]:
    professional = db.query(User).filter(User.id == professional_id).first()
    if not professional:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found",
        )

    day_of_week = target_date.weekday()
    windows = (
        db.query(Availability)
        .filter(
            Availability.professional_id == professional_id,
            Availability.day_of_week == day_of_week,
            Availability.is_active == True,
        )
        .all()
    )

    if not windows:
        return []

    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.professional_id == professional_id,
            Appointment.start_time >= datetime.combine(target_date, time.min),
            Appointment.start_time < datetime.combine(target_date, time.max),
            Appointment.status != "cancelled",
        )
        .all()
    )

    if service_id:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            return []
        duration = timedelta(minutes=service.duration_minutes)
    else:
        duration = None

    slots: list[dict] = []

    for window in windows:
        ranges = [(window.start_time, window.end_time)]

        for appointment in appointments:
            appt_start = appointment.start_time.time()
            appt_end = appointment.end_time.time()

            new_ranges = []
            for r_start, r_end in ranges:
                if appt_start >= r_end or appt_end <= r_start:
                    new_ranges.append((r_start, r_end))
                else:
                    if appt_start > r_start:
                        new_ranges.append((r_start, appt_start))
                    if appt_end < r_end:
                        new_ranges.append((appt_end, r_end))
            ranges = new_ranges

        for r_start, r_end in ranges:
            if duration:
                cursor = datetime.combine(target_date, r_start)
                end_dt = datetime.combine(target_date, r_end)
                while cursor + duration <= end_dt:
                    slots.append({
                        "start_time": cursor.isoformat(),
                        "end_time": (cursor + duration).isoformat(),
                    })
                    cursor += duration
            else:
                slots.append({
                    "start_time": datetime.combine(target_date, r_start).isoformat(),
                    "end_time": datetime.combine(target_date, r_end).isoformat(),
                })

    return slots
