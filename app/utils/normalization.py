from typing import Optional


def normalize_email(email: str) -> str:
    # Keep email comparisons consistent and avoid hidden whitespace/case issues.
    return email.strip().lower()


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    if phone is None:
        return None
    cleaned = phone.strip()
    return cleaned or None
