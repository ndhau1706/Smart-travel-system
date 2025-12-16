"""
Booking schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


# Request Schemas
class CreateBookingRequest(BaseModel):
    restaurant_id: str
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # HH:MM
    guests: int = Field(..., ge=1, le=50)
    customer_name: str = Field(..., min_length=2)
    customer_phone: str
    customer_email: Optional[EmailStr] = None
    special_requests: Optional[str] = None


class UpdateBookingRequest(BaseModel):
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    guests: Optional[int] = Field(None, ge=1, le=50)
    special_requests: Optional[str] = None


class CancelBookingRequest(BaseModel):
    reason: Optional[str] = None


class UpdateBookingStatusRequest(BaseModel):
    status: BookingStatus
    cancel_reason: Optional[str] = None


# Response Schemas
class BookingResponse(BaseModel):
    id: str
    user_id: str
    restaurant_id: str
    restaurant_name: Optional[str] = None
    restaurant_address: Optional[str] = None
    restaurant_phone: Optional[str] = None
    restaurant_image: Optional[str] = None
    date: str
    time: str
    guests: int
    status: BookingStatus
    special_requests: Optional[str] = None
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    confirmation_code: Optional[str] = None
    cancel_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Query Params
class BookingQueryParams(BaseModel):
    page: int = 1
    limit: int = 10
    status: Optional[BookingStatus] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
