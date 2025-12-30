"""
Restaurant report (phản ánh) model
"""

from __future__ import annotations

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class RestaurantReport(Base):
    __tablename__ = "restaurant_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"), nullable=False, index=True)

    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.OPEN, nullable=False)

    owner_response = Column(Text, nullable=True)
    owner_responded_at = Column(DateTime, nullable=True)
    admin_note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    restaurant = relationship("Restaurant")

