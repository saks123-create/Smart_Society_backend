from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.flat import FlatCreate, FlatUpdate, FlatOut
from app.services.admin_flat_service import list_flats, get_flat, create_flat, update_flat, delete_flat
from app.utils.deps import get_current_user, get_db, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/admin/flats", tags=["admin", "Flats"])

@router.get("/", response_model=list[FlatOut], dependencies=[Depends(require_roles([UserRole.admin]))])
def all_flats(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    return list_flats(db, offset=offset, limit=limit)

@router.get("/{flat_id}", response_model=FlatOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def one_flat(flat_id: int, db: Session = Depends(get_db)):
    return get_flat(db, flat_id)

@router.post("/", response_model=FlatOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def add_flat(data: FlatCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_flat(db, data, actor_user_id=current_user.id)

@router.put("/{flat_id}", response_model=FlatOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def edit_flat(flat_id: int, data: FlatUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return update_flat(db, flat_id, data, actor_user_id=current_user.id)

@router.delete("/{flat_id}", dependencies=[Depends(require_roles([UserRole.admin]))])
def remove_flat(flat_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return delete_flat(db, flat_id, actor_user_id=current_user.id)
