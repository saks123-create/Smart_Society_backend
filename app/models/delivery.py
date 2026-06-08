from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database.connection import Base
from app.models.mixins import TimestampMixin

class DeliveryStatus(str, enum.Enum):
    received = "received"
    handed_over = "handed_over"
    returned = "returned"

class Delivery(Base, TimestampMixin):
    __tablename__ = "deliveries"
    __table_args__ = (
        Index("ix_deliveries_flat_id", "flat_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    vendor = Column(String(255), nullable=False)
    delivery_person_name = Column(String(255), nullable=False)
    block_tower = Column(String(100), nullable=True)
    mobile_number = Column(String(20), nullable=True)
    delivery_type = Column(String(50), nullable=True)
    description = Column(String(255), nullable=True)
    flat_id = Column(Integer, ForeignKey("flats.id", ondelete="RESTRICT"), nullable=True)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.received, nullable=False)
    received_time = Column(DateTime(timezone=True), server_default=func.now())
    handed_over_time = Column(DateTime(timezone=True), nullable=True)
    resident_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    entry_allowed_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    flat = relationship("Flat", back_populates="deliveries")
    created_by = relationship("User")

    @property
    def flat_no(self):
        if self.flat is None:
            return None
        return self.flat.flat_number

    @property
    def flat_number(self):
        return self.flat_no

    @property
    def flat_block(self):
        if self.flat is None:
            return None
        return self.flat.block

    @property
    def flat_label(self):
        if self.flat is None:
            return None
        return f"{self.flat.block}-{self.flat.flat_number}"
