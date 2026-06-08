from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.payment import (
    PaymentOut,
    RazorpayOrderRequest,
    RazorpayOrderResponse,
    RazorpayVerifyRequest,
)
from app.services.resident_payment_service import list_resident_payments
from app.services.payment_service import create_razorpay_order, verify_razorpay_payment
from app.services.resident_profile_service import get_profile_by_user_id
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/resident/payments", tags=["resident", "payments"])

@router.get("/", response_model=list[PaymentOut], dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def my_payments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    profile = get_profile_by_user_id(db, current_user.id)
    return list_resident_payments(db, profile.id, offset=offset, limit=limit)

@router.post("/razorpay/order", response_model=RazorpayOrderResponse, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def create_razorpay_payment_order(
    data: RazorpayOrderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a Razorpay order for a pending payment."""
    profile = get_profile_by_user_id(db, current_user.id)
    return create_razorpay_order(db, data.payment_id, profile.id)


@router.post("/razorpay/verify", response_model=PaymentOut, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def verify_razorpay(
    data: RazorpayVerifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Verify Razorpay signature and mark payment as paid."""
    profile = get_profile_by_user_id(db, current_user.id)
    return verify_razorpay_payment(
        db,
        data.payment_id,
        profile.id,
        data.order_id,
        data.razorpay_payment_id,
        data.razorpay_signature,
        method=data.method,
    )
