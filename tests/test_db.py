import logging
import os

import pytest

from modules import storage
from modules import db_factory


def _reset_db(monkeypatch) -> None:
    db_factory._DB = None  # type: ignore[attr-defined]
    for var in [
        "DB_BACKEND",
        "SQLITE_DB_PATH",
        "PG_HOST",
        "PG_PORT",
        "PG_DB",
        "PG_USER",
        "PG_PASSWORD",
    ]:
        monkeypatch.delenv(var, raising=False)


def test_sqlite_smoke(tmp_path, monkeypatch):
    _reset_db(monkeypatch)
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    db_file = tmp_path / "test.sqlite"
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_file))

    storage.db_init()
    storage.db_add_allowed_email("user@example.com")
    storage.db_add_user("user@example.com", 1)
    user = storage.db_get_user_by_telegram_id(1)
    assert user["telegram_id"] == 1


def test_postgres_smoke(monkeypatch):
    if not os.getenv("PG_HOST"):
        pytest.skip("PostgreSQL not configured")
    _reset_db(monkeypatch)
    monkeypatch.setenv("DB_BACKEND", "postgres")
    try:
        storage.db_init()
    except Exception:
        pytest.skip("PostgreSQL unavailable")
    storage.db_add_allowed_email("pg@example.com")
    storage.db_add_user("pg@example.com", 2)
    user = storage.db_get_user_by_telegram_id(2)
    assert user["telegram_id"] == 2


def test_invalid_sql_logs(tmp_path, monkeypatch, caplog):
    _reset_db(monkeypatch)
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    db_file = tmp_path / "test.sqlite"
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_file))
    storage.db_init()
    caplog.set_level(logging.ERROR)
    with pytest.raises(Exception):
        db_factory.get_db().execute("SELECT * FROM missing_table")
    assert "missing_table" in caplog.text
