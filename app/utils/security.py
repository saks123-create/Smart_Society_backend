import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from jose import jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is required.")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REMEMBER_ME_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("REMEMBER_ME_ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
)
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "15"))
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES", "1440")
)

# Prefer bcrypt_sha256 to safely support passwords > 72 bytes while
# still verifying existing bcrypt hashes.
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

def _normalize_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        digest = hashlib.sha256(pw_bytes).hexdigest()
        return f"sha256:{digest}"
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(_normalize_password(plain_password), hashed_password)
    except (ValueError, UnknownHashError):
        # Malformed/unknown hashes should not crash auth flow; treat as invalid.
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(_normalize_password(password))

def get_access_token_expires_delta(remember_me: bool = False) -> timedelta:
    minutes = (
        REMEMBER_ME_ACCESS_TOKEN_EXPIRE_MINUTES
        if remember_me
        else ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return timedelta(minutes=minutes)


def create_access_token(
    subject: dict,
    expires_delta: Optional[timedelta] = None,
    remember_me: bool = False,
) -> str:
    to_encode = subject.copy()
    expire = datetime.utcnow() + (expires_delta or get_access_token_expires_delta(remember_me))
    # Tag access tokens so we can distinguish them from other JWTs.
    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_password_reset_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES))
    payload = {"user_id": user_id, "exp": expire, "token_type": "password_reset"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_email_verification_token(
    user_id: int,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expire,
        "token_type": "email_verification",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_email_verification_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("token_type") != "email_verification":
        raise ValueError("Invalid email verification token type")
    return payload

def decode_password_reset_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("token_type") != "password_reset":
        raise ValueError("Invalid reset token type")
    return payload
