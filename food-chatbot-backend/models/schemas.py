"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Chat request model."""
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    user_location: Optional[Dict[str, float]] = Field(None, description="User's location with 'lat' and 'lon' keys")

class RestaurantInfo(BaseModel):
    """Restaurant information model."""
    id: Optional[int] = None
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    price_level: Optional[str] = None
    food_tags: Optional[List[str]] = None
    coordinates_lat: Optional[float] = None
    coordinates_lon: Optional[float] = None
    distance: Optional[float] = None
    distance_text: Optional[str] = None
    relevance_score: Optional[float] = None
    trending_score: Optional[float] = None
    is_open: Optional[bool] = None
    open_status: Optional[str] = None
    badges: Optional[List[str]] = None
    signature_dishes: Optional[List[str]] = None
    review_insights: Optional[str] = None
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    session_id: str
    message: str
    restaurants: Optional[List[RestaurantInfo]] = None
    language: str
    explanation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionCreate(BaseModel):
    """Session creation request."""
    user_id: Optional[str] = None
    title: Optional[str] = "New Chat"
    language: Optional[str] = "vi"


class SessionInfo(BaseModel):
    """Session information."""
    id: str
    user_id: Optional[str] = None
    title: str
    language: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0


class MessageInfo(BaseModel):
    """Message information."""
    id: int
    session_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class FeedbackRequest(BaseModel):
    """User feedback request."""
    session_id: str
    message_id: Optional[int] = None
    restaurant_id: Optional[int] = None
    feedback_type: str = Field(..., pattern="^(positive|negative|neutral)$")
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response."""
    success: bool
    message: str


class SessionListResponse(BaseModel):
    """Session list response."""
    sessions: List[SessionInfo]
    total: int


class SessionHistoryResponse(BaseModel):
    """Session history response."""
    session: SessionInfo
    messages: List[MessageInfo]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
