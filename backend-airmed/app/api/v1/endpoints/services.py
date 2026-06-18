from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_professional, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate
from app.services.service_service import (
    create_service,
    delete_service,
    get_service,
    list_services,
    update_service,
)

router = APIRouter()


@router.get("/", response_model=list[ServiceOut])
async def list_all_services(
    professional_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list_services(db, professional_id)


@router.post("/", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
async def create_new_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_professional),
):
    return create_service(db, service, current_user.id)


@router.get("/{service_id}", response_model=ServiceOut)
async def get_service_by_id(
    service_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    db_service = get_service(db, service_id)
    if not db_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return db_service


@router.put("/{service_id}", response_model=ServiceOut)
async def update_service_by_id(
    service_id: int,
    update: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_professional),
):
    db_service = get_service(db, service_id)
    if not db_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if db_service.professional_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your service")
    return update_service(db, db_service, update)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_by_id(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_professional),
):
    db_service = get_service(db, service_id)
    if not db_service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if db_service.professional_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your service")
    delete_service(db, db_service)
