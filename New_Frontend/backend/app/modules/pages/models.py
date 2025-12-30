"""
Site page content model (simple CMS)
"""

from __future__ import annotations

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class SitePage(Base):
    __tablename__ = "site_pages"

    slug = Column(String(64), primary_key=True)  # e.g. "policy", "about", "contact"
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    updated_by_user = relationship("User")

