"""
Restaurant schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GeoLocation(BaseModel):
    lat: float
    lng: float


class NutritionInfo(BaseModel):
    calories: Optional[int] = None
    protein: Optional[int] = None
    carbs: Optional[int] = None
    fat: Optional[int] = None


# Menu Item Schemas
class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: int
    original_price: Optional[int] = None
    image: Optional[str] = None
    category: str
    is_available: bool = True
    is_popular: bool = False
    allergens: List[str] = []
    nutrition_info: Optional[NutritionInfo] = None


class MenuItemCreate(MenuItemBase):
    restaurant_id: str


class MenuItemResponse(MenuItemBase):
    id: str
    restaurant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Restaurant Schemas
class RestaurantBase(BaseModel):
    name: str
    image: Optional[str] = None
    images: List[str] = []
    cuisine: str
    price_level: int = Field(2, ge=1, le=4)
    open_time: str = "07:00"
    close_time: str = "22:00"
    specialty: List[str] = []
    description: Optional[str] = None
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class RestaurantCreate(RestaurantBase):
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RestaurantCreateRequest(RestaurantCreate):
    owner_id: Optional[str] = None
    is_active: Optional[bool] = None


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    image: Optional[str] = None
    images: Optional[List[str]] = None
    cuisine: Optional[str] = None
    price_level: Optional[int] = Field(None, ge=1, le=4)
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    specialty: Optional[List[str]] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RestaurantResponse(RestaurantBase):
    id: str
    rating: float = 0.0
    review_count: int = 0
    distance: Optional[str] = None
    is_open: bool = True
    location: Optional[GeoLocation] = None
    menu: List[MenuItemResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RestaurantListResponse(RestaurantBase):
    id: str
    rating: float = 0.0
    review_count: int = 0
    distance: Optional[str] = None
    is_open: bool = True
    
    class Config:
        from_attributes = True


# Query Params
class RestaurantQueryParams(BaseModel):
    page: int = 1
    limit: int = 10
    search: Optional[str] = None
    cuisine: Optional[str] = None
    price_level: Optional[int] = None
    rating: Optional[float] = None
    sort_by: Optional[str] = "rating"  # rating, distance, price, name
    sort_order: Optional[str] = "desc"  # asc, desc
