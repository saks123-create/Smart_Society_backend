from pydantic import Field, ConfigDict, validator
from typing import Optional
from datetime import datetime
from app.models.complaint import ComplaintStatus
import enum
from app.schemas.base import BaseSchema
from app.schemas.validators import validate_required_text


class ComplaintPriority(str, enum.Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"

class ComplaintCreate(BaseSchema):
    title: str
    description: str
    priority: Optional[ComplaintPriority] = None
    category: Optional[str] = None

    _title = validator("title", allow_reuse=True)(lambda v: validate_required_text(v, "Title"))
    _description = validator("description", allow_reuse=True)(lambda v: validate_required_text(v, "Description"))

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "title": "Water leakage",
                "description": "Leak in bathroom pipe since morning",
                "priority": "HIGH",
                "category": "Plumbing",
            }
        })

class ComplaintUpdateStatus(BaseSchema):
    status: ComplaintStatus


class ComplaintUpdate(BaseSchema):
    status: Optional[ComplaintStatus] = None
    priority: Optional[ComplaintPriority] = None

class ComplaintOut(BaseSchema):
    id: int
    resident_id: int
    title: str
    description: str
    category: Optional[str] = None
    priority: Optional[str] = None
    summary: Optional[str] = None
    image_path: Optional[str] = None
    status: ComplaintStatus
    rating: Optional[int] = None
    rating_feedback: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ComplaintSummary(BaseSchema):
    total: int
    open: int
    in_progress: int
    resolved: int
    average_rating: float


class ComplaintRatingRequest(BaseSchema):
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None
