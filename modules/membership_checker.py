import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv
from modules.template_engine import render_template
from modules.config import expiration, templates
from modules.storage import (
    db_fetch_members_for_warning,
    db_fetch_expired_members,
    db_mark_warning_sent,
    db_set_confirmation,
)
from modules.time_utils import humanize_period
from modules.logging_config import logger

load_dotenv()
ACCESS_CHATS = [int(cid.strip()) for cid in os.getenv("ACCESS_CHATS", "").split(",") if cid.strip()]


async def check_membership_expiry_loop(app):
    warn_before = int(expiration.get("warn_before_sec", 86400))
    check_interval = int(expiration.get("check_interval", 60))
    warning_template = templates.get("warning", "expiry_warning.txt")
    expired_template = templates.get("expired", "expired.txt")
    while True:
        await asyncio.sleep(check_interval)
        now = datetime.utcnow()
        for member in db_fetch_members_for_warning(now, warn_before):
            expires_at = member.get("expires_at")
            if isinstance(expires_at, str):
                expires_dt = datetime.fromisoformat(expires_at)
            else:
                expires_dt = expires_at
            remaining = int((expires_dt - now).total_seconds())
            text = render_template(warning_template, remaining=humanize_period(remaining))
            try:
                await app.bot.send_message(chat_id=member["telegram_id"], text=text)
                db_mark_warning_sent(member["telegram_id"])
            except Exception as e:
                logger.exception("Failed to send warning to %s: %s", member["telegram_id"], e)

        for member in db_fetch_expired_members(now):
            text = render_template(expired_template)
            try:
                await app.bot.send_message(chat_id=member["telegram_id"], text=text)
                for chat_id in ACCESS_CHATS:
                    try:
                        await app.bot.ban_chat_member(chat_id=chat_id, user_id=member["telegram_id"])
                        await app.bot.unban_chat_member(chat_id=chat_id, user_id=member["telegram_id"])
                    except Exception as e:
                        logger.warning("Failed to remove %s from %s: %s", member["telegram_id"], chat_id, e)
            finally:
                db_set_confirmation(member["membership_id"], False, None)

