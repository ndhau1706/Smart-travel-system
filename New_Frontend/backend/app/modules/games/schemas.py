"""
Pydantic schemas for online games APIs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Player = Literal["X", "O"]
Winner = Literal["X", "O", "draw"]


class CaroPos(BaseModel):
    r: int = Field(ge=0)
    c: int = Field(ge=0)


class CaroMove(CaroPos):
    p: Player


class CreateCaroGameRequest(BaseModel):
    player_name: Optional[str] = None
    board_size: Optional[int] = Field(default=None, ge=11)


class JoinCaroGameRequest(BaseModel):
    player_name: Optional[str] = None


class MakeCaroMoveRequest(BaseModel):
    token: str = Field(min_length=8)
    r: int = Field(ge=0)
    c: int = Field(ge=0)
    expected_version: int = Field(ge=0)


class CaroGamePublic(BaseModel):
    id: str
    status: str
    board_size: int
    win_length: int
    player_x_name: Optional[str] = None
    player_o_name: Optional[str] = None
    turn: Player
    winner: Optional[Winner] = None
    moves: list[CaroMove] = []
    win_line: list[CaroPos] = []
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaroYou(BaseModel):
    player: Optional[Player] = None
    token: Optional[str] = None


class CaroGameEnvelope(BaseModel):
    game: CaroGamePublic
    you: CaroYou
