from __future__ import annotations

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from modules.template_engine import render_template
from modules.states import UserState
from modules.config import telegram_start
from modules.auth_utils import is_admin
from modules.log_utils import log_async_call
from modules.inactivity import clear_user_activity
from modules.i18n import normalize_lang
from modules.storage import db_get_user_locale
from modules.media_utils import send_localized_image_with_text


@log_async_call
async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    clear_user_activity(user.id)
    username = user.first_name or user.username or "user"
    lang = db_get_user_locale(user.id)
    lang = normalize_lang(lang or getattr(user, "language_code", None))
    text = render_template(telegram_start.get("template", "start_user.txt"), username=username, lang=lang)
    button_text = telegram_start.get("action_button_text", "Получить доступ")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text=button_text, callback_data="request_access")]])
    context.user_data["state"] = UserState.WAITING_FOR_REQUEST_BUTTON
    if telegram_start.get("enabled_image", True):
        await send_localized_image_with_text(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            asset_key="start.image",
            cfg_section=telegram_start,
            lang=lang,
            text=text,
            reply_markup=keyboard,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


@log_async_call
async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    template = "help_admin.txt" if is_admin(update.effective_user.id) else "help_user.txt"
    text = render_template(template)
    await update.message.reply_text(text)

