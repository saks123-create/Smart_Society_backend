from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from app.models.payment import Payment
from app.models.payment import PaymentStatus
from app.models.resident import Resident
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.admin_audit_service import log_admin_action

def list_payments(db: Session, offset: int = 0, limit: Optional[int] = None):
    query = db.query(Payment).order_by(Payment.created_at.desc())
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()


def payment_summary(db: Session):
    total_transactions = db.query(Payment).count()
    total_collected = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(Payment.status == PaymentStatus.paid)
        .scalar()
        or 0.0
    )
    pending_amount = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(Payment.status == PaymentStatus.pending)
        .scalar()
        or 0.0
    )
    overdue_count = db.query(Payment).filter(Payment.status == PaymentStatus.overdue).count()
    return {
        "total_transactions": total_transactions,
        "total_collected": float(total_collected),
        "pending_amount": float(pending_amount),
        "overdue_count": overdue_count,
    }

def create_payment(db: Session, data: PaymentCreate, actor_user_id: int | None = None):
    resident = db.query(Resident).filter(Resident.id == data.resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    payment = Payment(**data.model_dump())
    db.add(payment)
    db.flush()
    if actor_user_id is not None:
        log_admin_action(
            db,
            actor_user_id=actor_user_id,
            action="payment.created",
            target_type="payment",
            target_id=payment.id,
            details={
                "resident_id": payment.resident_id,
                "amount": float(payment.amount),
                "status": payment.status.value,
            },
        )
    db.commit()
    db.refresh(payment)
    return payment

def update_payment(db: Session, payment_id: int, data: PaymentUpdate, actor_user_id: int | None = None):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    updates = data.model_dump(exclude_unset=True)

    if updates.get("paid_at") and "status" not in updates:
        updates["status"] = PaymentStatus.paid

    payment_fields = {"method", "provider", "provider_order_id", "provider_payment_id"}
    if payment_fields.intersection(updates) and updates.get("status", payment.status) != PaymentStatus.paid:
        raise HTTPException(
            status_code=400,
            detail="Provider or payment method details can only be set for paid payments",
        )

    if "status" in updates:
        next_status = updates["status"]
        if next_status == PaymentStatus.paid and "paid_at" not in updates and payment.paid_at is None:
            payment.paid_at = datetime.utcnow()
        if next_status == PaymentStatus.paid and "method" not in updates and not payment.method:
            payment.method = "Manual"
        if next_status != PaymentStatus.paid:
            payment.paid_at = None
            payment.method = None
            payment.provider = None
            payment.provider_order_id = None
            payment.provider_payment_id = None
            payment.provider_signature = None
            payment.idempotency_key = None

    for key, value in updates.items():
        setattr(payment, key, value)
    if actor_user_id is not None and updates:
        log_admin_action(
            db,
            actor_user_id=actor_user_id,
            action="payment.updated",
            target_type="payment",
            target_id=payment.id,
            details={"updated_fields": sorted(updates.keys())},
        )
    db.commit()
    db.refresh(payment)
    return payment
