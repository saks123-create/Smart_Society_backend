from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.complaint import Complaint, ComplaintStatus
from app.models.delivery import Delivery
from app.models.flat import Flat
from app.models.notice import Notice
from app.models.payment import Payment, PaymentStatus
from app.models.resident import Resident
from app.models.user import User, UserRole, UserStatus


def admin_stats(db: Session):
    total_residents = db.query(Resident).count()
    total_guards = db.query(User).filter(User.role == UserRole.security).count()
    total_flats = db.query(Flat).count()
    pending_approvals = (
        db.query(User)
        .filter(User.role == UserRole.resident, User.status == UserStatus.pending)
        .count()
    )
    open_count = db.query(Complaint).filter(Complaint.status == ComplaintStatus.open).count()
    in_progress_count = db.query(Complaint).filter(Complaint.status == ComplaintStatus.in_progress).count()
    resolved_count = db.query(Complaint).filter(Complaint.status == ComplaintStatus.resolved).count()
    closed_count = db.query(Complaint).filter(Complaint.status == ComplaintStatus.closed).count()
    open_complaints = open_count + in_progress_count
    pending_payments = db.query(Payment).filter(Payment.status != PaymentStatus.paid).count()
    overdue_payments = db.query(Payment).filter(Payment.status == PaymentStatus.overdue).count()
    return {
        "total_residents": total_residents,
        "total_guards": total_guards,
        "total_flats": total_flats,
        "pending_approvals": pending_approvals,
        "open_complaints": open_complaints,
        "complaints_open": open_count,
        "complaints_in_progress": in_progress_count,
        "complaints_resolved": resolved_count,
        "complaints_closed": closed_count,
        "pending_payments": pending_payments,
        "overdue_payments": overdue_payments,
    }


def admin_payment_overview(db: Session):
    total = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status == PaymentStatus.paid)
        .scalar()
    )
    pending = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status != PaymentStatus.paid)
        .scalar()
    )
    payments_this_month = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.status == PaymentStatus.paid,
            Payment.paid_at.isnot(None),
            func.date_trunc("month", Payment.paid_at) == func.date_trunc("month", func.now()),
        )
        .scalar()
    )
    return {
        "total_maintenance": float(total or 0),
        "pending_dues": float(pending or 0),
        "payments_this_month": float(payments_this_month or 0),
    }


MAX_RECENT_ACTIVITY = 5


def admin_recent_activity(db: Session, limit: int = MAX_RECENT_ACTIVITY):
    limit = min(max(limit, 1), MAX_RECENT_ACTIVITY)
    items = []

    complaints = (
        db.query(Complaint)
        .options(joinedload(Complaint.resident))
        .order_by(Complaint.created_at.desc())
        .limit(limit)
        .all()
    )
    for complaint in complaints:
        flat_text = (
            complaint.resident.flat_label
            if complaint.resident and complaint.resident.flat_label
            else "Flat -"
        )
        if complaint.created_at:
            items.append(
                {
                    "message": f"Complaint logged: {complaint.title} ({flat_text})",
                    "created_at": complaint.created_at,
                    "type": "complaint",
                }
            )

    payments = (
        db.query(Payment)
        .options(joinedload(Payment.resident))
        .order_by(func.coalesce(Payment.paid_at, Payment.created_at).desc())
        .limit(limit)
        .all()
    )
    for payment in payments:
        flat_text = (
            payment.resident.flat_label
            if payment.resident and payment.resident.flat_label
            else "Flat -"
        )
        amount_text = f"INR {float(payment.amount):,.2f}"
        activity_time = payment.paid_at or payment.created_at
        if activity_time:
            label = "Payment received" if payment.status == PaymentStatus.paid else "Payment logged"
            items.append(
                {
                    "message": f"{label}: {amount_text} ({flat_text})",
                    "created_at": activity_time,
                    "type": "payment",
                }
            )

    residents = db.query(Resident).order_by(Resident.created_at.desc()).limit(limit).all()
    for resident in residents:
        flat_text = resident.flat_label or "Flat -"
        if resident.created_at:
            items.append(
                {
                    "message": f"Resident added: {resident.name} ({flat_text})",
                    "created_at": resident.created_at,
                    "type": "resident",
                }
            )

    notices = db.query(Notice).order_by(Notice.created_at.desc()).limit(limit).all()
    for notice in notices:
        if notice.created_at:
            items.append(
                {
                    "message": f"Notice posted: {notice.title}",
                    "created_at": notice.created_at,
                    "type": "notice",
                }
            )

    deliveries = db.query(Delivery).order_by(Delivery.received_time.desc()).limit(limit).all()
    for delivery in deliveries:
        flat_text = delivery.flat_label or "Flat -"
        if delivery.received_time:
            items.append(
                {
                    "message": f"Delivery logged: {delivery.vendor} ({flat_text})",
                    "created_at": delivery.received_time,
                    "type": "delivery",
                }
            )

    items.sort(key=lambda item: item["created_at"], reverse=True)
    return items[:limit]
