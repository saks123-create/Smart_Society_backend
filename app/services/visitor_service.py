import base64
import io
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.visitor import Visitor
from app.models.flat import Flat
from app.services.notification_service import notify_visitor_event

logger = logging.getLogger(__name__)


def _build_qr_payload(visitor_id: int, token: str) -> str:
    """Return the payload string embedded in the QR code."""
    return f"visitor:{visitor_id}:{token}"


def _generate_qr_base64(payload: str) -> Optional[str]:
    """Generate a base64 PNG QR code. Returns None if QR lib is missing."""
    try:
        import qrcode
    except Exception:
        logger.warning("qrcode dependency not installed; returning QR payload only")
        return None

    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def pre_register_visitor(
    db: Session,
    name: str,
    phone: Optional[str],
    purpose: Optional[str],
    flat_id: Optional[int],
    created_by_user_id: Optional[int],
    valid_for_hours: int = 24,
) -> dict:
    """Create a pre-registered visitor and generate QR payload."""
    if not flat_id:
        raise HTTPException(status_code=400, detail="Flat No is required.")
    flat = db.query(Flat).filter(Flat.id == flat_id).first()
    if not flat:
        raise HTTPException(status_code=400, detail="Flat No must be valid.")
    token = uuid4().hex
    valid_until = datetime.now(timezone.utc) + timedelta(hours=valid_for_hours)
    visitor = Visitor(
        name=name,
        phone=phone,
        purpose=purpose,
        flat_id=flat_id,
        created_by_user_id=created_by_user_id,
        qr_token=token,
        # A resident-generated QR pass is already authorized by that resident,
        # so guards can verify it directly at the gate.
        status="approved",
        entry_time=None,
        exit_time=None,
        pre_registered_at=datetime.now(timezone.utc),
        valid_until=valid_until,
    )
    db.add(visitor)
    db.commit()
    db.refresh(visitor)

    payload = _build_qr_payload(visitor.id, token)
    qr_base64 = _generate_qr_base64(payload)
    notify_visitor_event(db, visitor, "pre-registered")
    return {
        "visitor": visitor,
        "qr_payload": payload,
        "qr_image_base64": qr_base64,
        "valid_until": valid_until,
    }


def scan_visitor_entry(db: Session, qr_payload: str) -> Visitor:
    """Validate visitor QR and register entry time."""
    if not qr_payload.startswith("visitor:"):
        raise HTTPException(status_code=400, detail="Invalid QR payload")

    try:
        _prefix, visitor_id, token = qr_payload.split(":", 2)
        visitor_id_int = int(visitor_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid QR payload") from exc

    visitor = db.query(Visitor).filter(Visitor.id == visitor_id_int).first()
    if not visitor or visitor.qr_token != token:
        raise HTTPException(status_code=404, detail="Visitor not found")
    if visitor.status == "rejected":
        raise HTTPException(status_code=403, detail="Visitor request was rejected")
    if visitor.status == "pending":
        raise HTTPException(status_code=403, detail="Visitor not approved yet")
    if visitor.status == "exited":
        raise HTTPException(status_code=409, detail="Visitor already exited")
    if visitor.status == "entered":
        return visitor
    if visitor.valid_until and datetime.now(timezone.utc) > visitor.valid_until:
        visitor.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="Visitor pass expired")

    visitor.entry_time = datetime.now(timezone.utc)
    visitor.status = "entered"
    db.commit()
    db.refresh(visitor)
    notify_visitor_event(db, visitor, "entered")
    return visitor


def mark_visitor_exit(db: Session, visitor_id: int) -> Visitor:
    """Mark visitor exit time."""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    if visitor.status != "entered":
        raise HTTPException(status_code=400, detail="Only entered visitors can be marked exited")
    if visitor.exit_time:
        return visitor
    visitor.exit_time = datetime.now(timezone.utc)
    visitor.status = "exited"
    db.commit()
    db.refresh(visitor)
    notify_visitor_event(db, visitor, "exited")
    return visitor
