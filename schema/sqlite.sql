CREATE TABLE IF NOT EXISTS allowed_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    is_banned INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_allowed_email ON allowed_emails(email);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    full_name TEXT,
    email_id INTEGER,
    is_authorized INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_topic TEXT,
    last_message TEXT,
    request_count INTEGER DEFAULT 0,
    FOREIGN KEY (email_id) REFERENCES allowed_emails(id)
);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_email_id ON users(email_id);

CREATE TRIGGER IF NOT EXISTS trg_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS admins (
    telegram_id INTEGER PRIMARY KEY,
    is_top_level INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_admins_telegram_id ON admins(telegram_id);
