"""
Import restaurants from hcm_restaurants_with_local_images.json
"""
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal, engine, Base
from app.modules.auth.models import User
from app.modules.restaurants.models import Restaurant, MenuItem
from app.modules.reviews.models import Review
from app.core.security import get_password_hash


def parse_price_level(price_level: str | None) -> int:
    """Convert price level string to integer (1-4)"""
    if not price_level:
        return 2
    mapping = {
        "PRICE_LEVEL_FREE": 1,
        "PRICE_LEVEL_INEXPENSIVE": 1,
        "PRICE_LEVEL_MODERATE": 2,
        "PRICE_LEVEL_EXPENSIVE": 3,
        "PRICE_LEVEL_VERY_EXPENSIVE": 4
    }
    return mapping.get(price_level, 2)


def parse_opening_hours(opening_hours: dict | None) -> tuple[str, str]:
    """Extract open and close time from opening hours"""
    if not opening_hours:
        return "07:00", "22:00"
    
    # Get first day's hours
    for day, hours in opening_hours.items():
        if hours and "–" in hours:
            parts = hours.split("–")
            open_time = parts[0].strip()[:5]  # Get HH:MM
            close_time = parts[1].strip()[:5]
            return open_time, close_time
    
    return "07:00", "22:00"


def extract_cuisine_from_category(category: str | None, food_tags: list | None) -> str:
    """Extract cuisine type from category and food tags"""
    if food_tags:
        # Map food tags to cuisine
        tag_to_cuisine = {
            "phở": "Phở & Bún",
            "bún": "Phở & Bún",
            "bánh mì": "Bánh mì",
            "cơm": "Cơm Việt Nam",
            "hải sản": "Hải sản",
            "lẩu": "Lẩu & Nướng",
            "nướng": "Lẩu & Nướng",
            "chay": "Chay",
            "bình dân": "Bình dân",
            "kem": "Tráng miệng",
            "café": "Cafe & Đồ uống",
            "cafe": "Cafe & Đồ uống",
            "trà": "Cafe & Đồ uống"
        }
        
        for tag in food_tags:
            tag_lower = tag.lower()
            for key, cuisine in tag_to_cuisine.items():
                if key in tag_lower:
                    return cuisine
    
    if category:
        if "cafe" in category.lower() or "cà phê" in category.lower():
            return "Cafe & Đồ uống"
        if "nhà hàng" in category.lower():
            return "Nhà hàng Việt"
    
    return "Ẩm thực Việt Nam"


def build_restaurant_description(
    cuisine: str | None,
    price_level: int | None,
    open_time: str | None,
    close_time: str | None,
    specialty: list | None,
) -> str:
    cuisine_label = (cuisine or "").strip() if isinstance(cuisine, str) else ""
    if not cuisine_label:
        cuisine_label = "Nhà hàng"

    parts: list[str] = [cuisine_label]

    open_str = (open_time or "").strip() if isinstance(open_time, str) else ""
    close_str = (close_time or "").strip() if isinstance(close_time, str) else ""
    if open_str and close_str:
        parts.append(f"Giờ mở cửa {open_str} - {close_str}")

    if isinstance(price_level, int) and 1 <= price_level <= 4:
        parts.append(f"Mức giá {'$' * price_level}")

    if isinstance(specialty, list):
        tags = [str(item).strip() for item in specialty if item]
        tags = [t for t in tags if t]
        # Dedupe + limit
        uniq: list[str] = []
        for t in tags:
            if t not in uniq:
                uniq.append(t)
            if len(uniq) >= 4:
                break
        if uniq:
            parts.append(f"Nổi bật: {', '.join(uniq)}")

    return " • ".join(parts)


async def import_restaurants():
    """Import restaurants from JSON file"""
    # Read JSON file
    json_path = Path(__file__).parent.parent / "hcm_restaurants_with_local_images.json"
    
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        return
    
    print(f"📖 Reading {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        restaurants_data = json.load(f)
    
    print(f"📊 Found {len(restaurants_data)} restaurants")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if data already exists
            existing = await db.execute(select(Restaurant).limit(1))
            if existing.scalar():
                print("⚠️  Database already has restaurants. Clearing...")
                await db.execute(Restaurant.__table__.delete())
                await db.execute(Review.__table__.delete())
                await db.commit()
            
            # Ensure we have users for reviews
            users_result = await db.execute(select(User))
            users = users_result.scalars().all()
            
            if not users:
                print("👤 Creating sample users...")
                admin_user = User(
                    id=str(uuid.uuid4()),
                    email="admin@smarttravel.vn",
                    name="Admin",
                    hashed_password=get_password_hash("admin123"),
                    role="admin",
                    is_verified=True,
                    is_active=True
                )
                regular_user = User(
                    id=str(uuid.uuid4()),
                    email="user@example.com",
                    name="Nguyễn Văn A",
                    phone="0912345678",
                    hashed_password=get_password_hash("user123"),
                    role="user",
                    is_verified=True,
                    is_active=True
                )
                db.add_all([admin_user, regular_user])
                await db.flush()
                users = [admin_user, regular_user]
            
            # Import restaurants
            print("🍜 Importing restaurants...")
            imported_count = 0
            review_count = 0
            
            for idx, data in enumerate(restaurants_data):
                if not data.get("success", True):
                    continue
                
                # Parse opening hours
                open_time, close_time = parse_opening_hours(data.get("opening_hours"))
                
                # Get images - prefer hosted_images, fallback to images
                images = data.get("hosted_images", []) or data.get("images", [])
                main_image = images[0] if images else None
                
                # Create restaurant
                cuisine = extract_cuisine_from_category(
                    data.get("category"),
                    data.get("food_tags"),
                )
                specialty = data.get("food_tags", [])

                restaurant = Restaurant(
                    id=str(uuid.uuid4()),
                    name=data.get("name", "Unknown"),
                    image=main_image,
                    images=images[:5],  # Limit to 5 images
                    cuisine=cuisine,
                    rating=float(data.get("rating", 0)) if data.get("rating") else 0.0,
                    review_count=data.get("rating_count", 0) or 0,
                    price_level=parse_price_level(data.get("price_level")),
                    open_time=open_time,
                    close_time=close_time,
                    is_open=True,
                    specialty=specialty,
                    description=build_restaurant_description(
                        cuisine=cuisine,
                        price_level=parse_price_level(data.get("price_level")),
                        open_time=open_time,
                        close_time=close_time,
                        specialty=specialty,
                    ),
                    description_generated=True,
                    address=data.get("address", ""),
                    phone=data.get("phone"),
                    email=None,
                    website=data.get("website") if data.get("website") and not data.get("website", "").startswith("https://drive.google") else None,
                    latitude=data.get("coordinates", {}).get("lat"),
                    longitude=data.get("coordinates", {}).get("lon"),
                    is_active=True
                )

                comments = data.get("comments", [])
                
                db.add(restaurant)
                imported_count += 1
                
                # Import reviews from comments
                for comment in comments[:5]:  # Limit to 5 reviews per restaurant
                    if not comment.get("text"):
                        continue
                    
                    # Use random user for review
                    import random
                    review_user = random.choice(users)
                    
                    review = Review(
                        id=str(uuid.uuid4()),
                        user_id=review_user.id,
                        restaurant_id=restaurant.id,
                        rating=int(comment.get("rating", 4)),
                        title=comment.get("author", "Review"),
                        content=comment.get("text", ""),
                        is_verified=True,
                        visit_date=None
                    )
                    db.add(review)
                    review_count += 1
                
                # Progress indicator
                if (idx + 1) % 50 == 0:
                    print(f"   Processed {idx + 1}/{len(restaurants_data)}...")
                    await db.flush()
            
            await db.commit()
            print(f"✅ Successfully imported {imported_count} restaurants and {review_count} reviews!")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error importing: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(import_restaurants())
