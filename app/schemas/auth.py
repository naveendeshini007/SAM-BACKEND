from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    require_password_change: Optional[bool] = False
    id: Optional[str] = None
    is_admin: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    username_or_email: Optional[str] = None
    old_password: Optional[str] = None
    new_password: str


class RefreshResponse(BaseModel):
    access_token: str
