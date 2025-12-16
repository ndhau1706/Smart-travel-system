"""
User schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    RESTAURANT_OWNER = "restaurant_owner"


# Request Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    remember_me: bool = False


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Response Schemas
class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    role: UserRole
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int  # seconds


class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    expires_in: int


class RegisterResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    expires_in: int
