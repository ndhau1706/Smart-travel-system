from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BlogStatus(str, Enum):
    draft = "draft"
    published = "published"


class VoucherType(str, Enum):
    percent = "percent"
    fixed = "fixed"


class UserVoucherStatus(str, Enum):
    available = "available"
    used = "used"
    expired = "expired"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)


class Blog(Base):
    __tablename__ = "blogs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False)
    cover_url = Column(String(1024), nullable=True)
    status = Column(SqlEnum(BlogStatus, name="blog_status"), nullable=False, default=BlogStatus.draft)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    views = Column(Integer, nullable=False, default=0)


class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(64), nullable=False, unique=True, index=True)
    type = Column(SqlEnum(VoucherType, name="voucher_type"), nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    max_discount = Column(Numeric(10, 2), nullable=True)
    min_order_value = Column(Numeric(10, 2), nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    expire_at = Column(DateTime(timezone=True), nullable=False)
    usage_limit = Column(Integer, nullable=False, default=1)
    used_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UserVoucher(Base):
    __tablename__ = "user_vouchers"
    __table_args__ = (
        UniqueConstraint("user_id", "source", "source_ref_id", name="uq_user_voucher_source"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    voucher_id = Column(String(36), ForeignKey("vouchers.id"), nullable=False)
    source = Column(String(64), nullable=False)
    source_ref_id = Column(String(36), nullable=False)
    claimed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    used_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        SqlEnum(UserVoucherStatus, name="user_voucher_status"),
        nullable=False,
        default=UserVoucherStatus.available,
    )
