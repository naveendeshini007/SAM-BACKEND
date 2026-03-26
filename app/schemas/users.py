from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str


class UserOut(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    full_name: str
    must_change_password: bool
    is_active: bool

    model_config = {"from_attributes": True}
