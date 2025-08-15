import yaml

with open("config/ui_config.yaml", "r", encoding="utf-8") as f:
    _ui = yaml.safe_load(f)

with open("config/membership.yaml", "r", encoding="utf-8") as f:
    _mb = yaml.safe_load(f)

with open("config/i18n.yaml", "r", encoding="utf-8") as f:
    _i18n = yaml.safe_load(f)

# User interface
telegram_start = _ui.get("start", {})
templates = _ui.get("messages", {})
admin_ui = _ui.get("admin_interface", {})
language_prompt = _ui.get("language_prompt", {})
start_language_prompt = _ui.get("start_language_prompt", {})
post_join = _ui.get("post_join", {})
behavior = _ui.get("behavior", {})
invalid_id_prompt = _ui.get("invalid_id_prompt", {})

# Membership rules
id_config = _mb.get("id", {})
admin_buttons = _mb.get("admin", {})
expiration = _mb.get("expiration", {})
session_timeout = _mb.get("session_timeout", {})
renewal = _mb.get("renewal", {})

# i18n
i18n = _i18n.get("i18n", {})
i18n_buttons = _i18n.get("i18n_buttons", {})
