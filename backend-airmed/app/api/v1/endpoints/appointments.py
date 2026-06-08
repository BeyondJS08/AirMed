from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.appointment import AppointmentOut, AppointmentCreate

router = APIRouter()


@router.post("/", response_model=AppointmentOut)
async def create_appointment(
    appointment: AppointmentCreate, db: Session = Depends(get_db)
):
    pass


@router.get("/", response_model=list[AppointmentOut])
async def list_appointments(db: Session = Depends(get_db)):
    pass
