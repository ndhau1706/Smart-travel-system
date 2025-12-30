"""
Reports (phản ánh) API routes
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.deps import require_admin, require_admin_or_owner
from app.modules.auth.models import User, UserRole
from app.modules.restaurants.models import Restaurant
from app.modules.bookings.models import Booking, BookingStatus as BookingStatusModel
from app.modules.reports.models import RestaurantReport, ReportStatus as ReportStatusModel
from app.modules.reports.schemas import (
    CreateReportRequest,
    RespondReportRequest,
    UpdateReportStatusRequest,
    ReportResponse,
)
from app.shared.schemas import success_response, error_response, paginated_response

router = APIRouter(prefix="/reports", tags=["Reports"])


def _vn_now() -> datetime:
    return datetime.utcnow() + timedelta(hours=7)


def _booking_happened(booking: Booking, now: datetime) -> bool:
    if booking.status == BookingStatusModel.COMPLETED:
        return True
    if booking.status != BookingStatusModel.CONFIRMED:
        return False
    try:
        scheduled = datetime.strptime(f"{booking.date} {booking.time}", "%Y-%m-%d %H:%M")
    except Exception:
        return False
    return now >= (scheduled + timedelta(hours=1))


async def _user_can_interact(db: AsyncSession, user_id: str, restaurant_id: str) -> bool:
    result = await db.execute(
        select(Booking).where(
            Booking.user_id == user_id,
            Booking.restaurant_id == restaurant_id,
            Booking.status.in_([BookingStatusModel.CONFIRMED, BookingStatusModel.COMPLETED]),
        )
    )
    bookings = result.scalars().all()
    now = _vn_now()
    return any(_booking_happened(b, now) for b in bookings)


@router.get("/eligibility/{restaurant_id}", response_model=dict)
async def report_eligibility(
    restaurant_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    can = await _user_can_interact(db, user_id, restaurant_id)
    return success_response(data={"can_report": can}, message="OK")


@router.post("", response_model=dict)
async def create_report(
    request: CreateReportRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Check restaurant exists
    rest_result = await db.execute(select(Restaurant).where(Restaurant.id == request.restaurant_id))
    restaurant = rest_result.scalar_one_or_none()
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")

    if not await _user_can_interact(db, user_id, request.restaurant_id):
        return error_response(
            "E4007",
            "Tính năng 'Phản ánh' chỉ khả dụng với các nhà hàng bạn đã dùng bữa.",
        )

    report = RestaurantReport(
        user_id=user_id,
        restaurant_id=request.restaurant_id,
        title=request.title,
        content=request.content,
        status=ReportStatusModel.OPEN,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    data = ReportResponse.model_validate(report).model_dump()
    data["restaurant_name"] = restaurant.name
    return success_response(data=data, message="Gửi phản ánh thành công")


@router.get("/me", response_model=dict)
async def get_my_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = select(RestaurantReport).where(RestaurantReport.user_id == user_id)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(RestaurantReport.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    reports = result.scalars().all()

    payload = []
    for r in reports:
        item = ReportResponse.model_validate(r).model_dump()
        rest_result = await db.execute(select(Restaurant).where(Restaurant.id == r.restaurant_id))
        rest = rest_result.scalar_one_or_none()
        if rest:
            item["restaurant_name"] = rest.name
        payload.append(item)

    return paginated_response(data=payload, total=total, page=page, limit=limit, message="Lấy phản ánh thành công")


@router.get("/restaurant/{restaurant_id}", response_model=dict)
async def get_reports_for_restaurant(
    restaurant_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(open|in_progress|resolved|rejected)$"),
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    rest_result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    restaurant = rest_result.scalar_one_or_none()
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")

    if user.role != UserRole.ADMIN and restaurant.owner_id != user.id:
        return error_response("E4003", "Bạn không có quyền truy cập nhà hàng này")

    query = select(RestaurantReport).where(RestaurantReport.restaurant_id == restaurant_id)
    if status:
        try:
            query = query.where(RestaurantReport.status == ReportStatusModel(status))
        except Exception:
            return error_response("E4000", "Trạng thái không hợp lệ")

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(RestaurantReport.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    reports = result.scalars().all()

    payload = []
    for r in reports:
        item = ReportResponse.model_validate(r).model_dump()
        item["restaurant_name"] = restaurant.name
        if r.user_id:
            user_result = await db.execute(select(User).where(User.id == r.user_id))
            u = user_result.scalar_one_or_none()
            if u:
                item["user_name"] = u.name
        payload.append(item)

    return paginated_response(data=payload, total=total, page=page, limit=limit, message="Lấy phản ánh thành công")


@router.put("/{report_id}/respond", response_model=dict)
async def respond_report(
    report_id: str,
    request: RespondReportRequest,
    user: User = Depends(require_admin_or_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RestaurantReport).where(RestaurantReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        return error_response("E3007", "Không tìm thấy phản ánh")

    rest_result = await db.execute(select(Restaurant).where(Restaurant.id == report.restaurant_id))
    restaurant = rest_result.scalar_one_or_none()
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")

    if user.role != UserRole.ADMIN and restaurant.owner_id != user.id:
        return error_response("E4003", "Bạn không có quyền phản hồi phản ánh này")

    report.owner_response = request.response
    report.owner_responded_at = datetime.utcnow()
    if request.status:
        report.status = ReportStatusModel(request.status.value)
    elif report.status == ReportStatusModel.OPEN:
        report.status = ReportStatusModel.IN_PROGRESS

    await db.flush()
    await db.refresh(report)

    data = ReportResponse.model_validate(report).model_dump()
    data["restaurant_name"] = restaurant.name
    return success_response(data=data, message="Phản hồi phản ánh thành công")


@router.put("/{report_id}/status", response_model=dict)
async def update_report_status(
    report_id: str,
    request: UpdateReportStatusRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RestaurantReport).where(RestaurantReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        return error_response("E3007", "Không tìm thấy phản ánh")

    report.status = ReportStatusModel(request.status.value)
    if request.admin_note is not None:
        report.admin_note = request.admin_note

    await db.flush()
    await db.refresh(report)

    return success_response(data=ReportResponse.model_validate(report).model_dump(), message="Cập nhật trạng thái thành công")
