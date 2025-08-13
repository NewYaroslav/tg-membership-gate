from __future__ import annotations

import re

from telegram import Update
from telegram.ext import ContextTypes

from modules.auth_utils import is_admin
from modules.config import id_config
from modules.template_engine import render_template
from modules.storage import db_set_ban
from modules.log_utils import log_async_call

id_pattern = re.compile(id_config.get("pattern", ".+"))


@log_async_call
async def handle_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return
    if not context.args:
        await update.message.reply_text(render_template("id_required.txt"))
        return
    membership_id = context.args[0].strip()
    if not id_pattern.fullmatch(membership_id):
        await update.message.reply_text(render_template("invalid_id.txt"))
        return
    db_set_ban(membership_id, True)
    await update.message.reply_text(
        render_template("admin_banned.txt", membership_id=membership_id)
    )


@log_async_call
async def handle_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return
    if not context.args:
        await update.message.reply_text(render_template("id_required.txt"))
        return
    membership_id = context.args[0].strip()
    if not id_pattern.fullmatch(membership_id):
        await update.message.reply_text(render_template("invalid_id.txt"))
        return
    db_set_ban(membership_id, False)
    await update.message.reply_text(
        render_template("admin_unbanned.txt", membership_id=membership_id)
    )

