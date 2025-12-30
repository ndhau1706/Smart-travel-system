"""
Restaurant model
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    image = Column(String(500), nullable=True)
    images = Column(JSON, default=list)  # Array of image URLs
    cuisine = Column(String(100), nullable=False, index=True)
    rating = Column(Float, default=0.0)
    rating_override = Column(Float, nullable=True)
    review_count = Column(Integer, default=0)
    price_level = Column(Integer, default=2)  # 1-4: $ to $$$$
    distance = Column(String(20), nullable=True)
    open_time = Column(String(10), default="07:00")
    close_time = Column(String(10), default="22:00")
    is_open = Column(Boolean, default=True)
    specialty = Column(JSON, default=list)  # Array of specialties
    description = Column(Text, nullable=True)
    description_generated = Column(Boolean, default=True)
    address = Column(String(500), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")
    owner = relationship("User", foreign_keys=[owner_id])


class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)  # Price in VND
    original_price = Column(Integer, nullable=True)
    image = Column(String(500), nullable=True)
    category = Column(String(100), nullable=False, index=True)
    is_available = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)
    allergens = Column(JSON, default=list)
    nutrition_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="menu_items")
