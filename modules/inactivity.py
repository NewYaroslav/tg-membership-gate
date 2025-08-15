import asyncio
from datetime import datetime, timedelta
from telegram.ext import ContextTypes

from modules.template_engine import render_template
from modules.config import session_timeout, templates
from modules.storage import db_get_user_locale
from modules.i18n import normalize_lang
from modules.states import UserState
from modules.log_utils import log_async_call
from modules.logging_config import logger


user_last_activity: dict[int, datetime] = {}


def update_user_activity(user) -> None:
    user_last_activity[user.id] = datetime.utcnow()


def clear_user_activity(user_id: int) -> None:
    user_last_activity.pop(user_id, None)


@log_async_call
async def check_user_inactivity_loop(app) -> None:
    timeout_seconds = int(session_timeout.get("seconds", 900))
    send_message = session_timeout.get("send_message", False)
    check_interval = min(timeout_seconds, 60)
    while True:
        await asyncio.sleep(check_interval)
        now = datetime.utcnow()
        expired = [uid for uid, ts in list(user_last_activity.items()) if now - ts > timedelta(seconds=timeout_seconds)]
        for uid in expired:
            context = ContextTypes.DEFAULT_TYPE(application=app)
            try:
                if send_message:
                    lang = normalize_lang(db_get_user_locale(uid))
                    text = render_template(
                        templates.get("session_timeout", "session_timeout.txt"),
                        lang=lang,
                    )
                    await context.bot.send_message(
                        chat_id=uid, text=text, parse_mode="HTML"
                    )
                ud = context.application.user_data.get(uid)
                if isinstance(ud, dict):
                    ud["state"] = UserState.IDLE
                logger.info("User %s reset after inactivity", uid)
            except Exception as e:
                logger.exception("Failed to reset user %s: %s", uid, e)
            finally:
                clear_user_activity(uid)

