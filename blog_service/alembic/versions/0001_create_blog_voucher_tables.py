"""create blog and voucher tables

Revision ID: 0001_create_blog_voucher_tables
Revises: 
Create Date: 2025-12-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_create_blog_voucher_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    blog_status = sa.Enum("draft", "published", name="blog_status", create_type=False)
    voucher_type = sa.Enum("percent", "fixed", name="voucher_type", create_type=False)
    user_voucher_status = sa.Enum("available", "used", "expired", name="user_voucher_status", create_type=False)

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" not in inspector.get_table_names():
        op.create_table(
            "users",
            sa.Column("id", sa.String(length=36), primary_key=True),
        )

    op.create_table(
        "blogs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("cover_url", sa.String(length=1024), nullable=True),
        sa.Column("status", blog_status, nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("slug", name="uq_blogs_slug"),
    )
    op.create_index("ix_blogs_slug", "blogs", ["slug"], unique=True)

    op.create_table(
        "vouchers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("type", voucher_type, nullable=False),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_discount", sa.Numeric(10, 2), nullable=True),
        sa.Column("min_order_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expire_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usage_limit", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code", name="uq_vouchers_code"),
    )
    op.create_index("ix_vouchers_code", "vouchers", ["code"], unique=True)

    op.create_table(
        "user_vouchers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("voucher_id", sa.String(length=36), sa.ForeignKey("vouchers.id"), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_ref_id", sa.String(length=36), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", user_voucher_status, nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "source",
            "source_ref_id",
            name="uq_user_voucher_source",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_vouchers")
    op.drop_index("ix_vouchers_code", table_name="vouchers")
    op.drop_table("vouchers")
    op.drop_index("ix_blogs_slug", table_name="blogs")
    op.drop_table("blogs")

    bind = op.get_bind()
    sa.Enum(name="user_voucher_status").drop(bind, checkfirst=True)
    sa.Enum(name="voucher_type").drop(bind, checkfirst=True)
    sa.Enum(name="blog_status").drop(bind, checkfirst=True)
