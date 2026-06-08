from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric, String, Enum
from sqlalchemy.orm import relationship
import enum
from app.database.connection import Base
from app.models.mixins import TimestampMixin

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"

class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="INR")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    method = Column(String(50), nullable=True)
    provider = Column(String(50), nullable=True)
    provider_order_id = Column(String(100), nullable=True)
    provider_payment_id = Column(String(100), nullable=True)
    provider_signature = Column(String(255), nullable=True)
    idempotency_key = Column(String(120), nullable=True)
    receipt = Column(String(120), nullable=True)
    reminder_stage = Column(Integer, nullable=False, default=0)

    resident = relationship("Resident", back_populates="payments")
