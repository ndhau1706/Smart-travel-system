"""
Reports (phản ánh) schemas
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ReportStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class CreateReportRequest(BaseModel):
    restaurant_id: str
    title: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=10, max_length=5000)


class RespondReportRequest(BaseModel):
    response: str = Field(..., min_length=2, max_length=5000)
    status: Optional[ReportStatus] = None


class UpdateReportStatusRequest(BaseModel):
    status: ReportStatus
    admin_note: Optional[str] = Field(None, max_length=5000)


class ReportResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    restaurant_id: str
    restaurant_name: Optional[str] = None
    title: Optional[str] = None
    content: str
    status: ReportStatus
    owner_response: Optional[str] = None
    owner_responded_at: Optional[datetime] = None
    admin_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

