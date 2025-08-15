from __future__ import annotations

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from modules.storage import db_get_member_by_telegram
from modules.post_join import maybe_send_post_join
from modules.log_utils import log_async_call


@log_async_call
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
        await maybe_send_post_join(context.bot, member, req.from_user)
    else:
        await context.bot.decline_chat_join_request(chat_id, user_id)


@log_async_call
async def on_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmu = update.chat_member
    old_s = cmu.old_chat_member.status
    new_s = cmu.new_chat_member.status
    user = cmu.new_chat_member.user
    if new_s in ("member", "administrator") and old_s in ("left", "kicked"):
        member = db_get_member_by_telegram(user.id)
        if member and member.get("is_confirmed"):
            await maybe_send_post_join(context.bot, member, user)
