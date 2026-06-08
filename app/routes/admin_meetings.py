from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.meeting_summary import MeetingSummaryCreate, MeetingSummaryOut
from app.services.meeting_summary_service import list_meeting_summaries, create_meeting_summary
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/admin/meetings", tags=["admin", "Meetings"])

@router.get("/", response_model=list[MeetingSummaryOut], dependencies=[Depends(require_roles([UserRole.admin]))])
def all_meetings(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_meeting_summaries(db, offset=offset, limit=limit)

@router.post("/", response_model=MeetingSummaryOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def create_meeting(data: MeetingSummaryCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_meeting_summary(
        db,
        data,
        current_user.id,
        actor_user_id=current_user.id,
    )
