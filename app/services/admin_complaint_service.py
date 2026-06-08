from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from app.models.complaint import Complaint
from datetime import datetime
from app.schemas.complaint import ComplaintUpdateStatus, ComplaintUpdate
from app.models.complaint import ComplaintStatus
from app.services.admin_audit_service import log_admin_action

def list_complaints(db: Session, offset: int = 0, limit: Optional[int] = None):
    """List all complaints."""
    query = db.query(Complaint).order_by(Complaint.created_at.desc())
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()


def complaint_summary(db: Session):
    total = db.query(Complaint).count()
    open_count = db.query(Complaint).filter(Complaint.status == ComplaintStatus.open).count()
    in_progress = db.query(Complaint).filter(Complaint.status == ComplaintStatus.in_progress).count()
    resolved = db.query(Complaint).filter(Complaint.status == ComplaintStatus.resolved).count()
    average_rating = (
        db.query(func.avg(Complaint.rating))
        .filter(Complaint.rating.isnot(None))
        .scalar()
    )
    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "average_rating": round(float(average_rating or 0), 1),
    }

def update_complaint_status(
    db: Session,
    complaint_id: int,
    data: ComplaintUpdateStatus,
    actor_user_id: int | None = None,
):
    """Update complaint status with allowed transitions."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    _ensure_valid_transition(complaint.status, data.status)
    complaint.status = data.status
    if data.status == ComplaintStatus.resolved:
        complaint.resolved_at = datetime.utcnow()
    if actor_user_id is not None:
        log_admin_action(
            db,
            actor_user_id=actor_user_id,
            action="complaint.status_updated",
            target_type="complaint",
            target_id=complaint.id,
            details={"status": complaint.status.value},
        )
    db.commit()
    db.refresh(complaint)
    return complaint


def update_complaint(
    db: Session,
    complaint_id: int,
    data: ComplaintUpdate,
    actor_user_id: int | None = None,
):
    """Update complaint fields (status, priority)."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    updated_fields: list[str] = []
    if data.status:
        _ensure_valid_transition(complaint.status, data.status)
        complaint.status = data.status
        if data.status == ComplaintStatus.resolved:
            complaint.resolved_at = datetime.utcnow()
        updated_fields.append("status")
    if data.priority:
        complaint.priority = data.priority.value
        updated_fields.append("priority")
    if actor_user_id is not None and updated_fields:
        log_admin_action(
            db,
            actor_user_id=actor_user_id,
            action="complaint.updated",
            target_type="complaint",
            target_id=complaint.id,
            details={"updated_fields": updated_fields},
        )
    db.commit()
    db.refresh(complaint)
    return complaint


def _ensure_valid_transition(current_status: ComplaintStatus, next_status: ComplaintStatus) -> None:
    """Enforce complaint status flow OPEN -> IN_PROGRESS -> RESOLVED."""
    allowed = {
        ComplaintStatus.open: {ComplaintStatus.in_progress},
        ComplaintStatus.in_progress: {ComplaintStatus.resolved},
        ComplaintStatus.resolved: set(),
        ComplaintStatus.closed: set(),
    }
    if current_status == next_status:
        return
    if next_status not in allowed.get(current_status, set()):
        raise HTTPException(status_code=400, detail="Invalid status transition")
