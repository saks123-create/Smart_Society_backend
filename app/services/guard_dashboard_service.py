from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.visitor import Visitor
from app.models.delivery import Delivery

def guard_stats(db: Session):
    # Use timezone-aware UTC to match timezone-aware DB columns
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    visitors = db.query(Visitor).filter(Visitor.entry_time >= start_of_day).count()
    deliveries = db.query(Delivery).filter(Delivery.received_time >= start_of_day).count()
    return {
        "today_visitors": visitors,
        "today_deliveries": deliveries,
    }
 