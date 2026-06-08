from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models.resident import Resident
from app.models.visitor import Visitor


def list_pending_requests(db: Session, user_id: int, offset: int = 0, limit: Optional[int] = None):
    profile = db.query(Resident).filter(Resident.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    if not profile.flat_id:
        return []
    query = (
        db.query(Visitor)
        .filter(
            Visitor.flat_id == profile.flat_id,
            Visitor.status == "pending",
            Visitor.qr_token.is_(None),
        )
        .order_by(Visitor.pre_registered_at.desc())
    )
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()


def approve_request(db: Session, user_id: int, visitor_id: int):
    profile = db.query(Resident).filter(Resident.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    if not profile.flat_id:
        raise HTTPException(status_code=400, detail="Flat not assigned")

    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor or visitor.flat_id != profile.flat_id:
        raise HTTPException(status_code=404, detail="Visitor not found")
    if visitor.status != "pending":
        raise HTTPException(status_code=400, detail="Visitor already processed")

    visitor.status = "approved"
    db.commit()
    db.refresh(visitor)
    return visitor


def reject_request(db: Session, user_id: int, visitor_id: int):
    profile = db.query(Resident).filter(Resident.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    if not profile.flat_id:
        raise HTTPException(status_code=400, detail="Flat not assigned")

    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor or visitor.flat_id != profile.flat_id:
        raise HTTPException(status_code=404, detail="Visitor not found")
    if visitor.status != "pending":
        raise HTTPException(status_code=400, detail="Visitor already processed")

    visitor.status = "rejected"
    db.commit()
    db.refresh(visitor)
    return visitor
