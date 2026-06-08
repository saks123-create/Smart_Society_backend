from sqlalchemy.orm import Session
from typing import Optional
from app.models.complaint import Complaint, ComplaintStatus
from app.schemas.complaint import ComplaintCreate
from app.services.ai_service import triage_complaint
from fastapi import HTTPException
from app.services.notification_service import notify_complaint_created
from app.services.storage_service import save_complaint_image

def list_resident_complaints(db: Session, resident_id: int, offset: int = 0, limit: Optional[int] = None):
    """List complaints for a resident."""
    query = (
        db.query(Complaint)
        .filter(Complaint.resident_id == resident_id)
        .order_by(Complaint.created_at.desc())
    )
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()

def create_resident_complaint(
    db: Session,
    resident_id: int,
    data: ComplaintCreate,
    image_file=None,
):
    """Create a complaint and optionally attach an image."""
    image_path = None
    if image_file is not None:
        image_path = save_complaint_image(resident_id, image_file)
    category = None
    priority = None
    summary = None
    try:
        triage = triage_complaint(data.title, data.description)
        category = triage.get("category")
        priority = triage.get("priority")
        summary = triage.get("summary")
    except HTTPException:
        pass

    payload = data.dict()
    payload.pop("priority", None)
    payload.pop("category", None)
    priority_value = data.priority.value if data.priority else None
    complaint = Complaint(
        resident_id=resident_id,
        category=category or data.category,
        priority=(priority or priority_value),
        summary=summary,
        image_path=image_path,
        **payload,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    notify_complaint_created(db, complaint)
    return complaint


def rate_complaint(
    db: Session,
    resident_id: int,
    complaint_id: int,
    rating: int,
    feedback: str | None = None,
):
    """Allow resident to rate a resolved complaint."""
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id, Complaint.resident_id == resident_id)
        .first()
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.status != ComplaintStatus.resolved:
        raise HTTPException(status_code=400, detail="Complaint is not resolved yet")
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    complaint.rating = rating
    complaint.rating_feedback = feedback
    db.commit()
    db.refresh(complaint)
    return complaint
