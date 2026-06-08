from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.payment import Payment

def list_resident_payments(db: Session, resident_id: int, offset: int = 0, limit: Optional[int] = None):
    query = (
        db.query(Payment)
        .filter(Payment.resident_id == resident_id)
        .filter(or_(Payment.receipt.is_(None), ~Payment.receipt.like("latefee_%")))
        .order_by(Payment.created_at.desc())
    )
    if limit is None:
        return query.all()
    return query.offset(offset).limit(limit).all()
