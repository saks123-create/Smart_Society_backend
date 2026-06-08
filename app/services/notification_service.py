import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

BREVO_API_BASE = os.getenv("BREVO_API_BASE", "https://api.brevo.com/v3")
_BREVO_WARNING_LOGGED = False


def _load_brevo_config() -> tuple[str, str, str, Optional[str]]:
    api_key = os.getenv("BREVO_API_KEY", "").strip()
    sender_email = os.getenv("BREVO_SENDER_EMAIL", "").strip()
    sender_name = os.getenv("BREVO_SENDER_NAME", "SmartSociety").strip() or "SmartSociety"
    reply_to = os.getenv("BREVO_REPLY_TO", "").strip() or None

    if not api_key or not sender_email:
        raise ValueError("BREVO_API_KEY and BREVO_SENDER_EMAIL are required")

    return api_key, sender_email, sender_name, reply_to


def is_brevo_configured() -> bool:
    return bool(os.getenv("BREVO_API_KEY", "").strip() and os.getenv("BREVO_SENDER_EMAIL", "").strip())


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send email via the Brevo transactional email API."""
    global _BREVO_WARNING_LOGGED
    try:
        api_key, sender_email, sender_name, reply_to = _load_brevo_config()
    except ValueError as exc:
        if not _BREVO_WARNING_LOGGED:
            logger.warning(
                "Email delivery disabled: %s. Set BREVO_API_KEY and BREVO_SENDER_EMAIL in backend/.env to enable transactional emails.",
                exc,
            )
            _BREVO_WARNING_LOGGED = True
        return False

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email,
        },
        "to": [
            {
                "email": to_email,
            }
        ],
        "subject": subject,
        "textContent": body,
    }
    if reply_to:
        payload["replyTo"] = {"email": reply_to}

    try:
        response = httpx.post(
            f"{BREVO_API_BASE.rstrip('/')}/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            json=payload,
            timeout=20.0,
        )
    except httpx.RequestError:
        logger.exception("Brevo request failed while sending email to %s", to_email)
        return False

    if response.status_code >= 400:
        logger.error(
            "Brevo email request failed for %s: status=%s body=%s",
            to_email,
            response.status_code,
            response.text,
        )
        return False

    return True


def send_sms(to_phone: str, message: str) -> bool:
    """Stub for sending SMS notifications."""
    logger.info("SMS stub: to=%s message=%s", to_phone, message)
    return True


def notify_payment_reminder(
    email: Optional[str],
    phone: Optional[str],
    amount: float,
    due_date_text: str,
) -> None:
    """Send payment reminder via available channels (email + SMS)."""
    subject = "Society Payment Reminder"
    body = f"Your payment of Rs. {amount} is pending. Due date: {due_date_text}."
    if email:
        send_email(email, subject, body)
    if phone:
        send_sms(phone, body)


def notify_notice_created(db, notice) -> None:
    """Notify residents about a new notice if enabled."""
    try:
        from app.services.admin_settings_service import get_settings
        from app.models.user import User, UserRole, UserStatus
    except Exception:
        logger.exception("Notification imports failed for notice")
        return

    settings = get_settings(db)
    if not settings.notify_notices:
        logger.info("Notice notifications disabled; skipping")
        return

    subject = f"New Notice: {notice.title}"
    body = notice.content
    residents = (
        db.query(User)
        .filter(User.role == UserRole.resident, User.status == UserStatus.approved)
        .all()
    )
    for user in residents:
        if user.email:
            send_email(user.email, subject, body)
        if user.phone:
            send_sms(user.phone, body)


def notify_complaint_created(db, complaint) -> None:
    """Notify admin about a new complaint if enabled."""
    try:
        from app.services.admin_settings_service import get_settings
        from app.models.resident import Resident
    except Exception:
        logger.exception("Notification imports failed for complaint")
        return

    settings = get_settings(db)
    if not settings.notify_complaints:
        logger.info("Complaint notifications disabled; skipping")
        return

    resident = db.query(Resident).filter(Resident.id == complaint.resident_id).first()
    resident_name = resident.name if resident else "Resident"
    subject = f"New Complaint from {resident_name}"
    body = f"{complaint.title}\n\n{complaint.description}"
    if settings.admin_email:
        send_email(settings.admin_email, subject, body)
    if settings.admin_phone:
        send_sms(settings.admin_phone, body)


def notify_visitor_event(db, visitor, event_label: str) -> None:
    """Notify resident about a visitor event if enabled."""
    try:
        from app.services.admin_settings_service import get_settings
        from app.models.user import User
    except Exception:
        logger.exception("Notification imports failed for visitor")
        return

    settings = get_settings(db)
    if not settings.notify_visitors:
        logger.info("Visitor notifications disabled; skipping")
        return

    if not visitor.created_by_user_id:
        return
    user = db.query(User).filter(User.id == visitor.created_by_user_id).first()
    if not user:
        return
    subject = f"Visitor {event_label}"
    body = f"{visitor.name} - {event_label}"
    if user.email:
        send_email(user.email, subject, body)
    if user.phone:
        send_sms(user.phone, body)


def notify_delivery_event(db, delivery) -> None:
    """Notify resident about a delivery arrival."""
    try:
        from app.models.resident import Resident
        from app.models.user import User
    except Exception:
        logger.exception("Notification imports failed for delivery")
        return

    if not delivery.flat_id:
        return

    residents = db.query(Resident).filter(Resident.flat_id == delivery.flat_id).all()
    if not residents:
        return

    subject = "Delivery Arrived"
    person = getattr(delivery, "delivery_person_name", None)
    if person:
        body = f"Your delivery has arrived. Person: {person}. Company: {delivery.vendor}."
    else:
        body = f"Your delivery has arrived. Company: {delivery.vendor}."
    for resident in residents:
        user = db.query(User).filter(User.id == resident.user_id).first()
        if not user:
            continue
        if user.email:
            send_email(user.email, subject, body)
        if user.phone:
            send_sms(user.phone, body)


def notify_guard_visitor_request(db, visitor) -> None:
    """Notify resident about a guard-initiated visitor request."""
    try:
        from app.services.admin_settings_service import get_settings
        from app.models.resident import Resident
        from app.models.user import User
    except Exception:
        logger.exception("Notification imports failed for guard visitor request")
        return

    settings = get_settings(db)
    if not settings.notify_visitors:
        logger.info("Visitor notifications disabled; skipping")
        return

    if not visitor.flat_id:
        return

    residents = db.query(Resident).filter(Resident.flat_id == visitor.flat_id).all()
    if not residents:
        return

    subject = "Visitor at Gate"
    body = f"Visitor waiting at gate: {visitor.name}. Please approve or reject."
    for resident in residents:
        user = db.query(User).filter(User.id == resident.user_id).first()
        if not user:
            continue
        if user.email:
            send_email(user.email, subject, body)
        if user.phone:
            send_sms(user.phone, body)
