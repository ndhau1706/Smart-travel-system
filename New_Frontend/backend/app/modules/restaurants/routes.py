"""
Restaurant API routes
"""
import json
import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus
from fastapi import APIRouter, Depends, Query, UploadFile, File
from starlette.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.core.database import get_db
from app.core.deps import require_admin, require_admin_or_owner
from app.modules.restaurants.models import Restaurant, MenuItem
from app.modules.restaurants.schemas import (
    RestaurantResponse,
    RestaurantListResponse,
    MenuItemResponse,
    RestaurantCreateRequest,
    RestaurantUpdate,
    MenuItemBase,
)
from app.shared.schemas import success_response, error_response, paginated_response
from app.modules.auth.models import User, UserRole

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "smart-travel-images-2025")
GCS_RESTAURANTS_PREFIX = os.environ.get("GCS_RESTAURANTS_PREFIX", "restaurants")
GCS_RESTAURANTS_BASE = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{GCS_RESTAURANTS_PREFIX}/"


def _google_maps_url(
    place_id: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    query: Optional[str] = None,
) -> str:
    # Prefer "place" action when we have a place_id to open the exact listing reliably.
    # See: https://developers.google.com/maps/documentation/urls/get-started#place-action
    if place_id and query:
        return (
            "https://www.google.com/maps/search/?api=1"
            f"&query={quote_plus(str(query))}"
            f"&query_place_id={quote_plus(str(place_id))}"
        )
    if place_id:
        return f"https://www.google.com/maps/search/?api=1&query=place_id:{quote_plus(str(place_id))}"
    if query:
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(str(query))}"
    if lat is not None and lng is not None:
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
    return ""


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if not item or not isinstance(item, str):
            continue
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _guess_gcs_images(restaurant_id: str, count: int = 3) -> list[str]:
    return [f"{GCS_RESTAURANTS_BASE}{restaurant_id}_{i:02d}.jpg" for i in range(1, count + 1)]


@lru_cache(maxsize=1)
def _load_places_photo_index() -> dict[str, list[str]]:
    path = Path(__file__).resolve().parents[3] / "places_photo_index.json"
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return raw if isinstance(raw, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def _indexed_gcs_images(restaurant_id: str) -> list[str]:
    index = _load_places_photo_index()
    items = index.get(restaurant_id)
    if not isinstance(items, list) or not items:
        return []
    filenames: list[str] = []
    for item in items:
        if not isinstance(item, str):
            continue
        normalized = item.replace("\\", "/")
        name = normalized.split("/")[-1].strip()
        if name:
            filenames.append(name)
    return [f"{GCS_RESTAURANTS_BASE}{name}" for name in filenames]


def _maybe_guess_gcs_images(restaurant_id: str, image: Optional[str]) -> list[str]:
    if not image or not isinstance(image, str):
        return []
    if not image.startswith(GCS_RESTAURANTS_BASE):
        return []
    if f"{restaurant_id}_" not in image:
        return []
    # Only guess when we already have at least one GCS image for this restaurant.
    return _guess_gcs_images(restaurant_id, 3)


def _augment_images(restaurant_id: str, image: Optional[str], images: Optional[list[str]]) -> tuple[Optional[str], list[str]]:
    merged = _dedupe_keep_order([
        *( [image] if image else [] ),
        *(images or []),
        *_indexed_gcs_images(restaurant_id),
        *_maybe_guess_gcs_images(restaurant_id, image),
    ])
    main = merged[0] if merged else image
    return main, merged


async def _get_restaurant_for_manage(
    restaurant_id: str, user: User, db: AsyncSession
) -> Optional[Restaurant]:
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        return None
    if user.role == UserRole.ADMIN:
        return restaurant
    if restaurant.owner_id != user.id:
        return None
    return restaurant


@router.get("", response_model=dict)
async def get_restaurants(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    cuisine: Optional[str] = None,
    price_level: Optional[int] = Query(None, ge=1, le=4),
    rating: Optional[float] = Query(None, ge=0, le=5),
    sort_by: Optional[str] = Query("rating", regex="^(rating|price|name)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of restaurants with filters"""
    query = select(Restaurant).where(Restaurant.is_active == True)
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                Restaurant.name.ilike(f"%{search}%"),
                Restaurant.description.ilike(f"%{search}%"),
                Restaurant.cuisine.ilike(f"%{search}%")
            )
        )
    
    if cuisine:
        query = query.where(Restaurant.cuisine.ilike(f"%{cuisine}%"))
    
    if price_level:
        query = query.where(Restaurant.price_level == price_level)
    
    if rating:
        query = query.where(Restaurant.rating >= rating)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply sorting
    if sort_by == "rating":
        order_col = Restaurant.rating
    elif sort_by == "price":
        order_col = Restaurant.price_level
    else:
        order_col = Restaurant.name
    
    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    restaurants = result.scalars().all()

    payload = []
    for r in restaurants:
        item = RestaurantListResponse.model_validate(r).model_dump()
        main, imgs = _augment_images(item["id"], item.get("image"), item.get("images"))
        item["image"] = main
        item["images"] = imgs
        item["google_maps_url"] = _google_maps_url(
            item.get("id") or "",
            r.latitude,
            r.longitude,
            f"{r.name or ''} {r.address or ''}".strip() or None,
        )
        payload.append(item)

    return paginated_response(
        data=payload,
        total=total,
        page=page,
        limit=limit,
        message="Lấy danh sách nhà hàng thành công"
    )


@router.get("/search", response_model=dict)
async def search_restaurants(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search restaurants by name, cuisine, or description"""
    query = select(Restaurant).where(
        Restaurant.is_active == True,
        or_(
            Restaurant.name.ilike(f"%{q}%"),
            Restaurant.description.ilike(f"%{q}%"),
            Restaurant.cuisine.ilike(f"%{q}%")
        )
    ).order_by(Restaurant.rating.desc()).limit(limit)
    
    result = await db.execute(query)
    restaurants = result.scalars().all()
    
    payload = []
    for r in restaurants:
        item = RestaurantListResponse.model_validate(r).model_dump()
        main, imgs = _augment_images(item["id"], item.get("image"), item.get("images"))
        item["image"] = main
        item["images"] = imgs
        item["google_maps_url"] = _google_maps_url(
            item.get("id") or "",
            r.latitude,
            r.longitude,
            f"{r.name or ''} {r.address or ''}".strip() or None,
        )
        payload.append(item)

    return success_response(
        data=payload,
        message="Tìm kiếm thành công"
    )


@router.get("/mine", response_model=dict)
async def get_my_restaurants(
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get restaurants owned by the current restaurant_owner (or all for admin)."""
    query = select(Restaurant)
    if user.role != UserRole.ADMIN:
        query = query.where(Restaurant.owner_id == user.id)

    result = await db.execute(query.order_by(Restaurant.updated_at.desc()))
    restaurants = result.scalars().all()

    payload = []
    for r in restaurants:
        item = RestaurantListResponse.model_validate(r).model_dump()
        main, imgs = _augment_images(item["id"], item.get("image"), item.get("images"))
        item["image"] = main
        item["images"] = imgs
        item["google_maps_url"] = _google_maps_url(
            item.get("id") or "",
            r.latitude,
            r.longitude,
            f"{r.name or ''} {r.address or ''}".strip() or None,
        )
        payload.append(item)

    return success_response(data=payload, message="OK")


@router.post("", response_model=dict)
async def create_restaurant(
    request: RestaurantCreateRequest,
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    """Create a restaurant (admin/owner). Owner-created restaurants require admin approval."""
    owner_id = None
    is_active = True

    if user.role == UserRole.ADMIN:
        owner_id = request.owner_id
        is_active = request.is_active if request.is_active is not None else True
    else:
        owner_id = user.id
        is_active = False

    description_generated = True
    if isinstance(request.description, str) and request.description.strip():
        description_generated = False

    restaurant = Restaurant(
        name=request.name,
        owner_id=owner_id,
        image=request.image,
        images=request.images,
        cuisine=request.cuisine,
        price_level=request.price_level,
        open_time=request.open_time,
        close_time=request.close_time,
        specialty=request.specialty,
        description=request.description,
        description_generated=description_generated,
        address=request.address,
        phone=request.phone,
        email=request.email,
        website=request.website,
        latitude=request.latitude,
        longitude=request.longitude,
        is_active=is_active,
        is_open=True,
    )

    db.add(restaurant)
    await db.flush()
    await db.refresh(restaurant)

    data = RestaurantResponse.model_validate(restaurant).model_dump()
    main, imgs = _augment_images(data["id"], data.get("image"), data.get("images"))
    data["image"] = main
    data["images"] = imgs

    message = "Tạo nhà hàng thành công"
    if user.role != UserRole.ADMIN:
        message = "Đã gửi yêu cầu tạo nhà hàng, chờ Admin phê duyệt"

    return success_response(data=data, message=message)


@router.put("/{restaurant_id}", response_model=dict)
async def update_restaurant(
    restaurant_id: str,
    request: RestaurantUpdate,
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    """Update restaurant info (admin/owner)."""
    restaurant = await _get_restaurant_for_manage(restaurant_id, user, db)
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng hoặc không có quyền")

    if request.name is not None:
        restaurant.name = request.name
    if request.image is not None:
        restaurant.image = request.image
    if request.images is not None:
        restaurant.images = request.images
    if request.cuisine is not None:
        restaurant.cuisine = request.cuisine
    if request.price_level is not None:
        restaurant.price_level = request.price_level
    if request.open_time is not None:
        restaurant.open_time = request.open_time
    if request.close_time is not None:
        restaurant.close_time = request.close_time
    if request.specialty is not None:
        restaurant.specialty = request.specialty
    if request.description is not None:
        restaurant.description = request.description
        if isinstance(request.description, str) and request.description.strip():
            restaurant.description_generated = False
        else:
            restaurant.description_generated = True
    if request.address is not None:
        restaurant.address = request.address
    if request.phone is not None:
        restaurant.phone = request.phone
    if request.email is not None:
        restaurant.email = request.email
    if request.website is not None:
        restaurant.website = request.website
    if request.latitude is not None:
        restaurant.latitude = request.latitude
    if request.longitude is not None:
        restaurant.longitude = request.longitude

    await db.flush()
    await db.refresh(restaurant)

    data = RestaurantResponse.model_validate(restaurant).model_dump()
    main, imgs = _augment_images(data["id"], data.get("image"), data.get("images"))
    data["image"] = main
    data["images"] = imgs

    return success_response(data=data, message="Cập nhật nhà hàng thành công")


@router.post("/{restaurant_id}/approve", response_model=dict)
async def approve_restaurant(
    restaurant_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve (activate) a restaurant (admin only)."""
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")

    restaurant.is_active = True
    await db.flush()
    await db.refresh(restaurant)

    data = RestaurantResponse.model_validate(restaurant).model_dump()
    main, imgs = _augment_images(data["id"], data.get("image"), data.get("images"))
    data["image"] = main
    data["images"] = imgs

    return success_response(data=data, message="Phê duyệt nhà hàng thành công")


@router.post("/{restaurant_id}/assign-owner", response_model=dict)
async def assign_restaurant_owner(
    restaurant_id: str,
    owner_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Assign a restaurant to a restaurant_owner user (admin only)."""
    rest_result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = rest_result.scalar_one_or_none()
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")

    user_result = await db.execute(select(User).where(User.id == owner_id))
    owner = user_result.scalar_one_or_none()
    if not owner or owner.role != UserRole.RESTAURANT_OWNER:
        return error_response("E3004", "Không tìm thấy đối tác hợp lệ")

    restaurant.owner_id = owner_id
    await db.flush()
    await db.refresh(restaurant)

    data = RestaurantResponse.model_validate(restaurant).model_dump()
    main, imgs = _augment_images(data["id"], data.get("image"), data.get("images"))
    data["image"] = main
    data["images"] = imgs

    return success_response(data=data, message="Gán đối tác cho nhà hàng thành công")


@router.post("/{restaurant_id}/images", response_model=dict)
async def upload_restaurant_images(
    restaurant_id: str,
    files: list[UploadFile] = File(...),
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    """Upload restaurant images to GCS and append to restaurant.images (admin/owner)."""
    restaurant = await _get_restaurant_for_manage(restaurant_id, user, db)
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng hoặc không có quyền")

    if not files:
        return error_response("E4000", "Chưa chọn ảnh")

    bucket_name = os.environ.get("GCS_BUCKET_NAME", "smart-travel-images-2025")
    prefix = os.environ.get("GCS_RESTAURANTS_PREFIX", "restaurants")
    upload_prefix = os.environ.get("GCS_RESTAURANTS_UPLOAD_PREFIX", "uploads")

    ext_map = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }

    uploaded_urls: list[str] = []
    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            continue
        raw = await file.read()
        if not raw:
            continue
        if len(raw) > 5 * 1024 * 1024:
            continue

        ext = ext_map.get(file.content_type.lower())
        if not ext:
            continue

        object_name = f"{prefix}/{upload_prefix}/{restaurant_id}/{os.urandom(12).hex()}.{ext}"

        try:
            from google.cloud import storage

            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            blob.cache_control = "public, max-age=31536000, immutable"
            await run_in_threadpool(blob.upload_from_string, raw, content_type=file.content_type.lower())
        except Exception as e:
            return error_response("E5000", "Không upload được ảnh nhà hàng", {"error": str(e)})

        uploaded_urls.append(f"https://storage.googleapis.com/{bucket_name}/{object_name}")

    if not uploaded_urls:
        return error_response("E4000", "Không có ảnh hợp lệ để upload")

    current_images = restaurant.images if isinstance(restaurant.images, list) else []
    restaurant.images = list(dict.fromkeys([*current_images, *uploaded_urls]))
    if not restaurant.image:
        restaurant.image = restaurant.images[0]

    await db.flush()
    await db.refresh(restaurant)

    data = RestaurantResponse.model_validate(restaurant).model_dump()
    main, imgs = _augment_images(data["id"], data.get("image"), data.get("images"))
    data["image"] = main
    data["images"] = imgs

    return success_response(data=data, message="Upload ảnh nhà hàng thành công")


@router.delete("/{restaurant_id}/images", response_model=dict)
async def remove_restaurant_image(
    restaurant_id: str,
    url: str,
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    """Remove an image URL from restaurant.images (admin/owner)."""
    restaurant = await _get_restaurant_for_manage(restaurant_id, user, db)
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng hoặc không có quyền")

    if not url or not isinstance(url, str):
        return error_response("E4000", "Thiếu url ảnh")

    current_images = restaurant.images if isinstance(restaurant.images, list) else []
    new_images = [u for u in current_images if u != url]
    restaurant.images = new_images
    if restaurant.image == url:
        restaurant.image = new_images[0] if new_images else None

    await db.flush()
    await db.refresh(restaurant)

    data = RestaurantResponse.model_validate(restaurant).model_dump()
    main, imgs = _augment_images(data["id"], data.get("image"), data.get("images"))
    data["image"] = main
    data["images"] = imgs

    return success_response(data=data, message="Xóa ảnh nhà hàng thành công")


@router.post("/{restaurant_id}/menu", response_model=dict)
async def create_menu_item(
    restaurant_id: str,
    request: MenuItemBase,
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    """Create a menu item (admin/owner). Owner-created items require admin approval."""
    restaurant = await _get_restaurant_for_manage(restaurant_id, user, db)
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng hoặc không có quyền")

    item = MenuItem(
        restaurant_id=restaurant_id,
        name=request.name,
        description=request.description,
        price=request.price,
        original_price=request.original_price,
        image=request.image,
        category=request.category,
        is_available=request.is_available,
        is_popular=request.is_popular,
        allergens=request.allergens,
        nutrition_info=request.nutrition_info.model_dump() if request.nutrition_info else None,
        is_approved=True if user.role == UserRole.ADMIN else False,
    )

    db.add(item)
    await db.flush()
    await db.refresh(item)

    data = MenuItemResponse.model_validate(item).model_dump()
    message = "Tạo món ăn thành công"
    if user.role != UserRole.ADMIN:
        message = "Đã gửi yêu cầu tạo món ăn, chờ Admin phê duyệt"

    return success_response(data=data, message=message)


@router.put("/{restaurant_id}/menu/{menu_item_id}", response_model=dict)
async def update_menu_item(
    restaurant_id: str,
    menu_item_id: str,
    request: MenuItemBase,
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    """Update a menu item (admin/owner)."""
    restaurant = await _get_restaurant_for_manage(restaurant_id, user, db)
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng hoặc không có quyền")

    result = await db.execute(
        select(MenuItem).where(MenuItem.id == menu_item_id, MenuItem.restaurant_id == restaurant_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return error_response("E3006", "Không tìm thấy món ăn")

    item.name = request.name
    item.description = request.description
    item.price = request.price
    item.original_price = request.original_price
    item.image = request.image
    item.category = request.category
    item.is_available = request.is_available
    item.is_popular = request.is_popular
    item.allergens = request.allergens
    item.nutrition_info = request.nutrition_info.model_dump() if request.nutrition_info else None

    await db.flush()
    await db.refresh(item)

    return success_response(data=MenuItemResponse.model_validate(item).model_dump(), message="Cập nhật món ăn thành công")


@router.post("/{restaurant_id}/menu/{menu_item_id}/approve", response_model=dict)
async def approve_menu_item(
    restaurant_id: str,
    menu_item_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve a menu item (admin only)."""
    result = await db.execute(
        select(MenuItem).where(MenuItem.id == menu_item_id, MenuItem.restaurant_id == restaurant_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return error_response("E3006", "Không tìm thấy món ăn")

    item.is_approved = True
    await db.flush()
    await db.refresh(item)

    return success_response(data=MenuItemResponse.model_validate(item).model_dump(), message="Phê duyệt món ăn thành công")


@router.put("/{restaurant_id}/rating-override", response_model=dict)
async def set_rating_override(
    restaurant_id: str,
    rating: Optional[float] = None,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Set/clear restaurant rating override (admin only)."""
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")

    if rating is None:
        restaurant.rating_override = None
        await db.flush()
        # Recompute from reviews when override cleared
        from app.modules.reviews.routes import update_restaurant_rating

        await update_restaurant_rating(db, restaurant_id)
    else:
        try:
            value = float(rating)
        except Exception:
            return error_response("E4000", "Rating không hợp lệ")
        if value < 0:
            value = 0.0
        if value > 5:
            value = 5.0
        restaurant.rating_override = value
        restaurant.rating = value
        await db.flush()

    await db.refresh(restaurant)
    data = RestaurantResponse.model_validate(restaurant).model_dump()
    main, imgs = _augment_images(data["id"], data.get("image"), data.get("images"))
    data["image"] = main
    data["images"] = imgs

    return success_response(data=data, message="Cập nhật rating thành công")


@router.get("/{restaurant_id}/stats", response_model=dict)
async def get_restaurant_stats(
    restaurant_id: str,
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get basic stats for a restaurant (admin/owner)."""
    restaurant = await _get_restaurant_for_manage(restaurant_id, user, db)
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng hoặc không có quyền")

    # Menu items approval counts
    menu_total_result = await db.execute(
        select(func.count(MenuItem.id)).where(MenuItem.restaurant_id == restaurant_id)
    )
    menu_total = int(menu_total_result.scalar() or 0)

    menu_pending_result = await db.execute(
        select(func.count(MenuItem.id)).where(
            MenuItem.restaurant_id == restaurant_id, MenuItem.is_approved == False
        )
    )
    menu_pending = int(menu_pending_result.scalar() or 0)

    return success_response(
        data={
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant.name,
            "rating": restaurant.rating,
            "review_count": restaurant.review_count,
            "menu_items_total": menu_total,
            "menu_items_pending_approval": menu_pending,
        },
        message="OK",
    )


@router.get("/{restaurant_id}", response_model=dict)
async def get_restaurant(
    restaurant_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get restaurant detail by ID"""
    result = await db.execute(
        select(Restaurant).where(
            Restaurant.id == restaurant_id,
            Restaurant.is_active == True
        )
    )
    restaurant = result.scalar_one_or_none()
    
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")
    
    # Get menu items
    menu_result = await db.execute(
        select(MenuItem).where(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.is_available == True,
            MenuItem.is_approved == True,
        ).order_by(MenuItem.category, MenuItem.name)
    )
    menu_items = menu_result.scalars().all()
    
    restaurant_data = RestaurantListResponse.model_validate(restaurant).model_dump()
    main, imgs = _augment_images(restaurant_data["id"], restaurant_data.get("image"), restaurant_data.get("images"))
    restaurant_data["image"] = main
    restaurant_data["images"] = imgs
    restaurant_data["menu"] = [MenuItemResponse.model_validate(m).model_dump() for m in menu_items]
    restaurant_data["google_maps_url"] = _google_maps_url(
        restaurant_data.get("id") or "",
        restaurant.latitude,
        restaurant.longitude,
        f"{restaurant.name or ''} {restaurant.address or ''}".strip() or None,
    )
    
    # Add location if available
    if restaurant.latitude and restaurant.longitude:
        restaurant_data["location"] = {
            "lat": restaurant.latitude,
            "lng": restaurant.longitude
        }
    
    return success_response(
        data=restaurant_data,
        message="Lấy thông tin nhà hàng thành công"
    )


@router.get("/{restaurant_id}/menu", response_model=dict)
async def get_restaurant_menu(
    restaurant_id: str,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get menu items for a restaurant"""
    # Check restaurant exists
    rest_result = await db.execute(
        select(Restaurant).where(Restaurant.id == restaurant_id)
    )
    if not rest_result.scalar_one_or_none():
        return error_response("E3002", "Không tìm thấy nhà hàng")
    
    query = select(MenuItem).where(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.is_available == True,
        MenuItem.is_approved == True,
    )
    
    if category:
        query = query.where(MenuItem.category.ilike(f"%{category}%"))
    
    query = query.order_by(MenuItem.category, MenuItem.name)
    
    result = await db.execute(query)
    menu_items = result.scalars().all()
    
    return success_response(
        data=[MenuItemResponse.model_validate(m).model_dump() for m in menu_items],
        message="Lấy menu thành công"
    )
