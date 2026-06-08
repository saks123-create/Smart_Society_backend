from pydantic import ConfigDict, validator
from typing import Optional
from datetime import datetime
from app.schemas.base import BaseSchema
from app.schemas.validators import validate_name, validate_phone, validate_int, validate_required_phone

class VisitorCreate(BaseSchema):
    name: str
    phone: Optional[str] = None
    purpose: Optional[str] = None
    block_tower: Optional[str] = None
    flat_no: Optional[int] = None
    flat_id: Optional[int] = None

    _name = validator("name", allow_reuse=True)(validate_name)
    _phone = validator("phone", allow_reuse=True)(validate_phone)
    _flat_no = validator("flat_no", allow_reuse=True)(lambda v: validate_int(v, "Flat No"))
    _flat = validator("flat_id", allow_reuse=True)(lambda v: validate_int(v, "Flat No"))

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "name": "Amit Singh",
                "phone": "9876543210",
                "purpose": "Delivery",
                "block_tower": "A",
                "flat_no": 12,
            }
        })

class VisitorPreRegister(BaseSchema):
    name: str
    phone: Optional[str] = None
    purpose: Optional[str] = None
    flat_no: Optional[int] = None
    flat_id: Optional[int] = None
    valid_for_hours: Optional[int] = 24

    _name = validator("name", allow_reuse=True)(validate_name)
    _phone = validator("phone", allow_reuse=True)(validate_phone)
    _flat_no = validator("flat_no", allow_reuse=True)(lambda v: validate_int(v, "Flat No"))
    _flat = validator("flat_id", allow_reuse=True)(lambda v: validate_int(v, "Flat No"))
    _hours = validator("valid_for_hours", allow_reuse=True)(lambda v: validate_int(v, "Valid hours"))

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "name": "Amit Singh",
                "phone": "9876543210",
                "purpose": "Delivery",
                "flat_no": 12,
                "valid_for_hours": 24,
            }
        })


class VisitorScanRequest(BaseSchema):
    qr_payload: str

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "qr_payload": "visitor:15:2f9c8a...",
            }
        })

class VisitorOut(BaseSchema):
    id: int
    name: str
    phone: Optional[str]
    purpose: Optional[str]
    flat_no: Optional[int]
    flat_id: Optional[int]
    flat_block: Optional[str] = None
    flat_number: Optional[int] = None
    flat_label: Optional[str] = None
    entry_time: Optional[datetime]
    exit_time: Optional[datetime]
    status: Optional[str] = None
    valid_until: Optional[datetime] = None
    pre_registered_at: Optional[datetime] = None



class VisitorPreRegisterOut(BaseSchema):
    visitor: VisitorOut
    qr_payload: str
    qr_image_base64: Optional[str] = None
    valid_until: Optional[datetime] = None
