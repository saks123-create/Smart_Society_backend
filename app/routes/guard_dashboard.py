from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.dashboard import GuardDashboardStats
from app.services.guard_dashboard_service import guard_stats
from app.utils.deps import get_db, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/guard/dashboard", tags=["guard", "Dashboard"])

@router.get("/", response_model=GuardDashboardStats, dependencies=[Depends(require_roles([UserRole.security, UserRole.admin]))])
def dashboard(
    db: Session = Depends(get_db),
):
    return guard_stats(db)
