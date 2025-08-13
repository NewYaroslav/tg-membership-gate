import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from modules.template_engine import render_template
from modules.logging_config import logger
from modules.states import UserState
from modules.config import session_timeout, telegram_start
from modules.storage import db_get_user_by_telegram_id, db_get_email_by_id
from modules.log_utils import log_async_call

user_last_activity = {}

def update_user_activity(user):
    username = user.first_name or user.username or "user"
    user_last_activity[user.id] = {
        "timestamp": datetime.utcnow(),
        "username": username,
    }

def clear_user_activity(user_id):
    user_last_activity.pop(user_id, None)

@log_async_call
async def check_user_inactivity_loop(app):
    timeout_seconds = int(session_timeout.get("seconds", 900))
    timeout_minutes = timeout_seconds // 60
    send_message = session_timeout.get("send_message", False)
    template_name = session_timeout.get("message_template")
    check_interval = min(timeout_seconds, 60)

    while True:
        await asyncio.sleep(check_interval)
        now = datetime.utcnow()
        expired = [
            (uid, data) for uid, data in list(user_last_activity.items())
            if now - data["timestamp"] > timedelta(seconds=timeout_seconds)
        ]
        for uid, data in expired:
            context = ContextTypes.DEFAULT_TYPE(application=app)
            try:
                if send_message and template_name:
                    text = render_template(template_name, timeout_minutes=timeout_minutes)
                    await context.bot.send_message(chat_id=uid, text=text, parse_mode="HTML")

                user_data = db_get_user_by_telegram_id(uid)
                email = db_get_email_by_id(user_data["email_id"]) if user_data else ""
                welcome = render_template(
                    "welcome_user.txt",
                    username=data["username"],
                    email=email,
                )
                button_text = telegram_start.get("action_button_text", "Submit a request")
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text=button_text, callback_data="submit_request")]
                ])
                await context.bot.send_message(
                    chat_id=uid,
                    text=welcome,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )

                ud = context.application.user_data.get(uid)
                if isinstance(ud, dict):
                    ud["state"] = UserState.WAITING_FOR_REQUEST_BUTTON

                logger.info(f"User {uid} reset to start after inactivity")
            except Exception as e:
                logger.exception(f"Failed to reset user {uid} after inactivity: {e}")
            finally:
                clear_user_activity(uid)
