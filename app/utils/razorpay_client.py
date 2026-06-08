import os
import hmac
import hashlib
import logging
from typing import Any, Optional, Tuple

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

RAZORPAY_API_BASE = os.getenv("RAZORPAY_API_BASE", "https://api.razorpay.com/v1")


def _load_keys() -> Tuple[str, str]:
    """Load Razorpay credentials at call time to allow late-bound env config."""
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise HTTPException(
            status_code=503,
            detail="Razorpay is not configured (missing RAZORPAY_KEY_ID/RAZORPAY_KEY_SECRET)",
        )
    return key_id, key_secret


def get_razorpay_key_id() -> str:
    """Expose configured Razorpay key id for client-side initialization."""
    key_id, _ = _load_keys()
    return key_id


def create_order(amount_paise: int, currency: str, receipt: str, notes: Optional[dict] = None) -> dict:
    """Create a Razorpay order and return the payload."""
    key_id, key_secret = _load_keys()
    url = f"{RAZORPAY_API_BASE}/orders"
    payload: dict[str, Any] = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": receipt,
        "payment_capture": 1,
    }
    if notes:
        payload["notes"] = notes

    try:
        response = httpx.post(
            url,
            json=payload,
            auth=(key_id, key_secret),
            timeout=20.0,
        )
    except httpx.RequestError as exc:
        logger.exception("Razorpay order request failed")
        raise HTTPException(status_code=502, detail="Razorpay request failed") from exc

    if response.status_code >= 400:
        logger.error("Razorpay order creation failed: %s", response.text)
        raise HTTPException(status_code=502, detail="Razorpay request failed")

    return response.json()


def verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay signature using HMAC SHA256."""
    _, key_secret = _load_keys()
    payload = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(
        key_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
