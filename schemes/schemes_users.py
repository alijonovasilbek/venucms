from pydantic import BaseModel, EmailStr
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional

# --- USER SCHEMAS ---
class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    surname: str
    password: str
    is_active: bool = True

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    surname: str
    is_active: bool


class UserListResponse(BaseModel):
    users: List[UserResponse]
    statistics: dict

class UserToggleResponse(BaseModel):
    is_active: bool
    active_user_count: int
    inactive_user_count: int


# --- GENERAL RESPONSE SCHEMAS ---
class SuccessResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str


# --- DASHBOARD STATISTICS SCHEMA ---
class DashboardStatistics(BaseModel):
    user_count: int
    active_user_count: int
    inactive_user_count: int

class DashboardResponse(BaseModel):
    users: List[dict]
    statistics: DashboardStatistics


class UserPermissionResponse(BaseModel):
    """
    User permissions response schema
    """
    user_id: int
    user_email: str
    user_name: str

    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "user_email": "user@example.com",
                "user_name": "John Doe",
            }
        }


class SuccessResponse(BaseModel):
    """
    Muvaffaqiyatli operatsiya uchun response
    """
    message: str

    class Config:
        schema_extra = {
            "example": {
                "message": "Operatsiya muvaffaqiyatli bajarildi"
            }
        }


class TodayCustomerInfo(BaseModel):
    id: int
    full_name: str
    platform: str
    username: Optional[str] = None
    phone_number: str
    status: str
    assistant_name: Optional[str] = None
    created_at: str  # ISO

    class Config:
        from_attributes = True


class DailyMetricsResponse(BaseModel):
    today_customers: List[TodayCustomerInfo]
    need_to_call_count: int

    class Config:
        from_attributes = True

class CreateResponse(BaseModel):
    message: str
    id: int


