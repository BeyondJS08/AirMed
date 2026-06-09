from sqlalchemy.orm import Session

from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate


def create_service(
    db: Session, service: ServiceCreate, professional_id: int
) -> Service:
    db_service = Service(
        professional_id=professional_id,
        name=service.name,
        description=service.description,
        duration_minutes=service.duration_minutes,
        price=service.price,
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


def list_services(db: Session, professional_id: int | None = None) -> list[Service]:
    query = db.query(Service)
    if professional_id is not None:
        query = query.filter(Service.professional_id == professional_id)
    return query.all()


def get_service(db: Session, service_id: int) -> Service | None:
    return db.query(Service).filter(Service.id == service_id).first()


def update_service(
    db: Session, db_service: Service, update: ServiceUpdate
) -> Service:
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_service, field, value)
    db.commit()
    db.refresh(db_service)
    return db_service


def delete_service(db: Session, db_service: Service) -> None:
    db.delete(db_service)
    db.commit()
