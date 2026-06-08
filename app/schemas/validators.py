import re
from typing import Optional

PHONE_RE = re.compile(r"^\d{10}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
STRONG_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$"
)


def ensure_string(value: Optional[str], label: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    return value.strip()


def validate_name(value: Optional[str], label: str = "Name") -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} is required")
    if cleaned.isdigit():
        raise ValueError(f"{label} cannot be numbers only")
    return cleaned


def validate_required_text(value: Optional[str], label: str) -> Optional[str]:
    if value is None:
        raise ValueError(f"{label} is required")
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} is required")
    return cleaned


def validate_optional_text(value: Optional[str], label: str) -> Optional[str]:
    if value is None:
        return None
    return validate_required_text(value, label)


def validate_phone(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, int):
        value = str(value)
    if not isinstance(value, str):
        raise ValueError("Phone number must be a string")
    cleaned = value.strip()
    if not PHONE_RE.fullmatch(cleaned):
        raise ValueError("Phone number must be 10 digits")
    return cleaned


def validate_required_phone(value: Optional[str]) -> str:
    if value is None:
        raise ValueError("Phone number is required")
    cleaned = validate_phone(value)
    if cleaned is None:
        raise ValueError("Phone number is required")
    return cleaned


def validate_email(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Email must be a string")
    cleaned = value.strip().lower()
    if not EMAIL_RE.fullmatch(cleaned):
        raise ValueError("Email is not valid")
    return cleaned


def validate_int(value: Optional[int], label: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value <= 0:
        raise ValueError(f"{label} must be positive")
    return value


def validate_non_negative_int(value: Optional[int], label: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < 0:
        raise ValueError(f"{label} must be 0 or greater")
    return value


def validate_amount(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Amount must be numeric")
    if value < 0:
        raise ValueError("Amount cannot be negative")
    return float(value)


def validate_strong_password(value: Optional[str], label: str = "Password") -> str:
    cleaned = validate_required_text(value, label)
    if cleaned is None:
        raise ValueError(f"{label} is required")
    if not STRONG_PASSWORD_RE.fullmatch(cleaned):
        raise ValueError(
            f"{label} must be at least 8 characters and include uppercase, lowercase, number, and special character"
        )
    return cleaned
