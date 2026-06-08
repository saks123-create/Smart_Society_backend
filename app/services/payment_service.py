import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus
from app.utils.razorpay_client import create_order, verify_signature, get_razorpay_key_id

logger = logging.getLogger(__name__)


def _amount_to_paise(amount: float) -> int:
    paise = int(round(float(amount) * 100))
    if paise <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")
    return paise


def create_razorpay_order(
    db: Session,
    payment_id: int,
    resident_id: int,
) -> dict:
    """Create a Razorpay order for a pending payment and store provider metadata."""
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.resident_id == resident_id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status not in {PaymentStatus.pending, PaymentStatus.overdue, PaymentStatus.paid}:
        raise HTTPException(status_code=400, detail="Payment is not eligible for checkout")
    currency = payment.currency or "INR"
    if payment.status == PaymentStatus.paid:
        key_id = get_razorpay_key_id()
        return {
            "order_id": payment.provider_order_id,
            "amount": float(payment.amount),
            "currency": currency,
            "key_id": key_id,
            "already_paid": True,
        }
    if payment.provider_order_id:
        key_id = get_razorpay_key_id()
        return {
            "order_id": payment.provider_order_id,
            "amount": float(payment.amount),
            "currency": currency,
            "key_id": key_id,
            "already_paid": False,
        }

    receipt = payment.receipt or f"payment_{payment.id}"
    amount_paise = _amount_to_paise(float(payment.amount))
    order = create_order(amount_paise, currency, receipt, notes={"payment_id": str(payment.id)})

    payment.provider = "razorpay"
    payment.currency = currency
    payment.provider_order_id = order.get("id")
    payment.receipt = receipt
    payment.idempotency_key = order.get("id")
    db.commit()
    db.refresh(payment)

    key_id = get_razorpay_key_id()
    return {
        "order_id": order.get("id"),
        "amount": float(payment.amount),
        "currency": currency,
        "key_id": key_id,
        "already_paid": False,
    }


def verify_razorpay_payment(
    db: Session,
    payment_id: int,
    resident_id: int,
    order_id: str,
    provider_payment_id: str,
    signature: str,
    method: Optional[str] = None,
) -> Payment:
    """Verify Razorpay signature and mark payment as paid (idempotent)."""
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.resident_id == resident_id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == PaymentStatus.paid:
        if payment.provider_order_id and payment.provider_order_id != order_id:
            raise HTTPException(status_code=409, detail="Payment already completed with another order")
        if payment.provider_payment_id and payment.provider_payment_id != provider_payment_id:
            raise HTTPException(status_code=409, detail="Payment already completed with another transaction")
        return payment

    existing = (
        db.query(Payment)
        .filter(Payment.provider_payment_id == provider_payment_id)
        .first()
    )
    if existing and existing.id != payment.id:
        raise HTTPException(status_code=409, detail="Duplicate payment detected")

    if not payment.provider_order_id:
        raise HTTPException(status_code=400, detail="Create a Razorpay order before verification")

    if payment.provider_order_id != order_id:
        raise HTTPException(status_code=400, detail="Order mismatch for payment")

    if not verify_signature(order_id, provider_payment_id, signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    payment.status = PaymentStatus.paid
    payment.paid_at = datetime.utcnow()
    payment.method = method or "Razorpay"
    payment.provider = "razorpay"
    payment.provider_order_id = order_id
    payment.provider_payment_id = provider_payment_id
    payment.provider_signature = signature
    db.commit()
    db.refresh(payment)
    logger.info("Payment %s marked as paid via Razorpay", payment.id)
    return payment
