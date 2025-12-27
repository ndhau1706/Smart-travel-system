from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from models import BlogStatus, VoucherType, UserVoucherStatus


class BlogCreate(BaseModel):
    title: str
    content: str
    cover_url: Optional[str] = None


class BlogUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    cover_url: Optional[str] = None


class BlogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    author_id: str
    title: str
    slug: str
    content: str
    cover_url: Optional[str]
    status: BlogStatus
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    views: int


class BlogListResponse(BaseModel):
    items: List[BlogResponse]
    total: int
    skip: int
    limit: int


class VoucherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    type: VoucherType
    value: float
    expire_at: datetime
    status: UserVoucherStatus


class PublishResponse(BaseModel):
    status: str
    voucher_awarded: bool
    voucher_code: Optional[str] = None
