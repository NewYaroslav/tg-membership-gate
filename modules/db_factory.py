from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

from .db_base import DatabaseAdapter
from .db_postgres_adapter import PostgresAdapter
from .db_sqlite_adapter import SQLiteAdapter

load_dotenv()

_DB: Optional[DatabaseAdapter] = None


def _read_backend() -> str:
    return os.getenv("DB_BACKEND", "sqlite")


def get_db() -> DatabaseAdapter:
    """Return singleton DB adapter based on configuration."""
    global _DB
    if _DB is None:
        backend = _read_backend().lower()
        log_queries = os.getenv("DB_LOG_QUERIES", "false").lower() == "true"
        if backend == "postgres":
            _DB = PostgresAdapter(
                host=os.getenv("PG_HOST", "127.0.0.1"),
                port=int(os.getenv("PG_PORT", "5432")),
                db=os.getenv("PG_DB", ""),
                user=os.getenv("PG_USER", ""),
                password=os.getenv("PG_PASSWORD", ""),
                sslmode=os.getenv("PG_SSLMODE", "disable"),
                log_queries=log_queries,
            )
        else:
            _DB = SQLiteAdapter(
                db_path=os.getenv("SQLITE_DB_PATH", "database/db.sqlite3"),
                log_queries=log_queries,
            )
    return _DB
