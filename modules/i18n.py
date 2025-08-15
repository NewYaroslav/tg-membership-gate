from __future__ import annotations

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from modules.config import i18n, i18n_buttons, language_prompt
from modules.storage import db_set_user_locale
from modules.log_utils import log_async_call
from modules.media_utils import send_localized_image_with_text
from modules.states import UserState

SUPPORTED = set(i18n.get("supported_langs", []))
DEFAULT_LANG = i18n.get("default_lang", "en")


def get_button_text(cfg_value, lang: str, fallback: str | None = None) -> str:
    """Return localized button text from config value.

    cfg_value can be either a plain string or a dict mapping language codes
    to translations. Fallback order: requested lang -> DEFAULT_LANG -> "en" ->
    provided fallback -> empty string.
    """
    if isinstance(cfg_value, dict):
        return (
            cfg_value.get(lang)
            or cfg_value.get(DEFAULT_LANG)
            or cfg_value.get("en")
            or (fallback if fallback is not None else "")
        )
    if cfg_value:
        return cfg_value
    return fallback or ""


def make_username(user, lang: str) -> str:
    first = getattr(user, "first_name", "") or ""
    last = getattr(user, "last_name", "") or ""
    name = (first + " " + last).strip()
    if not name:
        lang_cfg = i18n_buttons.get(lang, i18n_buttons.get(DEFAULT_LANG, {}))
        name = lang_cfg.get("default_username", "User")
    return name

def normalize_lang(code: str | None) -> str:
    if not code:
        return DEFAULT_LANG
    base = code.split("-")[0].lower()
    return base if base in SUPPORTED else DEFAULT_LANG

def resolve_user_lang(update, user_row) -> str:
    if user_row and user_row.get("locale") in SUPPORTED:
        return user_row["locale"]
    if not i18n.get("enabled_start_prompt", True):
        return normalize_lang(getattr(update.effective_user, "language_code", None))
    return DEFAULT_LANG


def plural_days(n: int, lang: str) -> str:
    if lang == "ru":
        n10 = n % 10
        n100 = n % 100
        if n10 == 1 and n100 != 11:
            return "день"
        if 2 <= n10 <= 4 and not 12 <= n100 <= 14:
            return "дня"
        return "дней"
    return "day" if n == 1 else "days"


async def send_language_prompt(update, context, cfg, *, asset_prefix: str, default_template: str):
    from modules.template_engine import render_template

    lang_ui = normalize_lang(getattr(update.effective_user, "language_code", None))
    username = make_username(update.effective_user, lang_ui)
    lang_cfg = i18n_buttons.get(lang_ui, i18n_buttons.get(DEFAULT_LANG, {}))
    titles = lang_cfg.get("language_choices", {})
    row = [
        InlineKeyboardButton(titles.get(code, code), callback_data=f"lang:{code}")
        for code in i18n.get("supported_langs", [])
    ]
    kb = InlineKeyboardMarkup([row])
    text = render_template(cfg.get("template", default_template), lang=lang_ui, username=username)
    if cfg.get("enabled_image"):
        await send_localized_image_with_text(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            asset_key=f"{asset_prefix}.image",
            cfg_section=cfg,
            lang=lang_ui,
            text=text,
            reply_markup=kb,
        )
    else:
        await update.effective_message.reply_text(text, reply_markup=kb)


@log_async_call
async def cmd_language(update, context):
    await send_language_prompt(
        update,
        context,
        language_prompt,
        asset_prefix="language_prompt",
        default_template="language_prompt.txt",
    )


@log_async_call
async def on_lang_pick(update, context):
    from modules.template_engine import render_template
    from modules.common import handle_start_command

    q = update.callback_query
    code = q.data.split(":", 1)[1]
    db_set_user_locale(update.effective_user.id, code)
    await q.answer()

    text = render_template("language_set.txt", lang=code)

    msg = q.message
    # Если сообщение — обычный текст
    if getattr(msg, "text", None):
        await q.edit_message_text(text)
    # Если сообщение — фото/медиа с подписью
    elif getattr(msg, "caption", None):
        await q.edit_message_caption(caption=text)
    # На всякий случай fallback — отправить новое сообщение
    else:
        await msg.reply_text(text)
    await handle_start_command(update, context)
