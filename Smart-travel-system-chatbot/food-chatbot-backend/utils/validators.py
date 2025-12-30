"""
Input Validators - Pydantic models and custom validators

This module provides comprehensive input validation for the API endpoints.
"""

import re
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID


# ============================================================================
# Constants
# ============================================================================

# Maximum lengths
MAX_MESSAGE_LENGTH = 2000
MAX_SESSION_TITLE_LENGTH = 100
MAX_FEEDBACK_LENGTH = 1000
MAX_USERNAME_LENGTH = 50
MAX_EMAIL_LENGTH = 100

# Minimum lengths
MIN_MESSAGE_LENGTH = 1
MIN_PASSWORD_LENGTH = 8

# Valid ranges
MIN_RATING = 1
MAX_RATING = 5
MIN_RESTAURANT_ID = 1
MAX_RESTAURANT_ID = 100000

# Patterns
UUID_PATTERN = re.compile(
    r'^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$',
    re.IGNORECASE
)
SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{10,64}$')
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


# ============================================================================
# Validation Helpers
# ============================================================================

def sanitize_string(value: str) -> str:
    """
    Sanitize a string by removing potentially dangerous characters.
    
    - Removes control characters
    - Trims whitespace
    - Limits consecutive whitespace
    """
    if not value:
        return value
    
    # Remove control characters (except newlines and tabs)
    value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    
    # Normalize whitespace
    value = re.sub(r'[ \t]+', ' ', value)
    value = re.sub(r'\n{3,}', '\n\n', value)
    
    return value.strip()


def validate_no_sql_injection(value: str) -> str:
    """
    Check for common SQL injection patterns.
    
    Note: This is a basic check. The main defense is parameterized queries.
    """
    if not value:
        return value
    
    # Common SQL injection patterns
    dangerous_patterns = [
        r';\s*drop\s+',
        r';\s*delete\s+',
        r';\s*update\s+',
        r';\s*insert\s+',
        r'--\s*$',
        r'/\*.*\*/',
        r'union\s+select',
        r'exec\s*\(',
        r'execute\s*\(',
    ]
    
    lower_value = value.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, lower_value):
            raise ValueError("Invalid input detected")
    
    return value


def validate_no_xss(value: str) -> str:
    """
    Check for common XSS patterns.
    
    Note: This is a basic check. Always escape output as well.
    """
    if not value:
        return value
    
    # Common XSS patterns
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe',
        r'<object',
        r'<embed',
        r'<link',
        r'<style',
    ]
    
    lower_value = value.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, lower_value):
            raise ValueError("Invalid content detected")
    
    return value


# ============================================================================
# Chat Validators
# ============================================================================

class ChatMessageValidator(BaseModel):
    """Validator for chat messages."""
    
    message: str = Field(
        ...,
        min_length=MIN_MESSAGE_LENGTH,
        max_length=MAX_MESSAGE_LENGTH,
        description="The chat message from the user"
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for conversation continuity"
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user ID for personalization"
    )
    language: Optional[str] = Field(
        None,
        pattern=r'^(vi|en|auto)$',
        description="Language preference: vi, en, or auto-detect"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = sanitize_string(v)
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        
        if len(v) < MIN_MESSAGE_LENGTH:
            raise ValueError(f"Message must be at least {MIN_MESSAGE_LENGTH} character(s)")
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"Message must not exceed {MAX_MESSAGE_LENGTH} characters")
        
        return v
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError("Invalid session ID format")
        
        return v
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        # Accept both UUID and legacy format
        if UUID_PATTERN.match(v):
            return v
        if SESSION_ID_PATTERN.match(v):
            return v
        
        raise ValueError("Invalid user ID format")


class StreamingChatRequest(ChatMessageValidator):
    """Validator for streaming chat requests."""
    
    stream: bool = Field(
        True,
        description="Enable streaming response"
    )


# ============================================================================
# Session Validators
# ============================================================================

class SessionCreateValidator(BaseModel):
    """Validator for session creation."""
    
    title: Optional[str] = Field(
        None,
        max_length=MAX_SESSION_TITLE_LENGTH,
        description="Optional session title"
    )
    user_id: Optional[str] = Field(
        None,
        description="User ID to associate with the session"
    )
    metadata: Optional[dict] = Field(
        None,
        description="Optional metadata for the session"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        v = sanitize_string(v)
        v = validate_no_xss(v)
        
        if len(v) > MAX_SESSION_TITLE_LENGTH:
            raise ValueError(f"Title must not exceed {MAX_SESSION_TITLE_LENGTH} characters")
        
        return v


class SessionUpdateValidator(BaseModel):
    """Validator for session updates."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=MAX_SESSION_TITLE_LENGTH,
        description="New session title"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = sanitize_string(v)
        v = validate_no_xss(v)
        
        if not v:
            raise ValueError("Title cannot be empty")
        
        return v


# ============================================================================
# Feedback Validators
# ============================================================================

class FeedbackValidator(BaseModel):
    """Validator for feedback submission."""
    
    session_id: str = Field(
        ...,
        description="Session ID to associate feedback with"
    )
    rating: int = Field(
        ...,
        ge=MIN_RATING,
        le=MAX_RATING,
        description=f"Rating from {MIN_RATING} to {MAX_RATING}"
    )
    feedback: Optional[str] = Field(
        None,
        max_length=MAX_FEEDBACK_LENGTH,
        description="Optional feedback text"
    )
    message_id: Optional[str] = Field(
        None,
        description="Optional message ID for message-specific feedback"
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user ID"
    )
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError("Invalid session ID format")
        return v
    
    @field_validator('feedback')
    @classmethod
    def validate_feedback(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        v = sanitize_string(v)
        v = validate_no_xss(v)
        
        if len(v) > MAX_FEEDBACK_LENGTH:
            raise ValueError(f"Feedback must not exceed {MAX_FEEDBACK_LENGTH} characters")
        
        return v
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if v < MIN_RATING or v > MAX_RATING:
            raise ValueError(f"Rating must be between {MIN_RATING} and {MAX_RATING}")
        return v


class RestaurantFeedbackValidator(BaseModel):
    """Validator for restaurant-specific feedback."""
    
    restaurant_id: int = Field(
        ...,
        ge=MIN_RESTAURANT_ID,
        le=MAX_RESTAURANT_ID,
        description="Restaurant ID"
    )
    rating: int = Field(
        ...,
        ge=MIN_RATING,
        le=MAX_RATING,
        description=f"Rating from {MIN_RATING} to {MAX_RATING}"
    )
    review: Optional[str] = Field(
        None,
        max_length=MAX_FEEDBACK_LENGTH,
        description="Optional review text"
    )
    
    @field_validator('review')
    @classmethod
    def validate_review(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        v = sanitize_string(v)
        v = validate_no_xss(v)
        
        return v


# ============================================================================
# Authentication Validators
# ============================================================================

class UserRegistrationValidator(BaseModel):
    """Validator for user registration."""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=MAX_USERNAME_LENGTH,
        description="Username (3-50 alphanumeric characters)"
    )
    email: str = Field(
        ...,
        max_length=MAX_EMAIL_LENGTH,
        description="Valid email address"
    )
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        description=f"Password (minimum {MIN_PASSWORD_LENGTH} characters)"
    )
    display_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional display name"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        
        if not USERNAME_PATTERN.match(v):
            raise ValueError(
                "Username must be 3-50 characters and contain only "
                "letters, numbers, underscores, and hyphens"
            )
        
        # Check for reserved usernames
        reserved = ['admin', 'root', 'system', 'moderator', 'support']
        if v in reserved:
            raise ValueError("This username is reserved")
        
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Invalid email address format")
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        
        # Check password strength
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)
        
        strength = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength < 2:
            raise ValueError(
                "Password must contain at least 2 of: uppercase, lowercase, "
                "digit, special character"
            )
        
        return v


class UserLoginValidator(BaseModel):
    """Validator for user login."""
    
    username: str = Field(
        ...,
        description="Username or email"
    )
    password: str = Field(
        ...,
        description="Password"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        
        if not v:
            raise ValueError("Username is required")
        
        return v


# ============================================================================
# Search Validators
# ============================================================================

class SearchQueryValidator(BaseModel):
    """Validator for search queries."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query"
    )
    filters: Optional[dict] = Field(
        None,
        description="Optional search filters"
    )
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Maximum number of results"
    )
    offset: int = Field(
        0,
        ge=0,
        description="Result offset for pagination"
    )
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = sanitize_string(v)
        v = validate_no_sql_injection(v)
        
        if not v:
            raise ValueError("Search query cannot be empty")
        
        return v
    
    @field_validator('filters')
    @classmethod
    def validate_filters(cls, v: Optional[dict]) -> Optional[dict]:
        if v is None:
            return v
        
        # Allowed filter keys
        allowed_keys = {
            'district', 'cuisine', 'price_range', 'rating_min',
            'open_now', 'delivery', 'dine_in', 'takeout'
        }
        
        # Remove unknown keys
        return {k: v for k, v in v.items() if k in allowed_keys}


# ============================================================================
# Pagination Validators
# ============================================================================

class PaginationValidator(BaseModel):
    """Validator for pagination parameters."""
    
    page: int = Field(
        1,
        ge=1,
        le=1000,
        description="Page number (1-based)"
    )
    page_size: int = Field(
        20,
        ge=1,
        le=100,
        description="Items per page"
    )
    sort_by: Optional[str] = Field(
        None,
        pattern=r'^[a-zA-Z_]+$',
        description="Field to sort by"
    )
    sort_order: Optional[str] = Field(
        'asc',
        pattern=r'^(asc|desc)$',
        description="Sort order: asc or desc"
    )
    
    @property
    def offset(self) -> int:
        """Calculate offset from page number."""
        return (self.page - 1) * self.page_size
