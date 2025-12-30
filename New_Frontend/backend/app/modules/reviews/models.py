"""
Review model
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)  # Nullable for imported reviews
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    images = Column(JSON, default=list)  # Array of image URLs
    likes = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)  # Verified diner
    visit_date = Column(String(10), nullable=True)  # YYYY-MM-DD or DD/MM/YYYY
    reply_content = Column(Text, nullable=True)
    reply_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Store author name for imported reviews (no user account)
    author_name = Column(String(255), nullable=True)

    # Sentiment scoring (0-100) computed from review content via TextBlob + translation
    sentiment_score = Column(Integer, nullable=True)
    sentiment_polarity = Column(Float, nullable=True)
    sentiment_subjectivity = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    restaurant = relationship("Restaurant", back_populates="reviews")
