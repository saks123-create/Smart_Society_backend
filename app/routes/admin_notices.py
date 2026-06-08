from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeOut
from app.schemas.ai import NoticeDraftRequest, NoticeDraftResponse
from app.services.admin_notice_service import list_notices, create_notice, update_notice, delete_notice
from app.services.ai_service import draft_notice
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/admin/notices", tags=["admin", "Notices"])

@router.get("/", response_model=list[NoticeOut], dependencies=[Depends(require_roles([UserRole.admin]))])
def all_notices(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_notices(db, offset=offset, limit=limit)

@router.post("/", response_model=NoticeOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def add_notice(data: NoticeCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_notice(db, data, current_user.id, actor_user_id=current_user.id)

@router.post("/draft", response_model=NoticeDraftResponse, dependencies=[Depends(require_roles([UserRole.admin]))])
def draft(data: NoticeDraftRequest):
    result = draft_notice(data.prompt, data.language)
    return {"title": result.get("title", ""), "body": result.get("body", "")}

@router.put("/{notice_id}", response_model=NoticeOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def edit_notice(notice_id: int, data: NoticeUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return update_notice(db, notice_id, data, actor_user_id=current_user.id)

@router.delete("/{notice_id}", dependencies=[Depends(require_roles([UserRole.admin]))])
def remove_notice(notice_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return delete_notice(db, notice_id, actor_user_id=current_user.id)
