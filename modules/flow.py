import os
import re
from datetime import datetime, timedelta
from typing import List

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from modules.config import (
    telegram_start,
    templates,
    id_config,
    admin_buttons,
    admin_ui,
    renewal,
    ask_id_prompt,
    invalid_id_prompt,
)
from modules.storage import (
    db_get_member_by_telegram,
    db_get_member_by_id,
    db_upsert_member,
    db_set_confirmation,
    db_set_ban,
    db_get_user_locale,
    ROOT_ADMIN_ID,
)
from modules.auth_utils import is_admin
from modules.states import UserState
from modules.template_engine import render_template
from modules.media_utils import send_localized_image_with_text
from modules.i18n import (
    normalize_lang,
    resolve_user_lang,
    make_username,
    get_button_text,
    DEFAULT_LANG,
)
from modules.log_utils import log_async_call
from modules.logging_config import logger
from modules.time_utils import humanize_period
from modules.join_links import ensure_join_request_link
from modules.inactivity import clear_user_activity

load_dotenv()
ACCESS_CHATS = [int(cid.strip()) for cid in os.getenv("ACCESS_CHATS", "").split(",") if cid.strip()]

id_pattern = re.compile(id_config.get("pattern", ".+"))


def build_admin_keyboard(membership_id: str, lang: str = DEFAULT_LANG) -> InlineKeyboardMarkup:
    buttons: List[List[InlineKeyboardButton]] = []
    approve_seconds = admin_buttons.get("approve_durations", [])
    for sec in approve_seconds:
        period = humanize_period(int(sec))
        tmpl = get_button_text(admin_ui.get("approve_template"), lang, "Approve")
        text = tmpl.format(period=period)
        buttons.append(
            [InlineKeyboardButton(text=text, callback_data=f"approve:{membership_id}:{sec}")]
        )
    row: List[InlineKeyboardButton] = []
    if admin_buttons.get("enable_decline", True):
        decline = get_button_text(admin_ui.get("decline_text"), lang, "Decline")
        row.append(InlineKeyboardButton(decline, callback_data=f"decline:{membership_id}"))
    if admin_buttons.get("enable_ban", True):
        ban = get_button_text(admin_ui.get("ban_text"), lang, "Ban")
        row.append(InlineKeyboardButton(ban, callback_data=f"ban:{membership_id}"))
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def _user_lang(update: Update) -> str:
    user_row = {"locale": db_get_user_locale(update.effective_user.id)}
    return resolve_user_lang(update, user_row)


@log_async_call
async def handle_request_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = UserState.WAITING_FOR_ID
    lang = _user_lang(update)
    username = make_username(update.effective_user, lang)
    text = render_template(
        ask_id_prompt.get("template", "ask_id.txt"),
        lang=lang,
        username=username,
    )
    if ask_id_prompt.get("enabled_image"):
        await send_localized_image_with_text(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            asset_key="ask_id.image",
            cfg_section=ask_id_prompt,
            lang=lang,
            text=text,
        )
    else:
        await update.callback_query.message.reply_text(text, parse_mode="HTML")


@log_async_call
async def handle_id_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    raw_id = update.message.text.strip()
    lang = _user_lang(update)

    if not id_pattern.fullmatch(raw_id):
        text = render_template(
            invalid_id_prompt.get("template", "id_invalid.txt"),
            lang=lang,
        )
        if invalid_id_prompt.get("enabled_image"):
            await send_localized_image_with_text(
                bot=context.bot,
                chat_id=update.effective_chat.id,
                asset_key="invalid_id.image",
                cfg_section=invalid_id_prompt,
                lang=lang,
                text=text,
            )
        else:
            await update.message.reply_text(text, parse_mode="HTML")
        context.user_data["state"] = UserState.WAITING_FOR_ID
        return

    member = db_get_member_by_id(raw_id)
    db_upsert_member(raw_id, user.id, user.username, user.full_name, member.get("is_confirmed") if member else False)

    if member and member.get("is_banned"):
        text = render_template(
            templates.get("banned", "id_banned.txt"),
            membership_id=raw_id,
            lang=lang,
        )
        await update.message.reply_text(text, parse_mode="HTML")
        context.user_data["state"] = UserState.IDLE
        return

    if member and member.get("is_confirmed"):
        links: List[str] = []
        for chat_id in ACCESS_CHATS:
            try:
                links.append(await ensure_join_request_link(context.bot, chat_id))
            except Exception as e:
                logger.warning("link fail %s: %s", chat_id, e)
        if links:
            text = render_template(
                templates.get("granted", "access_granted.txt"),
                links=links,
                lang=lang,
            )
        else:
            text = render_template(
                templates.get("links_unavailable", "links_unavailable.txt"),
                lang=lang,
            )
        await update.message.reply_text(
            text, disable_web_page_preview=True, parse_mode="HTML"
        )
        context.user_data["state"] = UserState.IDLE
        return

    # not confirmed yet
    admin_text = render_template(templates.get("admin_request", "admin_request.txt"), membership_id=raw_id, telegram_id=user.id)
    keyboard = build_admin_keyboard(raw_id)
    try:
        await context.bot.send_message(chat_id=ROOT_ADMIN_ID, text=admin_text, reply_markup=keyboard)
    except Exception as e:
        logger.exception("Failed to notify admin: %s", e)
    clear_user_activity(ROOT_ADMIN_ID)

    if member:
        template = templates.get("waiting", "id_waiting.txt")
    else:
        template = templates.get("not_found", "id_not_found.txt")
    text = render_template(template, membership_id=raw_id, lang=lang)
    await update.message.reply_text(text, parse_mode="HTML")
    clear_user_activity(user.id)
    context.user_data["state"] = UserState.IDLE


@log_async_call
async def handle_idle_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = UserState.WAITING_FOR_REQUEST_BUTTON
    lang = _user_lang(update)
    username = make_username(update.effective_user, lang)
    text = render_template(telegram_start.get("template", "start_user.txt"), username=username, lang=lang)
    button_text = get_button_text(telegram_start.get("action_button_text"), lang, "Get access")
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text=button_text, callback_data="request_access")]]
    )
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
        await update.message.reply_text(text, reply_markup=keyboard)


@log_async_call
async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _user_lang(update)
    text = render_template("unknown_action.txt", lang=lang)
    # await update.message.reply_text(text)
    await update.effective_message.reply_text(text)


# Admin decision handlers ---------------------------------------------


@log_async_call
async def handle_renewal_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer(render_template("unknown_action.txt"))
        return
    _, membership_id, plan_id = parts
    member = db_get_member_by_id(membership_id)
    if not member or member.get("telegram_id") != update.effective_user.id:
        await query.answer(render_template("not_authorized.txt"), show_alert=True)
        return
    plan = next((p for p in renewal.get("user_plans", []) if p.get("id") == plan_id), None)
    if not plan:
        await query.answer(render_template("unknown_action.txt"), show_alert=True)
        return
    seconds = int(plan.get("duration_sec", 0))
    period = "бессрочно" if seconds == 0 else humanize_period(seconds)
    admin_text = render_template(
        templates.get("renewal_requested_admin", "renewal_requested_admin.txt"),
        username=member.get("username"),
        membership_id=membership_id,
        plan_label=get_button_text(plan.get("label"), DEFAULT_LANG),
        plan_period=period,
    )
    approve_tmpl = get_button_text(
        admin_ui.get("approve_template"), DEFAULT_LANG, "Approve for {period}"
    )
    decline_text = get_button_text(admin_ui.get("decline_text"), DEFAULT_LANG, "Decline")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=approve_tmpl.format(period=period),
                    callback_data=f"approve:{membership_id}:{seconds}",
                )
            ],
            [InlineKeyboardButton(text=decline_text, callback_data=f"decline:{membership_id}")],
        ]
    )
    try:
        await context.bot.send_message(chat_id=ROOT_ADMIN_ID, text=admin_text, reply_markup=keyboard)
    except Exception as e:
        logger.exception("Failed to notify admin about renewal: %s", e)
    clear_user_activity(ROOT_ADMIN_ID)
    lang = _user_lang(update)
    await query.message.reply_text(render_template(templates.get("waiting", "id_waiting.txt"), lang=lang))

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
        now = datetime.utcnow()
        current = member.get("expires_at")
        if current:
            if isinstance(current, str):
                current_dt = datetime.fromisoformat(current)
            else:
                current_dt = current
            base = max(now, current_dt)
        else:
            base = now
        expires_at = None if seconds == 0 else base + timedelta(seconds=seconds)
        db_set_confirmation(membership_id, True, expires_at)
        if user_id:
            user_lang = normalize_lang(db_get_user_locale(user_id))
            links: List[str] = []
            for chat_id in ACCESS_CHATS:
                try:
                    links.append(await ensure_join_request_link(context.bot, chat_id))
                except Exception as e:
                    logger.warning("link fail %s: %s", chat_id, e)
            if links:
                text = render_template(templates.get("granted", "access_granted.txt"), links=links, lang=user_lang)
            else:
                text = render_template(templates.get("links_unavailable", "links_unavailable.txt"), lang=user_lang)
            await context.bot.send_message(chat_id=user_id, text=text, disable_web_page_preview=True)
            clear_user_activity(user_id)
        await query.edit_message_text(render_template("admin_approved.txt", membership_id=membership_id))
    elif action == "decline":
        db_set_confirmation(membership_id, False, None)
        if user_id:
            user_lang = normalize_lang(db_get_user_locale(user_id))
            text = render_template(templates.get("denied", "access_denied.txt"), lang=user_lang)
            await context.bot.send_message(chat_id=user_id, text=text)
            clear_user_activity(user_id)
        await query.edit_message_text(render_template("admin_declined.txt", membership_id=membership_id))
    elif action == "ban":
        db_set_ban(membership_id, True)
        if user_id:
            user_lang = normalize_lang(db_get_user_locale(user_id))
            text = render_template(templates.get("banned", "id_banned.txt"), membership_id=membership_id, lang=user_lang)
            await context.bot.send_message(chat_id=user_id, text=text)
            clear_user_activity(user_id)
        await query.edit_message_text(render_template("admin_banned.txt", membership_id=membership_id))
    else:
        await query.answer(render_template("unknown_action.txt"))

