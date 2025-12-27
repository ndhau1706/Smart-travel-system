from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
import string
import uuid
from typing import List, Optional

from slugify import slugify
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Blog, BlogStatus, UserVoucher, UserVoucherStatus, Voucher, VoucherType


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_voucher_code(prefix: str = "BLOG", length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}-{suffix}"


def _candidate_slug(base: str, suffix: int) -> str:
    return base if suffix == 0 else f"{base}-{suffix}"


def generate_unique_slug(db: Session, title: str, max_attempts: int = 50) -> str:
    base = slugify(title) or "post"
    for i in range(max_attempts):
        candidate = _candidate_slug(base, i)
        exists = db.query(Blog.id).filter(Blog.slug == candidate).first()
        if not exists:
            return candidate
    raise RuntimeError("Unable to generate unique slug")


def create_blog(db: Session, author_id: str, title: str, content: str, cover_url: Optional[str]) -> Blog:
    for _ in range(10):
        slug = generate_unique_slug(db, title)
        blog = Blog(
            id=str(uuid.uuid4()),
            author_id=author_id,
            title=title,
            slug=slug,
            content=content,
            cover_url=cover_url,
            status=BlogStatus.draft,
            created_at=utcnow(),
            updated_at=utcnow(),
            views=0,
        )
        db.add(blog)
        try:
            db.commit()
            db.refresh(blog)
            return blog
        except IntegrityError:
            db.rollback()
    raise RuntimeError("Failed to create blog due to slug conflicts")


def get_blog_by_id(db: Session, blog_id: str) -> Optional[Blog]:
    return db.query(Blog).filter(Blog.id == blog_id).first()


def get_blog_by_slug(db: Session, slug: str) -> Optional[Blog]:
    stmt = (
        update(Blog)
        .where(Blog.slug == slug, Blog.status == BlogStatus.published)
        .values(views=Blog.views + 1, updated_at=utcnow())
        .returning(Blog.id)
    )
    result = db.execute(stmt)
    row = result.fetchone()
    if row:
        db.commit()
        return db.query(Blog).filter(Blog.id == row.id).first()
    return None


def list_blogs(db: Session, skip: int, limit: int, status: Optional[BlogStatus]) -> List[Blog]:
    query = db.query(Blog)
    if status:
        query = query.filter(Blog.status == status)
    else:
        query = query.filter(Blog.status == BlogStatus.published)
    return query.order_by(Blog.created_at.desc()).offset(skip).limit(limit).all()


def count_blogs(db: Session, status: Optional[BlogStatus]) -> int:
    query = db.query(func.count(Blog.id))
    if status:
        query = query.filter(Blog.status == status)
    else:
        query = query.filter(Blog.status == BlogStatus.published)
    return query.scalar() or 0


def update_blog(db: Session, blog: Blog, updates: dict) -> Blog:
    for _ in range(5):
        if "title" in updates and updates["title"]:
            updates["slug"] = generate_unique_slug(db, updates["title"])
        for key, value in updates.items():
            setattr(blog, key, value)
        blog.updated_at = utcnow()
        db.add(blog)
        try:
            db.commit()
            db.refresh(blog)
            return blog
        except IntegrityError:
            db.rollback()
    raise RuntimeError("Failed to update blog due to slug conflicts")


def delete_blog(db: Session, blog: Blog) -> None:
    db.delete(blog)
    db.commit()


def _get_or_create_active_voucher(db: Session) -> Voucher:
    voucher = (
        db.query(Voucher)
        .filter(Voucher.is_active.is_(True))
        .order_by(Voucher.created_at.desc())
        .first()
    )
    if voucher:
        return voucher

    for _ in range(5):
        voucher = Voucher(
            id=str(uuid.uuid4()),
            code=generate_voucher_code(),
            type=VoucherType.percent,
            value=10,
            max_discount=None,
            min_order_value=None,
            start_at=utcnow(),
            expire_at=utcnow() + timedelta(days=30),
            usage_limit=1,
            used_count=0,
            is_active=True,
            created_at=utcnow(),
        )
        db.add(voucher)
        try:
            db.commit()
            db.refresh(voucher)
            return voucher
        except IntegrityError:
            db.rollback()
    raise RuntimeError("Failed to create voucher template")


def publish_blog(db: Session, blog: Blog, user_id: str) -> dict:
    if blog.status == BlogStatus.published:
        return {
            "status": "already_published",
            "voucher_awarded": False,
            "voucher_code": None,
        }

    voucher_awarded = False
    voucher_code = None
    now = utcnow()

    voucher = _get_or_create_active_voucher(db)
    try:
        updated = (
            db.query(Blog)
            .filter(Blog.id == blog.id, Blog.status == BlogStatus.draft)
            .update({"status": BlogStatus.published, "published_at": now, "updated_at": now})
        )
        if updated == 0:
            db.commit()
            return {
                "status": "already_published",
                "voucher_awarded": False,
                "voucher_code": None,
            }
        db.flush()

        try:
            with db.begin_nested():
                stmt = (
                    insert(UserVoucher)
                    .values(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        voucher_id=voucher.id,
                        source="blog_publish",
                        source_ref_id=blog.id,
                        claimed_at=now,
                        status=UserVoucherStatus.available,
                    )
                    .on_conflict_do_nothing(
                        index_elements=["user_id", "source", "source_ref_id"]
                    )
                )
                result = db.execute(stmt)
                if result.rowcount == 1:
                    voucher_awarded = True
                    voucher_code = voucher.code
                    db.query(Voucher).filter(Voucher.id == voucher.id).update(
                        {"used_count": Voucher.used_count + 1}
                    )
        except IntegrityError:
            voucher_awarded = False
            voucher_code = None

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "status": "published",
        "voucher_awarded": voucher_awarded,
        "voucher_code": voucher_code,
    }


def list_user_vouchers(db: Session, user_id: str) -> List[dict]:
    stmt = (
        select(
            Voucher.code,
            Voucher.type,
            Voucher.value,
            Voucher.expire_at,
            UserVoucher.status,
        )
        .join(UserVoucher, UserVoucher.voucher_id == Voucher.id)
        .where(UserVoucher.user_id == user_id)
        .order_by(UserVoucher.claimed_at.desc())
    )
    results = db.execute(stmt).all()
    return [
        {
            "code": row.code,
            "type": row.type,
            "value": float(row.value),
            "expire_at": row.expire_at,
            "status": row.status,
        }
        for row in results
    ]
