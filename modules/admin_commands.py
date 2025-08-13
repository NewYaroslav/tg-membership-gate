from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from modules.storage import db_is_admin, db_set_ban
from modules.log_utils import log_async_call


@log_async_call
async def handle_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Укажите ID")
        return
    membership_id = context.args[0]
    db_set_ban(membership_id, True)
    await update.message.reply_text(f"ID {membership_id} заблокирован")


@log_async_call
async def handle_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Укажите ID")
        return
    membership_id = context.args[0]
    db_set_ban(membership_id, False)
    await update.message.reply_text(f"ID {membership_id} разблокирован")

