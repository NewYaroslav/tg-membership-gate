# tg-brsc-support

**Телеграм-бот для автоматизации обработки обращений в ИТ-поддержку сотрудников АО «БРСК».**

Проект разработан с учётом внутренних процессов компании и предназначен для ускорения и стандартизации приёма обращений от сотрудников через Telegram. Бот обеспечивает авторизацию по корпоративной почте, классификацию обращений, сбор необходимой информации и передачу данных в Telegram-группу поддержки и/или на email.


## 🚀 Возможности

- Авторизация сотрудников по корпоративному email (с проверкой по белому списку)
- Поддержка ручного и пакетного добавления email-адресов, включая загрузку CSV-файлов
- Блокировка, удаление и проверка статуса email-адресов через команды администратора
- Интерфейс выбора категории обращения через Telegram-клавиатуру
- Ввод текста обращения, прикрепление фотографий и одного документа
- Отправка обращений в Telegram-группу и/или по email в виде HTML-писем
- Гибкая система шаблонов (Jinja2) и состояний для персонализированного взаимодействия
- Конфигурация поведения бота через YAML-файлы
- Таймер бездействия, автоматически сбрасывающий диалог при долгом отсутствии активности
- Логирование в файл и консоль для администрирования и отладки

## Алгоритм работы бота

Бот работает как конечный автомат (FSM) с пошаговой логикой обработки пользователей. Вот краткое описание его работы:

### 1. ▶️ Запуск и команда `/start`

- Пользователь запускает бота командой `/start`.
- Бот проверяет, авторизован ли пользователь по Telegram ID.

---

### 2. 🔐 Авторизация по email

- Если пользователь не авторизован, бот просит ввести корпоративный email.
- Если включено `allow_incomplete_input`, то email можно вводить без домена (например, `ivanov` → `ivanov@yourcompany.com`).
- Email проверяется:
  - по регулярному выражению (`email_pattern`),
  - на наличие в белом списке (таблица email-ов в БД),
  - на отсутствие блокировки (`is_banned`).

#### Возможные сценарии:
- ✅ Email найден и не заблокирован → авторизация, переход к следующему шагу.
- ⛔ Email не найден → бот уведомляет, что email не зарегистрирован.
- 🚫 Email заблокирован → бот уведомляет и не авторизует пользователя.

---

### 3. 🔄 Повторная авторизация

Если пользователь уже авторизован:

- При повторном вводе того же email — бот сообщает, что авторизация уже выполнена.
- При вводе нового email — бот просит подтвердить смену email.

---

### 4. 👋 Приветствие и ввод обращения

- После успешной авторизации бот может (в зависимости от настроек):
  - отправить приветствие (`welcome_user.txt`),
  - предложить выбрать категорию обращения.

---

### 5. ℹ️ Выбор категории

- Пользователь выбирает тему обращения (например, «🛠 Ошибки в работе ПО»), после чего, при необходимости, выбирает подкатегорию.
- Используется inline-клавиатура с категориями и подкатегориями из `ticket_categories`.

---

### 6. 💬 Ввод сообщения

- Бот просит ввести текст обращения.
- Проверяется длина (если превышает `max_submission_length`, сообщение отклоняется).
- Проверяется частота обращений (`max_requests` в `interval_sec`).

---

### 7. 📤 Отправка обращения

- Бот формирует текст обращения на основе шаблонов (`ticket_summary.txt`, `support_email.html`).
- Отправляет обращение в:
  - указанный Telegram-чат (`SUPPORT_CHAT_ID`),
  - email (через SMTP-параметры из `.env`).

---

### 8. 🔁 Возврат в IDLE

- После отправки бот переходит в состояние `IDLE`, ожидая новых команд или запросов от пользователя.


### 9. ⏱ Тайм-аут неактивности

- Если пользователь бездействует дольше `session_timeout.seconds`, бот сбрасывает состояние диалога.
- При `send_message: true` перед сбросом отправляется сообщение из шаблона `message_template`.


## 📦 Установка

> Требуется Python 3.9 или выше.

### Вариант 1: ручная установка

1. Перейдите в репозиторий:
   ```bash
   cd tg-brsc-support
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   # Windows:
   call venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
   
4. Настройте бота:
   * `.env` — переменные окружения.
   * `auth.yaml` — поведение авторизации пользователей через email.
   * `ui_config.yaml` — файл конфигурации интерфейса.
   * `templates/` — шаблоны сообщений в формате Jinja2 (*.txt, *.html)

4. Запустите бота:

   ```bash
   python telegram_bot.py
   ```
   
### Вариант 2: запуск через скрипты

Windows:

```bash
setup.bat
start.bat
```

Linux/macOS:

```bash
./setup.sh
./start.sh
```

Убедитесь, что файлы setup.sh и start.sh имеют права на исполнение:

```bash
chmod +x setup.sh start.sh
```

> 📌 Перед запуском не забудьте настроить бота: `.env`, `auth.yaml`, `ui_config.yaml`, а также шаблоны в папке `templates/` — как указано в шаге 4 варианта 1.


## ⚙️ Конфигурационные файлы

### `.env`

В файле `.env` указываются ключевые параметры:

```dotenv
BOT_TOKEN=your_bot_token
EMAIL_SENDER=bot@yourcompany.com
EMAIL_PASSWORD=app_password
SMTP_SERVER=smtp.yourcompany.com
SMTP_PORT=587
SUPPORT_EMAIL=support@yourcompany.com
SUPPORT_CHAT_ID=-1001234567890
LOG_LEVEL=DEBUG
DB_BACKEND=sqlite
SQLITE_DB_PATH=database/db.sqlite3
PG_HOST=127.0.0.1
PG_PORT=5432
PG_DB=appdb
PG_USER=app
PG_PASSWORD=secret
PG_SSLMODE=disable
```

#### Пояснения к параметрам

| Переменная         | Назначение                                                                 |
|--------------------|----------------------------------------------------------------------------|
| `BOT_TOKEN`         | Токен Telegram-бота от [@BotFather](https://t.me/BotFather).              |
| `EMAIL_SENDER`      | Адрес email-отправителя (например, корпоративный ящик бота).              |
| `EMAIL_PASSWORD`    | Пароль/токен приложения для SMTP-аутентификации отправителя.              |
| `SMTP_SERVER`       | SMTP-сервер, используемый для отправки email-сообщений.                   |
| `SMTP_PORT`         | Порт SMTP-сервера (обычно `587` для STARTTLS или `465` для SMTPS).        |
| `SUPPORT_EMAIL`     | Email службы поддержки — указывается в уведомлениях и шаблонах.           |
| `SUPPORT_CHAT_ID`   | Telegram chat ID (например, группы) для пересылки тикетов.                |
| `LOG_LEVEL`         | Уровень логирования: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.     |
| `DB_BACKEND`       | Backend for database (`sqlite` or `postgres`). |
| `SQLITE_DB_PATH`   | Path to SQLite database file. |
| `PG_HOST`          | PostgreSQL host. |
| `PG_PORT`          | PostgreSQL port. |
| `PG_DB`            | PostgreSQL database name. |
| `PG_USER`          | PostgreSQL user. |
| `PG_PASSWORD`      | PostgreSQL password. |
| `PG_SSLMODE`       | SSL mode (`disable`, `prefer`, `require`). |


### `config/auth.yaml`

Файл auth.yaml управляет поведением авторизации пользователей через email. 
Он используется в логике обработки команды /start и ввода email в Telegram-боте.

#### Пример конфигурации

```yaml
auth:
  email_pattern: "^[a-zA-Z0-9_.+-]+@yourcompany\.com$"
  email_autocomplete: "@yourcompany.com"
  allow_incomplete_input: true
  send_welcome_before_topic: true
  send_topic_after_auth: true
  delay_after_auth_success: 2
```

#### Пояснения к параметрам

| Параметр                     | Тип     | Описание |
|-----------------------------|---------|----------|
| `email_pattern`             | string  | Регулярное выражение, задающее допустимый формат email. Используется для валидации введённого email. Например, можно разрешить только домен `@yourcompany.com`. |
| `email_autocomplete`        | string  | Суффикс, который будет автоматически добавлен к email, если пользователь ввёл только логин без `@`. Например, `foo` превратится в `foo@yourcompany.com`. |
| `allow_incomplete_input`    | boolean | Разрешить ли автоматическое дополнение email при неполном вводе (например, `test` → `test@yourcompany.com`). Если `false`, то пользователь обязан вводить полный email. |
| `send_welcome_before_topic` | boolean | Если `true`, то перед показом выбора категории обращения будет отправлено приветственное сообщение. |
| `send_topic_after_auth`     | boolean | Управляет тем, будет ли показан выбор категории сразу после успешной авторизации. Если `false`, бот перейдёт в состояние ожидания и не будет предлагать выбрать тему. |
| `delay_after_auth_success`  | int     | Задержка (в секундах) перед отправкой выбора темы после авторизации. Может использоваться, если нужно дать время на отображение других сообщений (например, приветствия). |


### `config/ui_config.yaml`

Файл конфигурации интерфейса содержит параметры управления ботом, в том числе:
- команды меню,
- начальное поведение при авторизации,
- категории тикетов,
- ограничения.

Конфигурация интерфейса:

```yaml
telegram_menu: # Описывает команды, отображаемые в меню Telegram:
  - command: start
    description: "Обратиться за помощью"
  - command: help
    description: "Показать справку"
  - command: myid
    description: "Показать ID и email (если есть)"

telegram_start: # Параметры поведения после авторизации
  show_action_button_if_authorized: true      # Показывать кнопку действий после входа
  action_button_text: "📨 Отправить обращение" # Текст на этой кнопке

authorization: # Конфигурация авторизации и отображения статусов
  confirm_change_buttons:
    yes: "✅ Да" # Кнопка подтверждения смены email
    no: "❌ Нет" # Кнопка отмены смены email

  email_status_labels:
    allowed: "✅ Разрешён" # Метка для разрешённого email
    banned: "🚫 Забанен"   # Метка для забаненного email

ticket_categories: # Список категорий с подкатегориями и шаблонами подсказок
  - label: "💻 Ошибки в работе оборудования"
    subcategories:
      - label: "Не включается, завис ПК"
        template: hardware_issue_message.txt
      - label: "Не работает телефон"
        template: hardware_issue_message.txt
      - label: "Печать/замена картриджа"
        template: hardware_issue_message.txt
  - label: "🛠 Ошибки в работе ПО"
    subcategories:
      - label: "Ошибка при работе, запуске"
        template: software_issue_message.txt
      - label: "Нет доступа к системе"
        template: software_issue_message.txt
  - label: "💾 Установка ПО"
    template: software_install_message.txt
  - label: "🔑 Запросы на доступ к ресурсам"
    informational: true
    template: access_request_info.txt
  - label: "🌐 Сетевые проблемы"
    subcategories:
      - label: "Нет Интернета/доступа"
        template: software_issue_message.txt
      - label: "Не работает э/почта"
        template: software_issue_message.txt
  - label: "🛡 Кибербезопасность"
    subcategories:
      - label: "Подозрительные письма, звонки"
        template: contact_info_message.txt
      - label: "Вирусы"
        template: contact_info_message.txt
      - label: "Другое"
        template: contact_info_message.txt
  - label: "❗ Жалоба/благодарность"
    subcategories:
      - label: "Жалоба"
        template: contact_info_message.txt
      - label: "Благодарность"
        template: contact_info_message.txt
  - label: "📁 Другое"
    template: contact_info_message.txt

message_limits: # Ограничения по обращениям и текстам
  max_submission_length: 1500   # Максимально допустимая длина одного текстового обращения
  max_requests: 3               # Сколько обращений разрешено в пределах одного периода
  interval_sec: 3600            # Продолжительность периода в секундах (например, 1 час = 3600)
session_timeout: # Тайм-аут неактивности
  seconds: 900                  # Через сколько секунд бездействия сбрасывать состояние
  send_message: false           # Отправлять ли предупреждение перед сбросом
  message_template: inactivity_timeout.txt # Шаблон предупреждающего сообщения
```


## 📁 Шаблоны сообщений

Файлы шаблонов находятся в папке `templates/`. Они позволяют гибко кастомизировать текст сообщений:

| Файл                         | Назначение |
|------------------------------|------------|
| admin_waiting_for_csv.txt    | Запрос на загрузку CSV-файла от администратора |
| auth_already.txt             | Пользователь уже авторизован |
| auth_banned.txt              | Email в базе, но помечен как заблокированный |
| auth_change_cancelled.txt    | Смена email отменена |
| auth_change_confirm.txt      | Подтверждение смены email |
| auth_changed.txt             | Уведомление об успешной смене email |
| auth_invalid.txt             | Введён некорректный email |
| auth_not_registered.txt      | Email не найден в базе |
| auth_start.txt               | Приветствие при входе, если пользователь не авторизован |
| auth_success.txt             | Уведомление об успешной авторизации |
| access_request_info.txt      | Информация о получении доступа к ресурсам |
| email_added.txt              | Успешное добавление email |
| email_banned.txt             | Успешная блокировка email |
| email_removed.txt            | Успешное удаление email |
| email_required.txt           | Email не указан при вызове команды |
| email_status_found.txt       | Статус указанного email (разрешён/забанен) |
| email_status_not_found.txt   | Email не найден |
| email_subject.txt            | Тема письма при отправке email в техподдержку |
| enter_message.txt            | Просьба ввести текст обращения |
| hardware_issue_message.txt   | Инструкция по описанию проблемы с оборудованием |
| software_issue_message.txt   | Инструкция по описанию ошибки ПО или сети |
| software_install_message.txt | Запрос наименование ПО для установки |
| contact_info_message.txt     | Запрос контактных данных и дополнительной информации |
| help_admin.txt               | Справка для администраторов |
| help_user.txt                | Справка для обычных пользователей |
| invalid_csv_file.txt         | Ошибка при чтении CSV-файла (например, неправильная кодировка или структура) |
| invalid_input.txt            | Введено что-то не по формату/не в нужный момент |
| invalid_topic.txt            | Ошибка при вводе некорректной категории |
| message_too_long.txt         | Сообщение слишком длинное |
| my_id.txt                    | Сообщение с ID пользователя и email (если есть) |
| not_authorized.txt           | Ошибка: команда доступна только администраторам |
| rate_limit_exceeded.txt      | Сообщение о превышении лимита обращений, включает таймер ожидания |
| select_topic.txt             | Выбор категории обращения |
| select_topic_intro.txt       | Вводное сообщение при выборе темы, если кнопка была нажата не по inline-кнопке |
| support_email.html           | HTML-шаблон email сообщения для поддержки |
| ticket_sent.txt              | Подтверждение успешной отправки обращения |
| ticket_summary.txt           | Итоговое сообщение, отправляемое в Telegram и/или email |
| unsupported_file_type.txt    | Ошибка: файл должен быть формата .csv или .txt |
| welcome_user.txt             | Приветствие для авторизованного пользователя |


## Поддерживаемые базы данных

Бот может использовать SQLite (по умолчанию) или PostgreSQL.

### Переключение бэкенда

1. Установите переменную окружения `DB_BACKEND` (`sqlite` или `postgres`).
2. Для SQLite задайте путь к файлу в переменной `SQLITE_DB_PATH`.
3. Для PostgreSQL укажите в `.env` параметры `PG_HOST`, `PG_PORT`, `PG_DB`, `PG_USER`, `PG_PASSWORD`, `PG_SSLMODE`.

### Инициализация схемы

SQL-скрипты находятся в `schema/sqlite.sql` и `schema/postgres.sql` и выполняются при вызове `db_init()`.

### Проверка соединения с PostgreSQL

```bash
psql -h $PG_HOST -U $PG_USER -d $PG_DB -c '\dt'
```
