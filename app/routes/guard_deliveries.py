from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.delivery import DeliveryCreate, DeliveryUpdateStatus, DeliveryOut
from app.services.guard_delivery_service import list_deliveries, create_delivery, update_delivery_status, allow_delivery_entry
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/guard/deliveries", tags=["guard", "deliveries"])

@router.get("/", response_model=list[DeliveryOut], dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def all_deliveries(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_deliveries(db, offset=offset, limit=limit)

@router.post("/", response_model=DeliveryOut, dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def add_delivery(data: DeliveryCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_delivery(db, data, current_user.id)

@router.put("/{delivery_id}/status", response_model=DeliveryOut, dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def update_status(delivery_id: int, data: DeliveryUpdateStatus, db: Session = Depends(get_db)):
    return update_delivery_status(db, delivery_id, data)


@router.put("/{delivery_id}/allow-entry", response_model=DeliveryOut, dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def allow_entry(delivery_id: int, db: Session = Depends(get_db)):
    return allow_delivery_entry(db, delivery_id)
