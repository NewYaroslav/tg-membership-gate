from __future__ import annotations

import os
from dotenv import load_dotenv

from modules.log_utils import log_sync_call
from modules.db_factory import get_db

load_dotenv()
ROOT_ADMIN_ID = int(os.getenv("ROOT_ADMIN_ID", 0))


@log_sync_call
def db_init() -> None:
    get_db().init()


@log_sync_call
def db_add_allowed_email(email: str) -> None:
    get_db().add_allowed_email(email)


@log_sync_call
def db_get_telegram_ids_by_email(email: str) -> list[int]:
    return get_db().get_telegram_ids_by_email(email)


@log_sync_call
def db_remove_allowed_email(email: str) -> None:
    get_db().remove_allowed_email(email)


@log_sync_call
def db_unlink_users_from_email(email: str) -> None:
    get_db().unlink_users_from_email(email)


@log_sync_call
def db_ban_allowed_email(email: str) -> None:
    get_db().ban_allowed_email(email)


@log_sync_call
def db_unban_allowed_email(email: str) -> None:
    get_db().unban_allowed_email(email)


@log_sync_call
def db_get_user_by_telegram_id(telegram_id: int):
    return get_db().get_user_by_telegram_id(telegram_id)


@log_sync_call
def db_get_users_by_email(email: str) -> list[dict]:
    return get_db().get_users_by_email(email)


@log_sync_call
def db_get_email_by_id(email_id: int):
    return get_db().get_email_by_id(email_id)


@log_sync_call
def db_get_email_row(email: str):
    return get_db().get_email_row(email)


@log_sync_call
def db_add_user(
    email: str,
    telegram_id: int,
    username: str | None = None,
    full_name: str | None = None,
    authorized: bool = True,
) -> None:
    get_db().add_user(email, telegram_id, username, full_name, authorized)


@log_sync_call
def db_update_user_email(telegram_id: int, new_email: str) -> bool:
    return get_db().update_user_email(telegram_id, new_email)


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
