from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.resident import ResidentOut
from app.schemas.profile import ProfileUpdate
from app.services.resident_profile_service import get_profile_by_user_id, update_profile
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/resident/profile", tags=["resident", "profile"])

@router.get("/", response_model=ResidentOut, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def my_profile(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_profile_by_user_id(db, current_user.id)

@router.put("/", response_model=ResidentOut, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def edit_profile(data: ProfileUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    profile = get_profile_by_user_id(db, current_user.id)
    return update_profile(db, profile.id, data)
