from pydantic import validator
from typing import Optional, List
from datetime import datetime
from app.schemas.base import BaseSchema
from app.schemas.validators import validate_required_text

class MeetingSummaryCreate(BaseSchema):
    title: str
    transcript: str

    _title = validator("title", allow_reuse=True)(lambda v: validate_required_text(v, "Title"))
    _transcript = validator("transcript", allow_reuse=True)(lambda v: validate_required_text(v, "Transcript"))

class MeetingSummaryOut(BaseSchema):
    id: int
    title: str
    transcript: str
    summary: str
    action_items: Optional[List[str]] = None
    created_by_user_id: Optional[int]
    created_at: Optional[datetime] = None

class MeetingSummaryPublic(BaseSchema):
    id: int
    title: str
    summary: str
    action_items: Optional[List[str]] = None
    created_by_user_id: Optional[int]
    created_at: Optional[datetime] = None
