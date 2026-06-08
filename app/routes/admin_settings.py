from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.admin_settings_service import get_settings, update_settings, change_admin_password
from app.schemas.settings import SettingsOut, SettingsUpdate, AdminPasswordChangeRequest
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/admin/settings", tags=["admin", "Settings"])

@router.get("/", response_model=SettingsOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def settings(
    db: Session = Depends(get_db),
):
    return get_settings(db)

@router.put("/", response_model=SettingsOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def update(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_settings(db, data, actor_user=current_user)

@router.post("/change-password", dependencies=[Depends(require_roles([UserRole.admin]))])
def change_password(
    data: AdminPasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    change_admin_password(db, current_user.id, data.current_password, data.new_password)
    return {"message": "Password updated successfully"}
