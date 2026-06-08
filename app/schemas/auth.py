from datetime import datetime
from pydantic import EmailStr, ConfigDict, validator
from typing import Optional
from app.models.user import UserRole, UserStatus
from app.schemas.base import BaseSchema
from app.schemas.validators import (
    validate_phone,
    validate_name,
    validate_int,
    validate_required_text,
    validate_strong_password,
)

class LoginRequest(BaseSchema):
    email: EmailStr
    password: str
    remember_me: bool = False

    _password = validator("password", allow_reuse=True)(lambda v: validate_required_text(v, "Password"))

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "email": "admin@society.com",
                "password": "Admin@123",
            }
        })

class RegisterRequest(BaseSchema):
    email: EmailStr
    password: str
    phone: str
    full_name: str
    block: str
    flat_number: int

    _phone = validator("phone", allow_reuse=True)(validate_phone)
    _name = validator("full_name", allow_reuse=True)(validate_name)
    _block = validator("block", allow_reuse=True)(lambda v: validate_required_text(v, "Block"))
    _flat = validator("flat_number", allow_reuse=True)(lambda v: validate_int(v, "Flat number"))
    _password = validator("password", allow_reuse=True)(validate_strong_password)

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "email": "resident@society.com",
                "password": "Resident@123",
                "phone": "9999999999",
                "full_name": "Rahul Sharma",
                "block": "A",
                "flat_number": 12,
            }
        })

class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserOut(BaseSchema):
    id: int
    email: EmailStr
    email_verified: bool = False
    role: UserRole
    status: Optional[UserStatus] = None
    phone: Optional[str]
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RegisterResponse(BaseSchema):
    user: UserOut
    message: str

class TokenData(BaseSchema):
    user_id: int
    role: UserRole

class GuardCreate(BaseSchema):
    email: EmailStr
    password: str
    phone: Optional[str] = None

    _phone = validator("phone", allow_reuse=True)(validate_phone)
    _password = validator("password", allow_reuse=True)(validate_strong_password)


class GuardUpdate(BaseSchema):
    phone: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

    _phone = validator("phone", allow_reuse=True)(validate_phone)
    _password = validator("password", allow_reuse=True)(validate_strong_password)


class GuardSummary(BaseSchema):
    total_guards: int
    active_guards: int
    inactive_guards: int
    guards_with_phone: int

class ForgotPasswordRequest(BaseSchema):
    email: EmailStr

class ResetPasswordRequest(BaseSchema):
    token: str
    new_password: str

    _password = validator("new_password", allow_reuse=True)(lambda v: validate_strong_password(v, "Password"))
