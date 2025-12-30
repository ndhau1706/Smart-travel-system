"""
Online games persistence models (DB-backed to work on Cloud Run).
"""

from __future__ import annotations

from datetime import datetime
import secrets
import uuid

from sqlalchemy import Column, DateTime, Integer, JSON, String, UniqueConstraint

from app.core.database import Base


class CaroGame(Base):
    __tablename__ = "caro_games"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    status = Column(String(16), default="waiting", index=True)  # waiting | playing | finished
    board_size = Column(Integer, default=15)
    win_length = Column(Integer, default=5)

    player_x_name = Column(String(120), nullable=True)
    player_o_name = Column(String(120), nullable=True)

    # Per-player tokens are used to authorize moves without requiring auth.
    player_x_token = Column(String(128), nullable=False, default=lambda: secrets.token_urlsafe(24))
    player_o_token = Column(String(128), nullable=True)

    turn = Column(String(1), default="X")  # X | O
    winner = Column(String(8), nullable=True)  # X | O | draw

    # Stored as list[{"r": int, "c": int, "p": "X"|"O"}]
    moves = Column(JSON, default=list)
    # Stored as list[{"r": int, "c": int}] (length = win_length)
    win_line = Column(JSON, default=list)

    version = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GameScore(Base):
    __tablename__ = "game_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    game = Column(String(24), index=True, nullable=False)
    player_id = Column(String(64), index=True, nullable=False)
    player_name = Column(String(120), nullable=False)
    score = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GameScoreEntry(Base):
    __tablename__ = "game_score_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    game = Column(String(24), index=True, nullable=False)
    player_id = Column(String(64), index=True, nullable=False)
    player_name = Column(String(120), nullable=False)
    score = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class GameVoucherAward(Base):
    __tablename__ = "game_voucher_awards"
    __table_args__ = (
        UniqueConstraint("game", "round_index", name="ux_game_voucher_round"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    game = Column(String(24), index=True, nullable=False)
    round_index = Column(Integer, index=True, nullable=False)
    winner_user_id = Column(String(64), nullable=False)
    winner_email = Column(String(255), nullable=True)
    voucher_code = Column(String(16), nullable=False)
    voucher_percent = Column(Integer, default=15)
    sent_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
