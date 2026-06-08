from fastapi import APIRouter, Depends, Form, File, UploadFile, Query
from sqlalchemy.orm import Session
from app.schemas.complaint import ComplaintCreate, ComplaintOut, ComplaintRatingRequest
from app.services.resident_complaint_service import (
    list_resident_complaints,
    create_resident_complaint,
    rate_complaint,
)
from app.services.resident_profile_service import get_profile_by_user_id
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/resident/complaints", tags=["resident", "complaints"])

@router.get("/", response_model=list[ComplaintOut], dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def my_complaints(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    profile = get_profile_by_user_id(db, current_user.id)
    return list_resident_complaints(db, profile.id, offset=offset, limit=limit)

@router.post("/", response_model=ComplaintOut, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def raise_complaint(
    title: str = Form(...),
    description: str = Form(""),
    priority: str | None = Form(None),
    category: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    profile = get_profile_by_user_id(db, current_user.id)
    payload_description = description or title
    data = ComplaintCreate(
        title=title,
        description=payload_description,
        priority=priority,
        category=category,
    )
    return create_resident_complaint(db, profile.id, data, image_file=image)


@router.post("/{complaint_id}/rate", response_model=ComplaintOut, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def rate(
    complaint_id: int,
    data: ComplaintRatingRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Rate a resolved complaint."""
    profile = get_profile_by_user_id(db, current_user.id)
    return rate_complaint(db, profile.id, complaint_id, data.rating, data.feedback)
