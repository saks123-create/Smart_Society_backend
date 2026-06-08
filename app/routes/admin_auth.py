from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserRole, UserStatus
from app.models.resident import Resident
from app.schemas.auth import UserOut
from app.utils.deps import get_current_user, get_db, require_roles
from app.services.admin_audit_service import log_admin_action

router = APIRouter(prefix="/admin", tags=["admin", "auth"])

@router.patch("/approve-user/{user_id}", response_model=UserOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != UserRole.resident:
        raise HTTPException(status_code=400, detail="User role must be resident")
    user.status = UserStatus.approved
    log_admin_action(
        db,
        actor_user_id=current_user.id,
        action="resident.approved",
        target_type="user",
        target_id=user.id,
        details={"email": user.email, "role": user.role.value},
    )
    db.commit()
    db.refresh(user)
    return user

@router.delete("/reject-user/{user_id}", dependencies=[Depends(require_roles([UserRole.admin]))])
def reject_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != UserRole.resident:
        raise HTTPException(status_code=400, detail="User role must be resident")
    if user.status != UserStatus.pending:
        raise HTTPException(status_code=400, detail="User is not pending")
    resident = db.query(Resident).filter(Resident.user_id == user.id).first()
    log_admin_action(
        db,
        actor_user_id=current_user.id,
        action="resident.rejected",
        target_type="user",
        target_id=user.id,
        details={"email": user.email, "role": user.role.value},
    )
    if resident:
        db.delete(resident)
    db.delete(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Resident could not be rejected because linked records still exist")
    return {"message": "Resident rejected"}

@router.get("/pending-residents", response_model=list[UserOut], dependencies=[Depends(require_roles([UserRole.admin]))])
def pending_residents(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
):
    query = db.query(User).filter(User.role == UserRole.resident, User.status == UserStatus.pending)
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()
