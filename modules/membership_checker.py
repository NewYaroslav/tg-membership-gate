import asyncio
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from modules.template_engine import render_template
from modules.config import expiration, templates, renewal
from modules.storage import (
    db_fetch_members_for_warning,
    db_fetch_expired_members,
    db_fetch_recently_expired,
    db_mark_warning_sent,
    db_mark_grace_notified,
    db_set_confirmation,
    db_get_user_locale,
)
from modules.i18n import normalize_lang, get_button_text
from modules.time_utils import humanize_period
from modules.logging_config import logger

load_dotenv()
ACCESS_CHATS = [int(cid.strip()) for cid in os.getenv("ACCESS_CHATS", "").split(",") if cid.strip()]


async def check_membership_expiry_loop(app):
    warn_before = int(renewal.get("warn_before_sec", expiration.get("warn_before_sec", 86400)))
    check_interval = int(expiration.get("check_interval", 60))
    grace_after = int(renewal.get("grace_after_expiry_sec", 86400))
    warning_template = templates.get("renewal_warning", "renewal_warning.txt")
    grace_template = templates.get("grace_warning", "grace_warning.txt")
    expired_template = templates.get("expired", "expired.txt")
    plans = renewal.get("user_plans", [])
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
            user_lang = normalize_lang(db_get_user_locale(member["telegram_id"]))
            text = render_template(warning_template, remaining=humanize_period(remaining), lang=user_lang)
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            get_button_text(p.get("label"), user_lang),
                            callback_data=f"renew:{member['membership_id']}:{p['id']}",
                        )
                    ]
                    for p in plans
                ]
            )
            try:
                await app.bot.send_message(chat_id=member["telegram_id"], text=text, reply_markup=keyboard)
                db_mark_warning_sent(member["telegram_id"])
            except Exception as e:
                logger.exception("Failed to send warning to %s: %s", member["telegram_id"], e)
        for member in db_fetch_recently_expired(now, grace_after):
            expires_at = member.get("expires_at")
            if isinstance(expires_at, str):
                exp_dt = datetime.fromisoformat(expires_at)
            else:
                exp_dt = expires_at
            remaining = grace_after - int((now - exp_dt).total_seconds())
            user_lang = normalize_lang(db_get_user_locale(member["telegram_id"]))
            text = render_template(grace_template, remaining=humanize_period(remaining), lang=user_lang)
            try:
                await app.bot.send_message(chat_id=member["telegram_id"], text=text)
                db_mark_grace_notified(member["telegram_id"])
            except Exception as e:
                logger.exception("Failed to send grace warning to %s: %s", member["telegram_id"], e)

        cutoff = now - timedelta(seconds=grace_after)
        for member in db_fetch_expired_members(cutoff):
            user_lang = normalize_lang(db_get_user_locale(member["telegram_id"]))
            text = render_template(expired_template, lang=user_lang)
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

