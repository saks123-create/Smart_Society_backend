from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.complaint import ComplaintOut, ComplaintUpdateStatus, ComplaintUpdate, ComplaintSummary
from app.services.admin_complaint_service import (
    list_complaints,
    complaint_summary,
    update_complaint_status,
    update_complaint,
)
from app.utils.deps import get_current_user, get_db, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/admin/complaints", tags=["admin", "Complaints"])

@router.get("/", response_model=list[ComplaintOut], dependencies=[Depends(require_roles([UserRole.admin]))])
def all_complaints(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_complaints(db, offset=offset, limit=limit)

@router.get("/summary", response_model=ComplaintSummary, dependencies=[Depends(require_roles([UserRole.admin]))])
def complaints_summary(db: Session = Depends(get_db)):
    return complaint_summary(db)

@router.put("/{complaint_id}/status", response_model=ComplaintOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def set_status(
    complaint_id: int,
    data: ComplaintUpdateStatus,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_complaint_status(db, complaint_id, data, actor_user_id=current_user.id)


@router.put("/{complaint_id}", response_model=ComplaintOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def update_complaint_fields(
    complaint_id: int,
    data: ComplaintUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update complaint status or priority."""
    return update_complaint(db, complaint_id, data, actor_user_id=current_user.id)
