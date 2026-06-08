import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from urllib.parse import urlparse
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    Token,
    RegisterResponse,
    UserOut,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import (
    register_user,
    authenticate_user,
    request_password_reset,
    reset_password_with_token,
    verify_email_with_token,
)
from app.utils.deps import get_db, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

@router.post("/signup", response_model=RegisterResponse)
def signup(data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    user = register_user(
        db,
        data,
        frontend_base_url=_resolve_frontend_base(request),
    )
    return {"user": user, "message": "Registration successful. Please verify your email."}


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    verify_email_with_token(db, token)
    return {"message": "Email verified successfully"}

@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    token, _user, expires_in = authenticate_user(
        db,
        data.email,
        data.password,
        remember_me=data.remember_me,
    )
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in}

@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user

def _resolve_frontend_base(request: Request) -> str:
    configured = os.getenv("FRONTEND_BASE_URL", "").strip()
    detected_origin = ""
    for header_name in ("origin", "referer"):
        raw_value = (request.headers.get(header_name) or "").strip()
        if not raw_value:
            continue
        parsed = urlparse(raw_value)
        if parsed.scheme and parsed.netloc:
            detected_origin = f"{parsed.scheme}://{parsed.netloc}"
            break

    if configured:
        parsed_config = urlparse(configured)
        config_host = (parsed_config.hostname or "").lower()
        if detected_origin and config_host in {"localhost", "127.0.0.1"}:
            detected_parsed = urlparse(detected_origin)
            detected_host = (detected_parsed.hostname or "").lower()
            if detected_host not in {"localhost", "127.0.0.1"}:
                return detected_origin
        return configured

    if detected_origin:
        return detected_origin

    app_env = os.getenv("APP_ENV", os.getenv("ENV", "development")).strip().lower()
    if app_env in {"development", "dev", "local"}:
        return "http://localhost:3000"
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Frontend base URL is not configured.",
    )


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    reset_meta = request_password_reset(
        db,
        data.email,
        frontend_base_url=_resolve_frontend_base(request),
    )
    response = {"message": "If the email exists, a reset link has been sent."}
    if reset_meta and not reset_meta.get("email_sent", False):
        logger.warning(
            "Password reset requested for %s but the reset email could not be delivered.",
            data.email,
        )
    return response

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_password_with_token(db, data.token, data.new_password)
    return {"message": "Password reset successful"}
