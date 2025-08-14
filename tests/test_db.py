from datetime import datetime, timedelta

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.db_sqlite_adapter import SQLiteAdapter


def test_member_flow(tmp_path):
    db_file = tmp_path / "db.sqlite"
    db = SQLiteAdapter(str(db_file))
    db.init()
    db.upsert_member("123", 111, "user", "User")
    member = db.get_member_by_membership_id("123")
    assert member["telegram_id"] == 111
    assert member["username"] == "user"
    db.set_confirmation("123", True, datetime.utcnow() + timedelta(seconds=10))
    member = db.get_member_by_membership_id("123")
    assert member["is_confirmed"] == 1
    assert isinstance(member["expires_at"], str)
    db.set_ban("123", True)
    member = db.get_member_by_membership_id("123")
    assert member["is_banned"] == 1
    db.upsert_join_link(1, "https://t.me/joinchat/test")
    link = db.get_join_link(1)
    assert link["invite_link"] == "https://t.me/joinchat/test"
    db.set_user_locale(111, "en")
    assert db.get_user_locale(111) == "en"
    db.upsert_media_cache("start.image", "en", "hash", "file")
    cache = db.get_media_cache("start.image", "en")
    assert cache["file_id"] == "file"
