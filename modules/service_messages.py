from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from modules.log_utils import log_async_call
from modules.states import UserState


@log_async_call
async def suppress_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete service messages like joins or pins if the feature is enabled."""
    context.user_data["state"] = UserState.IDLE
    if not context.bot_data.get("suppress_service_messages", True):
        return
    try:
        await update.effective_message.delete()
    except TelegramError:
        # Ignore deletion errors (e.g., insufficient rights)
        pass
