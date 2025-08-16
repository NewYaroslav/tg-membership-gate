# Tg-Bot Membership Gate
<img src="docs/logo.png" alt="Logo" width="600"/>

Телеграм‑бот, который управляет доступом в закрытые чаты/каналы по реферальному ID.

## 🚀 Возможности

- Стартовое сообщение по шаблону с опциональной картинкой и кнопкой «Получить доступ».
- Проверка ID по регулярному выражению из конфигурации.
- Уведомление администратора о новых запросах. Под сообщением админ видит набор
  кнопок: подтвердить (на разные сроки), отклонить, заблокировать.
- Поддержка списка каналов/чатов. При подтверждении бот отправляет приглашения,
  а по истечении срока – удаляет пользователя из этих чатов.
- Фоновая задача следит за истечением доступа и заблаговременно предупреждает
  пользователя. Таймауты бездействия также сбрасываются фоновой задачей.
- Два бэкенда базы данных: SQLite (по умолчанию) и PostgreSQL. Переключение через `.env`.
- Набор админ‑команд: `/ban`, `/unban`, `/kick`, `/remove`, `/export_users`, `/user`.
- Выбор языка командой `/language` и локализация шаблонов и изображений.
- Персонализированное приветствие с именем пользователя и локализованным именем по умолчанию.
- Все тексты вынесены в Jinja2‑шаблоны (`templates/`).

## ⚙️ Настройка

1. **Установка зависимостей**
   ```bash
   pip install -r requirements.txt
   ```

2. **Переменные окружения (`.env`)**
   - `BOT_TOKEN` – токен бота от `@BotFather`.
   - `ROOT_ADMIN_ID` – Telegram ID администратора для уведомлений.
   - `DB_BACKEND` – `sqlite` или `postgres`.
   - `SQLITE_DB_PATH` – путь к файлу базы (для SQLite).
   - `PG_HOST` – хост PostgreSQL (по умолчанию `127.0.0.1`).
   - `PG_PORT` – порт PostgreSQL (по умолчанию `5432`).
   - `PG_DB` – имя базы данных.
   - `PG_USER` – имя пользователя.
   - `PG_PASSWORD` – пароль пользователя.
   - `PG_SSLMODE` – режим SSL (`disable`, `require` и т.д.).
   - `ACCESS_CHATS` – ID чатов/каналов, из которых нужно удалять при окончании доступа.
   - `JOIN_INVITE_LABEL_PREFIX` – опциональный префикс для создаваемых заявочных ссылок.
   - `LOG_LEVEL` – уровень логирования (по умолчанию `INFO`).
   - `DB_LOG_QUERIES` – при `true` выводит SQL-запросы в лог.

   Пример `.env` для SQLite:
   ```env
   BOT_TOKEN=123456:ABCDEF
   ROOT_ADMIN_ID=123456789
   ACCESS_CHATS=-1001111111,-1002222222
   DB_BACKEND=sqlite
   SQLITE_DB_PATH=./db.sqlite3
   ```

   Пример `.env` для PostgreSQL:
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

   Перед запуском создайте в PostgreSQL пользователя и базу:
   ```sql
   CREATE USER gate_user WITH PASSWORD 'secret';
   CREATE DATABASE tg_gate OWNER gate_user;
   ```

3. **Конфигурация (`config/`)**
   Все параметры бота вынесены в три YAML‑файла:

   **`ui_config.yaml` — интерфейс и шаблоны**
   - `start` – параметры стартового сообщения: файл шаблона, текст кнопки,
     флаг `enabled_image` и набор картинок по языкам.
  - `messages` – соответствие событий имени шаблона: `ask_id`, `waiting`,
    `banned`, `not_found`, `granted`, `denied`, `warning`, `expired`,
    `admin_request`, `renewal_warning`, `grace_warning`,
    `renewal_requested_admin`, `links_unavailable`, `session_timeout`.
   - `admin_interface` – подписи для кнопок администратора. Шаблон
     `approve_template` принимает `{period}`.
  - `language_prompt` – шаблон и картинка для смены языка через `/language`.
  - `start_language_prompt` – шаблон и картинка для первичного выбора языка на `/start`.
  - `ask_id_prompt` – запрос ID с опциональной картинкой.
  - `invalid_id_prompt` – уведомление о некорректном ID с опциональной картинкой.
  - `post_join` – сообщение после вступления в чат: шаблон, опциональная
    картинка и флаг `enabled`.

   Пример `ui_config.yaml`:
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
    kick_text:
      en: "Kick"
      ru: "Кикнуть"
    remove_text:
      en: "Remove"
      ru: "Удалить"

   language_prompt:
     enabled_image: false
     template: language_prompt.txt

   start_language_prompt:
     enabled_image: false
     template: start_language_prompt.txt

   ask_id_prompt:
     enabled_image: false
     template: ask_id.txt

   invalid_id_prompt:
     enabled_image: false
     template: id_invalid.txt

   post_join:
     enabled: true
     enabled_image: true
     template: post_join.txt
     image:
       en: { path: assets/en/final.jpg }
       ru: { path: assets/ru/final.jpg }
   ```

   **`membership.yaml` — правила доступа**
   - `id.pattern` – регулярное выражение для проверки введённого ID.
   - `admin.approve_durations` – список длительностей выдачи доступа в секундах
     (0 — бессрочно). Также можно отключить кнопки `decline` и `ban`.
   - `expiration.check_interval` и `warn_before_sec` – период проверки и
     заблаговременное предупреждение об окончании доступа.
   - `session_timeout.seconds` – время неактивности для сброса диалога;
     `send_message` включает отправку стартового сообщения при сбросе.
   - `renewal` – логика продления доступа: время предупреждения,
     длительность «grace period» и список тарифов `user_plans` (id/label/
     duration_sec).

   Пример `membership.yaml`:
   ```yaml
   id:
     pattern: "^[A-Z0-9]{4,10}$"

   admin:
     approve_durations:
       - 0        # бессрочно
       - 2592000 # 30 дней
       - 15552000 # 180 дней
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

   **`i18n.yaml` — языковые настройки**
   - `i18n.enabled_start_prompt` – если `true`, бот стартует на языке по
     умолчанию и предлагает выбрать язык командой `/language`.
   - `i18n.default_lang` и `supported_langs` – язык по умолчанию и список
     поддерживаемых языков.
   - `i18n_buttons` – подписи кнопок выбора языка (`language_choices`) и fallback-имя `default_username`.

   Пример `i18n.yaml`:
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

4. **Запуск**

   ```bash
   python telegram_bot.py
   ```

   Есть вспомогательные скрипты:
   - `setup.sh` / `setup.bat` — создают виртуальное окружение и устанавливают зависимости (выполняются один раз);
   - `start.sh` / `start.bat` — активируют окружение и запускают бота.

## 🌐 Localized images

 - Сложите картинки по языкам: `assets/<lang>/start.jpg`, `assets/<lang>/post_join.jpg` и, при необходимости, `assets/<lang>/language_prompt.jpg` и `assets/<lang>/start_language_prompt.jpg`.
 - В `config/ui_config.yaml` укажите пути или `file_id` для секций `start`,
   `language_prompt`, `start_language_prompt` и `post_join`.
 - Переключайте отправку картинок через `enabled_image` (`start` и
   `post_join` включены по умолчанию, `language_prompt` и `start_language_prompt` — отключены).
- Бот кеширует `file_id` в таблице `media_cache` и переиспользует его.
  При замене файла хеш (`sha256`) меняется — изображение переотправится и
  кеш обновится автоматически.
- Изображения опциональны; при отсутствии отправляется только текст.
- Если подпись превышает 1024 символа, фото придёт без подписи, а текст —
  отдельным сообщением.

## 🔄 Алгоритм работы

1. Пользователь вводит команду `/start`.
2. Бот отправляет приветствие и кнопку «Получить доступ».
3. После нажатия пользователь вводит свой ID.
4. Если ID подтверждён в БД – бот отправляет ссылки на закрытые чаты.
5. Если ID не найден или не подтверждён – администратор получает сообщение
   с inline‑кнопками для решения.
6. При одобрении пользователь получает приглашения. При отказе/бане – соответствующее уведомление.
7. Фоновая задача предупреждает об истечении срока и удаляет пользователя
   из чатов, когда срок закончится.

## 💬 Команды

**Пользовательские**

- `/start` — запустить бота и получить кнопку доступа.
- `/help` — справка.
- `/language` — выбрать язык интерфейса.

**Администраторские**

- `/ban <KEY>` — заблокировать пользователя и удалить из каналов.
- `/unban <KEY>` — снять бан.
- `/kick <KEY>` — удалить из каналов и сбросить подтверждение, но оставить в БД.
- `/remove <KEY>` — удалить из каналов и полностью удалить запись из БД.
- `/export_users [all|confirmed|unconfirmed|banned]` — экспорт пользователей в CSV.
- `/user <KEY>` — показать сведения о пользователе.

`<KEY>` может быть `membership_id`, числовым `telegram_id` или `@username`.

## 🧪 Тесты

```bash
pytest
```

На данный момент выполнен дымовой тест функциональности,
связанной с бессрочной подпиской и операциями отписки/бана.
Корректность работы подписки на ограниченный срок не проверялась.

## 🗂 Структура модулей

- `modules/` – код бота (роутер, обработчики, БД, планировщики).
- `templates/` – текстовые шаблоны сообщений.
- `schema/` – SQL‑схемы для SQLite и PostgreSQL.
- `config/` – YAML‑конфигурация интерфейса и правил доступа.

## 📄 Лицензия

Проект распространяется под лицензией MIT.

