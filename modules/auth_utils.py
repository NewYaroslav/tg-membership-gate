from __future__ import annotations

from modules.storage import db_is_admin, ROOT_ADMIN_ID


def is_admin(telegram_id: int) -> bool:
    """Return True if telegram_id has admin privileges."""
    try:
        telegram_id = int(telegram_id)
    except (ValueError, TypeError):
        return False
    return telegram_id == ROOT_ADMIN_ID or db_is_admin(telegram_id)


def is_root_admin(telegram_id: int) -> bool:
    """Return True if telegram_id matches ROOT_ADMIN_ID."""
    try:
        return int(telegram_id) == ROOT_ADMIN_ID
    except (ValueError, TypeError):
        return False
