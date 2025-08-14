from __future__ import annotations

import os
from modules.storage import db_get_join_link, db_upsert_join_link

label_prefix = os.getenv("JOIN_INVITE_LABEL_PREFIX")

async def ensure_join_request_link(bot, chat_id: int) -> str:
    row = db_get_join_link(chat_id)
    if row:
        return row["invite_link"]
    params = dict(chat_id=chat_id, creates_join_request=True)
    if label_prefix:
        params["name"] = f"{label_prefix}{chat_id}"
    inv = await bot.create_chat_invite_link(**params)
    db_upsert_join_link(chat_id, inv.invite_link)
    return inv.invite_link
