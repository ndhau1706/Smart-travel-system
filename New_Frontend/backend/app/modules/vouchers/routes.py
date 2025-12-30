"""
Voucher wallet APIs.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.shared.schemas import success_response
from app.modules.feed.models import FeedPost, FeedVoucher
from app.modules.games.models import GameVoucherAward
from app.modules.vouchers.schemas import VoucherItem, VoucherListResponse


router = APIRouter(prefix="/vouchers", tags=["Vouchers"])

GAME_LABELS = {
    "flappy": "Flappy Bird",
    "tetris": "Tetris",
    "caro_pve": "Caro PvE",
}


@router.get("", response_model=dict)
async def list_vouchers(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    items: list[dict] = []

    feed_result = await db.execute(
        select(FeedVoucher, FeedPost.title)
        .join(FeedPost, FeedPost.id == FeedVoucher.post_id, isouter=True)
        .where(FeedVoucher.user_id == user_id)
        .order_by(desc(FeedVoucher.created_at))
    )
    for voucher, title in feed_result.all():
        items.append(
            VoucherItem(
                id=f"blog:{voucher.id}",
                source="blog",
                title=title or "Bài viết Blog",
                code=voucher.voucher_code,
                percent=int(voucher.voucher_percent or 0),
                status="Đã phát hành",
                created_at=voucher.created_at,
                sent_at=None,
            ).model_dump()
        )

    game_result = await db.execute(
        select(GameVoucherAward)
        .where(GameVoucherAward.winner_user_id == user_id)
        .order_by(desc(GameVoucherAward.created_at))
    )
    for award in game_result.scalars().all():
        label = GAME_LABELS.get(award.game, award.game)
        title = f"Top 1 {label} vòng #{award.round_index + 1}"
        status = "Đã gửi email" if award.sent_at else "Chờ gửi email"
        items.append(
            VoucherItem(
                id=f"game:{award.id}",
                source="game",
                title=title,
                code=award.voucher_code,
                percent=int(award.voucher_percent or 0),
                status=status,
                created_at=award.created_at,
                sent_at=award.sent_at,
            ).model_dump()
        )

    items.sort(key=lambda item: item["created_at"], reverse=True)
    payload = VoucherListResponse(items=items, total=len(items))
    return success_response(payload.model_dump(), message="OK")
