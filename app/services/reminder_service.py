import logging
import os
import calendar
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus
from app.models.resident import Resident
from app.models.user import User
from app.services.notification_service import send_email

logger = logging.getLogger(__name__)


def run_payment_reminders(db: Session) -> int:
    """Identify pending payments and send reminder notifications."""
    now = datetime.utcnow()
    _generate_monthly_maintenance(db, now)
    _apply_late_fees(db, now)
    count = _send_due_reminders(db, now)
    logger.info("Payment reminder run completed: %s reminders sent", count)
    return count


def _get_month_bounds(now: datetime) -> tuple[datetime, datetime]:
    first_day = datetime(now.year, now.month, 1)
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    return first_day, next_month


def _safe_day(year: int, month: int, day: int) -> int:
    last_day = calendar.monthrange(year, month)[1]
    return min(day, last_day)


def _generate_monthly_maintenance(db: Session, now: datetime) -> int:
    """Create monthly maintenance payments on the billing day."""
    billing_day = int(os.getenv("MAINTENANCE_BILLING_DAY", "1"))
    due_day = int(os.getenv("MAINTENANCE_DUE_DAY", "10"))
    amount = float(os.getenv("MAINTENANCE_AMOUNT", "3000"))

    if now.day != billing_day:
        return 0

    due_date = datetime(now.year, now.month, _safe_day(now.year, now.month, due_day))
    created = 0
    residents = db.query(Resident).all()
    for resident in residents:
        receipt = f"maintenance_{now.year}_{now.month:02d}_resident_{resident.id}"
        exists = (
            db.query(Payment)
            .filter(Payment.resident_id == resident.id, Payment.receipt == receipt)
            .first()
        )
        if exists:
            continue
        payment = Payment(
            resident_id=resident.id,
            amount=amount,
            status=PaymentStatus.pending,
            due_date=due_date,
            receipt=receipt,
        )
        db.add(payment)
        created += 1
    if created:
        db.commit()
    logger.info("Monthly maintenance generation completed: %s created", created)
    return created


def _apply_late_fees(db: Session, now: datetime) -> int:
    """Mark overdue payments without creating new rows."""
    overdue_payments = (
        db.query(Payment)
        .filter(Payment.status.in_([PaymentStatus.pending, PaymentStatus.overdue]))
        .filter(Payment.due_date.isnot(None))
        .filter(Payment.due_date < now)
        .all()
    )

    updated = 0
    for payment in overdue_payments:
        if payment.status != PaymentStatus.overdue:
            payment.status = PaymentStatus.overdue
            updated += 1

    if updated:
        db.commit()
    return updated


def _build_payment_email(stage: int, name: str, due_date_text: str) -> tuple[str, str]:
    if stage == 1:
        subject = "Friendly Reminder: Maintenance Payment Due Today"
        body = (
            f"Hello {name},\n"
            f"This is a friendly reminder that your maintenance payment is due today ({due_date_text}).\n"
            "Please complete the payment at your earliest convenience.\n"
            "If you have already paid, please ignore this message.\n"
            "Thank you,\n"
            "SmartSociety Team"
        )
        return subject, body
    if stage == 2:
        subject = "Payment Overdue by 3 Days"
        body = (
            f"Hello {name},\n"
            f"Your maintenance payment was due on {due_date_text} and is now 3 days overdue.\n"
            "Please make the payment as soon as possible to avoid any late fee.\n"
            "If you have already paid, please ignore this message.\n"
            "Thank you,\n"
            "SmartSociety Team"
        )
        return subject, body
    subject = "Urgent: Payment Overdue by 7 Days"
    body = (
        f"Hello {name},\n"
        f"Your maintenance payment was due on {due_date_text} and is now 7 days overdue.\n"
        "Please complete the payment immediately. A late fee may be applied for further delay.\n"
        "If you have already paid, please ignore this message.\n"
        "Thank you,\n"
        "SmartSociety Team"
    )
    return subject, body


def _send_due_reminders(db: Session, now: datetime) -> int:
    """Send staged payment reminders via email only."""
    payments = (
        db.query(Payment, Resident, User)
        .join(Resident, Payment.resident_id == Resident.id)
        .join(User, Resident.user_id == User.id)
        .filter(Payment.status.in_([PaymentStatus.pending, PaymentStatus.overdue]))
        .filter(Payment.due_date.isnot(None))
        .all()
    )
    count = 0
    for payment, resident, user in payments:
        due = payment.due_date
        if not due:
            continue
        days_overdue = (now.date() - due.date()).days
        if days_overdue < 0:
            continue

        if days_overdue >= 7:
            stage = 3
        elif days_overdue >= 3:
            stage = 2
        elif days_overdue == 0:
            stage = 1
        else:
            continue

        current_stage = payment.reminder_stage or 0
        if current_stage >= stage:
            continue

        email = user.email or resident.email
        if not email:
            continue

        due_date_text = due.strftime("%Y-%m-%d")
        name = resident.name or "Resident"
        subject, body = _build_payment_email(stage, name, due_date_text)
        if send_email(email, subject, body):
            payment.reminder_stage = stage
            count += 1

    if count:
        db.commit()
    return count
