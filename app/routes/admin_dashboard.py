from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.dashboard import AdminDashboardStats, AdminActivityItem, AdminPaymentOverview
from app.services.admin_dashboard_service import admin_stats, admin_recent_activity, admin_payment_overview
from app.utils.deps import get_db, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/admin/dashboard", tags=["admin", "Dashboard"])

@router.get("/", response_model=AdminDashboardStats, dependencies=[Depends(require_roles([UserRole.admin]))])
def dashboard(
    db: Session = Depends(get_db),
):
    return admin_stats(db)


@router.get("/activities", response_model=list[AdminActivityItem], dependencies=[Depends(require_roles([UserRole.admin]))])
def recent_activity(
    limit: int = Query(5, ge=1, le=5),
    db: Session = Depends(get_db),
):
    return admin_recent_activity(db, limit)


@router.get("/payment-overview", response_model=AdminPaymentOverview, dependencies=[Depends(require_roles([UserRole.admin]))])
def payment_overview(
    db: Session = Depends(get_db),
):
    return admin_payment_overview(db)
