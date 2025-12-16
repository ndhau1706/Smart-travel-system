"""
User model
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    RESTAURANT_OWNER = "restaurant_owner"


class OtpPurpose(str, enum.Enum):
    REGISTER = "register"
    RESET_PASSWORD = "reset_password"


class EmailOtp(Base):
    __tablename__ = "email_otps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), index=True, nullable=False)
    purpose = Column(Enum(OtpPurpose), index=True, nullable=False)
    code_hash = Column(String(128), nullable=False)
    payload_json = Column(Text, nullable=True)

    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)

    resend_window_started_at = Column(DateTime, nullable=True)
    resend_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    avatar = Column(String(500), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviews = relationship("Review", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
