from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    phone_number: str | None = None


class UserCreate(UserBase):
    password: str | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone_number: str | None = None


class UserOut(UserBase):
    id: int
    is_active: bool
    is_professional: bool
    google_id: str | None = None

    model_config = ConfigDict(from_attributes=True)
