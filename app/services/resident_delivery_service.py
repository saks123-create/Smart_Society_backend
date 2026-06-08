from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models.delivery import Delivery
from app.models.resident import Resident


def list_resident_deliveries(db: Session, user_id: int, offset: int = 0, limit: Optional[int] = None):
    profile = db.query(Resident).filter(Resident.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    if not profile.flat_id:
        return []
    query = (
        db.query(Delivery)
        .filter(Delivery.flat_id == profile.flat_id)
        .order_by(Delivery.received_time.desc())
    )
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()


def confirm_delivery(db: Session, user_id: int, delivery_id: int):
    profile = db.query(Resident).filter(Resident.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    if not profile.flat_id:
        raise HTTPException(status_code=400, detail="Flat not assigned")

    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery or delivery.flat_id != profile.flat_id:
        raise HTTPException(status_code=404, detail="Delivery not found")

    if delivery.resident_confirmed_at is None:
        delivery.resident_confirmed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(delivery)
    return delivery
