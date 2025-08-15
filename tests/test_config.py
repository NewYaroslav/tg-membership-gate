import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.config import (
    telegram_start,
    templates,
    admin_buttons,
    id_config,
    expiration,
    session_timeout,
    renewal,
    i18n,
    i18n_buttons,
    language_prompt,
    start_language_prompt,
    post_join,
    behavior,
    ask_id_prompt,
    invalid_id_prompt,
)


def test_config_loaded():
    assert "template" in telegram_start
    assert "enabled_image" in telegram_start
    assert "ask_id" in templates
    assert isinstance(admin_buttons.get("approve_durations"), list)
    assert "pattern" in id_config
    assert "warn_before_sec" in expiration
    assert "seconds" in session_timeout
    assert "user_plans" in renewal
    assert "default_lang" in i18n
    assert "en" in i18n_buttons
    assert "template" in language_prompt
    assert "template" in start_language_prompt
    assert "template" in ask_id_prompt
    assert "template" in invalid_id_prompt
    assert "template" in post_join
    assert "enabled_image" in post_join
    assert "suppress_service_messages" in behavior
