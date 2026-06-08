from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentOut, PaymentSummary
from app.services.admin_payment_service import list_payments, create_payment, update_payment, payment_summary
from app.utils.deps import get_current_user, get_db, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/admin/payments", tags=["admin", "Payments"])

@router.get("/", response_model=list[PaymentOut], dependencies=[Depends(require_roles([UserRole.admin]))])
def all_payments(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_payments(db, offset=offset, limit=limit)

@router.get("/summary", response_model=PaymentSummary, dependencies=[Depends(require_roles([UserRole.admin]))])
def payments_summary(db: Session = Depends(get_db)):
    return payment_summary(db)

@router.post("/", response_model=PaymentOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def add_payment(data: PaymentCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_payment(db, data, actor_user_id=current_user.id)

@router.put("/{payment_id}", response_model=PaymentOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def edit_payment(payment_id: int, data: PaymentUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return update_payment(db, payment_id, data, actor_user_id=current_user.id)
