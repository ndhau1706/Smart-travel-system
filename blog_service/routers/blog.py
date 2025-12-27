from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from crud.blog import (
    count_blogs,
    create_blog,
    delete_blog,
    get_blog_by_id,
    get_blog_by_slug,
    list_blogs,
    list_user_vouchers,
    publish_blog,
    update_blog,
)
from deps import CurrentUser, get_current_user, get_db
from models import BlogStatus
from schemas import BlogCreate, BlogListResponse, BlogResponse, BlogUpdate, PublishResponse, VoucherResponse


router = APIRouter(tags=["blogs"])


@router.post("/blogs", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
def create_blog_endpoint(
    payload: BlogCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> BlogResponse:
    try:
        blog = create_blog(
            db,
            author_id=current_user.id,
            title=payload.title,
            content=payload.content,
            cover_url=payload.cover_url,
        )
        return blog
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put("/blogs/{blog_id}", response_model=BlogResponse)
def update_blog_endpoint(
    blog_id: str,
    payload: BlogUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> BlogResponse:
    blog = get_blog_by_id(db, blog_id)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    if blog.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    updates = payload.model_dump(exclude_unset=True)
    try:
        updated = update_blog(db, blog, updates)
        return updated
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete("/blogs/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_endpoint(
    blog_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    blog = get_blog_by_id(db, blog_id)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    if blog.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    delete_blog(db, blog)


@router.get("/blogs", response_model=BlogListResponse)
def list_blogs_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[BlogStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
) -> BlogListResponse:
    total = count_blogs(db, status_filter)
    items = list_blogs(db, skip, limit, status_filter)
    return BlogListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/blogs/{slug}", response_model=BlogResponse)
def get_blog_endpoint(slug: str, db: Session = Depends(get_db)) -> BlogResponse:
    blog = get_blog_by_slug(db, slug)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return blog


@router.post(
    "/blogs/{blog_id}/publish",
    response_model=PublishResponse,
    responses={
        200: {
            "description": "Publish result. Frontend can show popup: 'Ban nhan voucher: CODE'.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "published",
                        "voucher_awarded": True,
                        "voucher_code": "BLOG-ABC12345",
                    }
                }
            },
        }
    },
)
def publish_blog_endpoint(
    blog_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> PublishResponse:
    blog = get_blog_by_id(db, blog_id)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    if blog.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    try:
        result = publish_blog(db, blog, blog.author_id)
        return PublishResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/me/vouchers", response_model=list[VoucherResponse], tags=["vouchers"])
def list_my_vouchers(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[VoucherResponse]:
    vouchers = list_user_vouchers(db, current_user.id)
    return [VoucherResponse(**voucher) for voucher in vouchers]
