"""Database adapter interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional


class DatabaseAdapter(ABC):
    """Interface for database operations."""

    log_queries: bool

    @abstractmethod
    def init(self) -> None:
        """Initialize database schema."""

    @abstractmethod
    def add_allowed_email(self, email: str) -> None:
        """Insert or unban an email."""

    @abstractmethod
    def get_telegram_ids_by_email(self, email: str) -> list[int]:
        """Return Telegram IDs linked with email."""

    @abstractmethod
    def remove_allowed_email(self, email: str) -> None:
        """Delete email from whitelist."""

    @abstractmethod
    def unlink_users_from_email(self, email: str) -> None:
        """Unlink users and delete email."""

    @abstractmethod
    def ban_allowed_email(self, email: str) -> None:
        """Mark email as banned."""

    @abstractmethod
    def unban_allowed_email(self, email: str) -> None:
        """Remove ban from email."""

    @abstractmethod
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[dict[str, Any]]:
        """Fetch user by Telegram ID."""

    @abstractmethod
    def get_users_by_email(self, email: str) -> list[dict[str, Any]]:
        """Fetch all users for email."""

    @abstractmethod
    def get_email_by_id(self, email_id: int) -> Optional[str]:
        """Return email string by its ID."""

    @abstractmethod
    def get_email_row(self, email: str) -> Optional[dict[str, Any]]:
        """Return full email row."""

    @abstractmethod
    def add_user(self, email: str, telegram_id: int, username: str | None = None,
                 full_name: str | None = None, authorized: bool = True) -> None:
        """Insert or update user."""

    @abstractmethod
    def update_user_email(self, telegram_id: int, new_email: str) -> bool:
        """Update user's email."""

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

    @abstractmethod
    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        """Execute raw SQL (testing)."""
