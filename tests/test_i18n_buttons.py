from modules.i18n import get_button_text, DEFAULT_LANG


def test_get_button_text_basic():
    cfg = {"en": "Get", "ru": "Получить"}
    assert get_button_text(cfg, "ru") == "Получить"
    assert get_button_text(cfg, "de") == cfg[DEFAULT_LANG]


def test_get_button_text_fallback():
    cfg = {"ru": "Получить"}
    assert get_button_text(cfg, "de", "Get") == "Get"
