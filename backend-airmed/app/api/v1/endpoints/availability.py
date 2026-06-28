from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_professional, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityOut,
    AvailabilityUpdate,
    AvailableSlotOut,
)
from app.services.availability_service import (
    create_availability,
    delete_availability,
    get_availabilities,
    get_availability,
    get_available_slots,
    update_availability,
)

router = APIRouter()


@router.get("/", response_model=list[AvailabilityOut])
async def list_availabilities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_professional),
):
    return get_availabilities(db, current_user.id)


@router.post("/", response_model=AvailabilityOut, status_code=status.HTTP_201_CREATED)
async def create_new_availability(
    data: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_professional),
):
    return create_availability(db, current_user.id, data)


@router.put("/{availability_id}", response_model=AvailabilityOut)
async def update_availability_by_id(
    availability_id: int,
    data: AvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_professional),
):
    av = get_availability(db, availability_id)
    if not av:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found")
    if av.professional_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your availability")
    return update_availability(db, av, data)


@router.delete("/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability_by_id(
    availability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_professional),
):
    av = get_availability(db, availability_id)
    if not av:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found")
    if av.professional_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your availability")
    delete_availability(db, av)


@router.get("/available-slots", response_model=list[AvailableSlotOut])
async def list_available_slots(
    professional_id: int = Query(...),
    date: date = Query(...),
    service_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_available_slots(db, professional_id, date, service_id)
