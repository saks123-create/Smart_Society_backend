from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.user import UserRole
from app.schemas.flat import FlatOut
from app.services.admin_flat_service import list_flats
from app.utils.deps import get_db, require_roles

router = APIRouter(prefix="/guard/flats", tags=["guard", "flats"])


@router.get("/", response_model=list[FlatOut], dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def all_guard_flats(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=500),
):
    return list_flats(db, offset=offset, limit=limit)
