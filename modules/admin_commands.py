from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from modules.log_utils import log_async_call
from modules.logging_config import logger
from modules.storage import (
    db_add_allowed_email,
    db_ban_allowed_email,
    db_unlink_users_from_email,
    db_get_users_by_email,
    db_get_email_row,
    db_get_user_by_telegram_id,
    db_get_email_by_id,
)
from modules.auth_utils import is_admin
from modules.template_engine import render_template
from modules.config import authorization_ui, telegram_start
from modules.states import UserState, AdminState
from io import BytesIO

email_status_labels = authorization_ui.get("email_status_labels", {})

@log_async_call
async def handle_add_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return

    if not context.args:
        # Нет аргументов - ждём файл
        context.application.user_data[user.id]["admin_state"] = AdminState.WAITING_FOR_EMAIL_FILE
        await update.message.reply_text(render_template("admin_waiting_for_csv.txt"))
        return

    await process_email_addition(update, context, context.args)

@log_async_call
async def handle_ban_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return

    if not context.args:
        await update.message.reply_text(render_template("email_required.txt", command="/ban_email"))
        return

    banned = []
    for email in context.args:
        email = email.strip()
        db_ban_allowed_email(email)
        logger.info(f"Admin {user.id} banned email: {email}")
        banned.append(email)

    await update.message.reply_text(render_template("email_banned.txt", emails=banned))

@log_async_call
async def handle_remove_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return

    if not context.args:
        await update.message.reply_text(render_template("email_required.txt", command="/remove_email"))
        return

    removed = []
    for email in context.args:
        email = email.strip()
        db_unlink_users_from_email(email)
        logger.info(f"Admin {user.id} removed allowed email: {email}")
        removed.append(email)

    await update.message.reply_text(render_template("email_removed.txt", emails=removed))

@log_async_call
async def handle_check_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return

    if not context.args:
        await update.message.reply_text(render_template("email_required.txt", command="/check_email"))
        return

    results = []
    for email in context.args:
        email = email.strip()
        row = db_get_email_row(email)
        if not row:
            results.append(render_template("email_status_not_found.txt", email=email))
        else:
            status_key = "banned" if row["is_banned"] else "allowed"
            status_label = email_status_labels.get(status_key, status_key)
            results.append(render_template("email_status_found.txt", email=email, status=status_label))

    await update.message.reply_text("\n".join(results))
    
@log_async_call
async def handle_my_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return

    chat = update.effective_chat
    user_data = db_get_user_by_telegram_id(user.id)
    email = None

    if user_data and user_data.get("is_authorized"):
        email = db_get_email_by_id(user_data.get("email_id"))

    text = render_template(
        "my_id.txt",
        telegram_id=user.id,
        username=user.username or user.first_name or "user",
        chat_id=chat.id,
        email=email
    )

    await update.message.reply_text(text)
    
@log_async_call
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_state = context.user_data.get("admin_state")

    if admin_state != AdminState.WAITING_FOR_EMAIL_FILE:
        return
        
    document = update.message.document
    file_name = document.file_name.lower()
    
    # Проверка расширения
    if not (file_name.endswith(".csv") or file_name.endswith(".txt")):
        await update.message.reply_text(render_template("unsupported_file_type.txt"))
        return

    try:
        telegram_file = await update.message.document.get_file()
        byte_data = await telegram_file.download_as_bytearray()
        byte_stream = BytesIO(byte_data)
        lines = byte_stream.read().decode("utf-8").splitlines()
        emails = [line.strip() for line in lines if line.strip() and "@" in line]

        await process_email_addition(update, context, emails)
        context.user_data["admin_state"] = AdminState.IDLE

    except Exception as e:
        logger.error(f"Failed to process uploaded email file: {e}")
        await update.message.reply_text(render_template("invalid_csv_file.txt"))
    
async def process_email_addition(update: Update, context: ContextTypes.DEFAULT_TYPE, email_list: list[str]):
    user = update.effective_user
    added = []

    for email in email_list:
        email = email.strip()
        db_add_allowed_email(email)
        logger.info(f"Admin {user.id} added allowed email: {email}")
        added.append(email)

        users_data = db_get_users_by_email(email)
        for user_data in users_data:
            try:
                if not user_data.get("is_authorized"):
                    continue
                telegram_id = user_data["telegram_id"]
                username = user_data.get("username") or "user"

                text = render_template("welcome_user.txt", username=username, email=email)
                button_text = telegram_start.get("action_button_text", "Submit a request")
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(text=button_text, callback_data="submit_request")]
                ])

                context.application.user_data[telegram_id]["state"] = UserState.WAITING_FOR_REQUEST_BUTTON

                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                logger.info(f"Sent authorization message to user {telegram_id}")
            except Exception as e:
                logger.error(f"Failed to notify user {telegram_id}: {e}")

    await update.message.reply_text(render_template("email_added.txt", emails=added))