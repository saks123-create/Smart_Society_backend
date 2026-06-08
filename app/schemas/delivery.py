from pydantic import ConfigDict, validator
from typing import Optional
from datetime import datetime
from app.models.delivery import DeliveryStatus
from app.schemas.base import BaseSchema
from app.schemas.validators import validate_required_text, validate_int, validate_required_phone

class DeliveryCreate(BaseSchema):
    vendor: str
    delivery_person_name: str
    block_tower: Optional[str] = None
    mobile_number: str
    delivery_type: str
    description: Optional[str] = None
    flat_no: Optional[int] = None
    flat_id: Optional[int] = None

    _vendor = validator("vendor", allow_reuse=True)(lambda v: validate_required_text(v, "Vendor"))
    _person = validator("delivery_person_name", allow_reuse=True)(lambda v: validate_required_text(v, "Delivery person name"))
    _block = validator("block_tower", allow_reuse=True)(lambda v: validate_required_text(v, "Block / Tower"))
    _mobile = validator("mobile_number", allow_reuse=True)(lambda v: validate_required_phone(v))
    _type = validator("delivery_type", allow_reuse=True)(lambda v: validate_required_text(v, "Delivery Type"))
    _flat_no = validator("flat_no", allow_reuse=True)(lambda v: validate_int(v, "Flat No"))
    _flat = validator("flat_id", allow_reuse=True)(lambda v: validate_int(v, "Flat No"))

    @validator("flat_id", always=True)
    def validate_flat_reference(cls, value, values):
        if values.get("flat_no") is None and value is None:
            raise ValueError("Flat No is required")
        return value

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "vendor": "Amazon",
                "delivery_person_name": "Ravi Kumar",
                "block_tower": "A",
                "mobile_number": "9876543210",
                "delivery_type": "Parcel",
                "description": "Small parcel",
                "flat_no": 12,
            }
        })

class DeliveryUpdateStatus(BaseSchema):
    status: DeliveryStatus
    handed_over_time: Optional[datetime] = None

class DeliveryOut(BaseSchema):
    id: int
    vendor: str
    delivery_person_name: Optional[str]
    block_tower: Optional[str]
    mobile_number: Optional[str]
    delivery_type: Optional[str]
    description: Optional[str]
    flat_no: Optional[int]
    flat_id: Optional[int]
    flat_block: Optional[str] = None
    flat_number: Optional[int] = None
    flat_label: Optional[str] = None
    status: DeliveryStatus
    received_time: datetime
    handed_over_time: Optional[datetime]
    resident_confirmed_at: Optional[datetime]
    entry_allowed_at: Optional[datetime]
