from sqlalchemy.orm import Session
from typing import Optional
from app.models.notice import Notice

def list_announcements(db: Session, offset: int = 0, limit: Optional[int] = None):
    query = db.query(Notice).order_by(Notice.created_at.desc())
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()
