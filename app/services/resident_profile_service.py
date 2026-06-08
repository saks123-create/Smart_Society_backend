from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.resident import Resident
from app.models.user import User
from app.schemas.profile import ProfileUpdate
from app.utils.normalization import normalize_phone

def get_profile(db: Session, resident_id: int):
    profile = db.query(Resident).filter(Resident.id == resident_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    return profile

def get_profile_by_user_id(db: Session, user_id: int):
    profile = db.query(Resident).filter(Resident.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    return profile

def update_profile(db: Session, resident_id: int, data: ProfileUpdate):
    profile = get_profile(db, resident_id)
    allowed_updates = data.dict(exclude_unset=True, include={"name", "phone"})
    user = db.query(User).filter(User.id == profile.user_id).first()
    if "phone" in allowed_updates:
        normalized_phone = normalize_phone(allowed_updates["phone"])
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Phone is required")
        existing_phone = (
            db.query(User)
            .filter(func.trim(User.phone) == normalized_phone, User.id != profile.user_id)
            .first()
        )
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already registered")
        allowed_updates["phone"] = normalized_phone
    for key, value in allowed_updates.items():
        setattr(profile, key, value)
        if key == "phone" and user:
            user.phone = value
    db.commit()
    db.refresh(profile)
    return profile
