from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.schemas.delivery import DeliveryOut
from app.services.resident_delivery_service import list_resident_deliveries, confirm_delivery
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/resident/deliveries", tags=["resident", "deliveries"])


@router.get("/", response_model=list[DeliveryOut], dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def my_deliveries(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_resident_deliveries(db, current_user.id, offset=offset, limit=limit)


@router.post("/{delivery_id}/confirm", response_model=DeliveryOut, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def confirm(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return confirm_delivery(db, current_user.id, delivery_id)
