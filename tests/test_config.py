import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.config import telegram_start, templates, admin_buttons, id_config, expiration, session_timeout, renewal


def test_config_loaded():
    assert "template" in telegram_start
    assert "ask_id" in templates
    assert isinstance(admin_buttons.get("approve_durations"), list)
    assert "pattern" in id_config
    assert "warn_before_sec" in expiration
    assert "seconds" in session_timeout
    assert "user_plans" in renewal
