from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.settings import Settings
from app.schemas.settings import SettingsUpdate
from app.models.user import User, UserRole
from app.services.admin_audit_service import log_admin_action
from app.utils.normalization import normalize_email, normalize_phone
from app.utils.security import verify_password, get_password_hash

DEFAULT_SETTINGS = {
    "society_name": "Green Valley Apartments",
    "society_address": "Sector 21, Noida",
    "society_phone": "9876543210",
    "society_email": "society@gmail.com",
    "admin_name": "Admin",
    "admin_email": "admin@gmail.com",
    "admin_phone": "9999999999",
    "notify_visitors": True,
    "notify_complaints": True,
    "notify_notices": True,
}

def _get_or_create_settings(db: Session) -> Settings:
    settings = db.query(Settings).order_by(Settings.id.asc()).first()
    if settings:
        return settings
    settings = Settings(id=1, **DEFAULT_SETTINGS)
    db.add(settings)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        settings = db.query(Settings).order_by(Settings.id.asc()).first()
        if settings:
            return settings
        raise
    db.refresh(settings)
    return settings

def get_settings(db: Session) -> Settings:
    return _get_or_create_settings(db)

def update_settings(
    db: Session,
    data: SettingsUpdate,
    *,
    actor_user: User | None = None,
) -> Settings:
    settings = _get_or_create_settings(db)
    updates = data.dict(exclude_unset=True)
    for key, value in updates.items():
        setattr(settings, key, value)

    if actor_user and actor_user.role == UserRole.admin:
        audit_details: dict[str, object] = {"updated_fields": sorted(updates.keys())}
        if "admin_email" in updates:
            admin_email = normalize_email(updates["admin_email"])
            existing = (
                db.query(User)
                .filter(func.lower(func.trim(User.email)) == admin_email, User.id != actor_user.id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
            actor_user.email = admin_email
            audit_details["admin_email"] = admin_email
        if "admin_phone" in updates:
            admin_phone = normalize_phone(updates["admin_phone"])
            existing_phone = (
                db.query(User)
                .filter(func.trim(User.phone) == admin_phone, User.id != actor_user.id)
                .first()
            )
            if existing_phone:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone already registered")
            actor_user.phone = admin_phone
            audit_details["admin_phone"] = admin_phone
        if "admin_name" in updates:
            audit_details["admin_name"] = updates["admin_name"]
        if updates:
            log_admin_action(
                db,
                actor_user_id=actor_user.id,
                action="settings.updated",
                target_type="settings",
                target_id=settings.id,
                details=audit_details,
            )

    db.commit()
    db.refresh(settings)
    return settings

def change_admin_password(db: Session, user_id: int, current_password: str, new_password: str) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if current_password == new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different from current password")
    user.hashed_password = get_password_hash(new_password)
    log_admin_action(
        db,
        actor_user_id=user.id,
        action="admin.password_changed",
        target_type="user",
        target_id=user.id,
        details={"role": user.role.value},
    )
    db.commit()
