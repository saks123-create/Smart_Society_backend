from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.resident import ResidentCreate, ResidentUpdate, ResidentOut, ResidentSummary
from app.services.admin_resident_service import list_residents, get_resident, create_resident, update_resident, delete_resident, resident_summary
from app.utils.deps import get_db, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/admin/residents", tags=["admin", "Residents"])

@router.get("/", response_model=list[ResidentOut], dependencies=[Depends(require_roles([UserRole.admin]))])
def all_residents(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_residents(db, offset=offset, limit=limit)

@router.get("/summary", response_model=ResidentSummary, dependencies=[Depends(require_roles([UserRole.admin]))])
def residents_summary(db: Session = Depends(get_db)):
    return resident_summary(db)

@router.get("/{resident_id}", response_model=ResidentOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def one_resident(resident_id: int, db: Session = Depends(get_db)):
    return get_resident(db, resident_id)

@router.post("/", response_model=ResidentOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def add_resident(data: ResidentCreate, db: Session = Depends(get_db)):
    return create_resident(db, data)

@router.put("/{resident_id}", response_model=ResidentOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def edit_resident(resident_id: int, data: ResidentUpdate, db: Session = Depends(get_db)):
    return update_resident(db, resident_id, data)

@router.delete("/{resident_id}", dependencies=[Depends(require_roles([UserRole.admin]))])
def remove_resident(resident_id: int, db: Session = Depends(get_db)):
    return delete_resident(db, resident_id)
