from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/professionals", response_model=list[UserOut])
async def list_professionals(db: Session = Depends(get_db)):
    return db.query(User).filter(User.is_professional == True, User.is_active == True).all()
