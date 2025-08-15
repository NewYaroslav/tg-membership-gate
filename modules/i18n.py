from __future__ import annotations

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from modules.config import i18n, i18n_buttons, language_prompt
from modules.storage import db_set_user_locale
from modules.log_utils import log_async_call
from modules.media_utils import send_localized_image_with_text

SUPPORTED = set(i18n.get("supported_langs", []))
DEFAULT_LANG = i18n.get("default_lang", "en")

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


@log_async_call
async def cmd_language(update, context):
    from modules.template_engine import render_template
    lang_ui = normalize_lang(getattr(update.effective_user, "language_code", None))
    buttons = []
    lang_cfg = i18n_buttons.get(lang_ui, i18n_buttons.get(DEFAULT_LANG, {}))
    titles = lang_cfg.get("language_choices", {})
    row = [
        InlineKeyboardButton(titles.get(code, code), callback_data=f"lang:{code}")
        for code in i18n.get("supported_langs", [])
    ]
    buttons.append(row)
    kb = InlineKeyboardMarkup(buttons)
    text = render_template(language_prompt.get("template", "start_language_prompt.txt"), lang=lang_ui)
    if language_prompt.get("enabled_image"):
        await send_localized_image_with_text(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            asset_key="language_prompt.image",
            cfg_section=language_prompt,
            lang=lang_ui,
            text=text,
            reply_markup=kb,
        )
    else:
        await update.effective_message.reply_text(text, reply_markup=kb)


@log_async_call
async def on_lang_pick(update, context):
    from modules.template_engine import render_template
    q = update.callback_query
    code = q.data.split(":", 1)[1]
    db_set_user_locale(update.effective_user.id, code)
    await q.answer()
    text = render_template("language_set.txt", lang=code)
    await q.edit_message_text(text)
