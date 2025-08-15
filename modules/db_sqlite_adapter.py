from __future__ import annotations

import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from .db_base import DatabaseAdapter
from .logging_config import logger

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "sqlite.sql"


class SQLiteAdapter(DatabaseAdapter):
    """SQLite implementation of the database adapter."""

    def __init__(self, db_path: str, log_queries: bool = False) -> None:
        self.db_path = db_path
        self.log_queries = log_queries

    # Internal helpers -------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _run(self, sql: str, params: Iterable[Any] | None = None,
             fetchone: bool = False, fetchall: bool = False) -> Any:
        params = params or []
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        start = time.time()
        try:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            if fetchone:
                res = cur.fetchone()
            elif fetchall:
                res = cur.fetchall()
            else:
                res = None
            conn.commit()
            if self.log_queries:
                duration = (time.time() - start) * 1000
                logger.debug("SQL: %s params=%s %.1fms", sql, params, duration)
            return res
        except Exception as exc:
            conn.rollback()
            logger.error("DB error: %s", exc)
            raise
        finally:
            conn.close()

    # Schema -----------------------------------------------------------
    def init(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self._connect()
        try:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()
            logger.info("Database initialized")
        finally:
            conn.close()

    # Member operations ------------------------------------------------
    def get_member_by_telegram(self, telegram_id: int) -> Optional[dict[str, Any]]:
        row = self._run(
            """
            SELECT m.*, u.username, u.full_name FROM members m
            LEFT JOIN users u ON m.telegram_id=u.telegram_id
            WHERE m.telegram_id=?
            """,
            [telegram_id],
            fetchone=True,
        )
        if row:
            res = dict(row)
            exp = res.get("expires_at")
            if exp is not None:
                res["expires_at"] = datetime.utcfromtimestamp(exp).isoformat()
            return res
        return None

    def get_member_by_membership_id(self, membership_id: str) -> Optional[dict[str, Any]]:
        row = self._run(
            """
            SELECT m.*, u.username, u.full_name FROM members m
            LEFT JOIN users u ON m.telegram_id=u.telegram_id
            WHERE m.membership_id=?
            """,
            [membership_id],
            fetchone=True,
        )
        if row:
            res = dict(row)
            exp = res.get("expires_at")
            if exp is not None:
                res["expires_at"] = datetime.utcfromtimestamp(exp).isoformat()
            return res
        return None

    def upsert_member(
        self,
        membership_id: str,
        telegram_id: int,
        username: str | None,
        full_name: str | None,
        is_confirmed: bool = False,
    ) -> None:
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.cursor()
            # upsert user row -------------------------------------------------
            cur.execute(
                """
                INSERT INTO users (telegram_id, username, full_name)
                VALUES (?,?,?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username=excluded.username,
                    full_name=excluded.full_name
                """,
                (telegram_id, username, full_name),
            )

            # fetch existing member rows -----------------------------------
            cur.execute(
                "SELECT * FROM members WHERE membership_id=?",
                (membership_id,),
            )
            row_mid = cur.fetchone()
            cur.execute(
                "SELECT * FROM members WHERE telegram_id=?",
                (telegram_id,),
            )
            row_tid = cur.fetchone()

            ic = 1 if is_confirmed else 0

            if row_mid and not row_tid:
                # A. membership exists, telegram not yet bound
                cur.execute(
                    "UPDATE members SET telegram_id=?, is_confirmed=COALESCE(is_confirmed, ?) WHERE id=?",
                    (telegram_id, ic, row_mid["id"]),
                )
            elif not row_mid and row_tid:
                # B. telegram bound to different membership -> rebind
                cur.execute(
                    "UPDATE members SET membership_id=?, is_confirmed=COALESCE(is_confirmed, ?) WHERE id=?",
                    (membership_id, ic, row_tid["id"]),
                )
            elif row_mid and row_tid and row_mid["id"] != row_tid["id"]:
                # C. conflicting membership/telegram pairs
                cur.execute(
                    "UPDATE members SET telegram_id=NULL WHERE id=?",
                    (row_tid["id"],),
                )
                cur.execute(
                    "UPDATE members SET telegram_id=?, is_confirmed=COALESCE(is_confirmed, ?) WHERE id=?",
                    (telegram_id, ic, row_mid["id"]),
                )
            elif row_mid and row_tid and row_mid["id"] == row_tid["id"]:
                # existing mapping, ensure confirmation field is set
                cur.execute(
                    "UPDATE members SET is_confirmed=COALESCE(is_confirmed, ?) WHERE id=?",
                    (ic, row_mid["id"]),
                )
            else:
                # D. no records yet
                cur.execute(
                    "INSERT INTO members (membership_id, telegram_id, is_confirmed) VALUES (?,?,?)",
                    (membership_id, telegram_id, ic),
                )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.error("Database error in db_upsert_member: %s", exc)
            raise
        finally:
            conn.close()

    def set_confirmation(self, membership_id: str, is_confirmed: bool, expires_at: datetime | None = None) -> None:
        expires = int(expires_at.timestamp()) if expires_at else None
        self._run(
            "UPDATE members SET is_confirmed=?, expires_at=?, warn_sent_at=NULL, grace_notified_at=NULL WHERE membership_id=?",
            [int(is_confirmed), expires, membership_id],
        )

    def set_ban(self, membership_id: str, is_banned: bool) -> None:
        self._run(
            "UPDATE members SET is_banned=? WHERE membership_id=?",
            [int(is_banned), membership_id],
        )

    # New helpers using telegram_id -----------------------------------
    def get_member_by_id_or_username(self, key: int | str) -> Optional[dict[str, Any]]:
        try:
            key_int = int(key)
            return self.get_member_by_telegram(key_int)
        except (ValueError, TypeError):
            username = str(key).lstrip("@")
            row = self._run(
                """
                SELECT m.*, u.username, u.full_name FROM members m
                JOIN users u ON m.telegram_id=u.telegram_id
                WHERE u.username=?
                """,
                [username],
                fetchone=True,
        )
        if row:
            res = dict(row)
            exp = res.get("expires_at")
            if exp is not None:
                res["expires_at"] = datetime.utcfromtimestamp(exp).isoformat()
            return res
        return None

    def get_member_by_username(self, username: str) -> Optional[dict[str, Any]]:
        row = self._run(
            """
            SELECT m.*, u.username, u.full_name FROM members m
            JOIN users u ON m.telegram_id=u.telegram_id
            WHERE u.username=?
            """,
            [username],
            fetchone=True,
        )
        if row:
            res = dict(row)
            exp = res.get("expires_at")
            if exp is not None:
                res["expires_at"] = datetime.utcfromtimestamp(exp).isoformat()
            return res
        return None

    def set_banned(self, member_id: int, banned: bool) -> None:
        self._run(
            "UPDATE members SET is_banned=? WHERE telegram_id=?",
            [int(banned), member_id],
        )

    def set_confirmed(
        self, member_id: int, confirmed: bool, expires_at: datetime | None = None
    ) -> None:
        expires = int(expires_at.timestamp()) if expires_at else None
        self._run(
            "UPDATE members SET is_confirmed=?, expires_at=?, warn_sent_at=NULL, grace_notified_at=NULL WHERE telegram_id=?",
            [int(confirmed), expires, member_id],
        )

    def delete_member_by_id(self, member_id: int) -> None:
        self._run("DELETE FROM members WHERE id=?", [member_id])

    def delete_user_by_telegram_id(self, telegram_id: int) -> None:
        self._run("DELETE FROM users WHERE telegram_id=?", [telegram_id])

    def iter_members(self, scope: str) -> Iterable[dict[str, Any]]:
        now = datetime.utcnow()
        if scope == "active":
            rows = self._run(
                "SELECT m.*, u.username, u.full_name FROM members m LEFT JOIN users u ON m.telegram_id=u.telegram_id WHERE m.is_banned=0 AND m.is_confirmed=1",
                fetchall=True,
            )
            result = []
            for r in rows:
                exp = r["expires_at"]
                if not exp or datetime.utcfromtimestamp(exp) > now:
                    row = dict(r)
                    if exp:
                        row["expires_at"] = datetime.utcfromtimestamp(exp).isoformat()
                    result.append(row)
            return result
        if scope == "expired":
            rows = self._run(
                "SELECT m.*, u.username, u.full_name FROM members m LEFT JOIN users u ON m.telegram_id=u.telegram_id WHERE m.is_confirmed=1 AND m.expires_at IS NOT NULL",
                fetchall=True,
            )
            result = []
            for r in rows:
                exp = r["expires_at"]
                if exp and datetime.utcfromtimestamp(exp) <= now:
                    row = dict(r)
                    row["expires_at"] = datetime.utcfromtimestamp(exp).isoformat()
                    result.append(row)
            return result
        if scope == "banned":
            rows = self._run(
                "SELECT m.*, u.username, u.full_name FROM members m LEFT JOIN users u ON m.telegram_id=u.telegram_id WHERE m.is_banned=1",
                fetchall=True,
            )
            result = []
            for r in rows:
                exp = r["expires_at"]
                row = dict(r)
                if exp:
                    row["expires_at"] = datetime.utcfromtimestamp(exp).isoformat()
                result.append(row)
            return result
        rows = self._run(
            "SELECT m.*, u.username, u.full_name FROM members m LEFT JOIN users u ON m.telegram_id=u.telegram_id",
            fetchall=True,
        )
        result = []
        for r in rows:
            exp = r["expires_at"]
            row = dict(r)
            if exp:
                row["expires_at"] = datetime.utcfromtimestamp(exp).isoformat()
            result.append(row)
        return result

    def update_expiration(self, membership_id: str, expires_at: datetime | None) -> None:
        expires = int(expires_at.timestamp()) if expires_at else None
        self._run(
            "UPDATE members SET expires_at=?, warn_sent_at=NULL, grace_notified_at=NULL WHERE membership_id=?",
            [expires, membership_id],
        )

    def fetch_members_for_warning(self, now: datetime, threshold: int) -> list[dict[str, Any]]:
        rows = self._run(
            "SELECT * FROM members WHERE is_confirmed=1 AND expires_at IS NOT NULL AND warn_sent_at IS NULL",
            fetchall=True,
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            expires = datetime.utcfromtimestamp(r["expires_at"])
            if 0 < (expires - now).total_seconds() <= threshold:
                row = dict(r)
                row["expires_at"] = expires.isoformat()
                result.append(row)
        return result

    def fetch_expired_members(self, now: datetime) -> list[dict[str, Any]]:
        rows = self._run(
            "SELECT * FROM members WHERE is_confirmed=1 AND expires_at IS NOT NULL",
            fetchall=True,
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            expires = datetime.utcfromtimestamp(r["expires_at"])
            if expires <= now:
                row = dict(r)
                row["expires_at"] = expires.isoformat()
                result.append(row)
        return result

    def mark_warning_sent(self, telegram_id: int) -> None:
        now = datetime.utcnow().isoformat()
        self._run("UPDATE members SET warn_sent_at=? WHERE telegram_id=?", [now, telegram_id])

    # Join links -------------------------------------------------------
    def get_join_link(self, chat_id: int) -> Optional[dict[str, Any]]:
        row = self._run(
            "SELECT * FROM join_invite_links WHERE chat_id=?",
            [chat_id],
            fetchone=True,
        )
        return dict(row) if row else None

    def upsert_join_link(self, chat_id: int, invite_link: str) -> None:
        self._run(
            """
            INSERT INTO join_invite_links (chat_id, invite_link)
            VALUES (?,?)
            ON CONFLICT(chat_id) DO UPDATE SET invite_link=excluded.invite_link
            """,
            [chat_id, invite_link],
        )

    # Renewal helpers --------------------------------------------------
    def fetch_recently_expired(self, now: datetime, grace_sec: int) -> list[dict[str, Any]]:
        rows = self._run(
            "SELECT * FROM members WHERE is_confirmed=1 AND expires_at IS NOT NULL AND grace_notified_at IS NULL",
            fetchall=True,
        )
        result: list[dict[str, Any]] = []
        for r in rows:
            expires = datetime.utcfromtimestamp(r["expires_at"])
            diff = (now - expires).total_seconds()
            if 0 <= diff <= grace_sec:
                row = dict(r)
                row["expires_at"] = expires.isoformat()
                result.append(row)
        return result

    def mark_grace_notified(self, telegram_id: int) -> None:
        now = datetime.utcnow().isoformat()
        self._run("UPDATE members SET grace_notified_at=? WHERE telegram_id=?", [now, telegram_id])

    # Admin operations --------------------------------------------------
    def is_admin(self, telegram_id: int) -> bool:
        row = self._run(
            "SELECT 1 FROM admins WHERE telegram_id=?",
            [telegram_id],
            fetchone=True,
        )
        return row is not None

    def add_admin(self, telegram_id: int, is_top_level: bool = False) -> None:
        self._run(
            """
            INSERT INTO admins (telegram_id, is_top_level)
            VALUES (?,?)
            ON CONFLICT(telegram_id) DO UPDATE SET is_top_level=excluded.is_top_level
            """,
            [telegram_id, int(is_top_level)],
        )

    def remove_admin(self, telegram_id: int) -> None:
        self._run("DELETE FROM admins WHERE telegram_id=?", [telegram_id])

    def list_admins(self) -> list[dict[str, Any]]:
        rows = self._run("SELECT * FROM admins", fetchall=True)
        return [dict(r) for r in rows]

    # Testing helper ---------------------------------------------------
    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        self._run(sql, params)

    # User preferences -------------------------------------------------
    def get_user_locale(self, telegram_id: int) -> Optional[str]:
        row = self._run(
            "SELECT locale FROM users WHERE telegram_id=?",
            [telegram_id],
            fetchone=True,
        )
        return row["locale"] if row else None

    def set_user_locale(self, telegram_id: int, lang: str) -> None:
        self._run(
            """
            INSERT INTO users (telegram_id, locale)
            VALUES (?,?)
            ON CONFLICT(telegram_id) DO UPDATE SET locale=excluded.locale
            """,
            [telegram_id, lang],
        )

    # Media cache ------------------------------------------------------
    def get_media_cache(self, asset_key: str, lang: str) -> Optional[dict[str, Any]]:
        row = self._run(
            "SELECT file_hash, file_id FROM media_cache WHERE asset_key=? AND lang=?",
            [asset_key, lang],
            fetchone=True,
        )
        return dict(row) if row else None

    def upsert_media_cache(self, asset_key: str, lang: str, file_hash: str, file_id: str) -> None:
        self._run(
            """
            INSERT INTO media_cache (asset_key, lang, file_hash, file_id)
            VALUES (?,?,?,?)
            ON CONFLICT(asset_key, lang) DO UPDATE SET
                file_hash=excluded.file_hash,
                file_id=excluded.file_id,
                updated_at=CURRENT_TIMESTAMP
            """,
            [asset_key, lang, file_hash, file_id],
        )

