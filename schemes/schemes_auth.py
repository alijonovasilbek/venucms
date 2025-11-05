from pydantic import BaseModel, EmailStr
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel
from typing import Optional, Dict
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    surname: str
    password: str




class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    surname: str
    is_active: bool

    class Config:
        from_attributes = True

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int

class RefreshIn(BaseModel):
    refresh_token: str

class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    email: EmailStr
    code: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class SuccessResponse(BaseModel):
    success: bool = True
    message: str


class RedirectResponse(BaseModel):
    redirect_url: str