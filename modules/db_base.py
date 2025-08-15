"""Database adapter interface for membership management."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Iterable, Optional


class DatabaseAdapter(ABC):
    """Interface for database operations used by the bot."""

    log_queries: bool

    @abstractmethod
    def init(self) -> None:
        """Initialize database schema."""

    # -- Member operations -------------------------------------------------
    @abstractmethod
    def get_member_by_telegram(self, telegram_id: int) -> Optional[dict[str, Any]]:
        """Return member row by Telegram ID."""

    @abstractmethod
    def get_member_by_membership_id(self, membership_id: str) -> Optional[dict[str, Any]]:
        """Return member row by membership ID."""

    @abstractmethod
    def get_member_by_username(self, username: str) -> Optional[dict[str, Any]]:
        """Return member row by username."""

    @abstractmethod
    def upsert_member(
        self,
        membership_id: str,
        telegram_id: int,
        username: str | None,
        full_name: str | None,
        is_confirmed: bool = False,
    ) -> None:
        """Insert or update member information."""

    @abstractmethod
    def set_confirmation(self, membership_id: str, is_confirmed: bool, expires_at: datetime | None = None) -> None:
        """Set confirmation status and expiration time for member."""

    @abstractmethod
    def set_ban(self, membership_id: str, is_banned: bool) -> None:
        """Set ban flag for member."""

    @abstractmethod
    def update_expiration(self, membership_id: str, expires_at: datetime | None) -> None:
        """Update member expiration timestamp."""

    @abstractmethod
    def get_member_by_id_or_username(self, key: int | str) -> Optional[dict[str, Any]]:
        """Return member by Telegram ID or username."""

    @abstractmethod
    def set_banned(self, member_id: int, banned: bool) -> None:
        """Set ban flag by Telegram ID."""

    @abstractmethod
    def set_confirmed(self, member_id: int, confirmed: bool, expires_at: datetime | None = None) -> None:
        """Set confirmation by Telegram ID."""

    @abstractmethod
    def delete_member_by_id(self, member_id: int) -> None:
        """Remove member row by internal ID."""

    @abstractmethod
    def delete_user_by_telegram_id(self, telegram_id: int) -> None:
        """Remove user row by Telegram ID."""

    @abstractmethod
    def iter_members(self, scope: str) -> Iterable[dict[str, Any]]:
        """Iterate members for export with optional scope filter."""

    @abstractmethod
    def fetch_members_for_warning(self, now: datetime, threshold: int) -> list[dict[str, Any]]:
        """Return members whose expiration is within threshold seconds and warning not sent."""

    @abstractmethod
    def fetch_expired_members(self, now: datetime) -> list[dict[str, Any]]:
        """Return members whose expiration has passed."""

    @abstractmethod
    def mark_warning_sent(self, telegram_id: int) -> None:
        """Mark that expiration warning was sent to member."""

    # -- Join request links ----------------------------------------------
    @abstractmethod
    def get_join_link(self, chat_id: int) -> Optional[dict[str, Any]]:
        """Retrieve stored join request invite link for chat."""

    @abstractmethod
    def upsert_join_link(self, chat_id: int, invite_link: str) -> None:
        """Insert or update join request invite link."""

    # -- Renewal helpers -------------------------------------------------
    @abstractmethod
    def fetch_recently_expired(self, now: datetime, grace_sec: int) -> list[dict[str, Any]]:
        """Members whose expiration passed but still within grace period."""

    @abstractmethod
    def mark_grace_notified(self, telegram_id: int) -> None:
        """Mark that user has been notified about grace period."""

    # -- Admin management --------------------------------------------------
    @abstractmethod
    def is_admin(self, telegram_id: int) -> bool:
        """Check if Telegram ID belongs to admin."""

    @abstractmethod
    def add_admin(self, telegram_id: int, is_top_level: bool = False) -> None:
        """Insert or update admin."""

    @abstractmethod
    def remove_admin(self, telegram_id: int) -> None:
        """Remove admin."""

    @abstractmethod
    def list_admins(self) -> list[dict[str, Any]]:
        """Return list of admins."""

    # -- Testing helpers ---------------------------------------------------
    @abstractmethod
    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        """Execute raw SQL (for testing)."""

    # -- User preferences ---------------------------------------------------
    @abstractmethod
    def get_user_locale(self, telegram_id: int) -> Optional[str]:
        """Return stored locale for user."""

    @abstractmethod
    def set_user_locale(self, telegram_id: int, lang: str) -> None:
        """Persist user locale."""

    # -- Media cache ------------------------------------------------------
    @abstractmethod
    def get_media_cache(self, asset_key: str, lang: str) -> Optional[dict[str, Any]]:
        """Return cached file_id and hash for asset."""

    @abstractmethod
    def upsert_media_cache(self, asset_key: str, lang: str, file_hash: str, file_id: str) -> None:
        """Update or insert cache entry for asset."""

