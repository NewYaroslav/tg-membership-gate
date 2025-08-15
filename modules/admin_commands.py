from __future__ import annotations

from datetime import datetime
import csv
import io

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from modules.auth_utils import is_admin
from modules.template_engine import render_template
from modules.storage import (
    db_get_member_by_membership_id,
    db_get_member_by_telegram,
    db_get_member_by_username,
    db_set_ban,
    db_set_confirmation,
    db_iter_members,
    db_delete_member_by_id,
    db_delete_user_by_telegram_id,
    db_get_user_locale,
)
from modules.access_control import (
    ban_in_all_access_chats,
    unban_in_all_access_chats,
    kick_in_all_access_chats,
    ACCESS_CHATS,
)
from modules.time_utils import humanize_period
from modules.log_utils import log_async_call


def resolve_member_by_key(key: str | int) -> dict | None:
    member = None
    if not str(key).startswith("@"):
        member = db_get_member_by_membership_id(str(key))
        if member:
            return member
    if str(key).lstrip("-+").isdigit():
        member = db_get_member_by_telegram(int(key))
        if member:
            return member
    if str(key).startswith("@"):
        member = db_get_member_by_username(str(key)[1:])
        if member:
            return member
    return None


def _calc_status(member: dict) -> tuple[str, str, str]:
    now = datetime.utcnow()
    expires = member.get("expires_at")
    expires_dt = None
    if expires:
        expires_dt = datetime.fromisoformat(expires) if isinstance(expires, str) else expires
    remaining = ""
    status = "none"
    if member.get("is_banned"):
        status = "banned"
    elif member.get("is_confirmed"):
        if not expires_dt:
            status = "lifetime"
        elif expires_dt > now:
            status = "active"
            remaining = str(int((expires_dt - now).total_seconds()))
        else:
            status = "expired"
            remaining = "0"
    return status, remaining, expires_dt.isoformat() if expires_dt else ""


async def _ban_member(bot, member: dict):
    user_id = member["telegram_id"]
    summary = await ban_in_all_access_chats(bot, user_id)
    db_set_ban(member["membership_id"], True)
    db_set_confirmation(member["membership_id"], False, None)
    member.update(is_banned=1, is_confirmed=0, expires_at=None)
    return summary


async def _unban_member(bot, member: dict):
    user_id = member["telegram_id"]
    summary = await unban_in_all_access_chats(bot, user_id)
    db_set_ban(member["membership_id"], False)
    member.update(is_banned=0)
    return summary


async def _kick_member(bot, member: dict):
    user_id = member["telegram_id"]
    summary = await kick_in_all_access_chats(bot, user_id)
    db_set_confirmation(member["membership_id"], False, None)
    member.update(is_confirmed=0, expires_at=None)
    return summary


async def _remove_member(bot, member: dict):
    summary = await _kick_member(bot, member)
    db_delete_member_by_id(member["id"])
    db_delete_user_by_telegram_id(member["telegram_id"])
    return summary


async def _build_user_card(bot, member: dict):
    status, remaining_sec, expires_at = _calc_status(member)
    remaining_human = humanize_period(int(remaining_sec)) if remaining_sec else ""
    in_channels = False
    for chat_id in ACCESS_CHATS:
        try:
            m = await bot.get_chat_member(chat_id, member["telegram_id"])
            if m.status not in ("left", "kicked"):
                in_channels = True
                break
        except Exception:
            continue
    user_locale = db_get_user_locale(member["telegram_id"])
    text = render_template(
        "admin_user_card.txt",
        membership_id=member.get("membership_id"),
        telegram_id=member["telegram_id"],
        username=member.get("username"),
        is_confirmed=member.get("is_confirmed"),
        is_banned=member.get("is_banned"),
        status=status,
        expires_at=expires_at,
        remaining=remaining_human,
        in_channels=in_channels,
        locale=user_locale,
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Ban", callback_data=f"admin:ban:{member['membership_id']}") ,
            InlineKeyboardButton("Unban", callback_data=f"admin:unban:{member['membership_id']}") ,
            InlineKeyboardButton("Kick", callback_data=f"admin:kick:{member['membership_id']}") ,
            InlineKeyboardButton("Remove", callback_data=f"admin:remove:{member['membership_id']}") ,
        ]
    ])
    return text, keyboard


@log_async_call
async def handle_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return
    if not context.args:
        await update.message.reply_text(render_template("id_required.txt"))
        return
    key = context.args[0]
    member = resolve_member_by_key(key)
    if not member:
        await update.message.reply_text(render_template("admin_user_not_found.txt"))
        return
    summary = await _ban_member(context.bot, member)
    total = len(summary["ok"]) + len(summary["errors"])
    text = render_template(
        "admin_ban_done.txt",
        username=member.get("username"),
        id=member["telegram_id"],
        ok=len(summary["ok"]),
        total=total,
        errors=summary["errors"],
    )
    await update.message.reply_text(text)


@log_async_call
async def handle_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return
    if not context.args:
        await update.message.reply_text(render_template("id_required.txt"))
        return
    key = context.args[0]
    member = resolve_member_by_key(key)
    if not member:
        await update.message.reply_text(render_template("admin_user_not_found.txt"))
        return
    summary = await _unban_member(context.bot, member)
    total = len(summary["ok"]) + len(summary["errors"])
    text = render_template(
        "admin_unban_done.txt",
        username=member.get("username"),
        id=member["telegram_id"],
        ok=len(summary["ok"]),
        total=total,
        errors=summary["errors"],
    )
    await update.message.reply_text(text)


@log_async_call
async def handle_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return
    if not context.args:
        await update.message.reply_text(render_template("id_required.txt"))
        return
    key = context.args[0]
    member = resolve_member_by_key(key)
    if not member:
        await update.message.reply_text(render_template("admin_user_not_found.txt"))
        return
    summary = await _kick_member(context.bot, member)
    total = len(summary["ok"]) + len(summary["errors"])
    text = render_template(
        "admin_kick_done.txt",
        username=member.get("username"),
        id=member["telegram_id"],
        ok=len(summary["ok"]),
        total=total,
        errors=summary["errors"],
    )
    await update.message.reply_text(text)


@log_async_call
async def handle_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return
    if not context.args:
        await update.message.reply_text(render_template("id_required.txt"))
        return
    key = context.args[0]
    member = resolve_member_by_key(key)
    if not member:
        await update.message.reply_text(render_template("admin_user_not_found.txt"))
        return
    summary = await _remove_member(context.bot, member)
    total = len(summary["ok"]) + len(summary["errors"])
    text = render_template(
        "admin_remove_done.txt",
        username=member.get("username"),
        id=member["telegram_id"],
        membership_id=member.get("membership_id"),
        ok=len(summary["ok"]),
        total=total,
        errors=summary["errors"],
    )
    await update.message.reply_text(text)


@log_async_call
async def handle_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return
    scope = context.args[0] if context.args else "all"
    members = db_iter_members(scope)
    output = io.StringIO()
    fieldnames = [
        "membership_id",
        "telegram_id",
        "username",
        "is_confirmed",
        "is_banned",
        "expires_at",
        "remaining_sec",
        "status",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    count = 0
    for m in members:
        status, remaining, expires_at = _calc_status(m)
        writer.writerow(
            dict(
                membership_id=m.get("membership_id"),
                telegram_id=m.get("telegram_id"),
                username=m.get("username"),
                is_confirmed=m.get("is_confirmed"),
                is_banned=m.get("is_banned"),
                expires_at=expires_at,
                remaining_sec=remaining,
                status=status,
            )
        )
        count += 1
    bio = io.BytesIO(output.getvalue().encode())
    bio.name = f"users_{scope}.csv"
    caption = render_template("admin_export_ready.txt", n=count)
    await update.message.reply_document(document=bio, filename=bio.name, caption=caption)


@log_async_call
async def handle_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(render_template("not_authorized.txt"))
        return
    if not context.args:
        await update.message.reply_text(render_template("id_required.txt"))
        return
    key = context.args[0]
    member = resolve_member_by_key(key)
    if not member:
        await update.message.reply_text(render_template("admin_user_not_found.txt"))
        return
    text, keyboard = await _build_user_card(context.bot, member)
    await update.message.reply_text(text, reply_markup=keyboard)


@log_async_call
async def handle_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer(render_template("not_authorized.txt"), show_alert=True)
        return
    parts = query.data.split(":")
    if len(parts) != 3 or parts[0] != "admin":
        await query.answer(render_template("unknown_action.txt"), show_alert=True)
        return
    _, action, key = parts
    member = resolve_member_by_key(key)
    if not member:
        await query.answer(render_template("admin_user_not_found.txt"), show_alert=True)
        return
    if action == "ban":
        await _ban_member(context.bot, member)
    elif action == "unban":
        await _unban_member(context.bot, member)
    elif action == "kick":
        await _kick_member(context.bot, member)
    elif action == "remove":
        summary = await _remove_member(context.bot, member)
        total = len(summary["ok"]) + len(summary["errors"])
        await query.message.edit_text(
            render_template(
                "admin_remove_done.txt",
                username=member.get("username"),
                id=member["telegram_id"],
                membership_id=member.get("membership_id"),
                ok=len(summary["ok"]),
                total=total,
                errors=summary["errors"],
            )
        )
        await query.answer()
        return
    text, keyboard = await _build_user_card(context.bot, member)
    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()
