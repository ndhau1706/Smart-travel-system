"""
Online Caro (Gomoku 15x15) APIs.

We persist game state in DB so it works even when the backend runs on multiple Cloud Run instances.
Clients can poll `GET /api/games/caro/{id}` for updates.
"""

from __future__ import annotations

import secrets
from typing import Any, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.schemas import error_response, success_response
from app.modules.games.models import CaroGame
from app.modules.games.schemas import (
    CaroGameEnvelope,
    CaroGamePublic,
    CaroMove,
    CaroPos,
    CreateCaroGameRequest,
    JoinCaroGameRequest,
    MakeCaroMoveRequest,
    Player,
)

router = APIRouter(prefix="/games/caro", tags=["Games"])

MIN_BOARD_SIZE = 11
MAX_BOARD_SIZE = 30


def _clean_name(raw: Optional[str], fallback: str) -> str:
    name = (raw or "").strip()
    if not name:
        return fallback
    return name[:60]


def _other(player: Player) -> Player:
    return "O" if player == "X" else "X"


def _in_bounds(r: int, c: int, size: int) -> bool:
    return 0 <= r < size and 0 <= c < size


def _build_board(moves: list[dict[str, Any]], size: int) -> list[list[Optional[Player]]]:
    board: list[list[Optional[Player]]] = [[None for _ in range(size)] for _ in range(size)]
    for m in moves:
        try:
            r = int(m.get("r"))
            c = int(m.get("c"))
            p = m.get("p")
        except Exception:
            continue
        if p not in ("X", "O"):
            continue
        if not _in_bounds(r, c, size):
            continue
        board[r][c] = p  # last-write-wins; we validate duplicates elsewhere
    return board


def _find_win_line(board: list[list[Optional[Player]]], last: CaroPos, player: Player, win_len: int) -> list[CaroPos] | None:
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    size = len(board)

    for dr, dc in directions:
        line: list[tuple[int, int]] = [(last.r, last.c)]

        rr, cc = last.r - dr, last.c - dc
        while _in_bounds(rr, cc, size) and board[rr][cc] == player:
            line.insert(0, (rr, cc))
            rr -= dr
            cc -= dc

        rr, cc = last.r + dr, last.c + dc
        while _in_bounds(rr, cc, size) and board[rr][cc] == player:
            line.append((rr, cc))
            rr += dr
            cc += dc

        if len(line) < win_len:
            continue

        # Return a concrete win_len segment containing the last move.
        try:
            idx = line.index((last.r, last.c))
        except ValueError:
            idx = len(line) // 2

        start = max(0, idx - win_len + 1)
        if start + win_len > len(line):
            start = max(0, len(line) - win_len)

        segment = line[start : start + win_len]
        return [CaroPos(r=r, c=c) for r, c in segment]

    return None


def _public(game: CaroGame) -> CaroGamePublic:
    # Ensure stable shapes for JSON columns.
    moves = game.moves or []
    win_line = game.win_line or []
    payload = CaroGamePublic.model_validate(game).model_dump()
    payload["moves"] = [CaroMove.model_validate(m).model_dump() for m in moves]
    payload["win_line"] = [CaroPos.model_validate(p).model_dump() for p in win_line]
    return CaroGamePublic.model_validate(payload)


@router.post("", response_model=dict)
async def create_game(request: CreateCaroGameRequest, db: AsyncSession = Depends(get_db)):
    name = _clean_name(request.player_name, "Player X")
    board_size = int(request.board_size or 15)
    if board_size < MIN_BOARD_SIZE or board_size > MAX_BOARD_SIZE:
        return error_response(
            "E9008",
            f"Kích thước bàn cờ phải từ {MIN_BOARD_SIZE} đến {MAX_BOARD_SIZE}",
            details={"min": MIN_BOARD_SIZE, "max": MAX_BOARD_SIZE},
        )
    game = CaroGame(
        status="waiting",
        board_size=board_size,
        win_length=5,
        player_x_name=name,
        turn="X",
        winner=None,
        moves=[],
        win_line=[],
        version=0,
    )
    db.add(game)
    await db.flush()
    await db.refresh(game)

    envelope = CaroGameEnvelope(
        game=_public(game),
        you={"player": "X", "token": game.player_x_token},
    ).model_dump()
    return success_response(envelope, message="Tạo phòng cờ caro thành công")


@router.post("/{game_id}/join", response_model=dict)
async def join_game(game_id: str, request: JoinCaroGameRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaroGame).where(CaroGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        return error_response("E9001", "Không tìm thấy phòng chơi")

    # If O seat is available, occupy it; otherwise spectator mode (no token).
    if not game.player_o_token:
        game.player_o_token = secrets.token_urlsafe(24)
        game.player_o_name = _clean_name(request.player_name, "Player O")
        if game.status != "finished":
            game.status = "playing"
        await db.flush()
        await db.refresh(game)

        envelope = CaroGameEnvelope(
            game=_public(game),
            you={"player": "O", "token": game.player_o_token},
        ).model_dump()
        return success_response(envelope, message="Tham gia phòng thành công")

    envelope = CaroGameEnvelope(
        game=_public(game),
        you={"player": None, "token": None},
    ).model_dump()
    return success_response(envelope, message="Phòng đã đủ 2 người, bạn đang xem (spectator)")


@router.get("/{game_id}", response_model=dict)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaroGame).where(CaroGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        return error_response("E9001", "Không tìm thấy phòng chơi")
    return success_response(_public(game).model_dump(), message="OK")


@router.post("/{game_id}/move", response_model=dict)
async def make_move(game_id: str, request: MakeCaroMoveRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaroGame).where(CaroGame.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        return error_response("E9001", "Không tìm thấy phòng chơi")

    token = request.token.strip()
    player: Optional[Player] = None
    if token and token == game.player_x_token:
        player = "X"
    elif token and game.player_o_token and token == game.player_o_token:
        player = "O"

    if not player:
        return error_response("E9002", "Token không hợp lệ hoặc bạn không phải người chơi")

    if game.winner or game.status == "finished":
        return error_response("E9003", "Ván cờ đã kết thúc")

    if request.expected_version != int(game.version or 0):
        return error_response(
            "E9004",
            "Trạng thái đã thay đổi, vui lòng thử lại",
            details={"expected_version": request.expected_version, "server_version": int(game.version or 0)},
        )

    if (game.turn or "X") != player:
        return error_response("E9005", "Chưa tới lượt của bạn")

    size = int(game.board_size or 15)
    win_len = int(game.win_length or 5)
    r = int(request.r)
    c = int(request.c)
    if not _in_bounds(r, c, size):
        return error_response("E9006", "Nước đi không hợp lệ")

    moves: list[dict[str, Any]] = list(game.moves or [])
    occupied = {f"{m.get('r')}:{m.get('c')}" for m in moves}
    if f"{r}:{c}" in occupied:
        return error_response("E9007", "Ô này đã có quân")

    moves.append({"r": r, "c": c, "p": player})
    game.moves = moves

    board = _build_board(moves, size)
    win = _find_win_line(board, CaroPos(r=r, c=c), player, win_len)
    if win:
        game.winner = player
        game.status = "finished"
        game.win_line = [p.model_dump() for p in win]
    elif len(moves) >= size * size:
        game.winner = "draw"
        game.status = "finished"
        game.win_line = []
    else:
        game.turn = _other(player)

    game.version = int(game.version or 0) + 1
    await db.flush()
    await db.refresh(game)

    return success_response(_public(game).model_dump(), message="OK")
