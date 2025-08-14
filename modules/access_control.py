from __future__ import annotations

import os
from typing import Dict, Any

from modules.logging_config import logger

ACCESS_CHATS = [int(cid.strip()) for cid in os.getenv("ACCESS_CHATS", "").split(",") if cid.strip()]

async def ban_in_all_access_chats(bot, user_id: int) -> Dict[str, Any]:
    summary = {"ok": [], "errors": {}}
    for chat_id in ACCESS_CHATS:
        try:
            await bot.ban_chat_member(chat_id, user_id)
            summary["ok"].append(chat_id)
        except Exception as e:  # pragma: no cover - network errors
            logger.warning("ban fail %s: %s", chat_id, e)
            summary["errors"][chat_id] = str(e)
    return summary

async def unban_in_all_access_chats(bot, user_id: int) -> Dict[str, Any]:
    summary = {"ok": [], "errors": {}}
    for chat_id in ACCESS_CHATS:
        try:
            await bot.unban_chat_member(chat_id, user_id, only_if_banned=False)
            summary["ok"].append(chat_id)
        except Exception as e:  # pragma: no cover - network errors
            logger.warning("unban fail %s: %s", chat_id, e)
            summary["errors"][chat_id] = str(e)
    return summary

async def kick_in_all_access_chats(bot, user_id: int) -> Dict[str, Any]:
    summary = {"ok": [], "errors": {}}
    for chat_id in ACCESS_CHATS:
        try:
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id)
            summary["ok"].append(chat_id)
        except Exception as e:  # pragma: no cover
            logger.warning("kick fail %s: %s", chat_id, e)
            summary["errors"][chat_id] = str(e)
    return summary
