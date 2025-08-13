from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable, Optional

from .db_base import DatabaseAdapter
from .logging_config import logger

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "sqlite.sql"


class SQLiteAdapter(DatabaseAdapter):
    """SQLite implementation."""

    def __init__(self, db_path: str, log_queries: bool = False) -> None:
        self.db_path = db_path
        self.log_queries = log_queries

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

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

    def add_allowed_email(self, email: str) -> None:
        self._run(
            """
            INSERT INTO allowed_emails (email, is_banned)
            VALUES (?, 0)
            ON CONFLICT(email) DO UPDATE SET is_banned=0
            """,
            [email],
        )
        row = self._run(
            "SELECT id FROM allowed_emails WHERE email=?", [email], fetchone=True
        )
        if row:
            email_id = row[0]
            self._run(
                """
                UPDATE users SET is_authorized=1
                WHERE email_id=? AND is_authorized=0
                """,
                [email_id],
            )
        else:
            logger.warning("Email %s inserted but id not found", email)

    def get_telegram_ids_by_email(self, email: str) -> list[int]:
        row = self._run(
            "SELECT id FROM allowed_emails WHERE email=?", [email], fetchone=True
        )
        if not row:
            return []
        email_id = row[0]
        rows = self._run(
            "SELECT telegram_id FROM users WHERE email_id=?",
            [email_id],
            fetchall=True,
        )
        return [r[0] for r in rows]

    def remove_allowed_email(self, email: str) -> None:
        self._run("DELETE FROM allowed_emails WHERE email=?", [email])

    def unlink_users_from_email(self, email: str) -> None:
        row = self._run(
            "SELECT id FROM allowed_emails WHERE email=?", [email], fetchone=True
        )
        if not row:
            return
        email_id = row[0]
        self._run(
            "UPDATE users SET email_id=NULL, is_authorized=0 WHERE email_id=?",
            [email_id],
        )
        self._run("DELETE FROM allowed_emails WHERE id=?", [email_id])

    def ban_allowed_email(self, email: str) -> None:
        self._run(
            "UPDATE allowed_emails SET is_banned=1 WHERE email=?", [email]
        )

    def unban_allowed_email(self, email: str) -> None:
        self._run(
            "UPDATE allowed_emails SET is_banned=0 WHERE email=?", [email]
        )

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[dict[str, Any]]:
        row = self._run(
            "SELECT * FROM users WHERE telegram_id=?",
            [telegram_id],
            fetchone=True,
        )
        return dict(row) if row else None

    def get_users_by_email(self, email: str) -> list[dict[str, Any]]:
        row = self._run(
            "SELECT id FROM allowed_emails WHERE email=?", [email], fetchone=True
        )
        if not row:
            return []
        email_id = row[0]
        rows = self._run(
            "SELECT * FROM users WHERE email_id=?", [email_id], fetchall=True
        )
        return [dict(r) for r in rows]

    def get_email_by_id(self, email_id: int) -> Optional[str]:
        row = self._run(
            "SELECT email FROM allowed_emails WHERE id=?", [email_id], fetchone=True
        )
        return row[0] if row else None

    def get_email_row(self, email: str) -> Optional[dict[str, Any]]:
        row = self._run(
            "SELECT * FROM allowed_emails WHERE email=?", [email], fetchone=True
        )
        return dict(row) if row else None

    def add_user(
        self,
        email: str,
        telegram_id: int,
        username: str | None = None,
        full_name: str | None = None,
        authorized: bool = True,
    ) -> None:
        row = self._run(
            "SELECT id, is_banned FROM allowed_emails WHERE email=?",
            [email],
            fetchone=True,
        )
        if not row:
            self._run(
                "INSERT INTO allowed_emails (email, is_banned) VALUES (?,1)",
                [email],
            )
            row = self._run(
                "SELECT id, is_banned FROM allowed_emails WHERE email=?",
                [email],
                fetchone=True,
            )
        email_id, is_banned = row
        is_authorized = int(authorized and not is_banned)
        self._run(
            """
            INSERT OR REPLACE INTO users
            (telegram_id, username, full_name, email_id, is_authorized)
            VALUES (?,?,?,?,?)
            """,
            [telegram_id, username, full_name, email_id, is_authorized],
        )

    def update_user_email(self, telegram_id: int, new_email: str) -> bool:
        row = self._run(
            "SELECT id, is_banned FROM allowed_emails WHERE email=?",
            [new_email],
            fetchone=True,
        )
        if not row or row[1]:
            return False
        email_id = row[0]
        self._run(
            "UPDATE users SET email_id=?, is_authorized=1 WHERE telegram_id=?",
            [email_id, telegram_id],
        )
        return True

    def is_admin(self, telegram_id: int) -> bool:
        row = self._run(
            "SELECT COUNT(*) FROM admins WHERE telegram_id=?",
            [telegram_id],
            fetchone=True,
        )
        return row[0] > 0 if row else False

    def add_admin(self, telegram_id: int, is_top_level: bool = False) -> None:
        self._run(
            "INSERT OR REPLACE INTO admins (telegram_id, is_top_level) VALUES (?,?)",
            [telegram_id, int(is_top_level)],
        )

    def remove_admin(self, telegram_id: int) -> None:
        self._run("DELETE FROM admins WHERE telegram_id=?", [telegram_id])

    def list_admins(self) -> list[dict[str, Any]]:
        rows = self._run("SELECT * FROM admins", fetchall=True)
        return [dict(r) for r in rows]

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        self._run(sql, params)
