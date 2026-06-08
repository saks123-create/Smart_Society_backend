from sqlalchemy import Column, Integer, String, Boolean, Text
from app.database.connection import Base
from app.models.mixins import TimestampMixin

class Settings(Base, TimestampMixin):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    society_name = Column(String(255), nullable=False)
    society_address = Column(String(255), nullable=False)
    society_phone = Column(String(50), nullable=False)
    society_email = Column(String(255), nullable=False)
    admin_name = Column(String(255), nullable=False)
    admin_email = Column(String(255), nullable=False)
    admin_phone = Column(String(50), nullable=False)
    notify_visitors = Column(Boolean, default=True, nullable=False)
    notify_complaints = Column(Boolean, default=True, nullable=False)
    notify_notices = Column(Boolean, default=True, nullable=False)
    policy_text = Column(Text, nullable=True)
