from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.schemas.visitor import VisitorPreRegister, VisitorPreRegisterOut, VisitorOut, VisitorScanRequest
from app.models.flat import Flat
from app.services.visitor_service import pre_register_visitor, scan_visitor_entry
from app.services.resident_visitor_service import list_pending_requests, approve_request, reject_request
from app.services.resident_profile_service import get_profile_by_user_id
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/resident/visitors", tags=["resident", "visitors"])


@router.post("/pre-register", response_model=VisitorPreRegisterOut, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def pre_register(
    data: VisitorPreRegister,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Pre-register a visitor and generate a QR payload."""
    profile = get_profile_by_user_id(db, current_user.id)
    if not profile.flat_id:
        raise HTTPException(status_code=400, detail="Flat not assigned")
    resident_flat = db.query(Flat).filter(Flat.id == profile.flat_id).first()
    if not resident_flat:
        raise HTTPException(status_code=400, detail="Assigned flat not found")

    if data.flat_no is not None:
        if resident_flat.flat_number != data.flat_no:
            raise HTTPException(
                status_code=403,
                detail="You can only pre-register visitors for your assigned flat.",
            )
    if data.flat_id is not None and data.flat_id != profile.flat_id:
        raise HTTPException(
            status_code=403,
            detail="You can only pre-register visitors for your assigned flat.",
        )
    return pre_register_visitor(
        db=db,
        name=data.name,
        phone=data.phone,
        purpose=data.purpose,
        flat_id=profile.flat_id,
        created_by_user_id=current_user.id,
        valid_for_hours=data.valid_for_hours or 24,
    )


@router.get("/requests", response_model=list[VisitorOut], dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def pending_requests(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_pending_requests(db, current_user.id, offset=offset, limit=limit)


@router.post("/{visitor_id}/approve", response_model=VisitorOut, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def approve(visitor_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return approve_request(db, current_user.id, visitor_id)


@router.post("/{visitor_id}/reject", response_model=VisitorOut, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def reject(visitor_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return reject_request(db, current_user.id, visitor_id)


@router.post("/scan", response_model=VisitorOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def scan_visitor(data: VisitorScanRequest, db: Session = Depends(get_db)):
    """Scan a visitor QR payload and register entry time."""
    return scan_visitor_entry(db, data.qr_payload)
