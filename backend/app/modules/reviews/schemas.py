"""
Review schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ReviewReply(BaseModel):
    content: str
    created_at: datetime
    restaurant_name: str


# Request Schemas
class CreateReviewRequest(BaseModel):
    restaurant_id: str
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    content: str = Field(..., min_length=10)
    images: List[str] = []
    visit_date: Optional[str] = None


class UpdateReviewRequest(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = None
    content: Optional[str] = Field(None, min_length=10)
    images: Optional[List[str]] = None


# Response Schemas
class ReviewResponse(BaseModel):
    id: str
    user_id: Optional[str] = None  # Can be null for imported reviews
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    author_name: Optional[str] = None  # For imported reviews without user account
    restaurant_id: str
    restaurant_name: Optional[str] = None
    rating: int
    title: Optional[str] = None
    content: str
    images: List[str] = []
    likes: int = 0
    sentiment_score: Optional[int] = None  # 0-100
    sentiment_polarity: Optional[float] = None  # -1..1 (TextBlob)
    sentiment_subjectivity: Optional[float] = None  # 0..1 (TextBlob)
    is_verified: bool = False
    visit_date: Optional[str] = None
    reply: Optional[ReviewReply] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Query Params
class ReviewQueryParams(BaseModel):
    page: int = 1
    limit: int = 10
    rating: Optional[int] = None
    sort_by: Optional[str] = "date"  # date, rating, likes
    sort_order: Optional[str] = "desc"
