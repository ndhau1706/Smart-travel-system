"""
Lightweight, idempotent migrations.

This project does not use Alembic; instead we run a small set of safe ALTERs on startup.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings


def _clamp_int(value: Any, lo: int, hi: int) -> int | None:
    try:
        parsed = int(value)
    except Exception:
        return None
    return max(lo, min(hi, parsed))


def _parse_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            decoded = json.loads(raw)
            items = decoded if isinstance(decoded, list) else []
        except Exception:
            return []
    else:
        return []

    out: list[str] = []
    for item in items:
        if not item:
            continue
        if not isinstance(item, str):
            item = str(item)
        cleaned = item.strip()
        if cleaned and cleaned not in out:
            out.append(cleaned)
        if len(out) >= 4:
            break
    return out


def _build_restaurant_description(
    cuisine: Any,
    price_level: Any,
    open_time: Any,
    close_time: Any,
    specialty: Any,
) -> str:
    cuisine_label = (cuisine or "").strip() if isinstance(cuisine, str) else ""
    if not cuisine_label:
        cuisine_label = "Nhà hàng"

    parts: list[str] = [cuisine_label]

    open_str = (open_time or "").strip() if isinstance(open_time, str) else ""
    close_str = (close_time or "").strip() if isinstance(close_time, str) else ""
    if open_str and close_str:
        parts.append(f"Giờ mở cửa {open_str} - {close_str}")

    level = _clamp_int(price_level, 1, 4)
    if level:
        parts.append(f"Mức giá {'$' * level}")

    tags = _parse_string_list(specialty)
    if tags:
        parts.append(f"Nổi bật: {', '.join(tags)}")

    return " • ".join(parts)


async def run_migrations(engine: AsyncEngine) -> None:
    if settings.CLOUD_SQL_CONNECTION_NAME:
        await _run_postgres_migrations(engine)
    else:
        await _run_sqlite_migrations(engine)


async def _run_postgres_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        # OTP storage (email_otps)
        # Ensure enum type exists (SQLAlchemy creates this on fresh installs).
        await conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'otppurpose') THEN
                        CREATE TYPE otppurpose AS ENUM ('REGISTER', 'RESET_PASSWORD');
                    END IF;
                END$$;
                """
            )
        )
        # Ensure table exists (create_all won't modify existing schema).
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS email_otps (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    purpose otppurpose NOT NULL,
                    code VARCHAR(128),
                    payload_json TEXT,
                    expires_at TIMESTAMPTZ,
                    attempts INTEGER DEFAULT 0,
                    resend_window_started_at TIMESTAMPTZ,
                    resend_count INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
        )
        # Support older/newer schemas: rename `code_hash` -> `code` if needed.
        await conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'email_otps' AND column_name = 'code_hash'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'email_otps' AND column_name = 'code'
                    ) THEN
                        ALTER TABLE email_otps RENAME COLUMN code_hash TO code;
                    END IF;
                END$$;
                """
            )
        )

        # Add missing columns if the table already existed with an older schema.
        await conn.execute(text("ALTER TABLE email_otps ADD COLUMN IF NOT EXISTS code VARCHAR(128)"))
        await conn.execute(text("ALTER TABLE email_otps ADD COLUMN IF NOT EXISTS payload_json TEXT"))
        await conn.execute(text("ALTER TABLE email_otps ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ"))
        await conn.execute(text("ALTER TABLE email_otps ADD COLUMN IF NOT EXISTS attempts INTEGER DEFAULT 0"))
        await conn.execute(text("ALTER TABLE email_otps ADD COLUMN IF NOT EXISTS resend_window_started_at TIMESTAMPTZ"))
        await conn.execute(text("ALTER TABLE email_otps ADD COLUMN IF NOT EXISTS resend_count INTEGER DEFAULT 0"))
        await conn.execute(text("ALTER TABLE email_otps ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"))
        await conn.execute(text("ALTER TABLE email_otps ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"))
        # Some older deployments used code VARCHAR(6). We store a SHA256 hex hash (64 chars),
        # so widen the column when needed.
        await conn.execute(
            text(
                """
                DO $$
                DECLARE maxlen integer;
                DECLARE dtype text;
                BEGIN
                    SELECT character_maximum_length, data_type
                    INTO maxlen, dtype
                    FROM information_schema.columns
                    WHERE table_name = 'email_otps' AND column_name = 'code';

                    IF dtype = 'character varying' AND maxlen IS NOT NULL AND maxlen < 128 THEN
                        EXECUTE 'ALTER TABLE email_otps ALTER COLUMN code TYPE VARCHAR(128)';
                    END IF;
                END$$;
                """
            )
        )
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_email_otps_email_purpose ON email_otps (email, purpose)"))

        # Restaurants ownership + rating override
        await conn.execute(text("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS owner_id VARCHAR(36)"))
        await conn.execute(text("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS rating_override DOUBLE PRECISION"))
        await conn.execute(text("ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS description_generated BOOLEAN DEFAULT TRUE"))
        await conn.execute(text("ALTER TABLE restaurants ALTER COLUMN description_generated SET DEFAULT TRUE"))

        # Menu approval workflow
        await conn.execute(text("ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS is_approved BOOLEAN DEFAULT TRUE"))

        # Review sentiment scoring
        await conn.execute(text("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS sentiment_score INTEGER"))
        await conn.execute(text("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS sentiment_polarity DOUBLE PRECISION"))
        await conn.execute(text("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS sentiment_subjectivity DOUBLE PRECISION"))

        # Enforce: 1 user can review a restaurant only once.
        # First, dedupe any existing duplicates (keep the most recently updated).
        await conn.execute(
            text(
                """
                DELETE FROM reviews
                WHERE id IN (
                  SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                             PARTITION BY user_id, restaurant_id
                             ORDER BY updated_at DESC, created_at DESC
                           ) AS rn
                    FROM reviews
                    WHERE user_id IS NOT NULL
                  ) t
                  WHERE t.rn > 1
                )
                """
            )
        )
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_reviews_user_restaurant ON reviews (user_id, restaurant_id)"
            )
        )

        # Treat empty descriptions as system-generated so they can be auto-filled.
        await conn.execute(
            text(
                """
                UPDATE restaurants
                SET description_generated = TRUE
                WHERE COALESCE(TRIM(description), '') = ''
                  AND (description_generated IS NULL OR description_generated = FALSE)
                """
            )
        )

        # Backfill restaurant descriptions (replace review-snippets / empty descriptions)
        result = await conn.execute(
            text(
                """
                SELECT r.id, r.cuisine, r.price_level, r.open_time, r.close_time, r.specialty
                FROM restaurants r
                WHERE COALESCE(r.description_generated, TRUE) = TRUE
                  AND (
                    COALESCE(TRIM(r.description), '') = ''
                    OR r.description NOT LIKE '%Giờ mở cửa%'
                  )
                """
            )
        )
        rows = result.fetchall()
        if rows:
            params = []
            for row in rows:
                mapping = row._mapping  # type: ignore[attr-defined]
                params.append(
                    {
                        "id": mapping["id"],
                        "description": _build_restaurant_description(
                            mapping["cuisine"],
                            mapping["price_level"],
                            mapping["open_time"],
                            mapping["close_time"],
                            mapping["specialty"],
                        ),
                    }
                )
            await conn.execute(
                text("UPDATE restaurants SET description = :description, description_generated = TRUE WHERE id = :id"),
                params,
            )


async def _run_sqlite_migrations(engine: AsyncEngine) -> None:
    # SQLite doesn't support IF NOT EXISTS for ADD COLUMN; check columns first.
    async with engine.begin() as conn:
        # OTP storage (email_otps)
        result = await conn.execute(text("PRAGMA table_info(email_otps)"))
        columns = {row[1] for row in result.fetchall()}
        if not columns:
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS email_otps (
                        id VARCHAR(36) PRIMARY KEY,
                        email VARCHAR(255) NOT NULL,
                        purpose VARCHAR(50) NOT NULL,
                        code VARCHAR(128),
                        payload_json TEXT,
                        expires_at DATETIME,
                        attempts INTEGER DEFAULT 0,
                        resend_window_started_at DATETIME,
                        resend_count INTEGER DEFAULT 0,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                    """
                )
            )
        else:
            if "code" not in columns:
                await conn.execute(text("ALTER TABLE email_otps ADD COLUMN code VARCHAR(128)"))
            if "payload_json" not in columns:
                await conn.execute(text("ALTER TABLE email_otps ADD COLUMN payload_json TEXT"))
            if "expires_at" not in columns:
                await conn.execute(text("ALTER TABLE email_otps ADD COLUMN expires_at DATETIME"))
            if "attempts" not in columns:
                await conn.execute(text("ALTER TABLE email_otps ADD COLUMN attempts INTEGER DEFAULT 0"))
            if "resend_window_started_at" not in columns:
                await conn.execute(text("ALTER TABLE email_otps ADD COLUMN resend_window_started_at DATETIME"))
            if "resend_count" not in columns:
                await conn.execute(text("ALTER TABLE email_otps ADD COLUMN resend_count INTEGER DEFAULT 0"))
            if "created_at" not in columns:
                await conn.execute(text("ALTER TABLE email_otps ADD COLUMN created_at DATETIME"))
            if "updated_at" not in columns:
                await conn.execute(text("ALTER TABLE email_otps ADD COLUMN updated_at DATETIME"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_email_otps_email_purpose ON email_otps (email, purpose)"))

        result = await conn.execute(text("PRAGMA table_info(restaurants)"))
        columns = {row[1] for row in result.fetchall()}
        if "owner_id" not in columns:
            await conn.execute(text("ALTER TABLE restaurants ADD COLUMN owner_id VARCHAR(36)"))
        if "rating_override" not in columns:
            await conn.execute(text("ALTER TABLE restaurants ADD COLUMN rating_override FLOAT"))
        if "description_generated" not in columns:
            await conn.execute(text("ALTER TABLE restaurants ADD COLUMN description_generated BOOLEAN DEFAULT 1"))

        result = await conn.execute(text("PRAGMA table_info(menu_items)"))
        columns = {row[1] for row in result.fetchall()}
        if "is_approved" not in columns:
            await conn.execute(text("ALTER TABLE menu_items ADD COLUMN is_approved BOOLEAN DEFAULT 1"))

        result = await conn.execute(text("PRAGMA table_info(reviews)"))
        columns = {row[1] for row in result.fetchall()}
        if "sentiment_score" not in columns:
            await conn.execute(text("ALTER TABLE reviews ADD COLUMN sentiment_score INTEGER"))
        if "sentiment_polarity" not in columns:
            await conn.execute(text("ALTER TABLE reviews ADD COLUMN sentiment_polarity FLOAT"))
        if "sentiment_subjectivity" not in columns:
            await conn.execute(text("ALTER TABLE reviews ADD COLUMN sentiment_subjectivity FLOAT"))

        await conn.execute(
            text(
                """
                DELETE FROM reviews
                WHERE id IN (
                  SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                             PARTITION BY user_id, restaurant_id
                             ORDER BY updated_at DESC, created_at DESC
                           ) AS rn
                    FROM reviews
                    WHERE user_id IS NOT NULL
                  ) t
                  WHERE t.rn > 1
                )
                """
            )
        )
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_reviews_user_restaurant ON reviews (user_id, restaurant_id)"
            )
        )

        await conn.execute(
            text(
                """
                UPDATE restaurants
                SET description_generated = 1
                WHERE COALESCE(TRIM(description), '') = ''
                  AND (description_generated IS NULL OR description_generated = 0)
                """
            )
        )

        # Backfill restaurant descriptions (replace review-snippets / empty descriptions)
        result = await conn.execute(
            text(
                """
                SELECT r.id, r.cuisine, r.price_level, r.open_time, r.close_time, r.specialty
                FROM restaurants r
                WHERE COALESCE(r.description_generated, 1) = 1
                  AND (
                    COALESCE(TRIM(r.description), '') = ''
                    OR r.description NOT LIKE '%Giờ mở cửa%'
                  )
                """
            )
        )
        rows = result.fetchall()
        if rows:
            params = []
            for row in rows:
                mapping = row._mapping  # type: ignore[attr-defined]
                params.append(
                    {
                        "id": mapping["id"],
                        "description": _build_restaurant_description(
                            mapping["cuisine"],
                            mapping["price_level"],
                            mapping["open_time"],
                            mapping["close_time"],
                            mapping["specialty"],
                        ),
                    }
                )
            await conn.execute(
                text("UPDATE restaurants SET description = :description, description_generated = 1 WHERE id = :id"),
                params,
            )
