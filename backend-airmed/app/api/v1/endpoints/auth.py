from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


@router.post("/login")
async def login():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Not implemented")
