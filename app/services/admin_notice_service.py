from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.notice import Notice
from app.schemas.notice import NoticeCreate, NoticeUpdate
from app.services.admin_audit_service import log_admin_action
from app.services.notification_service import notify_notice_created

def list_notices(db: Session, offset: int = 0, limit: Optional[int] = None):
    query = db.query(Notice).order_by(Notice.created_at.desc())
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()

def create_notice(
    db: Session,
    data: NoticeCreate,
    user_id: Optional[int] = None,
    actor_user_id: Optional[int] = None,
):
    notice = Notice(**data.dict(), created_by_user_id=user_id)
    db.add(notice)
    db.flush()
    if actor_user_id is not None:
        log_admin_action(
            db,
            actor_user_id=actor_user_id,
            action="notice.created",
            target_type="notice",
            target_id=notice.id,
            details={"title": notice.title},
        )
    db.commit()
    db.refresh(notice)
    notify_notice_created(db, notice)
    return notice

def update_notice(db: Session, notice_id: int, data: NoticeUpdate, actor_user_id: Optional[int] = None):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    updates = data.dict(exclude_unset=True)
    for key, value in updates.items():
        setattr(notice, key, value)
    if actor_user_id is not None and updates:
        log_admin_action(
            db,
            actor_user_id=actor_user_id,
            action="notice.updated",
            target_type="notice",
            target_id=notice.id,
            details={"updated_fields": sorted(updates.keys())},
        )
    db.commit()
    db.refresh(notice)
    return notice

def delete_notice(db: Session, notice_id: int, actor_user_id: Optional[int] = None):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    if actor_user_id is not None:
        log_admin_action(
            db,
            actor_user_id=actor_user_id,
            action="notice.deleted",
            target_type="notice",
            target_id=notice.id,
            details={"title": notice.title},
        )
    db.delete(notice)
    db.commit()
    return {"message": "Notice deleted"}
