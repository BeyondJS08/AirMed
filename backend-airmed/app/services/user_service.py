from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, user: UserCreate) -> User:
    pass


def get_user_by_email(db: Session, email: str) -> User | None:
    pass
