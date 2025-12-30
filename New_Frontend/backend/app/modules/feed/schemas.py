"""
Newsfeed schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

ReactionType = Literal["like", "love", "wow", "insightful"]


class FeedReactionCounts(BaseModel):
    like: int = 0
    love: int = 0
    wow: int = 0
    insightful: int = 0


class FeedCommentResponse(BaseModel):
    id: str
    author_name: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class FeedPostResponse(BaseModel):
    id: str
    author_name: str
    author_role: Optional[str] = None
    author_avatar: Optional[str] = None
    title: str
    body: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    location: Optional[str] = None
    image: Optional[str] = None
    reactions: FeedReactionCounts
    my_reaction: Optional[ReactionType] = None
    comments: list[FeedCommentResponse] = Field(default_factory=list)
    comment_count: int = 0
    share_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None


class FeedPostSummary(BaseModel):
    id: str
    title: str
    author_name: str


class FeedWallItem(BaseModel):
    id: str
    post_id: str
    shared_by: str
    shared_at: datetime
    post: Optional[FeedPostSummary] = None


class CreateFeedPostRequest(BaseModel):
    author_name: Optional[str] = None
    author_role: Optional[str] = None
    author_avatar: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[list[str]] = None
    location: Optional[str] = None
    image: Optional[str] = None


class FeedReactionRequest(BaseModel):
    reaction: Optional[ReactionType] = None


class FeedReactionResponse(BaseModel):
    post_id: str
    reactions: FeedReactionCounts
    my_reaction: Optional[ReactionType] = None


class FeedCommentRequest(BaseModel):
    author_name: Optional[str] = None
    content: str


class FeedCommentEnvelope(BaseModel):
    post_id: str
    comment: FeedCommentResponse
    comment_count: int


class FeedShareRequest(BaseModel):
    shared_by: Optional[str] = None


class FeedShareEnvelope(BaseModel):
    post_id: str
    share_id: str
    share_count: int
    wall_item: Optional[FeedWallItem] = None
