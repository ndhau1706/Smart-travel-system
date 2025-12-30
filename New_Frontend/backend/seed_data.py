"""
Seed data for development
"""
import asyncio
from app.core.database import AsyncSessionLocal, init_db
from app.core.security import get_password_hash
from app.modules.auth.models import User, UserRole
from app.modules.restaurants.models import Restaurant, MenuItem

# Sample restaurants data
RESTAURANTS_DATA = [
    {
        "name": "Phở Hà Nội",
        "image": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=800",
        "images": [
            "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=800",
            "https://images.unsplash.com/photo-1503764654157-72d979d9af2f?w=800"
        ],
        "cuisine": "Phở & Bún",
        "rating": 4.8,
        "review_count": 234,
        "price_level": 2,
        "open_time": "07:00",
        "close_time": "22:00",
        "specialty": ["Phở Bò", "Phở Gà", "Bún Chả"],
        "description": "Nhà hàng phở truyền thống với công thức nấu nước dùng hơn 50 năm. Phở Hà Nội mang đến hương vị phở đậm đà, nguyên bản từ Hà Thành.",
        "address": "123 Nguyễn Huệ, Quận 1, TP.HCM",
        "phone": "028 3823 4567",
        "latitude": 10.7769,
        "longitude": 106.7009,
        "menu": [
            {"name": "Phở Bò Tái", "description": "Phở bò tái mềm với nước dùng đậm đà", "price": 65000, "category": "Phở", "is_popular": True},
            {"name": "Phở Bò Chín", "description": "Phở bò chín với thịt bò mềm", "price": 70000, "category": "Phở"},
            {"name": "Phở Gà", "description": "Phở gà thanh ngọt với thịt gà thơm ngon", "price": 60000, "category": "Phở"},
            {"name": "Bún Chả Hà Nội", "description": "Bún chả với thịt nướng thơm phức", "price": 75000, "category": "Bún", "is_popular": True},
        ]
    },
    {
        "name": "Bánh Mì Sài Gòn",
        "image": "https://images.unsplash.com/photo-1600688640154-9619e002df30?w=800",
        "images": [],
        "cuisine": "Bánh mì & Đồ ăn sáng",
        "rating": 4.6,
        "review_count": 189,
        "price_level": 1,
        "open_time": "06:00",
        "close_time": "14:00",
        "specialty": ["Bánh Mì Thịt", "Bánh Mì Chả", "Bánh Mì Pate"],
        "description": "Bánh mì Sài Gòn giòn tan với nhiều loại nhân đa dạng. Sử dụng bánh mì nướng tươi mỗi ngày và nguyên liệu tươi ngon.",
        "address": "45 Pasteur, Quận 1, TP.HCM",
        "phone": "028 3829 1234",
        "latitude": 10.7756,
        "longitude": 106.6995,
        "menu": [
            {"name": "Bánh Mì Thịt Nướng", "description": "Bánh mì với thịt nướng thơm lừng", "price": 25000, "category": "Bánh mì", "is_popular": True},
            {"name": "Bánh Mì Pate", "description": "Bánh mì pate truyền thống", "price": 20000, "category": "Bánh mì"},
            {"name": "Bánh Mì Chả Cá", "description": "Bánh mì chả cá Nha Trang", "price": 30000, "category": "Bánh mì"},
        ]
    },
    {
        "name": "Nhà Hàng Hải Sản Biển Xanh",
        "image": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=800",
        "images": [],
        "cuisine": "Hải sản",
        "rating": 4.5,
        "review_count": 156,
        "price_level": 3,
        "open_time": "10:00",
        "close_time": "23:00",
        "specialty": ["Tôm Hùm", "Cua Rang Me", "Nghêu Hấp"],
        "description": "Nhà hàng hải sản cao cấp với nguồn hải sản tươi sống từ các vùng biển Việt Nam.",
        "address": "789 Võ Văn Tần, Quận 3, TP.HCM",
        "phone": "028 3930 5678",
        "latitude": 10.7731,
        "longitude": 106.6899,
        "menu": [
            {"name": "Tôm Hùm Nướng", "description": "Tôm hùm nướng bơ tỏi", "price": 850000, "category": "Hải sản", "is_popular": True},
            {"name": "Cua Rang Me", "description": "Cua biển rang me chua ngọt", "price": 450000, "category": "Hải sản"},
            {"name": "Nghêu Hấp Sả", "description": "Nghêu hấp sả ớt", "price": 120000, "category": "Hải sản"},
        ]
    },
    {
        "name": "Cơm Tấm Thuận Kiều",
        "image": "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=800",
        "images": [],
        "cuisine": "Cơm Việt Nam",
        "rating": 4.7,
        "review_count": 312,
        "price_level": 1,
        "open_time": "06:00",
        "close_time": "21:00",
        "specialty": ["Cơm Tấm Sườn", "Cơm Tấm Bì", "Cơm Tấm Chả"],
        "description": "Cơm tấm Sài Gòn đúng điệu với sườn nướng than hồng, bì giòn và chả trứng thơm ngon.",
        "address": "234 Phan Xích Long, Phú Nhuận, TP.HCM",
        "phone": "028 3845 9999",
        "latitude": 10.7985,
        "longitude": 106.6812,
        "menu": [
            {"name": "Cơm Tấm Sườn Bì Chả", "description": "Cơm tấm đầy đủ với sườn, bì, chả", "price": 55000, "category": "Cơm", "is_popular": True},
            {"name": "Cơm Tấm Sườn", "description": "Cơm tấm với sườn nướng", "price": 45000, "category": "Cơm"},
            {"name": "Cơm Tấm Bì Chả", "description": "Cơm tấm với bì và chả trứng", "price": 40000, "category": "Cơm"},
        ]
    },
    {
        "name": "Lẩu Thái Sawadee",
        "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800",
        "images": [],
        "cuisine": "Lẩu & Nướng",
        "rating": 4.4,
        "review_count": 98,
        "price_level": 2,
        "open_time": "11:00",
        "close_time": "22:00",
        "specialty": ["Lẩu Thái", "Lẩu Hải Sản", "Nướng BBQ"],
        "description": "Nhà hàng lẩu Thái đích thực với hương vị chua cay đặc trưng và không gian ấm cúng.",
        "address": "567 Nguyễn Đình Chiểu, Quận 3, TP.HCM",
        "phone": "028 3833 7890",
        "latitude": 10.7812,
        "longitude": 106.6912,
        "menu": [
            {"name": "Lẩu Thái Tom Yum", "description": "Lẩu Thái chua cay truyền thống", "price": 280000, "category": "Lẩu", "is_popular": True},
            {"name": "Lẩu Hải Sản", "description": "Lẩu hải sản tươi sống", "price": 350000, "category": "Lẩu"},
            {"name": "Set Nướng BBQ", "description": "Set nướng hỗn hợp cho 2-3 người", "price": 320000, "category": "Nướng"},
        ]
    }
]

USERS_DATA = [
    {
        "email": "admin@smarttravel.vn",
        "name": "Admin",
        "password": "admin123",
        "role": UserRole.ADMIN,
        "is_verified": True
    },
    {
        "email": "user@example.com",
        "name": "Nguyễn Văn A",
        "phone": "0912345678",
        "password": "user123",
        "role": UserRole.USER,
        "is_verified": True
    }
]


async def seed_database():
    """Seed database with sample data"""
    print("🌱 Seeding database...")
    
    await init_db()
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if already seeded
            from sqlalchemy import select
            existing = await db.execute(select(User).limit(1))
            if existing.scalar_one_or_none():
                print("⚠️  Database already has data. Skipping seed.")
                return
            
            # Create users
            print("👤 Creating users...")
            for user_data in USERS_DATA:
                user = User(
                    email=user_data["email"],
                    name=user_data["name"],
                    phone=user_data.get("phone"),
                    hashed_password=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    is_verified=user_data["is_verified"]
                )
                db.add(user)
            
            await db.flush()
            
            # Create restaurants and menu items
            print("🍜 Creating restaurants...")
            for rest_data in RESTAURANTS_DATA:
                menu_items = rest_data.pop("menu", [])
                
                restaurant = Restaurant(**rest_data)
                db.add(restaurant)
                await db.flush()
                
                # Add menu items
                for item_data in menu_items:
                    menu_item = MenuItem(
                        restaurant_id=restaurant.id,
                        image=rest_data["image"],
                        **item_data
                    )
                    db.add(menu_item)
            
            await db.commit()
            print("✅ Database seeded successfully!")
            print(f"   - {len(USERS_DATA)} users created")
            print(f"   - {len(RESTAURANTS_DATA)} restaurants created")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
