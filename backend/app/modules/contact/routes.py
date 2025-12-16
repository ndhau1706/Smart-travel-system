"""
Contact & Search API routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import uuid

from app.core.database import get_db
from app.modules.restaurants.models import Restaurant, MenuItem
from app.modules.contact.schemas import ContactFormRequest, ContactFormResponse, ContactType
from app.shared.schemas import success_response

router = APIRouter(tags=["Contact & Search"])


# Contact routes
@router.post("/contact", response_model=dict)
async def submit_contact_form(request: ContactFormRequest):
    """Submit contact form"""
    # In production, save to database and send email
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
    return success_response(
        data={
            "ticket_id": ticket_id,
            "message": "Cảm ơn bạn đã liên hệ. Chúng tôi sẽ phản hồi trong vòng 24 giờ."
        },
        message="Gửi liên hệ thành công"
    )


# Search routes
@router.get("/search", response_model=dict)
async def global_search(
    query: str = Query(..., min_length=1),
    type: str = Query("all", regex="^(all|restaurants|dishes)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Global search for restaurants and dishes"""
    restaurants = []
    dishes = []
    
    if type in ["all", "restaurants"]:
        rest_query = select(Restaurant).where(
            Restaurant.is_active == True,
            or_(
                Restaurant.name.ilike(f"%{query}%"),
                Restaurant.cuisine.ilike(f"%{query}%"),
                Restaurant.description.ilike(f"%{query}%")
            )
        ).order_by(Restaurant.rating.desc()).limit(limit)
        
        result = await db.execute(rest_query)
        restaurants = [{
            "id": r.id,
            "name": r.name,
            "cuisine": r.cuisine,
            "rating": r.rating,
            "image": r.image
        } for r in result.scalars().all()]
    
    if type in ["all", "dishes"]:
        dish_query = select(MenuItem).where(
            MenuItem.is_available == True,
            MenuItem.is_approved == True,
            or_(
                MenuItem.name.ilike(f"%{query}%"),
                MenuItem.description.ilike(f"%{query}%"),
                MenuItem.category.ilike(f"%{query}%")
            )
        ).limit(limit)
        
        result = await db.execute(dish_query)
        dishes = [{
            "id": m.id,
            "restaurant_id": m.restaurant_id,
            "name": m.name,
            "price": m.price,
            "image": m.image
        } for m in result.scalars().all()]
    
    return success_response(
        data={
            "restaurants": restaurants,
            "dishes": dishes,
            "total_results": len(restaurants) + len(dishes)
        },
        message="Tìm kiếm thành công"
    )
