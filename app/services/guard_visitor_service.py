from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.visitor import Visitor
from app.models.flat import Flat
from app.schemas.visitor import VisitorCreate
from app.services.notification_service import notify_guard_visitor_request


def _resolve_flat(db: Session, flat_no: int | None, flat_id: int | None, block_tower: str | None = None) -> Flat:
    if flat_no is not None:
        query = db.query(Flat).filter(Flat.flat_number == flat_no)
        cleaned_block = (block_tower or "").strip()
        if cleaned_block:
            query = query.filter(func.lower(Flat.block) == cleaned_block.lower())
        flats = query.all()
        if not flats:
            raise HTTPException(status_code=400, detail="Flat No must be valid.")
        if len(flats) > 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple flats found for this Flat No. Please specify the correct Block / Tower.",
            )
        return flats[0]
    if flat_id is not None:
        flat = db.query(Flat).filter(Flat.id == flat_id).first()
        if not flat:
            raise HTTPException(status_code=400, detail="Flat No must be valid.")
        return flat
    raise HTTPException(status_code=400, detail="Flat No is required.")


def list_visitors(db: Session, offset: int = 0, limit: Optional[int] = None):
    """List all visitors ordered by entry time."""
    query = db.query(Visitor).order_by(Visitor.pre_registered_at.desc())
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()

def create_visitor(db: Session, data: VisitorCreate, user_id: Optional[int] = None):
    """Create a visitor record with immediate entry time (walk-in)."""
    flat = _resolve_flat(db, data.flat_no, data.flat_id, data.block_tower)

    payload = data.dict(exclude={"flat_no", "block_tower"})
    payload["flat_id"] = flat.id
    visitor = Visitor(
        **payload,
        created_by_user_id=user_id,
        entry_time=None,
        pre_registered_at=datetime.now(timezone.utc),
        status="pending",
    )
    db.add(visitor)
    db.commit()
    db.refresh(visitor)
    notify_guard_visitor_request(db, visitor)
    return visitor

def allow_entry(db: Session, visitor_id: int):
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    if visitor.status != "approved":
        raise HTTPException(status_code=400, detail="Visitor not approved yet")
    visitor.entry_time = datetime.now(timezone.utc)
    visitor.status = "entered"
    db.commit()
    db.refresh(visitor)
    return visitor
