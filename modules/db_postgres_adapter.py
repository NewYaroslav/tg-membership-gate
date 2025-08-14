from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Iterable, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from .db_base import DatabaseAdapter
from .logging_config import logger

SCHEMA_PATH = __file__.rsplit('/', 2)[0] + '/schema/postgres.sql'


class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL implementation of the database adapter."""

    def __init__(
        self,
        host: str,
        port: int,
        db: str,
        user: str,
        password: str,
        sslmode: str = "disable",
        log_queries: bool = False,
    ) -> None:
        self.conn_params = dict(host=host, port=port, dbname=db, user=user, password=password, sslmode=sslmode)
        self.log_queries = log_queries

    # Internal helpers -------------------------------------------------
    def _run(self, sql: str, params: Iterable[Any] | None = None,
             fetchone: bool = False, fetchall: bool = False) -> Any:
        params = params or []
        start = time.time()
        with psycopg2.connect(**self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                res = None
                if fetchone:
                    res = cur.fetchone()
                elif fetchall:
                    res = cur.fetchall()
                conn.commit()
        if self.log_queries:
            duration = (time.time() - start) * 1000
            logger.debug("SQL: %s params=%s %.1fms", sql, params, duration)
        return res

    # Schema -----------------------------------------------------------
    def init(self) -> None:
        with psycopg2.connect(**self.conn_params) as conn:
            with conn.cursor() as cur:
                with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                    cur.execute(f.read())
            conn.commit()
        logger.info("Database initialized")

    # Member operations ------------------------------------------------
    def get_member_by_telegram(self, telegram_id: int) -> Optional[dict[str, Any]]:
        row = self._run(
            "SELECT * FROM members WHERE telegram_id=%s",
            [telegram_id],
            fetchone=True,
        )
        return dict(row) if row else None

    def get_member_by_membership_id(self, membership_id: str) -> Optional[dict[str, Any]]:
        row = self._run(
            "SELECT * FROM members WHERE membership_id=%s",
            [membership_id],
            fetchone=True,
        )
        return dict(row) if row else None

    def upsert_member(
        self,
        membership_id: str,
        telegram_id: int,
        username: str | None,
        full_name: str | None,
        is_confirmed: bool = False,
    ) -> None:
        self._run(
            """
            INSERT INTO members (membership_id, telegram_id, username, full_name, is_confirmed)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT(membership_id) DO UPDATE SET
                telegram_id=EXCLUDED.telegram_id,
                username=EXCLUDED.username,
                full_name=EXCLUDED.full_name
            """,
            [membership_id, telegram_id, username, full_name, is_confirmed],
        )

    def set_confirmation(self, membership_id: str, is_confirmed: bool, expires_at: datetime | None = None) -> None:
        self._run(
            "UPDATE members SET is_confirmed=%s, expires_at=%s, warn_sent_at=NULL, grace_notified_at=NULL WHERE membership_id=%s",
            [is_confirmed, expires_at, membership_id],
        )

    def set_ban(self, membership_id: str, is_banned: bool) -> None:
        self._run(
            "UPDATE members SET is_banned=%s WHERE membership_id=%s",
            [is_banned, membership_id],
        )

    def update_expiration(self, membership_id: str, expires_at: datetime | None) -> None:
        self._run(
            "UPDATE members SET expires_at=%s, warn_sent_at=NULL, grace_notified_at=NULL WHERE membership_id=%s",
            [expires_at, membership_id],
        )

    def fetch_members_for_warning(self, now: datetime, threshold: int) -> list[dict[str, Any]]:
        rows = self._run(
            "SELECT * FROM members WHERE is_confirmed=TRUE AND expires_at IS NOT NULL AND warn_sent_at IS NULL",
            fetchall=True,
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            if 0 < (r["expires_at"] - now).total_seconds() <= threshold:
                result.append(dict(r))
        return result

    def fetch_expired_members(self, now: datetime) -> list[dict[str, Any]]:
        rows = self._run(
            "SELECT * FROM members WHERE is_confirmed=TRUE AND expires_at IS NOT NULL",
            fetchall=True,
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            if r["expires_at"] <= now:
                result.append(dict(r))
        return result

    def mark_warning_sent(self, telegram_id: int) -> None:
        self._run("UPDATE members SET warn_sent_at=NOW() WHERE telegram_id=%s", [telegram_id])

    # Join links -------------------------------------------------------
    def get_join_link(self, chat_id: int) -> Optional[dict[str, Any]]:
        row = self._run(
            "SELECT * FROM join_invite_links WHERE chat_id=%s",
            [chat_id],
            fetchone=True,
        )
        return dict(row) if row else None

    def upsert_join_link(self, chat_id: int, invite_link: str) -> None:
        self._run(
            """
            INSERT INTO join_invite_links (chat_id, invite_link)
            VALUES (%s,%s)
            ON CONFLICT(chat_id) DO UPDATE SET invite_link=EXCLUDED.invite_link
            """,
            [chat_id, invite_link],
        )

    # Renewal helpers --------------------------------------------------
    def fetch_recently_expired(self, now: datetime, grace_sec: int) -> list[dict[str, Any]]:
        rows = self._run(
            "SELECT * FROM members WHERE is_confirmed=TRUE AND expires_at IS NOT NULL AND grace_notified_at IS NULL",
            fetchall=True,
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            diff = (now - r["expires_at"]).total_seconds()
            if 0 <= diff <= grace_sec:
                result.append(dict(r))
        return result

    def mark_grace_notified(self, telegram_id: int) -> None:
        self._run("UPDATE members SET grace_notified_at=NOW() WHERE telegram_id=%s", [telegram_id])

    # Admin operations --------------------------------------------------
    def is_admin(self, telegram_id: int) -> bool:
        row = self._run(
            "SELECT 1 FROM admins WHERE telegram_id=%s",
            [telegram_id],
            fetchone=True,
        )
        return row is not None

    def add_admin(self, telegram_id: int, is_top_level: bool = False) -> None:
        self._run(
            """
            INSERT INTO admins (telegram_id, is_top_level)
            VALUES (%s,%s)
            ON CONFLICT(telegram_id) DO UPDATE SET is_top_level=EXCLUDED.is_top_level
            """,
            [telegram_id, is_top_level],
        )

    def remove_admin(self, telegram_id: int) -> None:
        self._run("DELETE FROM admins WHERE telegram_id=%s", [telegram_id])

    def list_admins(self) -> list[dict[str, Any]]:
        rows = self._run("SELECT * FROM admins", fetchall=True)
        return [dict(r) for r in rows]

    # Testing helper ---------------------------------------------------
    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        self._run(sql, params)

