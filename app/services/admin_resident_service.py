from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from app.models.resident import Resident
from app.models.flat import Flat
from app.models.user import User, UserRole, UserStatus
from app.utils.normalization import normalize_email, normalize_phone
from app.utils.security import get_password_hash
from app.models.complaint import Complaint
from app.models.payment import Payment
from app.schemas.resident import ResidentCreate, ResidentUpdate
from app.services.auth_service import _send_signup_confirmation_email


def _validate_flat_assignment(db: Session, flat_id: int | None) -> None:
    if flat_id is None:
        return
    flat = db.query(Flat.id).filter(Flat.id == flat_id).first()
    if not flat:
        raise HTTPException(status_code=400, detail="Assigned flat not found")

def list_residents(db: Session, offset: int = 0, limit: Optional[int] = None):
    query = (
        db.query(Resident)
        .join(User, Resident.user_id == User.id)
        .filter(User.role == UserRole.resident, User.status == UserStatus.approved)
        .order_by(Resident.created_at.desc())
    )
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()


def resident_summary(db: Session):
    total_residents = (
        db.query(Resident)
        .join(User, Resident.user_id == User.id)
        .filter(User.role == UserRole.resident, User.status == UserStatus.approved)
        .count()
    )
    pending_approvals = (
        db.query(User)
        .filter(User.role == UserRole.resident, User.status == UserStatus.pending)
        .count()
    )
    assigned_flats = (
        db.query(func.count(func.distinct(Resident.flat_id)))
        .filter(Resident.flat_id.isnot(None))
        .scalar()
        or 0
    )
    move_out_scheduled = db.query(Resident).filter(Resident.move_out_date.isnot(None)).count()
    return {
        "total_residents": total_residents,
        "pending_approvals": pending_approvals,
        "assigned_flats": assigned_flats,
        "move_out_scheduled": move_out_scheduled,
    }

def get_resident(db: Session, resident_id: int):
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    return resident

def create_resident(db: Session, data: ResidentCreate):
    _validate_flat_assignment(db, data.flat_id)
    user = None
    normalized_email = normalize_email(data.email)
    normalized_phone = normalize_phone(data.phone)
    if data.user_id:
        user = db.query(User).filter(User.id == data.user_id).first()
    elif normalized_email:
        user = db.query(User).filter(User.email == normalized_email).first()
    if user:
        if user.role != UserRole.resident:
            raise HTTPException(status_code=400, detail="User role must be resident")
        existing = db.query(Resident).filter(Resident.user_id == user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Resident already exists for this user")
        if user.email and normalized_email and normalized_email != normalize_email(user.email):
            raise HTTPException(status_code=400, detail="Email does not match user record")
        if user.phone and normalized_phone and normalized_phone != normalize_phone(user.phone):
            raise HTTPException(status_code=400, detail="Phone does not match user record")
        if user.status != UserStatus.approved:
            user.status = UserStatus.approved
        email = normalize_email(user.email or normalized_email)
        phone = normalize_phone(user.phone or normalized_phone)
    else:
        if not data.password:
            raise HTTPException(status_code=400, detail="Password is required for a new resident")
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        existing_phone = db.query(User).filter(User.phone == normalized_phone).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already registered")
        user = User(
            email=normalized_email,
            phone=normalized_phone,
            hashed_password=get_password_hash(data.password),
            role=UserRole.resident,
            status=UserStatus.approved,
            is_active=True,
        )
        db.add(user)
        db.flush()
        email = normalized_email
        phone = normalized_phone
    resident = Resident(**data.dict(exclude={"password"}))
    resident.user_id = user.id
    resident.phone = phone
    resident.email = email
    db.add(resident)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Resident could not be created with the provided details")
    db.refresh(resident)
    if user.email and not user.email_verified:
        flat = db.query(Flat).filter(Flat.id == resident.flat_id).first() if resident.flat_id else None
        _send_signup_confirmation_email(
            user.id,
            resident.email,
            resident.name,
            flat.block if flat else "Unassigned",
            flat.flat_number if flat else None,
        )
    return resident

def update_resident(db: Session, resident_id: int, data: ResidentUpdate):
    resident = get_resident(db, resident_id)
    user = db.query(User).filter(User.id == resident.user_id).first()
    if data.move_out_date and (data.move_in_date or resident.move_in_date):
        move_in = data.move_in_date or resident.move_in_date
        if move_in and data.move_out_date <= move_in:
            raise HTTPException(status_code=400, detail="move_out_date must be after move_in_date")
    updates = data.dict(exclude_unset=True)

    if "flat_id" in updates:
        _validate_flat_assignment(db, updates["flat_id"])

    if "email" in updates:
        normalized_email = normalize_email(updates["email"])
        if not normalized_email:
            raise HTTPException(status_code=400, detail="Email is required")
        existing_user = (
            db.query(User)
            .filter(User.email == normalized_email, User.id != resident.user_id)
            .first()
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        resident.email = normalized_email
        if user:
            user.email = normalized_email
        updates.pop("email", None)

    if "phone" in updates:
        normalized_phone = normalize_phone(updates["phone"])
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Phone is required")
        existing_phone = (
            db.query(User)
            .filter(User.phone == normalized_phone, User.id != resident.user_id)
            .first()
        )
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already registered")
        resident.phone = normalized_phone
        if user:
            user.phone = normalized_phone
        updates.pop("phone", None)

    for key, value in updates.items():
        setattr(resident, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Resident could not be updated with the provided details")
    db.refresh(resident)
    return resident

def delete_resident(db: Session, resident_id: int):
    resident = get_resident(db, resident_id)
    has_complaints = (
        db.query(Complaint.id)
        .filter(Complaint.resident_id == resident_id)
        .first()
        is not None
    )
    if has_complaints:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete resident with existing complaints",
        )
    has_payments = (
        db.query(Payment.id)
        .filter(Payment.resident_id == resident_id)
        .first()
        is not None
    )
    if has_payments:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete resident with existing payments",
        )
    user = db.query(User).filter(User.id == resident.user_id).first()
    db.delete(resident)
    if user:
        db.delete(user)
    db.commit()
    return {"message": "Resident deleted"}
