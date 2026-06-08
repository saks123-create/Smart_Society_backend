from pydantic import ConfigDict, validator
from typing import Optional
from datetime import date, datetime
from app.schemas.base import BaseSchema
from app.schemas.validators import (
    validate_name,
    validate_phone,
    validate_int,
    validate_email,
    validate_required_text,
)
from app.models.resident import ResidentRole

class ResidentBaseIn(BaseSchema):
    name: str
    phone: str
    email: str
    flat_id: Optional[int] = None
    role: ResidentRole
    move_in_date: date
    move_out_date: Optional[date] = None

    _name = validator("name", allow_reuse=True)(validate_name)
    _phone = validator("phone", allow_reuse=True)(validate_phone)
    _email = validator("email", allow_reuse=True)(validate_email)
    _flat = validator("flat_id", allow_reuse=True)(lambda v: validate_int(v, "Flat ID"))
    @validator("move_out_date", allow_reuse=True)
    def validate_move_out_date(cls, value, values):
        move_in = values.get("move_in_date")
        if value is not None and move_in is not None and value <= move_in:
            raise ValueError("move_out_date must be after move_in_date")
        return value

class ResidentCreate(ResidentBaseIn):
    user_id: Optional[int] = None
    password: Optional[str] = None

    _password = validator("password", allow_reuse=True)(
        lambda v: validate_required_text(v, "Password") if v is not None else None
    )

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "user_id": 5,
                "password": "Resident@123",
                "name": "Rahul Sharma",
                "phone": "8888888888",
                "email": "rahul@example.com",
                "flat_id": 12,
                "role": "owner",
                "move_in_date": "2024-01-15",
            }
        })

class ResidentUpdate(BaseSchema):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    flat_id: Optional[int] = None
    role: Optional[ResidentRole] = None
    move_in_date: Optional[date] = None
    move_out_date: Optional[date] = None

    _name = validator("name", allow_reuse=True)(validate_name)
    _phone = validator("phone", allow_reuse=True)(validate_phone)
    _email = validator("email", allow_reuse=True)(validate_email)
    _flat = validator("flat_id", allow_reuse=True)(lambda v: validate_int(v, "Flat ID"))
    @validator("move_out_date", allow_reuse=True)
    def validate_move_out_date(cls, value, values):
        move_in = values.get("move_in_date")
        if value is not None and move_in is not None and value <= move_in:
            raise ValueError("move_out_date must be after move_in_date")
        return value

class ResidentOut(BaseSchema):
    id: int
    user_id: Optional[int] = None
    name: str
    phone: str
    email: str
    flat_id: Optional[int] = None
    flat_block: Optional[str] = None
    flat_number: Optional[int] = None
    flat_label: Optional[str] = None
    role: ResidentRole
    move_in_date: date
    move_out_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ResidentSummary(BaseSchema):
    total_residents: int
    pending_approvals: int
    assigned_flats: int
    move_out_scheduled: int
