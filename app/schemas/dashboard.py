from pydantic import BaseModel
from datetime import datetime

class AdminDashboardStats(BaseModel):
    total_residents: int
    total_guards: int
    total_flats: int
    pending_approvals: int
    open_complaints: int
    complaints_open: int
    complaints_in_progress: int
    complaints_resolved: int
    complaints_closed: int
    pending_payments: int
    overdue_payments: int

class GuardDashboardStats(BaseModel):
    today_visitors: int
    today_deliveries: int

class AdminActivityItem(BaseModel):
    message: str
    created_at: datetime
    type: str

class AdminPaymentOverview(BaseModel):
    total_maintenance: float
    pending_dues: float
    payments_this_month: float
