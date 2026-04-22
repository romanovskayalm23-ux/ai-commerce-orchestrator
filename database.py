from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import aiosqlite


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _month_key() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row

    async def close(self) -> None:
        if self.conn is not None:
            await self.conn.close()

    async def init(self) -> None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        await self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL DEFAULT '',
                plan TEXT NOT NULL DEFAULT 'free',
                daily_used INTEGER NOT NULL DEFAULT 0,
                monthly_used INTEGER NOT NULL DEFAULT 0,
                package_credits INTEGER NOT NULL DEFAULT 0,
                referrals_count INTEGER NOT NULL DEFAULT 0,
                referred_by INTEGER,
                last_daily_reset TEXT NOT NULL,
                last_monthly_reset TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                product_photo_url TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                visual_url TEXT NOT NULL,
                copy_text TEXT NOT NULL,
                hashtags TEXT NOT NULL,
                description TEXT NOT NULL,
                views INTEGER NOT NULL DEFAULT 0,
                clicks INTEGER NOT NULL DEFAULT 0,
                conversions INTEGER NOT NULL DEFAULT 0,
                ctr REAL NOT NULL DEFAULT 0.0,
                conversion_rate REAL NOT NULL DEFAULT 0.0,
                is_winner INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS winning_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                avg_ctr REAL NOT NULL,
                avg_conversion_rate REAL NOT NULL,
                usage_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS queue_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                campaign_id INTEGER,
                prompt TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
            CREATE INDEX IF NOT EXISTS idx_variants_campaign_id ON variants(campaign_id);
            CREATE INDEX IF NOT EXISTS idx_queue_tasks_status ON queue_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_winning_patterns_platform ON winning_patterns(platform);
            """
        )
        await self._migrate_users_table()
        await self.conn.commit()

    async def _migrate_users_table(self) -> None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        cur = await self.conn.execute("PRAGMA table_info(users)")
        rows = await cur.fetchall()
        existing = {row[1] for row in rows}

        required_columns = {
            "username": "TEXT NOT NULL DEFAULT ''",
            "plan": "TEXT NOT NULL DEFAULT 'free'",
            "daily_used": "INTEGER NOT NULL DEFAULT 0",
            "monthly_used": "INTEGER NOT NULL DEFAULT 0",
            "package_credits": "INTEGER NOT NULL DEFAULT 0",
            "referrals_count": "INTEGER NOT NULL DEFAULT 0",
            "referred_by": "INTEGER",
            "last_daily_reset": f"TEXT NOT NULL DEFAULT '{_today_iso()}'",
            "last_monthly_reset": f"TEXT NOT NULL DEFAULT '{_month_key()}'",
            "created_at": f"TEXT NOT NULL DEFAULT '{_utc_now_iso()}'",
        }

        for column, ddl in required_columns.items():
            if column not in existing:
                await self.conn.execute(f"ALTER TABLE users ADD COLUMN {column} {ddl}")

    async def _fetch_user(self, user_id: int) -> dict[str, Any] | None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        cur = await self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def _reset_limits_if_needed(self, user_id: int) -> None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        user = await self._fetch_user(user_id)
        if user is None:
            return

        today = _today_iso()
        month = _month_key()
        changed = False

        if user.get("last_daily_reset") != today:
            await self.conn.execute(
                "UPDATE users SET daily_used = 0, last_daily_reset = ? WHERE user_id = ?",
                (today, user_id),
            )
            changed = True

        if user.get("last_monthly_reset") != month:
            await self.conn.execute(
                "UPDATE users SET monthly_used = 0, last_monthly_reset = ? WHERE user_id = ?",
                (month, user_id),
            )
            changed = True

        if changed:
            await self.conn.commit()

    async def get_or_create_user(self, user_id: int, username: str = "") -> dict[str, Any]:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        await self._reset_limits_if_needed(user_id)
        user = await self._fetch_user(user_id)

        if user is not None:
            return user

        now = _utc_now_iso()
        today = _today_iso()
        month = _month_key()

        await self.conn.execute(
            """
            INSERT INTO users (user_id, username, last_daily_reset, last_monthly_reset, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, username, today, month, now),
        )
        await self.conn.commit()

        user = await self._fetch_user(user_id)
        if user is None:
            raise RuntimeError("Failed to create user.")
        return user

    async def increment_daily_used(self, user_id: int) -> None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        await self.conn.execute(
            "UPDATE users SET daily_used = daily_used + 1 WHERE user_id = ?",
            (user_id,),
        )
        await self.conn.commit()

    async def increment_monthly_used(self, user_id: int) -> None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        await self.conn.execute(
            "UPDATE users SET monthly_used = monthly_used + 1 WHERE user_id = ?",
            (user_id,),
        )
        await self.conn.commit()

    # Campaign methods
    async def create_campaign(
        self, user_id: int, product_name: str, product_photo_url: str
    ) -> int:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        now = _utc_now_iso()
        cur = await self.conn.execute(
            """
            INSERT INTO campaigns (user_id, product_name, product_photo_url, status, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            (user_id, product_name, product_photo_url, now, now),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def get_campaign(self, campaign_id: int) -> dict[str, Any] | None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        cur = await self.conn.execute(
            "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def get_user_campaigns(self, user_id: int, limit: int = 10) -> list[dict[str, Any]]:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        cur = await self.conn.execute(
            "SELECT * FROM campaigns WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cur.fetchall()
        return [dict(row) for row in rows]

    async def update_campaign_status(self, campaign_id: int, status: str) -> None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        now = _utc_now_iso()
        await self.conn.execute(
            "UPDATE campaigns SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, campaign_id),
        )
        await self.conn.commit()

    # Variant methods
    async def create_variant(
        self,
        campaign_id: int,
        platform: str,
        visual_url: str,
        copy_text: str,
        hashtags: str,
        description: str,
    ) -> int:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        now = _utc_now_iso()
        cur = await self.conn.execute(
            """
            INSERT INTO variants (campaign_id, platform, visual_url, copy_text, hashtags, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (campaign_id, platform, visual_url, copy_text, hashtags, description, now),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def get_campaign_variants(self, campaign_id: int) -> list[dict[str, Any]]:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        cur = await self.conn.execute(
            "SELECT * FROM variants WHERE campaign_id = ? ORDER BY created_at",
            (campaign_id,),
        )
        rows = await cur.fetchall()
        return [dict(row) for row in rows]

    async def get_variant(self, variant_id: int) -> dict[str, Any] | None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        cur = await self.conn.execute("SELECT * FROM variants WHERE id = ?", (variant_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def update_variant_metrics(
        self, variant_id: int, views: int, clicks: int, conversions: int
    ) -> None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        ctr = (clicks / views * 100) if views > 0 else 0.0
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0.0

        await self.conn.execute(
            """
            UPDATE variants
            SET views = ?, clicks = ?, conversions = ?, ctr = ?, conversion_rate = ?
            WHERE id = ?
            """,
            (views, clicks, conversions, ctr, conversion_rate, variant_id),
        )
        await self.conn.commit()

    async def mark_variant_as_winner(self, variant_id: int) -> None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        variant = await self.get_variant(variant_id)
        if not variant:
            return

        await self.conn.execute(
            "UPDATE variants SET is_winner = 0 WHERE campaign_id = ?",
            (variant["campaign_id"],),
        )
        await self.conn.execute(
            "UPDATE variants SET is_winner = 1 WHERE id = ?", (variant_id,)
        )
        await self.conn.commit()

    async def get_winner_variant(self, campaign_id: int) -> dict[str, Any] | None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        cur = await self.conn.execute(
            "SELECT * FROM variants WHERE campaign_id = ? AND is_winner = 1",
            (campaign_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    # Winning patterns methods
    async def save_winning_pattern(
        self,
        platform: str,
        pattern_type: str,
        pattern_data: dict,
        avg_ctr: float,
        avg_conversion_rate: float,
    ) -> int:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        now = _utc_now_iso()
        pattern_json = json.dumps(pattern_data)

        cur = await self.conn.execute(
            """
            INSERT INTO winning_patterns (platform, pattern_type, pattern_data, avg_ctr, avg_conversion_rate, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (platform, pattern_type, pattern_json, avg_ctr, avg_conversion_rate, now),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def get_best_patterns(self, platform: str, limit: int = 5) -> list[dict[str, Any]]:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        cur = await self.conn.execute(
            """
            SELECT * FROM winning_patterns
            WHERE platform = ?
            ORDER BY (avg_ctr * avg_conversion_rate) DESC
            LIMIT ?
            """,
            (platform, limit),
        )
        rows = await cur.fetchall()
        return [dict(row) for row in rows]

    async def increment_pattern_usage(self, pattern_id: int) -> None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        await self.conn.execute(
            "UPDATE winning_patterns SET usage_count = usage_count + 1 WHERE id = ?",
            (pattern_id,),
        )
        await self.conn.commit()

    # Queue methods
    async def create_queue_task(
        self, user_id: int, campaign_id: int, prompt: str, priority: int
    ) -> int:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        now = _utc_now_iso()
        cur = await self.conn.execute(
            """
            INSERT INTO queue_tasks (user_id, campaign_id, prompt, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', ?, ?, ?)
            """,
            (user_id, campaign_id, prompt, priority, now, now),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def set_queue_task_status(self, task_id: int, status: str) -> None:
        if self.conn is None:
            raise RuntimeError("Database is not connected.")

        now = _utc_now_iso()
        await self.conn.execute(
            "UPDATE queue_tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, task_id),
        )
        await self.conn.commit()
