from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentOut, AppointmentUpdate
from app.services.appointment_service import (
    create_appointment,
    get_appointment,
    get_appointments,
    update_appointment,
)

router = APIRouter()


@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_new_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_appointment(db, data, current_user)


@router.get("/", response_model=list[AppointmentOut])
async def list_user_appointments(
    status: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_appointments(db, current_user, status, date_from, date_to)


@router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment_by_id(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if appt.patient_id != current_user.id and appt.professional_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")
    return appt


@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment_by_id(
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if appt.patient_id != current_user.id and appt.professional_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")
    return update_appointment(db, appt, data, current_user)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if appt.patient_id != current_user.id and appt.professional_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")
    update_appointment(db, appt, AppointmentUpdate(status="cancelled"), current_user)
