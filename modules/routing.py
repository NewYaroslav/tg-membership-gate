from telegram import Update
from telegram.ext import ContextTypes

from modules.states import UserState
from modules.flow import (
    handle_request_button,
    handle_id_submission,
    handle_idle_state,
    handle_unknown_message,
    handle_admin_decision,
    handle_renewal_selection,
)
from modules.log_utils import log_async_call
from modules.inactivity import update_user_activity
from modules.logging_config import logger


@log_async_call
async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user_activity(update.effective_user)
    state = context.user_data.get("state")
    if state is None:
        context.user_data["state"] = UserState.IDLE
        state = UserState.IDLE
        logger.debug("Initialized state for user %s", update.effective_user.id)
    if state == UserState.WAITING_FOR_LANGUAGE:
        return
    if state == UserState.WAITING_FOR_ID:
        await handle_id_submission(update, context)
    else:
        await handle_idle_state(update, context)


@log_async_call
async def handle_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user_activity(update.effective_user)
    query = update.callback_query
    await query.answer()
    state = context.user_data.get("state")
    if state == UserState.WAITING_FOR_LANGUAGE:
        return
    data = query.data or ""
    # if data == "request_access" and state == UserState.WAITING_FOR_REQUEST_BUTTON:
    if data == "request_access" and state in (UserState.WAITING_FOR_REQUEST_BUTTON, UserState.IDLE, None):
        await handle_request_button(update, context)
    elif data.startswith("renew:"):
        await handle_renewal_selection(update, context)
    elif data.startswith("approve:") or data.startswith("decline:") or data.startswith("ban:"):
        await handle_admin_decision(update, context)
    else:
        await handle_unknown_message(update, context)

