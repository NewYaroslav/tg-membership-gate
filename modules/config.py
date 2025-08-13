import yaml

with open("config/ui_config.yaml", "r", encoding="utf-8") as f:
    _ui = yaml.safe_load(f)

with open("config/membership.yaml", "r", encoding="utf-8") as f:
    _mb = yaml.safe_load(f)

# User interface
telegram_start = _ui.get("start", {})
templates = _ui.get("messages", {})
admin_ui = _ui.get("admin_interface", {})

# Membership rules
id_config = _mb.get("id", {})
admin_buttons = _mb.get("admin", {})
expiration = _mb.get("expiration", {})
session_timeout = _mb.get("session_timeout", {})
