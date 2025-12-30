"""
Contact schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class ContactType(str, Enum):
    GENERAL = "general"
    FEEDBACK = "feedback"
    COMPLAINT = "complaint"
    PARTNERSHIP = "partnership"


# Request Schemas
class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str
    type: ContactType = ContactType.GENERAL


# Response Schemas
class ContactFormResponse(BaseModel):
    ticket_id: str
    message: str
