from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv

from modules.log_utils import log_sync_call
from modules.db_factory import get_db

load_dotenv()
ROOT_ADMIN_ID = int(os.getenv("ROOT_ADMIN_ID", 0))


@log_sync_call
def db_init() -> None:
    get_db().init()


@log_sync_call
def db_get_member_by_telegram(telegram_id: int):
    return get_db().get_member_by_telegram(telegram_id)


@log_sync_call
def db_get_member_by_membership_id(membership_id: str):
    return get_db().get_member_by_membership_id(membership_id)


# Backward-compatible alias
db_get_member_by_id = db_get_member_by_membership_id


@log_sync_call
def db_get_member_by_username(username: str):
    return get_db().get_member_by_username(username)


@log_sync_call
def db_upsert_member(membership_id: str, telegram_id: int, username: str | None, full_name: str | None, is_confirmed: bool = False) -> None:
    get_db().upsert_member(membership_id, telegram_id, username, full_name, is_confirmed)


@log_sync_call
def db_set_confirmation(membership_id: str, is_confirmed: bool, expires_at: datetime | None = None) -> None:
    get_db().set_confirmation(membership_id, is_confirmed, expires_at)


@log_sync_call
def db_set_ban(membership_id: str, is_banned: bool) -> None:
    get_db().set_ban(membership_id, is_banned)


@log_sync_call
def db_get_member_by_id_or_username(key: int | str):
    return get_db().get_member_by_id_or_username(key)


@log_sync_call
def db_set_banned(member_id: int, banned: bool) -> None:
    get_db().set_banned(member_id, banned)


@log_sync_call
def db_set_confirmed(member_id: int, confirmed: bool, expires_at: datetime | None) -> None:
    get_db().set_confirmed(member_id, confirmed, expires_at)


@log_sync_call
def db_delete_member_by_id(member_id: int) -> None:
    get_db().delete_member_by_id(member_id)


@log_sync_call
def db_delete_user_by_telegram_id(telegram_id: int) -> None:
    get_db().delete_user_by_telegram_id(telegram_id)


@log_sync_call
def db_iter_members(scope: str):
    return list(get_db().iter_members(scope))


@log_sync_call
def db_update_expiration(membership_id: str, expires_at: datetime | None) -> None:
    get_db().update_expiration(membership_id, expires_at)


@log_sync_call
def db_fetch_members_for_warning(now: datetime, threshold: int):
    return get_db().fetch_members_for_warning(now, threshold)


@log_sync_call
def db_fetch_expired_members(now: datetime):
    return get_db().fetch_expired_members(now)


@log_sync_call
def db_mark_warning_sent(telegram_id: int) -> None:
    get_db().mark_warning_sent(telegram_id)


@log_sync_call
def db_get_join_link(chat_id: int):
    return get_db().get_join_link(chat_id)


@log_sync_call
def db_upsert_join_link(chat_id: int, invite_link: str) -> None:
    get_db().upsert_join_link(chat_id, invite_link)


@log_sync_call
def db_fetch_recently_expired(now: datetime, grace_sec: int):
    return get_db().fetch_recently_expired(now, grace_sec)


@log_sync_call
def db_mark_grace_notified(telegram_id: int) -> None:
    get_db().mark_grace_notified(telegram_id)


@log_sync_call
def db_is_admin(telegram_id: int) -> bool:
    return get_db().is_admin(telegram_id)


@log_sync_call
def db_add_admin(telegram_id: int, is_top_level: bool = False) -> None:
    get_db().add_admin(telegram_id, is_top_level)


@log_sync_call
def db_remove_admin(telegram_id: int) -> None:
    get_db().remove_admin(telegram_id)


@log_sync_call
def db_list_admins() -> list[dict]:
    return get_db().list_admins()


@log_sync_call
def db_get_user_locale(telegram_id: int) -> str | None:
    return get_db().get_user_locale(telegram_id)


@log_sync_call
def db_set_user_locale(telegram_id: int, lang: str) -> None:
    get_db().set_user_locale(telegram_id, lang)


@log_sync_call
def db_get_media_cache(asset_key: str, lang: str) -> dict | None:
    return get_db().get_media_cache(asset_key, lang)


@log_sync_call
def db_upsert_media_cache(asset_key: str, lang: str, file_hash: str, file_id: str) -> None:
    get_db().upsert_media_cache(asset_key, lang, file_hash, file_id)

