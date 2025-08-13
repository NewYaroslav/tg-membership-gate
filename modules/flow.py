import os
import re
from datetime import datetime, timedelta
from typing import List

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from modules.config import telegram_start, templates, id_config, admin_buttons, admin_ui
from modules.storage import (
    db_get_member_by_telegram,
    db_get_member_by_id,
    db_upsert_member,
    db_set_confirmation,
    db_set_ban,
    ROOT_ADMIN_ID,
)
from modules.auth_utils import is_admin
from modules.states import UserState
from modules.template_engine import render_template
from modules.log_utils import log_async_call
from modules.logging_config import logger
from modules.time_utils import humanize_period

load_dotenv()
ACCESS_LINKS = [link.strip() for link in os.getenv("ACCESS_LINKS", "").split(",") if link.strip()]

id_pattern = re.compile(id_config.get("pattern", ".+"))


def build_admin_keyboard(membership_id: str) -> InlineKeyboardMarkup:
    buttons: List[List[InlineKeyboardButton]] = []
    approve_seconds = admin_buttons.get("approve_durations", [])
    for sec in approve_seconds:
        period = humanize_period(int(sec))
        text = admin_ui.get("approve_template", "Одобрить").format(period=period)
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"approve:{membership_id}:{sec}")])
    row: List[InlineKeyboardButton] = []
    if admin_buttons.get("enable_decline", True):
        row.append(InlineKeyboardButton(admin_ui.get("decline_text", "Отклонить"), callback_data=f"decline:{membership_id}"))
    if admin_buttons.get("enable_ban", True):
        row.append(InlineKeyboardButton(admin_ui.get("ban_text", "Забанить"), callback_data=f"ban:{membership_id}"))
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


@log_async_call
async def handle_request_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = UserState.WAITING_FOR_ID
    text = render_template(templates.get("ask_id", "ask_id.txt"))
    await update.callback_query.message.reply_text(text)


@log_async_call
async def handle_id_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    raw_id = update.message.text.strip()
    username = user.first_name or user.username or "user"

    if not id_pattern.fullmatch(raw_id):
        text = render_template(templates.get("not_found", "id_not_found.txt"), membership_id=raw_id)
        await update.message.reply_text(text)
        context.user_data["state"] = UserState.WAITING_FOR_ID
        return

    member = db_get_member_by_id(raw_id)
    db_upsert_member(raw_id, user.id, user.username, user.full_name, member.get("is_confirmed") if member else False)

    if member and member.get("is_banned"):
        text = render_template(templates.get("banned", "id_banned.txt"), membership_id=raw_id)
        await update.message.reply_text(text)
        context.user_data["state"] = UserState.IDLE
        return

    if member and member.get("is_confirmed"):
        links = ACCESS_LINKS
        text = render_template(templates.get("granted", "access_granted.txt"), links=links)
        await update.message.reply_text(text)
        context.user_data["state"] = UserState.IDLE
        return

    # not confirmed yet
    admin_text = render_template(templates.get("admin_request", "admin_request.txt"), membership_id=raw_id, telegram_id=user.id)
    keyboard = build_admin_keyboard(raw_id)
    try:
        await context.bot.send_message(chat_id=ROOT_ADMIN_ID, text=admin_text, reply_markup=keyboard)
    except Exception as e:
        logger.exception("Failed to notify admin: %s", e)

    if member:
        template = templates.get("waiting", "id_waiting.txt")
    else:
        template = templates.get("not_found", "id_not_found.txt")
    text = render_template(template, membership_id=raw_id)
    await update.message.reply_text(text)
    context.user_data["state"] = UserState.IDLE


@log_async_call
async def handle_idle_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.first_name or update.effective_user.username or "user"
    text = render_template(telegram_start.get("template", "start_user.txt"), username=username)
    button_text = telegram_start.get("action_button_text", "Получить доступ")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text=button_text, callback_data="request_access")]])
    await update.message.reply_text(text, reply_markup=keyboard)


@log_async_call
async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестная команда. Используйте /start")


# Admin decision handlers ---------------------------------------------

@log_async_call
async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    if not is_admin(user.id):
        await query.answer(render_template("not_authorized.txt"), show_alert=True)
        return
    data = query.data.split(":")
    action = data[0]
    membership_id = data[1]
    if not id_pattern.fullmatch(membership_id):
        await query.answer(render_template("invalid_id.txt"), show_alert=True)
        return
    member = db_get_member_by_id(membership_id)
    if not member:
        text = render_template("admin_id_not_found.txt", membership_id=membership_id)
        await query.answer(text, show_alert=True)
        return
    user_id = member.get("telegram_id")
    if action == "approve":
        seconds = int(data[2])
        expires_at = datetime.utcnow() + timedelta(seconds=seconds) if seconds > 0 else None
        db_set_confirmation(membership_id, True, expires_at)
        if user_id:
            links = ACCESS_LINKS
            text = render_template(templates.get("granted", "access_granted.txt"), links=links)
            await context.bot.send_message(chat_id=user_id, text=text)
        await query.edit_message_text(render_template("admin_approved.txt", membership_id=membership_id))
    elif action == "decline":
        db_set_confirmation(membership_id, False, None)
        if user_id:
            text = render_template(templates.get("denied", "access_denied.txt"))
            await context.bot.send_message(chat_id=user_id, text=text)
        await query.edit_message_text(render_template("admin_declined.txt", membership_id=membership_id))
    elif action == "ban":
        db_set_ban(membership_id, True)
        if user_id:
            text = render_template(templates.get("banned", "id_banned.txt"), membership_id=membership_id)
            await context.bot.send_message(chat_id=user_id, text=text)
        await query.edit_message_text(render_template("admin_banned.txt", membership_id=membership_id))
    else:
        await query.answer(render_template("unknown_action.txt"))

