"""
Newsfeed API routes.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.email import send_email
from app.core.security import get_current_user_id, get_current_user_id_optional
from app.shared.schemas import error_response, paginated_response, success_response
from app.modules.auth.models import User, UserRole
from app.modules.feed.models import FeedComment, FeedPost, FeedReaction, FeedShare, FeedVoucher
from app.modules.feed.schemas import (
    CreateFeedPostRequest,
    FeedCommentEnvelope,
    FeedCommentRequest,
    FeedCommentResponse,
    FeedPostResponse,
    FeedReactionCounts,
    FeedReactionRequest,
    FeedReactionResponse,
    FeedShareEnvelope,
    FeedShareRequest,
    FeedWallItem,
    FeedPostSummary,
)


router = APIRouter(prefix="/feed", tags=["Newsfeed"])

logger = logging.getLogger(__name__)

REACTION_FIELDS = {
    "like": "like_count",
    "love": "love_count",
    "wow": "wow_count",
    "insightful": "insightful_count",
}

VOUCHER_PERCENTS = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
VOUCHER_WEIGHTS = [30, 24, 18, 12, 7, 4, 3, 2, 1, 1, 1]


def _clean_text(value: Optional[str], limit: int) -> str:
    if not value:
        return ""
    cleaned = value.strip()
    if not cleaned:
        return ""
    return cleaned[:limit]


def _clean_name(value: Optional[str], fallback: str = "Thành viên") -> str:
    name = _clean_text(value, 120)
    return name or fallback


def _normalize_tags(tags: Optional[list[str]]) -> list[str]:
    if not tags:
        return []
    out: list[str] = []
    for raw in tags:
        if not raw:
            continue
        tag = str(raw).strip()
        if not tag or tag in out:
            continue
        out.append(tag)
        if len(out) >= 4:
            break
    return out


def _reaction_counts(post: FeedPost) -> FeedReactionCounts:
    return FeedReactionCounts(
        like=int(post.like_count or 0),
        love=int(post.love_count or 0),
        wow=int(post.wow_count or 0),
        insightful=int(post.insightful_count or 0),
    )


def _hash_code(seed: str) -> int:
    h = 0
    for ch in seed:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h


def _voucher_code(seed: str) -> str:
    code = _hash_code(seed) % 10_000_000_000
    return f"{code:010d}"


def _pick_voucher_percent() -> int:
    return random.choices(VOUCHER_PERCENTS, weights=VOUCHER_WEIGHTS, k=1)[0]


def _qualifies_for_voucher(body: str, image: Optional[str]) -> bool:
    return len(body.strip()) >= 150 and bool(image)


def _render_blog_voucher_email(*, name: str, code: str, percent: int) -> tuple[str, str, str]:
    subject = f"Voucher {percent}% - Cảm ơn bạn đã đăng bài"
    text = (
        f"Chào {name},\n\n"
        f"Cảm ơn bạn đã đăng bài trên Smart Travel.\n"
        f"Mã voucher {percent}% của bạn: {code}\n\n"
        "Vui lòng xuất trình mã này khi sử dụng ưu đãi."
    )
    html = (
        "<div style=\"font-family:Arial,sans-serif;color:#0f172a;line-height:1.5\">"
        f"<h2>Xin chào {name},</h2>"
        "<p>Cảm ơn bạn đã đăng bài trên Smart Travel.</p>"
        f"<p>Mã voucher <strong>{percent}%</strong> của bạn:</p>"
        f"<div style=\"font-size:20px;font-weight:700;letter-spacing:2px;\">{code}</div>"
        "<p>Vui lòng xuất trình mã này khi sử dụng ưu đãi.</p>"
        "</div>"
    )
    return subject, text, html


async def _send_blog_voucher_email(*, to_email: str, name: str, code: str, percent: int) -> None:
    try:
        subject, text, html = _render_blog_voucher_email(name=name, code=code, percent=percent)
        await asyncio.to_thread(
            send_email,
            to_email=to_email,
            subject=subject,
            html=html,
            text=text,
        )
    except Exception as exc:
        logger.warning("Failed to send blog voucher email to %s: %s", to_email, exc)


def _role_label(user: Optional[User]) -> str:
    if not user:
        return "Thành viên"
    if user.role == UserRole.ADMIN:
        return "Quản trị"
    if user.role == UserRole.RESTAURANT_OWNER:
        return "Chủ nhà hàng"
    return "Thành viên"


async def _get_user(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def _apply_reaction_delta(post: FeedPost, reaction: str, delta: int) -> None:
    field = REACTION_FIELDS.get(reaction)
    if not field:
        return
    current = int(getattr(post, field) or 0)
    setattr(post, field, max(0, current + delta))


@router.delete("/admin/purge", response_model=dict)
async def purge_feed(
    x_feed_purge_token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    expected = os.environ.get("FEED_PURGE_TOKEN", "").strip()
    if not expected or not x_feed_purge_token or x_feed_purge_token.strip() != expected:
        return error_response("E9199", "Không có quyền xóa dữ liệu")

    reactions_result = await db.execute(delete(FeedReaction))
    comments_result = await db.execute(delete(FeedComment))
    shares_result = await db.execute(delete(FeedShare))
    vouchers_result = await db.execute(delete(FeedVoucher))
    posts_result = await db.execute(delete(FeedPost))

    payload = {
        "reactions": reactions_result.rowcount or 0,
        "comments": comments_result.rowcount or 0,
        "shares": shares_result.rowcount or 0,
        "vouchers": vouchers_result.rowcount or 0,
        "posts": posts_result.rowcount or 0,
    }
    return success_response(payload, message="Đã xóa toàn bộ bài đăng")


@router.get("/posts", response_model=dict)
async def list_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    viewer_id: Optional[str] = Query(None),
    user_id: Optional[str] = Depends(get_current_user_id_optional),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(select(func.count()).select_from(FeedPost))
    total = int(total_result.scalar_one() or 0)

    offset = (page - 1) * limit
    result = await db.execute(
        select(FeedPost).order_by(FeedPost.created_at.desc()).offset(offset).limit(limit)
    )
    posts = result.scalars().all()
    post_ids = [p.id for p in posts]

    comments_by_post: dict[str, list[FeedCommentResponse]] = {}
    if post_ids:
        comments_result = await db.execute(
            select(FeedComment)
            .where(FeedComment.post_id.in_(post_ids))
            .order_by(FeedComment.created_at.asc())
        )
        for comment in comments_result.scalars().all():
            comments_by_post.setdefault(comment.post_id, []).append(
                FeedCommentResponse.model_validate(comment)
            )

    my_reactions: dict[str, Optional[str]] = {}
    viewer = user_id or viewer_id
    if viewer and post_ids:
        reaction_result = await db.execute(
            select(FeedReaction).where(
                FeedReaction.post_id.in_(post_ids),
                FeedReaction.actor_id == viewer,
            )
        )
        for reaction in reaction_result.scalars().all():
            my_reactions[reaction.post_id] = reaction.reaction

    payload: list[dict] = []
    for post in posts:
        response = FeedPostResponse(
            id=post.id,
            author_name=post.author_name,
            author_role=post.author_role,
            author_avatar=post.author_avatar,
            title=post.title,
            body=post.body,
            tags=post.tags or [],
            location=post.location,
            image=post.image,
            reactions=_reaction_counts(post),
            my_reaction=my_reactions.get(post.id),
            comments=comments_by_post.get(post.id, []),
            comment_count=int(post.comment_count or 0),
            share_count=int(post.share_count or 0),
            created_at=post.created_at,
            updated_at=post.updated_at,
        )
        payload.append(response.model_dump())

    return paginated_response(payload, total=total, page=page, limit=limit, message="OK")


@router.post("/posts", response_model=dict)
async def create_post(
    request: CreateFeedPostRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    author_name = _clean_name(request.author_name, user.name if user else "Thành viên")
    title = _clean_text(request.title, 180)
    body = _clean_text(request.body, 4000)

    if not title and not body:
        return error_response("E9101", "Vui lòng nhập tiêu đề hoặc nội dung bài viết")

    if not title:
        title = "Chia sẻ nhanh"

    post = FeedPost(
        author_id=user_id,
        author_name=author_name,
        author_role=_clean_text(request.author_role, 120) or _role_label(user),
        author_avatar=_clean_text(request.author_avatar, 500) or (user.avatar if user else None),
        title=title,
        body=body or None,
        tags=_normalize_tags(request.tags),
        location=_clean_text(request.location, 160) or None,
        image=_clean_text(request.image, 500) or None,
    )

    db.add(post)
    await db.flush()
    await db.refresh(post)

    if _qualifies_for_voucher(body, post.image):
        percent = _pick_voucher_percent()
        token = secrets.token_hex(4)
        code = _voucher_code(f"blog:{post.id}:{user_id}:{percent}:{token}")
        voucher = FeedVoucher(
            post_id=post.id,
            user_id=user_id,
            voucher_code=code,
            voucher_percent=percent,
        )
        db.add(voucher)
        await db.flush()
        if user and user.email:
            asyncio.create_task(
                _send_blog_voucher_email(
                    to_email=user.email,
                    name=user.name or author_name,
                    code=code,
                    percent=percent,
                )
            )

    response = FeedPostResponse(
        id=post.id,
        author_name=post.author_name,
        author_role=post.author_role,
        author_avatar=post.author_avatar,
        title=post.title,
        body=post.body,
        tags=post.tags or [],
        location=post.location,
        image=post.image,
        reactions=_reaction_counts(post),
        my_reaction=None,
        comments=[],
        comment_count=0,
        share_count=0,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )

    return success_response(response.model_dump(), message="Đăng bài thành công")


@router.post("/posts/{post_id}/reactions", response_model=dict)
async def set_reaction(
    post_id: str,
    request: FeedReactionRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FeedPost).where(FeedPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return error_response("E9103", "Không tìm thấy bài viết")

    existing_result = await db.execute(
        select(FeedReaction).where(
            FeedReaction.post_id == post_id,
            FeedReaction.actor_id == user_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    requested = request.reaction
    if requested and requested not in REACTION_FIELDS:
        return error_response("E9104", "Cảm xúc không hợp lệ")

    if existing:
        if requested is None or existing.reaction == requested:
            _apply_reaction_delta(post, existing.reaction, -1)
            await db.delete(existing)
            requested = None
        else:
            _apply_reaction_delta(post, existing.reaction, -1)
            existing.reaction = requested
            _apply_reaction_delta(post, requested, 1)
    elif requested:
        new_reaction = FeedReaction(
            post_id=post_id,
            actor_id=user_id,
            reaction=requested,
        )
        db.add(new_reaction)
        _apply_reaction_delta(post, requested, 1)

    await db.flush()
    await db.refresh(post)

    response = FeedReactionResponse(
        post_id=post.id,
        reactions=_reaction_counts(post),
        my_reaction=requested,
    )
    return success_response(response.model_dump(), message="OK")


@router.post("/posts/{post_id}/comments", response_model=dict)
async def add_comment(
    post_id: str,
    request: FeedCommentRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    content = _clean_text(request.content, 800)
    if not content:
        return error_response("E9106", "Bình luận không được để trống")

    result = await db.execute(select(FeedPost).where(FeedPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return error_response("E9103", "Không tìm thấy bài viết")

    user = await _get_user(db, user_id)
    comment = FeedComment(
        post_id=post_id,
        actor_id=user_id,
        author_name=_clean_name(request.author_name, user.name if user else "Thành viên"),
        content=content,
    )
    db.add(comment)
    post.comment_count = int(post.comment_count or 0) + 1
    await db.flush()
    await db.refresh(comment)

    envelope = FeedCommentEnvelope(
        post_id=post_id,
        comment=FeedCommentResponse.model_validate(comment),
        comment_count=int(post.comment_count or 0),
    )
    return success_response(envelope.model_dump(), message="Thêm bình luận thành công")


@router.post("/posts/{post_id}/shares", response_model=dict)
async def share_post(
    post_id: str,
    request: FeedShareRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FeedPost).where(FeedPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return error_response("E9103", "Không tìm thấy bài viết")

    user = await _get_user(db, user_id)
    share = FeedShare(
        post_id=post_id,
        actor_id=user_id,
        shared_by=_clean_name(request.shared_by, user.name if user else "Thành viên"),
    )
    db.add(share)
    post.share_count = int(post.share_count or 0) + 1
    await db.flush()
    await db.refresh(share)

    wall_item = FeedWallItem(
        id=share.id,
        post_id=post_id,
        shared_by=share.shared_by,
        shared_at=share.created_at,
        post=FeedPostSummary(id=post.id, title=post.title, author_name=post.author_name),
    )
    envelope = FeedShareEnvelope(
        post_id=post_id,
        share_id=share.id,
        share_count=int(post.share_count or 0),
        wall_item=wall_item,
    )
    return success_response(envelope.model_dump(), message="Đã chia sẻ lên tường")


@router.get("/wall", response_model=dict)
async def list_wall(
    limit: int = Query(12, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    shares_result = await db.execute(
        select(FeedShare)
        .where(FeedShare.actor_id == user_id)
        .order_by(FeedShare.created_at.desc())
        .limit(limit)
    )
    shares = shares_result.scalars().all()

    post_ids = [s.post_id for s in shares]
    posts_map: dict[str, FeedPost] = {}
    if post_ids:
        posts_result = await db.execute(select(FeedPost).where(FeedPost.id.in_(post_ids)))
        posts_map = {p.id: p for p in posts_result.scalars().all()}

    payload: list[dict] = []
    for share in shares:
        post = posts_map.get(share.post_id)
        summary = None
        if post:
            summary = FeedPostSummary(id=post.id, title=post.title, author_name=post.author_name)
        payload.append(
            FeedWallItem(
                id=share.id,
                post_id=share.post_id,
                shared_by=share.shared_by,
                shared_at=share.created_at,
                post=summary,
            ).model_dump()
        )

    return success_response(payload, message="OK")
