"""
Leaderboard schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

GameKey = Literal["flappy", "tetris", "caro_pve"]


class SubmitScoreRequest(BaseModel):
    player_name: Optional[str] = None
    score: int


class LeaderboardEntryResponse(BaseModel):
    id: str
    player_name: str
    score: int
    updated_at: datetime
    voucher_code: Optional[str] = None
    voucher_percent: Optional[int] = None

    class Config:
        from_attributes = True


class LeaderboardRoundInfo(BaseModel):
    index: int
    start_at: datetime
    end_at: datetime
    seconds_remaining: int


class LeaderboardResponse(BaseModel):
    game: GameKey
    entries: list[LeaderboardEntryResponse]
    total_players: int
    round: LeaderboardRoundInfo


class SubmitScoreResponse(BaseModel):
    entry: LeaderboardEntryResponse
    leaderboard: LeaderboardResponse
