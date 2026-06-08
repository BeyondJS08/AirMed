from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_current_user(db: Session = Depends(get_db)):
    pass
