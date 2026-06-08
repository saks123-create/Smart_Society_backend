from sqlalchemy import Column, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship

from app.database.connection import Base
from app.models.mixins import TimestampMixin


class AdminAuditLog(Base, TimestampMixin):
    __tablename__ = "admin_audit_logs"
    __table_args__ = (
        Index("ix_admin_audit_logs_actor_user_id", "actor_user_id"),
        Index("ix_admin_audit_logs_target_type_target_id", "target_type", "target_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(100), nullable=False)
    target_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)

    actor = relationship("User")
