"""
Site pages API routes
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.deps import require_admin
from app.modules.auth.models import User
from app.modules.pages.models import SitePage
from app.modules.pages.schemas import SitePageUpsertRequest, SitePageResponse
from app.shared.schemas import success_response, error_response, paginated_response

router = APIRouter(prefix="/pages", tags=["Pages"])


@router.get("", response_model=dict)
async def list_pages(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(SitePage)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(SitePage.updated_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    pages = result.scalars().all()

    payload = [SitePageResponse.model_validate(p).model_dump() for p in pages]
    return paginated_response(data=payload, total=total, page=page, limit=limit, message="OK")


@router.get("/{slug}", response_model=dict)
async def get_page(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SitePage).where(SitePage.slug == slug))
    page = result.scalar_one_or_none()
    if not page:
        return error_response("E3010", "Không tìm thấy trang")
    return success_response(data=SitePageResponse.model_validate(page).model_dump(), message="OK")


@router.put("/{slug}", response_model=dict)
async def upsert_page(
    slug: str,
    request: SitePageUpsertRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SitePage).where(SitePage.slug == slug))
    page = result.scalar_one_or_none()

    if not page:
        page = SitePage(slug=slug, title=request.title, body=request.body, updated_by=user.id)
        db.add(page)
        await db.flush()
    else:
        page.title = request.title
        page.body = request.body
        page.updated_by = user.id
        await db.flush()

    await db.refresh(page)
    return success_response(data=SitePageResponse.model_validate(page).model_dump(), message="Cập nhật trang thành công")

