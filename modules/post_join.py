from __future__ import annotations

from modules.i18n import resolve_user_lang, make_username
from modules.template_engine import render_template
from modules.media_utils import send_localized_image_with_text
from modules.storage import (
    db_get_user_locale,
    db_was_post_join_sent,
    db_mark_post_join_sent,
)
from modules.config import post_join as POST
from modules.log_utils import log_async_call


@log_async_call
async def maybe_send_post_join(bot, member_row: dict, user) -> None:
    """Send post-join message once after user joins a channel."""
    if not POST.get("enabled", True):
        return
    if db_was_post_join_sent(member_row["id"]):
        return
    lang = resolve_user_lang(None, {"locale": db_get_user_locale(member_row["telegram_id"])})
    username = make_username(user, lang)
    text = render_template(POST.get("template", "post_join.txt"), lang=lang, username=username)
    await send_localized_image_with_text(
        bot,
        member_row["telegram_id"],
        asset_key="post_join.image",
        cfg_section=POST,
        lang=lang,
        text=text,
    )
    db_mark_post_join_sent(member_row["id"])
