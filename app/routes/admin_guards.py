from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.auth import GuardCreate, GuardSummary, GuardUpdate, UserOut
from app.utils.deps import get_current_user, get_db, require_roles
from app.utils.normalization import normalize_email, normalize_phone
from app.utils.security import get_password_hash
from app.services.admin_audit_service import log_admin_action

router = APIRouter(prefix="/admin/guards", tags=["admin", "Guards"])


def _guard_query(db: Session):
    return db.query(User).filter(User.role == UserRole.security)


def _get_guard(db: Session, guard_id: int) -> User:
    guard = _guard_query(db).filter(User.id == guard_id).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Guard not found")
    return guard


@router.get("/", response_model=list[UserOut], dependencies=[Depends(require_roles([UserRole.admin]))])
def list_guards(
    db: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1, le=100),
    search: str | None = Query(None),
    active: bool | None = Query(None),
):
    query = _guard_query(db)
    cleaned_search = (search or "").strip().lower()
    if cleaned_search:
        like = f"%{cleaned_search}%"
        query = query.filter(
            func.lower(User.email).like(like) |
            func.coalesce(func.lower(User.phone), "").like(like)
        )
    if active is not None:
        query = query.filter(User.is_active == active)
    query = query.order_by(User.created_at.desc(), User.id.desc())
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()


@router.get("/summary", response_model=GuardSummary, dependencies=[Depends(require_roles([UserRole.admin]))])
def guard_summary(
    db: Session = Depends(get_db),
):
    total_guards = _guard_query(db).count()
    active_guards = _guard_query(db).filter(User.is_active.is_(True)).count()
    inactive_guards = total_guards - active_guards
    guards_with_phone = _guard_query(db).filter(User.phone.isnot(None)).count()
    return {
        "total_guards": total_guards,
        "active_guards": active_guards,
        "inactive_guards": inactive_guards,
        "guards_with_phone": guards_with_phone,
    }


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles([UserRole.admin]))])
def create_guard(
    data: GuardCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    email = normalize_email(data.email)
    phone = normalize_phone(data.phone)
    existing = db.query(User).filter(func.lower(func.trim(User.email)) == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if phone:
        existing_phone = db.query(User).filter(func.trim(User.phone) == phone).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already registered")

    user = User(
        email=email,
        phone=phone,
        hashed_password=get_password_hash(data.password),
        role=UserRole.security,
        status=None,
        is_active=True,
    )
    db.add(user)
    db.flush()
    log_admin_action(
        db,
        actor_user_id=current_user.id,
        action="guard.created",
        target_type="user",
        target_id=user.id,
        details={"email": email, "has_phone": bool(phone)},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Guard could not be created with the provided details")
    db.refresh(user)
    return user


@router.patch("/{guard_id}", response_model=UserOut, dependencies=[Depends(require_roles([UserRole.admin]))])
def update_guard(
    guard_id: int,
    data: GuardUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guard = _get_guard(db, guard_id)
    updates = data.dict(exclude_unset=True)
    audit_details: dict[str, object] = {"updated_fields": sorted(updates.keys())}

    if "phone" in updates:
        phone = normalize_phone(updates["phone"])
        if phone:
            existing_phone = (
                db.query(User)
                .filter(func.trim(User.phone) == phone, User.id != guard.id)
                .first()
            )
            if existing_phone:
                raise HTTPException(status_code=400, detail="Phone already registered")
        guard.phone = phone
        audit_details["phone"] = phone

    if "password" in updates and updates["password"]:
        guard.hashed_password = get_password_hash(updates["password"])

    if "is_active" in updates:
        guard.is_active = updates["is_active"]
        audit_details["is_active"] = updates["is_active"]

    if updates:
        log_admin_action(
            db,
            actor_user_id=current_user.id,
            action="guard.updated",
            target_type="user",
            target_id=guard.id,
            details=audit_details,
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Guard could not be updated with the provided details")
    db.refresh(guard)
    return guard


@router.delete("/{guard_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles([UserRole.admin]))])
def delete_guard(
    guard_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guard = _get_guard(db, guard_id)
    log_admin_action(
        db,
        actor_user_id=current_user.id,
        action="guard.deleted",
        target_type="user",
        target_id=guard.id,
        details={"email": guard.email},
    )
    db.delete(guard)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
