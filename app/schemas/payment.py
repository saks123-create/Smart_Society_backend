from pydantic import ConfigDict, validator
from typing import Optional
from datetime import datetime
from app.models.payment import PaymentStatus
from app.schemas.base import BaseSchema
from app.schemas.validators import validate_amount, validate_int

class PaymentCreate(BaseSchema):
    resident_id: int
    amount: float
    due_date: Optional[datetime] = None

    _resident = validator("resident_id", allow_reuse=True)(lambda v: validate_int(v, "Resident id"))
    _amount = validator("amount", allow_reuse=True)(validate_amount)

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "resident_id": 7,
                "amount": 2500.00,
                "due_date": "2026-04-05T00:00:00Z",
            }
        })

class PaymentUpdate(BaseSchema):
    status: Optional[PaymentStatus] = None
    paid_at: Optional[datetime] = None
    method: Optional[str] = None
    provider: Optional[str] = None
    provider_order_id: Optional[str] = None
    provider_payment_id: Optional[str] = None

class PaymentOut(BaseSchema):
    id: int
    resident_id: int
    amount: float
    currency: Optional[str] = None
    status: PaymentStatus
    due_date: Optional[datetime]
    paid_at: Optional[datetime]
    method: Optional[str]
    provider: Optional[str] = None
    provider_order_id: Optional[str] = None
    provider_payment_id: Optional[str] = None
    receipt: Optional[str] = None

class PaymentSummary(BaseSchema):
    total_transactions: int
    total_collected: float
    pending_amount: float
    overdue_count: int


class RazorpayOrderRequest(BaseSchema):
    payment_id: int

    _payment = validator("payment_id", allow_reuse=True)(lambda v: validate_int(v, "Payment id"))

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "payment_id": 12,
            }
        })


class RazorpayOrderResponse(BaseSchema):
    order_id: Optional[str]
    amount: float
    currency: str
    key_id: Optional[str]
    already_paid: bool = False


class RazorpayVerifyRequest(BaseSchema):
    payment_id: int
    order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    method: Optional[str] = None

    _payment = validator("payment_id", allow_reuse=True)(lambda v: validate_int(v, "Payment id"))

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "payment_id": 12,
                "order_id": "order_9A33XWu170gUtm",
                "razorpay_payment_id": "pay_29QQoUBi66xm2f",
                "razorpay_signature": "a2c4d3...",
                "method": "UPI",
            }
        })
