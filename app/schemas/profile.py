from pydantic import validator
from typing import Optional
from datetime import date
from app.schemas.base import BaseSchema
from app.schemas.validators import validate_name, validate_phone, validate_int, validate_email
from app.models.resident import ResidentRole

class ProfileUpdate(BaseSchema):
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
