"""
Leaderboard APIs for Flappy Bird and Tetris.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import asyncio
import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import send_email
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.shared.schemas import error_response, success_response
from app.modules.games.leaderboard_schemas import (
    GameKey,
    LeaderboardEntryResponse,
    LeaderboardResponse,
    LeaderboardRoundInfo,
    SubmitScoreRequest,
    SubmitScoreResponse,
)
from app.modules.games.models import GameScore, GameScoreEntry, GameVoucherAward
from app.modules.auth.models import User


router = APIRouter(prefix="/games/leaderboard", tags=["Games"])

logger = logging.getLogger(__name__)

VALID_GAMES: set[str] = {"flappy", "tetris", "caro_pve"}
MAX_SCORE = 9_999_999_999
ROUND_SECONDS = 3 * 24 * 60 * 60
ROUND_EPOCH = datetime(2025, 1, 1)


def _hash_code(seed: str) -> int:
    h = 0
    for ch in seed:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h


def _voucher_code(seed: str) -> str:
    code = _hash_code(seed) % 10_000_000_000
    return f"{code:010d}"


def _clean_text(value: str | None, limit: int) -> str:
    if not value:
        return ""
    cleaned = value.strip()
    if not cleaned:
        return ""
    return cleaned[:limit]


def _clean_name(value: str | None) -> str:
    return _clean_text(value, 120) or "Khách"


async def _get_user(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def _round_index(now: datetime) -> int:
    delta = now - ROUND_EPOCH
    seconds = max(0, int(delta.total_seconds()))
    return seconds // ROUND_SECONDS


def _round_bounds(round_index: int) -> tuple[datetime, datetime]:
    start = ROUND_EPOCH + timedelta(seconds=round_index * ROUND_SECONDS)
    end = start + timedelta(seconds=ROUND_SECONDS)
    return start, end


def _render_voucher_email(*, name: str, game: str, code: str, percent: int, round_index: int) -> tuple[str, str]:
    game_label = {
        "flappy": "Flappy Bird",
        "tetris": "Tetris",
        "caro_pve": "Caro PvE",
    }.get(game, game)
    display_round = round_index + 1
    subject = f"Voucher {percent}% - Top 1 {game_label} vòng #{display_round}"
    text = (
        f"Chúc mừng {name}!\n\n"
        f"Bạn là Top 1 của {game_label} trong vòng tính điểm #{display_round} (3 ngày).\n"
        f"Mã voucher {percent}% của bạn: {code}\n\n"
        "Vui lòng xuất trình mã này khi sử dụng ưu đãi.\n"
        "Cảm ơn bạn đã tham gia!"
    )
    html = (
        "<div style=\"font-family:Arial,sans-serif;color:#0f172a;line-height:1.5\">"
        f"<h2>Chúc mừng {name}!</h2>"
        f"<p>Bạn là <strong>Top 1</strong> của {game_label} trong vòng tính điểm #{display_round} (3 ngày).</p>"
        f"<p>Mã voucher <strong>{percent}%</strong> của bạn:</p>"
        f"<div style=\"font-size:20px;font-weight:700;letter-spacing:2px;\">{code}</div>"
        "<p>Vui lòng xuất trình mã này khi sử dụng ưu đãi.</p>"
        "<p>Cảm ơn bạn đã tham gia!</p>"
        "</div>"
    )
    return subject, html


def _build_round_info(now: datetime) -> LeaderboardRoundInfo:
    current_round = _round_index(now)
    start, end = _round_bounds(current_round)
    remaining = max(0, int((end - now).total_seconds()))
    return LeaderboardRoundInfo(
        index=current_round,
        start_at=start,
        end_at=end,
        seconds_remaining=remaining,
    )


async def _maybe_award_previous_round(db: AsyncSession, game: str) -> None:
    now = datetime.utcnow()
    current_round = _round_index(now)
    previous_round = current_round - 1
    if previous_round < 0:
        return

    result = await db.execute(
        select(GameVoucherAward).where(
            GameVoucherAward.game == game,
            GameVoucherAward.round_index == previous_round,
        )
    )
    award = result.scalar_one_or_none()
    if award and award.sent_at:
        return

    start, end = _round_bounds(previous_round)
    if game == "caro_pve":
        entry_result = await db.execute(
            select(
                GameScoreEntry.player_id,
                func.max(GameScoreEntry.player_name).label("player_name"),
                func.sum(GameScoreEntry.score).label("score"),
                func.min(GameScoreEntry.created_at).label("first_at"),
            )
            .where(
                GameScoreEntry.game == game,
                GameScoreEntry.created_at >= start,
                GameScoreEntry.created_at < end,
            )
            .group_by(GameScoreEntry.player_id)
            .order_by(desc("score"), asc("first_at"))
            .limit(1)
        )
        row = entry_result.first()
        if not row:
            return
        winner_entry = type(
            "RoundWinner",
            (),
            {
                "player_id": row.player_id,
                "player_name": row.player_name,
                "score": int(row.score or 0),
            },
        )()
    else:
        entry_result = await db.execute(
            select(GameScoreEntry)
            .where(
                GameScoreEntry.game == game,
                GameScoreEntry.created_at >= start,
                GameScoreEntry.created_at < end,
            )
            .order_by(GameScoreEntry.score.desc(), GameScoreEntry.created_at.asc())
            .limit(1)
        )
        winner_entry = entry_result.scalar_one_or_none()
        if not winner_entry:
            return

    winner = await _get_user(db, winner_entry.player_id)
    winner_email = winner.email if winner else None
    winner_name = winner.name if winner else winner_entry.player_name
    voucher_code = _voucher_code(f"{game}:{previous_round}:{winner_entry.player_id}")

    if not award:
        award = GameVoucherAward(
            game=game,
            round_index=previous_round,
            winner_user_id=winner_entry.player_id,
            winner_email=winner_email,
            voucher_code=voucher_code,
            voucher_percent=15,
        )
        db.add(award)
        await db.flush()
    else:
        award.winner_user_id = winner_entry.player_id
        award.winner_email = winner_email
        award.voucher_code = voucher_code
        award.voucher_percent = 15
        await db.flush()

    if not winner_email:
        logger.warning("Voucher round %s for %s has no winner email.", previous_round, game)
        return

    try:
        subject, html = _render_voucher_email(
            name=winner_name,
            game=game,
            code=voucher_code,
            percent=15,
            round_index=previous_round,
        )
        await asyncio.to_thread(
            send_email,
            to_email=winner_email,
            subject=subject,
            html=html,
            text=None,
        )
        award.sent_at = datetime.utcnow()
        await db.flush()
    except Exception as exc:
        logger.error("Failed to send voucher email for %s round %s: %s", game, previous_round, exc)


def _build_entries(game: str, entries: list[GameScore]) -> list[dict]:
    payload: list[dict] = []
    for entry in entries:
        payload.append(
            LeaderboardEntryResponse(
                id=entry.id,
                player_name=entry.player_name,
                score=int(entry.score or 0),
                updated_at=entry.updated_at,
                voucher_code=None,
                voucher_percent=None,
            ).model_dump()
        )
    return payload


@router.get("/{game}", response_model=dict)
async def list_leaderboard(
    game: GameKey,
    limit: int = Query(200, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    if game not in VALID_GAMES:
        return error_response("E9201", "Trò chơi không hợp lệ")

    await _maybe_award_previous_round(db, game)

    total_result = await db.execute(
        select(func.count()).select_from(GameScore).where(GameScore.game == game)
    )
    total = int(total_result.scalar_one() or 0)

    result = await db.execute(
        select(GameScore)
        .where(GameScore.game == game)
        .order_by(GameScore.score.desc(), GameScore.updated_at.desc())
        .limit(limit)
    )
    entries = result.scalars().all()
    payload = _build_entries(game, entries)

    leaderboard = LeaderboardResponse(
        game=game,
        entries=payload,
        total_players=total,
        round=_build_round_info(datetime.utcnow()),
    )
    return success_response(leaderboard.model_dump(), message="OK")


@router.post("/{game}", response_model=dict)
async def submit_score(
    game: GameKey,
    request: SubmitScoreRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if game not in VALID_GAMES:
        return error_response("E9201", "Trò chơi không hợp lệ")

    await _maybe_award_previous_round(db, game)

    user = await _get_user(db, user_id)
    player_name = _clean_name(request.player_name) if request.player_name else (user.name if user else "Khách")
    score = max(0, min(int(request.score or 0), MAX_SCORE))
    is_caro_pve = game == "caro_pve"

    entry_log = GameScoreEntry(
        game=game,
        player_id=user_id,
        player_name=player_name,
        score=1 if is_caro_pve else score,
    )
    db.add(entry_log)

    existing_result = await db.execute(
        select(GameScore).where(GameScore.game == game, GameScore.player_id == user_id)
    )
    entry = existing_result.scalar_one_or_none()

    if entry:
        entry.player_name = player_name
        if is_caro_pve:
            entry.score = min(MAX_SCORE, int(entry.score or 0) + 1)
        elif score > int(entry.score or 0):
            entry.score = score
    else:
        entry = GameScore(
            game=game,
            player_id=user_id,
            player_name=player_name,
            score=1 if is_caro_pve else score,
        )
        db.add(entry)

    await db.flush()
    await db.refresh(entry)

    result = await db.execute(
        select(GameScore)
        .where(GameScore.game == game)
        .order_by(GameScore.score.desc(), GameScore.updated_at.desc())
        .limit(200)
    )
    entries = result.scalars().all()
    payload_entries = _build_entries(game, entries)

    total_result = await db.execute(
        select(func.count()).select_from(GameScore).where(GameScore.game == game)
    )
    total = int(total_result.scalar_one() or 0)

    leaderboard = LeaderboardResponse(
        game=game,
        entries=payload_entries,
        total_players=total,
        round=_build_round_info(datetime.utcnow()),
    )
    entry_payload = LeaderboardEntryResponse(
        id=entry.id,
        player_name=entry.player_name,
        score=int(entry.score or 0),
        updated_at=entry.updated_at,
    ).model_dump()
    response = SubmitScoreResponse(entry=entry_payload, leaderboard=leaderboard)
    return success_response(response.model_dump(), message="OK")
