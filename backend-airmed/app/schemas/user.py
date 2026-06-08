from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str | None = None


class UserUpdate(UserBase):
    pass


class UserOut(UserBase):
    id: int
    is_active: bool
    is_professional: bool

    model_config = ConfigDict(from_attributes=True)
