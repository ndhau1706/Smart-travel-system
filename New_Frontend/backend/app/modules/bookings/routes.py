"""
Booking API routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.deps import require_admin_or_owner
from app.modules.bookings.models import Booking, BookingStatus
from app.modules.restaurants.models import Restaurant
from app.modules.auth.models import User, UserRole
from app.modules.bookings.schemas import (
    CreateBookingRequest,
    UpdateBookingRequest,
    CancelBookingRequest,
    UpdateBookingStatusRequest,
    BookingResponse,
    BookingQueryParams
)
from app.shared.schemas import success_response, error_response, paginated_response

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("", response_model=dict)
async def get_bookings(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's bookings"""
    query = select(Booking).where(Booking.user_id == user_id)
    
    if status:
        query = query.where(Booking.status == status)
    
    if from_date:
        query = query.where(Booking.date >= from_date)
    
    if to_date:
        query = query.where(Booking.date <= to_date)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Booking.date.desc(), Booking.time.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    # Enrich with restaurant data
    booking_list = []
    for booking in bookings:
        rest_result = await db.execute(
            select(Restaurant).where(Restaurant.id == booking.restaurant_id)
        )
        restaurant = rest_result.scalar_one_or_none()
        
        booking_data = BookingResponse.model_validate(booking).model_dump()
        if restaurant:
            booking_data["restaurant_name"] = restaurant.name
            booking_data["restaurant_address"] = restaurant.address
            booking_data["restaurant_phone"] = restaurant.phone
            booking_data["restaurant_image"] = restaurant.image
        
        booking_list.append(booking_data)
    
    return paginated_response(
        data=booking_list,
        total=total,
        page=page,
        limit=limit,
        message="Lấy danh sách đặt bàn thành công"
    )


@router.get("/{booking_id}", response_model=dict)
async def get_booking(
    booking_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get booking detail"""
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.user_id == user_id
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        return error_response("E3003", "Không tìm thấy đặt bàn")
    
    # Get restaurant info
    rest_result = await db.execute(
        select(Restaurant).where(Restaurant.id == booking.restaurant_id)
    )
    restaurant = rest_result.scalar_one_or_none()
    
    booking_data = BookingResponse.model_validate(booking).model_dump()
    if restaurant:
        booking_data["restaurant_name"] = restaurant.name
        booking_data["restaurant_address"] = restaurant.address
        booking_data["restaurant_phone"] = restaurant.phone
        booking_data["restaurant_image"] = restaurant.image
    
    return success_response(
        data=booking_data,
        message="Lấy thông tin đặt bàn thành công"
    )


@router.post("", response_model=dict)
async def create_booking(
    request: CreateBookingRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new booking"""
    # Check restaurant exists
    rest_result = await db.execute(
        select(Restaurant).where(
            Restaurant.id == request.restaurant_id,
            Restaurant.is_active == True
        )
    )
    restaurant = rest_result.scalar_one_or_none()
    
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")
    
    # Create booking
    new_booking = Booking(
        user_id=user_id,
        restaurant_id=request.restaurant_id,
        date=request.date,
        time=request.time,
        guests=request.guests,
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        customer_email=request.customer_email,
        special_requests=request.special_requests,
        status=BookingStatus.PENDING
    )
    new_booking.generate_confirmation_code()
    
    db.add(new_booking)
    await db.flush()
    await db.refresh(new_booking)
    
    booking_data = BookingResponse.model_validate(new_booking).model_dump()
    booking_data["restaurant_name"] = restaurant.name
    booking_data["restaurant_address"] = restaurant.address
    booking_data["restaurant_phone"] = restaurant.phone
    booking_data["restaurant_image"] = restaurant.image
    
    return success_response(
        data=booking_data,
        message="Đặt bàn thành công"
    )


@router.put("/{booking_id}", response_model=dict)
async def update_booking(
    booking_id: str,
    request: UpdateBookingRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a booking"""
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.user_id == user_id
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        return error_response("E3003", "Không tìm thấy đặt bàn")
    
    if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
        return error_response("E4002", "Không thể cập nhật đặt bàn đã hủy hoặc hoàn thành")
    
    # Update fields
    if request.date is not None:
        booking.date = request.date
    if request.time is not None:
        booking.time = request.time
    if request.guests is not None:
        booking.guests = request.guests
    if request.special_requests is not None:
        booking.special_requests = request.special_requests
    
    # Reset status to pending after update
    booking.status = BookingStatus.PENDING
    
    await db.flush()
    await db.refresh(booking)
    
    return success_response(
        data=BookingResponse.model_validate(booking).model_dump(),
        message="Cập nhật đặt bàn thành công"
    )


@router.delete("/{booking_id}", response_model=dict)
async def cancel_booking(
    booking_id: str,
    request: CancelBookingRequest = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a booking"""
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.user_id == user_id
        )
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        return error_response("E3003", "Không tìm thấy đặt bàn")
    
    if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
        return error_response("E4002", "Không thể hủy đặt bàn đã hủy hoặc hoàn thành")
    
    booking.status = BookingStatus.CANCELLED
    if request and request.reason:
        booking.cancel_reason = request.reason
    
    await db.flush()
    await db.refresh(booking)
    
    return success_response(
        data=BookingResponse.model_validate(booking).model_dump(),
        message="Hủy đặt bàn thành công"
    )


@router.get("/availability/check", response_model=dict)
async def check_availability(
    restaurant_id: str,
    date: str,
    time: str,
    guests: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Check booking availability"""
    # In a real app, this would check against restaurant capacity and existing bookings
    return success_response(
        data={
            "available": True,
            "alternatives": ["18:00", "18:30", "19:30", "20:00"]
        },
        message="Kiểm tra thành công"
    )


@router.get("/restaurant/{restaurant_id}", response_model=dict)
async def get_bookings_for_restaurant(
    restaurant_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get bookings for a restaurant (admin/owner)."""
    rest_result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = rest_result.scalar_one_or_none()
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")

    if user.role != UserRole.ADMIN and restaurant.owner_id != user.id:
        return error_response("E4003", "Bạn không có quyền truy cập nhà hàng này")

    query = select(Booking).where(Booking.restaurant_id == restaurant_id)

    if status:
        query = query.where(Booking.status == status)
    if from_date:
        query = query.where(Booking.date >= from_date)
    if to_date:
        query = query.where(Booking.date <= to_date)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Booking.date.desc(), Booking.time.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    bookings = result.scalars().all()

    payload = []
    for booking in bookings:
        item = BookingResponse.model_validate(booking).model_dump()
        item["restaurant_name"] = restaurant.name
        item["restaurant_address"] = restaurant.address
        item["restaurant_phone"] = restaurant.phone
        item["restaurant_image"] = restaurant.image
        payload.append(item)

    return paginated_response(
        data=payload,
        total=total,
        page=page,
        limit=limit,
        message="Lấy danh sách đặt bàn thành công",
    )


@router.put("/{booking_id}/status", response_model=dict)
async def update_booking_status(
    booking_id: str,
    request: UpdateBookingStatusRequest,
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    """Update booking status (admin/owner)."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        return error_response("E3003", "Không tìm thấy đặt bàn")

    rest_result = await db.execute(select(Restaurant).where(Restaurant.id == booking.restaurant_id))
    restaurant = rest_result.scalar_one_or_none()
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")

    if user.role != UserRole.ADMIN and restaurant.owner_id != user.id:
        return error_response("E4003", "Bạn không có quyền cập nhật đặt bàn này")

    # Map schema enum -> model enum (same values)
    booking.status = BookingStatus(request.status.value)
    if booking.status == BookingStatus.CANCELLED and request.cancel_reason:
        booking.cancel_reason = request.cancel_reason

    await db.flush()
    await db.refresh(booking)

    data = BookingResponse.model_validate(booking).model_dump()
    data["restaurant_name"] = restaurant.name
    data["restaurant_address"] = restaurant.address
    data["restaurant_phone"] = restaurant.phone
    data["restaurant_image"] = restaurant.image

    return success_response(data=data, message="Cập nhật trạng thái đặt bàn thành công")
