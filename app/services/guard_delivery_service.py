from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.delivery import Delivery
from app.models.flat import Flat
from app.schemas.delivery import DeliveryCreate, DeliveryUpdateStatus
from app.services.notification_service import notify_delivery_event


def _resolve_flat(db: Session, flat_no: int | None, flat_id: int | None, block_tower: str | None = None) -> Flat:
    if flat_no is not None:
        query = db.query(Flat).filter(Flat.flat_number == flat_no)
        cleaned_block = (block_tower or "").strip()
        if cleaned_block:
            query = query.filter(Flat.block.ilike(cleaned_block))
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


def list_deliveries(db: Session, offset: int = 0, limit: Optional[int] = None):
    query = db.query(Delivery).order_by(Delivery.received_time.desc())
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()

def create_delivery(db: Session, data: DeliveryCreate, user_id: Optional[int] = None):
    flat = _resolve_flat(db, data.flat_no, data.flat_id, data.block_tower)

    payload = data.dict(exclude={"flat_no", "block_tower"})
    payload["flat_id"] = flat.id
    payload["block_tower"] = flat.block
    delivery = Delivery(**payload, created_by_user_id=user_id)
    db.add(delivery)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Flat No must be valid.")
    db.refresh(delivery)
    notify_delivery_event(db, delivery)
    return delivery

def update_delivery_status(db: Session, delivery_id: int, data: DeliveryUpdateStatus):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if data.status == "handed_over" and not delivery.resident_confirmed_at:
        raise HTTPException(status_code=400, detail="Resident confirmation required before marking delivered.")
    if data.status == "handed_over" and not delivery.entry_allowed_at:
        raise HTTPException(status_code=400, detail="Guard must allow entry before marking delivered.")
    delivery.status = data.status
    if data.status == "handed_over":
        if data.handed_over_time is None:
            delivery.handed_over_time = datetime.now(timezone.utc)
        elif data.handed_over_time.tzinfo is None:
            delivery.handed_over_time = data.handed_over_time.replace(tzinfo=timezone.utc)
        else:
            delivery.handed_over_time = data.handed_over_time
    else:
        delivery.handed_over_time = None
    db.commit()
    db.refresh(delivery)
    return delivery


def allow_delivery_entry(db: Session, delivery_id: int):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if not delivery.resident_confirmed_at:
        raise HTTPException(status_code=400, detail="Resident confirmation required before allowing entry.")
    if delivery.entry_allowed_at is None:
        delivery.entry_allowed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(delivery)
    return delivery
