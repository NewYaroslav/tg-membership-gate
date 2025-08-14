import os
import asyncio
from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatJoinRequestHandler,
    filters,
)
from rich.console import Console

from modules.routing import route_message, handle_inline_button
from modules.join_approver import on_join_request
from modules.common import handle_start_command, handle_help_command
from modules.i18n import cmd_language, on_lang_pick
from modules.admin_commands import (
    handle_ban,
    handle_unban,
    handle_kick,
    handle_export,
    handle_user,
    handle_user_action,
)
from modules.storage import db_init
from modules.log_utils import log_async_call, log_sync_call
from modules.logging_config import logger
from modules.inactivity import check_user_inactivity_loop
from modules.membership_checker import check_membership_expiry_loop

# Консоль и логгер
console = Console()

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

background_tasks = []


@log_async_call
async def setup_bot_commands(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start", "Запустить"),
        BotCommand("help", "Справка"),
        BotCommand("language", "Язык"),
    ])


@log_async_call
async def post_init(app: Application):
    await setup_bot_commands(app)
    inactivity_task = asyncio.create_task(check_user_inactivity_loop(app))
    background_tasks.append(inactivity_task)
    expiry_task = asyncio.create_task(check_membership_expiry_loop(app))
    background_tasks.append(expiry_task)

# Запуск
@log_sync_call
def run_telegram_bot():
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN not set in .env")
        console.print("[bold red]Error: BOT_TOKEN not set in .env[/bold red]")
        exit(1)

    logger.info("Starting Telegram bot...")
    db_init()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", handle_start_command))
    app.add_handler(CommandHandler("help", handle_help_command))
    app.add_handler(CommandHandler("language", cmd_language))
    app.add_handler(CommandHandler("ban", handle_ban))
    app.add_handler(CommandHandler("unban", handle_unban))
    app.add_handler(CommandHandler("kick", handle_kick))
    app.add_handler(CommandHandler("remove", handle_kick))
    app.add_handler(CommandHandler("export_users", handle_export))
    app.add_handler(CommandHandler("user", handle_user))
    app.add_handler(CallbackQueryHandler(handle_user_action, pattern=r"^(ban|unban|kick):\d+$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_message))
    app.add_handler(CallbackQueryHandler(on_lang_pick, pattern=r"^lang:"))
    app.add_handler(CallbackQueryHandler(handle_inline_button))
    app.add_handler(ChatJoinRequestHandler(on_join_request))

    console.print("[bold green]Telegram bot is running[/bold green]")
    logger.info("Telegram bot is now polling for messages")

    try:
        app.run_polling(close_loop=False)
    finally:
        logger.info("Bot is shutting down, cancelling background tasks...")
        for task in background_tasks:
            if not task.done():
                task.cancel()
            coro = getattr(task, 'get_coro', lambda: None)()
            name = getattr(coro, '__name__', 'unknown')
            logger.debug(f"Cancelled task: {name}")

if __name__ == "__main__":
    try:
        run_telegram_bot()
    except KeyboardInterrupt:
        console.print("\n[yellow][!] Stopped by user (Ctrl+C).[/yellow]")
    finally:
        pass
