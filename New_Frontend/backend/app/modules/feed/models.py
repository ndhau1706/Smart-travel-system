"""
Newsfeed persistence models.
"""
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint

from app.core.database import Base


class FeedPost(Base):
    __tablename__ = "feed_posts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    author_id = Column(String(36), nullable=True, index=True)
    author_name = Column(String(120), nullable=False)
    author_role = Column(String(120), nullable=True)
    author_avatar = Column(String(500), nullable=True)

    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    location = Column(String(200), nullable=True)
    image = Column(String(500), nullable=True)

    like_count = Column(Integer, default=0)
    love_count = Column(Integer, default=0)
    wow_count = Column(Integer, default=0)
    insightful_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeedReaction(Base):
    __tablename__ = "feed_reactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("feed_posts.id"), index=True, nullable=False)
    actor_id = Column(String(64), index=True, nullable=False)
    reaction = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeedComment(Base):
    __tablename__ = "feed_comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("feed_posts.id"), index=True, nullable=False)
    actor_id = Column(String(64), index=True, nullable=False)
    author_name = Column(String(120), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedShare(Base):
    __tablename__ = "feed_shares"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("feed_posts.id"), index=True, nullable=False)
    actor_id = Column(String(64), index=True, nullable=False)
    shared_by = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedVoucher(Base):
    __tablename__ = "feed_vouchers"
    __table_args__ = (
        UniqueConstraint("post_id", name="ux_feed_voucher_post"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("feed_posts.id"), index=True, nullable=False)
    user_id = Column(String(64), index=True, nullable=False)
    voucher_code = Column(String(16), nullable=False)
    voucher_percent = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
