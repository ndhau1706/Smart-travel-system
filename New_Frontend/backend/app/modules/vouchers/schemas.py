"""
Voucher schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

VoucherSource = Literal["blog", "game"]


class VoucherItem(BaseModel):
    id: str
    source: VoucherSource
    title: str
    code: str
    percent: int
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None


class VoucherListResponse(BaseModel):
    items: list[VoucherItem]
    total: int
