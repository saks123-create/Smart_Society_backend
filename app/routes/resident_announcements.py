from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.notice import NoticeOut
from app.services.resident_announcement_service import list_announcements
from app.utils.deps import get_db, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/resident/announcements", tags=["resident", "announcements"])

@router.get("/", response_model=list[NoticeOut], dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def announcements(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_announcements(db, offset=offset, limit=limit)
