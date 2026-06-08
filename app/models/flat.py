from sqlalchemy import Column, Integer, String, Numeric, Enum, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
import enum
from app.database.connection import Base
from app.models.mixins import TimestampMixin

class FlatStatus(str, enum.Enum):
    occupied = "occupied"
    vacant = "vacant"
    under_maintenance = "under_maintenance"


class FlatType(str, enum.Enum):
    one_bhk = "1BHK"
    two_bhk = "2BHK"
    three_bhk = "3BHK"
    duplex = "duplex"


class Flat(Base, TimestampMixin):
    __tablename__ = "flats"
    __table_args__ = (
        UniqueConstraint("block", "flat_number", name="uq_flats_block_flat_number"),
        CheckConstraint("floor_number >= 0", name="ck_flats_floor_non_negative"),
        CheckConstraint("maintenance_due >= 0", name="ck_flats_maintenance_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    block = Column(String(50), nullable=False)
    floor_number = Column(Integer, nullable=False)
    flat_number = Column(Integer, nullable=False)
    status = Column(Enum(FlatStatus), nullable=False, default=FlatStatus.vacant)
    type = Column(
        Enum(
            FlatType,
            name="flat_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    maintenance_due = Column(Numeric(10, 2), nullable=False, default=0)

    residents = relationship("Resident", back_populates="flat")
    visitors = relationship("Visitor", back_populates="flat")
    deliveries = relationship("Delivery", back_populates="flat")
