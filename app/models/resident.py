from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database.connection import Base
from app.models.mixins import TimestampMixin

class ResidentRole(str, enum.Enum):
    owner = "owner"
    tenant = "tenant"
    family_member = "family_member"


class Resident(Base, TimestampMixin):
    __tablename__ = "residents"
    __table_args__ = (
        CheckConstraint(
            "(move_out_date IS NULL) OR (move_in_date IS NULL) OR (move_out_date > move_in_date)",
            name="ck_residents_move_out_after_move_in",
        ),
        Index("ix_residents_user_id", "user_id"),
        Index("ix_residents_flat_id", "flat_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    flat_id = Column(Integer, ForeignKey("flats.id", ondelete="RESTRICT"), nullable=True)
    role = Column(Enum(ResidentRole), nullable=False)
    move_in_date = Column(Date, nullable=False, server_default=func.current_date())
    move_out_date = Column(Date, nullable=True)

    user = relationship("User")
    flat = relationship("Flat", back_populates="residents")
    complaints = relationship("Complaint", back_populates="resident")
    payments = relationship("Payment", back_populates="resident")

    @property
    def flat_number(self):
        if self.flat is None:
            return None
        return self.flat.flat_number

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
