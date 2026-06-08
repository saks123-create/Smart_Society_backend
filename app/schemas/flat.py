from pydantic import ConfigDict, validator
from typing import Optional
from datetime import datetime
from app.schemas.base import BaseSchema
from app.schemas.validators import (
    validate_required_text,
    validate_int,
    validate_amount,
    validate_non_negative_int,
)
from app.models.flat import FlatStatus, FlatType

class FlatBase(BaseSchema):
    block: str
    floor_number: int
    flat_number: int
    status: FlatStatus
    type: FlatType
    maintenance_due: float

    _block = validator("block", allow_reuse=True)(lambda v: validate_required_text(v, "Block"))
    _floor = validator("floor_number", allow_reuse=True)(lambda v: validate_non_negative_int(v, "Floor number"))
    _flat_number = validator("flat_number", allow_reuse=True)(lambda v: validate_int(v, "Flat number"))
    _maintenance = validator("maintenance_due", allow_reuse=True)(lambda v: validate_amount(v))

class FlatCreate(FlatBase):
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "block": "A",
                "floor_number": 5,
                "flat_number": 502,
                "status": "vacant",
                "type": "2BHK",
                "maintenance_due": 0,
            }
        })

class FlatUpdate(BaseSchema):
    block: Optional[str] = None
    floor_number: Optional[int] = None
    flat_number: Optional[int] = None
    status: Optional[FlatStatus] = None
    type: Optional[FlatType] = None
    maintenance_due: Optional[float] = None

    _block = validator("block", allow_reuse=True)(lambda v: validate_required_text(v, "Block"))
    _floor = validator("floor_number", allow_reuse=True)(lambda v: validate_non_negative_int(v, "Floor number"))
    _flat_number = validator("flat_number", allow_reuse=True)(lambda v: validate_int(v, "Flat number"))
    _maintenance = validator("maintenance_due", allow_reuse=True)(lambda v: validate_amount(v))

class FlatOut(FlatBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
