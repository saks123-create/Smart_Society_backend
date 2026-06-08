from pydantic import EmailStr, validator
from typing import Optional
from app.schemas.base import BaseSchema
from app.schemas.validators import (
    validate_name,
    validate_phone,
    validate_required_text,
    validate_optional_text,
    validate_strong_password,
)

class SettingsBase(BaseSchema):
    society_name: str
    society_address: str
    society_phone: str
    society_email: EmailStr
    admin_name: str
    admin_email: EmailStr
    admin_phone: str
    notify_visitors: bool = True
    notify_complaints: bool = True
    notify_notices: bool = True
    policy_text: Optional[str] = None

    _society_name = validator("society_name", allow_reuse=True)(lambda v: validate_optional_text(v, "Society name"))
    _society_address = validator("society_address", allow_reuse=True)(lambda v: validate_optional_text(v, "Society address"))
    _society_phone = validator("society_phone", allow_reuse=True)(validate_phone)
    _admin_name = validator("admin_name", allow_reuse=True)(lambda v: validate_name(v, "Admin name"))
    _admin_phone = validator("admin_phone", allow_reuse=True)(validate_phone)

class SettingsUpdate(BaseSchema):
    society_name: Optional[str] = None
    society_address: Optional[str] = None
    society_phone: Optional[str] = None
    society_email: Optional[EmailStr] = None
    admin_name: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    admin_phone: Optional[str] = None
    notify_visitors: Optional[bool] = None
    notify_complaints: Optional[bool] = None
    notify_notices: Optional[bool] = None
    policy_text: Optional[str] = None

    _society_name = validator("society_name", allow_reuse=True)(lambda v: validate_required_text(v, "Society name"))
    _society_address = validator("society_address", allow_reuse=True)(lambda v: validate_required_text(v, "Society address"))
    _society_phone = validator("society_phone", allow_reuse=True)(validate_phone)
    _admin_name = validator("admin_name", allow_reuse=True)(lambda v: validate_name(v, "Admin name"))
    _admin_phone = validator("admin_phone", allow_reuse=True)(validate_phone)

class AdminPasswordChangeRequest(BaseSchema):
    current_password: str
    new_password: str
    confirm_password: str

    _current_password = validator("current_password", allow_reuse=True)(lambda v: validate_required_text(v, "Current password"))
    _new_password = validator("new_password", allow_reuse=True)(lambda v: validate_strong_password(v, "New password"))
    _confirm_password = validator("confirm_password", allow_reuse=True)(lambda v: validate_required_text(v, "Confirm password"))

    @validator("confirm_password")
    def passwords_match(cls, value, values):
        if values.get("new_password") and value != values["new_password"]:
            raise ValueError("Confirm password must match new password")
        return value

class SettingsOut(SettingsBase):
    id: int
