from __future__ import annotations

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from modules.storage import db_get_member_by_telegram


async def on_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    user_id = req.from_user.id
    chat_id = req.chat.id
    member = db_get_member_by_telegram(user_id)
    ok = False
    if member and member.get("is_confirmed") and not member.get("is_banned"):
        expires = member.get("expires_at")
        if not expires:
            ok = True
        else:
            if isinstance(expires, str):
                expires_dt = datetime.fromisoformat(expires)
            else:
                expires_dt = expires
            ok = expires_dt > datetime.utcnow()
    if ok:
        await context.bot.approve_chat_join_request(chat_id, user_id)
    else:
        await context.bot.decline_chat_join_request(chat_id, user_id)
