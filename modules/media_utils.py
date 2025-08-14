from __future__ import annotations

import hashlib
import os
from typing import Any, Tuple

from telegram import Bot
from telegram.error import TelegramError

from modules.storage import db_get_media_cache, db_upsert_media_cache
from modules.logging_config import logger
from modules.i18n import DEFAULT_LANG


def pick_localized_media(cfg_section: dict | None, lang: str, default_lang: str = DEFAULT_LANG) -> dict | None:
    if not cfg_section:
        return None
    if lang in cfg_section:
        return cfg_section[lang]
    if default_lang in cfg_section:
        return cfg_section[default_lang]
    return None


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


async def ensure_file_id_for_asset(
    bot: Bot,
    chat_id: int,
    asset_key: str,
    lang: str,
    path: str,
    *,
    caption: str | None = None,
    reply_markup: Any = None,
    parse_mode: str | None = "HTML",
) -> Tuple[str, bool]:
    """Ensure file_id for a local asset, uploading if necessary.
    Returns (file_id, uploaded) where uploaded indicates whether photo was sent."""
    file_hash = file_sha256(path)
    cached = db_get_media_cache(asset_key, lang)
    if cached and cached.get("file_hash") == file_hash:
        return cached["file_id"], False
    with open(path, "rb") as f:
        msg = await bot.send_photo(
            chat_id=chat_id,
            photo=f,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    file_id = msg.photo[-1].file_id
    db_upsert_media_cache(asset_key, lang, file_hash, file_id)
    return file_id, True


async def send_localized_image_with_text(
    bot: Bot,
    chat_id: int,
    *,
    asset_key: str,
    cfg_section: dict,
    lang: str,
    text: str,
    reply_markup: Any | None = None,
    parse_mode: str = "HTML",
) -> None:
    media_cfg = pick_localized_media(cfg_section.get("image"), lang, DEFAULT_LANG)
    if not media_cfg:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    caption = text if len(text) <= 1024 else None
    rm_for_photo = reply_markup if caption else None
    try:
        if media_cfg.get("file_id"):
            try:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=media_cfg["file_id"],
                    caption=caption,
                    reply_markup=rm_for_photo,
                    parse_mode=parse_mode if caption else None,
                )
            except TelegramError:
                if media_cfg.get("path") and os.path.exists(media_cfg["path"]):
                    file_id, uploaded = await ensure_file_id_for_asset(
                        bot,
                        chat_id,
                        asset_key,
                        lang,
                        media_cfg["path"],
                        caption=caption,
                        reply_markup=rm_for_photo,
                        parse_mode=parse_mode if caption else None,
                    )
                    if not uploaded:
                        await bot.send_photo(
                            chat_id=chat_id,
                            photo=file_id,
                            caption=caption,
                            reply_markup=rm_for_photo,
                            parse_mode=parse_mode if caption else None,
                        )
                else:
                    await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
                    return
        elif media_cfg.get("path") and os.path.exists(media_cfg["path"]):
            file_id, uploaded = await ensure_file_id_for_asset(
                bot,
                chat_id,
                asset_key,
                lang,
                media_cfg["path"],
                caption=caption,
                reply_markup=rm_for_photo,
                parse_mode=parse_mode if caption else None,
            )
            if not uploaded:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=file_id,
                    caption=caption,
                    reply_markup=rm_for_photo,
                    parse_mode=parse_mode if caption else None,
                )
        else:
            logger.warning("Missing image for %s %s", asset_key, lang)
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
            return
    except Exception as e:
        logger.warning("Photo send failed for %s: %s", asset_key, e)
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    if not caption:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
