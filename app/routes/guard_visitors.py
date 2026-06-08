from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.visitor import VisitorCreate, VisitorOut, VisitorScanRequest
from app.services.guard_visitor_service import list_visitors, create_visitor, allow_entry
from app.services.visitor_service import scan_visitor_entry, mark_visitor_exit
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/guard/visitors", tags=["guard", "visitors"])

@router.get("/", response_model=list[VisitorOut], dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def all_visitors(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_visitors(db, offset=offset, limit=limit)

@router.post("/", response_model=VisitorOut, dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def add_visitor(data: VisitorCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_visitor(db, data, current_user.id)

@router.post("/scan", response_model=VisitorOut, dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def scan_visitor(data: VisitorScanRequest, db: Session = Depends(get_db)):
    """Scan a visitor QR payload and register entry time."""
    return scan_visitor_entry(db, data.qr_payload)


@router.put("/{visitor_id}/exit-now", response_model=VisitorOut, dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def exit_now(visitor_id: int, db: Session = Depends(get_db)):
    """Mark visitor exit time immediately."""
    return mark_visitor_exit(db, visitor_id)


@router.put("/{visitor_id}/allow-entry", response_model=VisitorOut, dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def allow(visitor_id: int, db: Session = Depends(get_db)):
    """Allow visitor entry after resident approval."""
    return allow_entry(db, visitor_id)
