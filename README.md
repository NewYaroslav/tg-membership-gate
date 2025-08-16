# Tg-Bot Membership Gate
[Русская версия](README-RU.md)
<img src="docs/logo.png" alt="Logo" width="600"/>

Telegram bot that controls access to private chats/channels by referral ID.

## 🚀 Features

- Start message from template with optional image and "Get access" button.
- ID validation via regex from configuration.
- Notifies administrator about new requests with inline buttons: approve for various periods, decline, ban.
- Supports multiple channels/chats. On approval bot sends invites and removes users after expiry.
- Background tasks warn about access expiration and reset idle sessions.
- Two database backends: SQLite (default) and PostgreSQL via `.env`.
- Admin commands: `/ban`, `/unban`, `/kick`, `/remove`, `/export_users`, `/user`.
- Language selection with `/language` and localized templates/images.
- Personalized greetings using user's name and localized default username.
- All texts are rendered from Jinja2 templates (`templates/`).

## ⚙️ Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment variables (`.env`)**
   - `BOT_TOKEN` – bot token from `@BotFather`.
   - `ROOT_ADMIN_ID` – Telegram ID of admin to notify.
   - `DB_BACKEND` – `sqlite` or `postgres`.
   - `SQLITE_DB_PATH` – path to database file (SQLite).
   - `PG_HOST` – PostgreSQL host (default `127.0.0.1`).
   - `PG_PORT` – PostgreSQL port (default `5432`).
   - `PG_DB` – database name.
   - `PG_USER` – username.
   - `PG_PASSWORD` – password.
   - `PG_SSLMODE` – SSL mode (`disable`, `require`, etc.).
   - `ACCESS_CHATS` – chat/channel IDs to purge on expiry.
   - `JOIN_INVITE_LABEL_PREFIX` – optional prefix for generated invite links.
   - `LOG_LEVEL` – logging verbosity (default `INFO`).
   - `DB_LOG_QUERIES` – set to `true` to log SQL queries.

   Example `.env` for SQLite:
   ```env
   BOT_TOKEN=123456:ABCDEF
   ROOT_ADMIN_ID=123456789
   ACCESS_CHATS=-1001111111,-1002222222
   DB_BACKEND=sqlite
   SQLITE_DB_PATH=./db.sqlite3
   ```

   Example `.env` for PostgreSQL:
   ```env
   BOT_TOKEN=123456:ABCDEF
   ROOT_ADMIN_ID=123456789
   ACCESS_CHATS=-1001111111,-1002222222
   DB_BACKEND=postgres
   PG_HOST=localhost
   PG_PORT=5432
   PG_DB=tg_gate
   PG_USER=gate_user
   PG_PASSWORD=secret
   PG_SSLMODE=disable
   ```

   Before first run create PostgreSQL user and database:
   ```sql
   CREATE USER gate_user WITH PASSWORD 'secret';
   CREATE DATABASE tg_gate OWNER gate_user;
   ```

3. **Configuration (`config/`)**
   Parameters are stored in three YAML files:

   **`ui_config.yaml` — interface and templates**
   - `start` – start message template, button text, `enabled_image`, image map by language.
   - `messages` – maps events to template names: `ask_id`, `waiting`, `banned`, `not_found`, `granted`, `denied`, `warning`, `expired`, `admin_request`, `renewal_warning`, `grace_warning`, `renewal_requested_admin`, `links_unavailable`, `session_timeout`.
   - `admin_interface` – admin button labels. `approve_template` expects `{period}`.
   - `language_prompt` – template and image for `/language` prompt.
   - `start_language_prompt` – template and image for initial language choice on `/start`.
   - `ask_id_prompt` – ID request with optional image.
   - `invalid_id_prompt` – notification about invalid ID with optional image.
   - `post_join` – message sent after joining chat with optional image and `enabled` flag.

   Example `ui_config.yaml`:
   ```yaml
   start:
     template: start_user.txt
     action_button_text:
       en: "Get access"
       ru: "Получить доступ"
     enabled_image: true
     image:
       en: { path: assets/en/start.jpg }
       ru: { path: assets/ru/start.jpg }

   messages:
     ask_id: ask_id.txt
     waiting: id_waiting.txt
     banned: id_banned.txt
     not_found: id_not_found.txt
     granted: access_granted.txt
     denied: access_denied.txt
     session_timeout: session_timeout.txt

   admin_interface:
     approve_template:
       en: "Approve for {period}"
       ru: "Разрешить на {period}"
     decline_text:
       en: "Decline"
       ru: "Отклонить"
     ban_text:
       en: "Ban"
       ru: "Забанить"
     unban_text:
       en: "Unban"
       ru: "Разбанить"
     plans:
       - 259200   # 3 days
       - 604800   # 7 days
       - 2592000  # 30 days
       - 15552000 # 180 days
     enable_decline: true
     enable_ban: true

   expiration:
     check_interval: 60
     warn_before_sec: 86400

   session_timeout:
     seconds: 900
     send_message: true

   renewal:
     warn_before_sec: 86400
     grace_after_expiry_sec: 86400
     user_plans:
       - id: trial_3d
         label: "Подписаться на пробный период"
         duration_sec: 259200
       - id: month_30
         label: "Купить подписку на 30 дней"
         duration_sec: 2592000
       - id: lifetime
         label: "Купить бессрочную подписку"
         duration_sec: 0
   ```

   **`i18n.yaml` — language settings**
   - `i18n.enabled_start_prompt` – if `true`, bot starts in default language and offers `/language` command.
   - `i18n.default_lang` and `supported_langs` – default and supported languages.
   - `i18n_buttons` – button labels and `default_username` fallback.

   Example `i18n.yaml`:
   ```yaml
   i18n:
     enabled_start_prompt: true
     default_lang: en
     supported_langs: [en, ru]

   i18n_buttons:
     en:
       default_username: "Friend"
       choose_language_title: "Choose your language"
       language_choices:
         en: "English"
         ru: "Русский"
     ru:
       default_username: "Друг"
       choose_language_title: "Выберите язык"
       language_choices:
         en: "English"
         ru: "Русский"
   ```

4. **Run**

   ```bash
   python telegram_bot.py
   ```

   Helper scripts are also available:
   - `setup.sh` / `setup.bat` – create a virtual environment and install dependencies (run once);
   - `start.sh` / `start.bat` – activate the environment and launch the bot.

## 🌐 Localized images

 - Store images per language: `assets/<lang>/start.jpg`, `assets/<lang>/post_join.jpg`, optional `assets/<lang>/language_prompt.jpg` and `assets/<lang>/start_language_prompt.jpg`.
 - Set paths or `file_id` in `config/ui_config.yaml` for `start`, `language_prompt`, `start_language_prompt`, and `post_join`.
 - Toggle images with `enabled_image` (`start` and `post_join` enabled by default, `language_prompt` and `start_language_prompt` disabled).
 - Bot caches `file_id` in `media_cache` and reuses it. Changing the file changes hash (`sha256`) and refreshes cache.
 - Images are optional; if missing only text is sent.
 - If caption exceeds 1024 characters, photo is sent without caption and text follows as separate message.

## 🔄 Flow

1. User sends `/start`.
2. Bot replies with greeting and "Get access" button.
3. After pressing, user enters their ID.
4. If ID confirmed in DB – bot sends invite links.
5. If ID not found/confirmed – admin receives message with inline buttons.
6. On approval user gets invites; on decline/ban – respective notifications.
7. Background task warns about expiry and removes user from chats when time is up.

## 💬 Commands

**User**

- `/start` — launch bot and get access button.
- `/help` — help.
- `/language` — choose interface language.

**Admin**

- `/ban <KEY>` — ban user and remove from channels.
- `/unban <KEY>` — remove ban.
- `/kick <KEY>` — remove from channels and reset confirmation but keep in DB.
- `/remove <KEY>` — remove from channels and delete record.
- `/export_users [all|confirmed|unconfirmed|banned]` — export users to CSV.
- `/user <KEY>` — show user info.

`<KEY>` may be `membership_id`, numeric `telegram_id`, or `@username`.

## 🧪 Tests

```bash
pytest
```

A smoke test has been run for lifetime subscription functionality and unsubscribe/ban operations. Limited-time subscriptions have not been validated.

## 🗂 Modules

- `modules/` – bot code (router, handlers, DB, schedulers).
- `templates/` – message templates.
- `schema/` – SQL schemas for SQLite and PostgreSQL.
- `config/` – YAML configs for interface and access rules.

## 📄 License

This project is released under the MIT License.
