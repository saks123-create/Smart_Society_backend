from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
from app.models.mixins import TimestampMixin

class Visitor(Base, TimestampMixin):
    __tablename__ = "visitors"
    __table_args__ = (
        Index("ix_visitors_flat_id", "flat_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    purpose = Column(String(255), nullable=True)
    flat_id = Column(Integer, ForeignKey("flats.id", ondelete="RESTRICT"), nullable=True)
    entry_time = Column(DateTime(timezone=True), nullable=True)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    qr_token = Column(String(120), nullable=True)
    status = Column(String(50), nullable=True, default="pending")
    pre_registered_at = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    flat = relationship("Flat", back_populates="visitors")
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
