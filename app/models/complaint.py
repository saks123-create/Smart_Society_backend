from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from app.database.connection import Base
from app.models.mixins import TimestampMixin

class ComplaintStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class Complaint(Base, TimestampMixin):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    image_path = Column(String(2048), nullable=True)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.open, nullable=False)
    rating = Column(Integer, nullable=True)
    rating_feedback = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    resident = relationship("Resident", back_populates="complaints")
