from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from app.models.flat import Flat
from app.schemas.flat import FlatCreate, FlatUpdate
from app.services.admin_audit_service import log_admin_action


def _normalize_block(value: str) -> str:
    return value.strip().upper()

def list_flats(db: Session, offset: int = 0, limit: Optional[int] = None):
    query = db.query(Flat).order_by(Flat.id.desc())
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()

def get_flat(db: Session, flat_id: int):
    flat = db.query(Flat).filter(Flat.id == flat_id).first()
    if not flat:
        raise HTTPException(status_code=404, detail="Flat not found")
    return flat

def create_flat(db: Session, data: FlatCreate, actor_user_id: int | None = None):
    normalized_block = _normalize_block(data.block)
    existing = db.query(Flat).filter(
        func.upper(func.trim(Flat.block)) == normalized_block,
        Flat.flat_number == data.flat_number,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Flat already exists")

    flat = Flat(
        block=normalized_block,
        floor_number=data.floor_number,
        flat_number=data.flat_number,
        status=data.status,
        type=data.type,
        maintenance_due=data.maintenance_due,
    )
    db.add(flat)
    db.flush()
    if actor_user_id is not None:
        log_admin_action(
            db,
            actor_user_id=actor_user_id,
            action="flat.created",
            target_type="flat",
            target_id=flat.id,
            details={
                "block": flat.block,
                "flat_number": flat.flat_number,
                "floor_number": flat.floor_number,
            },
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Flat already exists")
    db.refresh(flat)
    return flat

def update_flat(db: Session, flat_id: int, data: FlatUpdate, actor_user_id: int | None = None):
    flat = get_flat(db, flat_id)
    new_block = _normalize_block(data.block) if data.block is not None else flat.block
    new_flat_number = data.flat_number if data.flat_number is not None else flat.flat_number
    conflict = db.query(Flat).filter(
        Flat.id != flat_id,
        func.upper(func.trim(Flat.block)) == new_block,
        Flat.flat_number == new_flat_number,
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Flat already exists")
    updates = data.dict(exclude_unset=True)
    if "block" in updates and updates["block"] is not None:
        updates["block"] = _normalize_block(updates["block"])
    for key, value in updates.items():
        setattr(flat, key, value)
    if actor_user_id is not None and updates:
        log_admin_action(
            db,
            actor_user_id=actor_user_id,
            action="flat.updated",
            target_type="flat",
            target_id=flat.id,
            details={"updated_fields": sorted(updates.keys())},
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Flat already exists")
    db.refresh(flat)
    return flat

def delete_flat(db: Session, flat_id: int, actor_user_id: int | None = None):
    flat = get_flat(db, flat_id)
    if actor_user_id is not None:
        log_admin_action(
            db,
            actor_user_id=actor_user_id,
            action="flat.deleted",
            target_type="flat",
            target_id=flat.id,
            details={"block": flat.block, "flat_number": flat.flat_number},
        )
    db.delete(flat)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete flat while it is linked to existing records",
        )
    return {"message": "Flat deleted"}
