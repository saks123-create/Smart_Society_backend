from sqlalchemy import Column, Integer, String, Boolean, Enum, CheckConstraint
import enum
from app.database.connection import Base
from app.models.mixins import TimestampMixin

class UserRole(str, enum.Enum):
    admin = "admin"
    resident = "resident"
    security = "security"

class UserStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"

class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "(role = 'resident' AND status IS NOT NULL) OR (role != 'resident' AND status IS NULL)",
            name="ck_users_status_resident_only",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), nullable=True, default=None)
    is_active = Column(Boolean, default=True)
