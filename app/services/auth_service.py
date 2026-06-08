from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.user import User, UserRole, UserStatus
from app.models.resident import Resident, ResidentRole
from app.models.flat import Flat
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_access_token_expires_delta,
    create_password_reset_token,
    decode_password_reset_token,
    create_email_verification_token,
    decode_email_verification_token,
)
from app.schemas.auth import RegisterRequest
from app.utils.normalization import normalize_email, normalize_phone
from app.services.notification_service import send_email
import os
from typing import Optional
from datetime import date
import logging


logger = logging.getLogger(__name__)

def _send_signup_confirmation_email(
    user_id: int,
    email: str,
    full_name: str,
    block: str,
    flat_number: int | None,
    frontend_base_url: Optional[str] = None,
) -> None:
    subject = "Verify your SmartSociety email"
    resident_name = full_name.strip() if full_name else "Resident"
    flat_text = f"Flat: {block}-{flat_number}" if flat_number is not None else f"Block: {block}"
    frontend_base = frontend_base_url or os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    token = create_email_verification_token(user_id, email)
    verify_link = f"{frontend_base.rstrip('/')}/verify-email?token={token}"
    body = (
        f"Hello {resident_name},\n\n"
        "Your SmartSociety signup request has been received successfully.\n"
        "Please verify your email by opening the link below:\n"
        f"{verify_link}\n\n"
        "After email verification, your account will still need admin approval before login works.\n\n"
        f"{flat_text}\n\n"
        "If you did not create this request, please ignore this email.\n\n"
        "Regards,\n"
        "SmartSociety"
    )
    email_sent = send_email(email, subject, body)
    if not email_sent:
        logger.warning("Signup confirmation email could not be sent to %s", email)

def register_user(db: Session, data: RegisterRequest, frontend_base_url: Optional[str] = None):
    email = normalize_email(data.email)
    phone = normalize_phone(data.phone)
    normalized_block = data.block.strip().upper()
    existing = db.query(User).filter(func.lower(func.trim(User.email)) == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    existing_phone = db.query(User).filter(User.phone == phone).first()
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone already registered")

    flat = (
        db.query(Flat)
        .filter(
            func.upper(func.trim(Flat.block)) == normalized_block,
            Flat.flat_number == data.flat_number,
        )
        .first()
    )
    if not flat:
        raise HTTPException(status_code=400, detail="Flat not found for the selected block")
    resolved_flat_id = flat.id

    user = User(
        email=email,
        email_verified=False,
        phone=phone,
        hashed_password=get_password_hash(data.password),
        role=UserRole.resident,
        status=UserStatus.pending,
        is_active=True,
    )
    db.add(user)
    db.flush()

    resident = Resident(
        user_id=user.id,
        name=data.full_name,
        phone=phone,
        email=email,
        flat_id=resolved_flat_id,
        role=ResidentRole.owner,
        move_in_date=date.today(),
    )
    db.add(resident)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Registration failed due to invalid or duplicate data")
    db.refresh(user)
    _send_signup_confirmation_email(
        user.id,
        email,
        data.full_name,
        normalized_block,
        data.flat_number,
        frontend_base_url=frontend_base_url,
    )
    return user

def authenticate_user(db: Session, email: str, password: str, remember_me: bool = False):
    normalized_email = normalize_email(email)
    user = db.query(User).filter(func.lower(func.trim(User.email)) == normalized_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    if user.role == UserRole.resident and not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    if user.role == UserRole.resident and user.status != UserStatus.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resident not approved")
    expires_delta = get_access_token_expires_delta(remember_me)
    token = create_access_token(
        {"user_id": user.id, "role": user.role},
        expires_delta=expires_delta,
        remember_me=remember_me,
    )
    return token, user, int(expires_delta.total_seconds())

def request_password_reset(
    db: Session,
    email: str,
    frontend_base_url: Optional[str] = None,
) -> Optional[dict]:
    normalized_email = normalize_email(email)
    user = db.query(User).filter(func.lower(func.trim(User.email)) == normalized_email).first()
    if not user or not user.is_active:
        return None

    token = create_password_reset_token(user.id)
    frontend_base = frontend_base_url or os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    reset_link = f"{frontend_base.rstrip('/')}/reset?token={token}"
    subject = "Reset your SmartSociety password"
    body = f"Use this link to reset your password: {reset_link}"
    email_sent = send_email(user.email, subject, body)
    return {
        "token": token,
        "reset_link": reset_link,
        "email_sent": email_sent,
    }


def verify_email_with_token(db: Session, token: str) -> User:
    try:
        payload = decode_email_verification_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")

    user_id = payload.get("user_id")
    email = normalize_email(payload.get("email"))
    if not user_id or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")
    if normalize_email(user.email) != email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")

    if not user.email_verified:
        user.email_verified = True
        db.commit()
        db.refresh(user)
    return user

def reset_password_with_token(db: Session, token: str, new_password: str) -> None:
    try:
        payload = decode_password_reset_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")

    user.hashed_password = get_password_hash(new_password)
    db.commit()
