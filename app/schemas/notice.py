from pydantic import ConfigDict, validator
from typing import Optional
from datetime import datetime
from app.schemas.base import BaseSchema
from app.schemas.validators import validate_required_text, validate_optional_text

class NoticeCreate(BaseSchema):
    title: str
    content: str
    expires_at: Optional[datetime] = None

    _title = validator("title", allow_reuse=True)(lambda v: validate_optional_text(v, "Title"))
    _content = validator("content", allow_reuse=True)(lambda v: validate_optional_text(v, "Content"))

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "title": "Water supply shutdown",
                "content": "Water supply will be off on Saturday 10 AM - 2 PM.",
                "expires_at": "2026-04-01T00:00:00Z",
            }
        })

class NoticeUpdate(BaseSchema):
    title: Optional[str] = None
    content: Optional[str] = None
    expires_at: Optional[datetime] = None

    _title = validator("title", allow_reuse=True)(lambda v: validate_required_text(v, "Title"))
    _content = validator("content", allow_reuse=True)(lambda v: validate_required_text(v, "Content"))

class NoticeOut(BaseSchema):
    id: int
    title: str
    content: str
    created_at: datetime
    expires_at: Optional[datetime]
    created_by_user_id: Optional[int]
