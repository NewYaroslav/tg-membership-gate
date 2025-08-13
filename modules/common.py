from __future__ import annotations

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from modules.template_engine import render_template
from modules.states import UserState
from modules.config import telegram_start
from modules.storage import db_is_admin
from modules.log_utils import log_async_call
from modules.logging_config import logger
from modules.inactivity import clear_user_activity


@log_async_call
async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    clear_user_activity(user.id)
    username = user.first_name or user.username or "user"
    text = render_template(telegram_start.get("template", "start_user.txt"), username=username)
    button_text = telegram_start.get("action_button_text", "Получить доступ")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text=button_text, callback_data="request_access")]])
    image = telegram_start.get("image")
    context.user_data["state"] = UserState.WAITING_FOR_REQUEST_BUTTON
    if image:
        try:
            with open(image, "rb") as f:
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=f, caption=text, reply_markup=keyboard)
        except FileNotFoundError:
            logger.warning("Start image %s not found", image)
            await update.message.reply_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)


@log_async_call
async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    template = "help_admin.txt" if db_is_admin(update.effective_user.id) else "help_user.txt"
    text = render_template(template)
    await update.message.reply_text(text)

