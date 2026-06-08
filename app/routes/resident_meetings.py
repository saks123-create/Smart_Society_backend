from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.meeting_summary import MeetingSummaryPublic
from app.services.meeting_summary_service import list_meeting_summaries
from app.utils.deps import get_db, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/resident/meetings", tags=["resident", "meetings"])

@router.get("/", response_model=list[MeetingSummaryPublic], dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def meetings(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    summaries = list_meeting_summaries(db, offset=offset, limit=limit)
    return [
        {
            "id": item["id"],
            "title": item["title"],
            "summary": item["summary"],
            "action_items": item["action_items"],
            "created_by_user_id": item["created_by_user_id"],
            "created_at": item["created_at"],
        }
        for item in summaries
    ]
