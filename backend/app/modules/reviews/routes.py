"""
Review API routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.deps import require_admin
from app.modules.reviews.models import Review
from app.modules.reviews.sentiment import analyze_review_sentiment
from app.modules.restaurants.models import Restaurant
from app.modules.auth.models import User
from app.modules.reviews.schemas import (
    CreateReviewRequest,
    UpdateReviewRequest,
    ReviewResponse
)
from app.shared.schemas import success_response, error_response, paginated_response
from typing import Optional

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/me", response_model=dict)
async def get_my_reviews(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's reviews"""
    result = await db.execute(
        select(Review).where(Review.user_id == user_id).order_by(Review.created_at.desc())
    )
    reviews = result.scalars().all()
    
    review_list = []
    for review in reviews:
        # Get restaurant name
        rest_result = await db.execute(
            select(Restaurant).where(Restaurant.id == review.restaurant_id)
        )
        restaurant = rest_result.scalar_one_or_none()
        
        # Get user info
        user_result = await db.execute(select(User).where(User.id == review.user_id))
        user = user_result.scalar_one_or_none()
        
        review_data = ReviewResponse.model_validate(review).model_dump()
        if restaurant:
            review_data["restaurant_name"] = restaurant.name
        if user:
            review_data["user_name"] = user.name
            review_data["user_avatar"] = user.avatar
        
        review_list.append(review_data)
    
    return success_response(
        data=review_list,
        message="Lấy danh sách đánh giá thành công"
    )


@router.get("/restaurant/{restaurant_id}/mine", response_model=dict)
async def get_my_review_for_restaurant(
    restaurant_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's review for a restaurant (if any)."""
    result = await db.execute(
        select(Review).where(Review.restaurant_id == restaurant_id, Review.user_id == user_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        return success_response(data=None, message="OK")

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    review_data = ReviewResponse.model_validate(review).model_dump()
    if user:
        review_data["user_name"] = user.name
        review_data["user_avatar"] = user.avatar

    return success_response(data=review_data, message="OK")


@router.post("", response_model=dict)
async def create_review(
    request: CreateReviewRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new review"""
    # Check restaurant exists
    rest_result = await db.execute(
        select(Restaurant).where(Restaurant.id == request.restaurant_id)
    )
    restaurant = rest_result.scalar_one_or_none()
    
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")
    
    # Check if user already reviewed this restaurant
    existing = await db.execute(
        select(Review).where(
            Review.user_id == user_id,
            Review.restaurant_id == request.restaurant_id
        )
    )
    if existing.scalar_one_or_none():
        return error_response("E4005", "Bạn đã đánh giá nhà hàng này rồi")

    sentiment = await analyze_review_sentiment(request.content)
    
    # Create review
    new_review = Review(
        user_id=user_id,
        restaurant_id=request.restaurant_id,
        rating=request.rating,
        title=request.title,
        content=request.content,
        images=request.images,
        visit_date=request.visit_date,
        sentiment_score=sentiment.score,
        sentiment_polarity=sentiment.polarity,
        sentiment_subjectivity=sentiment.subjectivity,
    )
    
    db.add(new_review)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        return error_response("E4005", "Bạn đã đánh giá nhà hàng này rồi")
    
    # Update restaurant rating
    await update_restaurant_rating(db, request.restaurant_id)
    
    await db.refresh(new_review)
    
    # Get user info
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    review_data = ReviewResponse.model_validate(new_review).model_dump()
    review_data["restaurant_name"] = restaurant.name
    if user:
        review_data["user_name"] = user.name
        review_data["user_avatar"] = user.avatar
    
    return success_response(
        data=review_data,
        message="Đánh giá thành công"
    )


@router.put("/{review_id}", response_model=dict)
async def update_review(
    review_id: str,
    request: UpdateReviewRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a review"""
    result = await db.execute(
        select(Review).where(
            Review.id == review_id,
            Review.user_id == user_id
        )
    )
    review = result.scalar_one_or_none()
    
    if not review:
        return error_response("E3005", "Không tìm thấy đánh giá")
    
    # Update fields
    if request.rating is not None:
        review.rating = request.rating
    if request.title is not None:
        review.title = request.title
    if request.content is not None:
        review.content = request.content
        sentiment = await analyze_review_sentiment(request.content)
        review.sentiment_score = sentiment.score
        review.sentiment_polarity = sentiment.polarity
        review.sentiment_subjectivity = sentiment.subjectivity
    if request.images is not None:
        review.images = request.images
    
    await db.flush()
    
    # Update restaurant rating
    await update_restaurant_rating(db, review.restaurant_id)
    
    await db.refresh(review)
    
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    review_data = ReviewResponse.model_validate(review).model_dump()
    if user:
        review_data["user_name"] = user.name
        review_data["user_avatar"] = user.avatar

    return success_response(data=review_data, message="Cập nhật đánh giá thành công")


@router.delete("/{review_id}", response_model=dict)
async def delete_review(
    review_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a review"""
    result = await db.execute(
        select(Review).where(
            Review.id == review_id,
            Review.user_id == user_id
        )
    )
    review = result.scalar_one_or_none()
    
    if not review:
        return error_response("E3005", "Không tìm thấy đánh giá")
    
    restaurant_id = review.restaurant_id
    await db.delete(review)
    await db.flush()
    
    # Update restaurant rating
    await update_restaurant_rating(db, restaurant_id)
    
    return success_response(
        data=None,
        message="Xóa đánh giá thành công"
    )


@router.delete("/admin/{review_id}", response_model=dict)
async def admin_delete_review(
    review_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin delete any review and recalculate rating."""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()

    if not review:
        return error_response("E3005", "Không tìm thấy đánh giá")

    restaurant_id = review.restaurant_id
    await db.delete(review)
    await db.flush()

    await update_restaurant_rating(db, restaurant_id)

    return success_response(data=None, message="Xóa đánh giá thành công")


@router.post("/{review_id}/like", response_model=dict)
async def like_review(
    review_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Like a review"""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        return error_response("E3005", "Không tìm thấy đánh giá")
    
    review.likes += 1
    await db.flush()
    
    return success_response(
        data={"likes": review.likes},
        message="Thích đánh giá thành công"
    )


# Restaurant reviews endpoint
@router.get("/restaurant/{restaurant_id}", response_model=dict)
async def get_restaurant_reviews(
    restaurant_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    rating: Optional[int] = Query(None, ge=1, le=5),
    sort_by: Optional[str] = Query("date", regex="^(date|rating|likes)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get reviews for a restaurant"""
    query = select(Review).where(Review.restaurant_id == restaurant_id)
    
    if rating:
        query = query.where(Review.rating == rating)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply sorting
    if sort_by == "rating":
        order_col = Review.rating
    elif sort_by == "likes":
        order_col = Review.likes
    else:
        order_col = Review.created_at
    
    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    # Enrich with user data
    review_list = []
    for review in reviews:
        if review.sentiment_score is None and review.content:
            sentiment = await analyze_review_sentiment(review.content)
            review.sentiment_score = sentiment.score
            review.sentiment_polarity = sentiment.polarity
            review.sentiment_subjectivity = sentiment.subjectivity

        review_data = ReviewResponse.model_validate(review).model_dump()
        
        # Get user name - from user account or imported author_name
        if review.user_id:
            user_result = await db.execute(select(User).where(User.id == review.user_id))
            user = user_result.scalar_one_or_none()
            if user:
                review_data["user_name"] = user.name
                review_data["user_avatar"] = user.avatar
        elif review.author_name:
            review_data["user_name"] = review.author_name
            review_data["user_avatar"] = None
        
        # Add reply if exists
        if review.reply_content:
            rest_result = await db.execute(
                select(Restaurant).where(Restaurant.id == review.restaurant_id)
            )
            restaurant = rest_result.scalar_one_or_none()
            review_data["reply"] = {
                "content": review.reply_content,
                "created_at": review.reply_date.isoformat() if review.reply_date else None,
                "restaurant_name": restaurant.name if restaurant else None
            }
        
        review_list.append(review_data)
    
    return paginated_response(
        data=review_list,
        total=total,
        page=page,
        limit=limit,
        message="Lấy đánh giá thành công"
    )


async def update_restaurant_rating(db: AsyncSession, restaurant_id: str):
    """Update restaurant average rating"""
    result = await db.execute(
        select(
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("count")
        ).where(Review.restaurant_id == restaurant_id)
    )
    row = result.first()
    
    rest_result = await db.execute(
        select(Restaurant).where(Restaurant.id == restaurant_id)
    )
    restaurant = rest_result.scalar_one_or_none()
    
    if restaurant:
        if restaurant.rating_override is None:
            restaurant.rating = round(row.avg_rating or 0, 1)
        else:
            try:
                restaurant.rating = float(restaurant.rating_override)
            except Exception:
                restaurant.rating = round(row.avg_rating or 0, 1)
        restaurant.review_count = row.count or 0
        await db.flush()
