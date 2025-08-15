CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    locale TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    membership_id TEXT UNIQUE NOT NULL,
    telegram_id INTEGER UNIQUE,
    is_confirmed INTEGER NOT NULL DEFAULT 0 CHECK (is_confirmed IN (0,1)),
    is_banned INTEGER NOT NULL DEFAULT 0 CHECK (is_banned IN (0,1)),
    expires_at INTEGER,
    warn_sent_at TEXT,
    grace_notified_at TEXT,
    post_join_sent_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
);

CREATE INDEX IF NOT EXISTS idx_members_membership_id ON members(membership_id);
CREATE INDEX IF NOT EXISTS idx_members_telegram_id ON members(telegram_id);
CREATE INDEX IF NOT EXISTS idx_members_expires_at ON members(expires_at);
CREATE INDEX IF NOT EXISTS idx_members_confirmed ON members(is_confirmed);
CREATE INDEX IF NOT EXISTS idx_members_banned ON members(is_banned);

CREATE TRIGGER IF NOT EXISTS trg_members_updated_at
AFTER UPDATE ON members
FOR EACH ROW
BEGIN
    UPDATE members SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS admins (
    telegram_id INTEGER PRIMARY KEY,
    is_top_level INTEGER NOT NULL DEFAULT 0 CHECK (is_top_level IN (0,1))
);

CREATE INDEX IF NOT EXISTS idx_admins_telegram_id ON admins(telegram_id);

CREATE TABLE IF NOT EXISTS join_invite_links (
    chat_id INTEGER PRIMARY KEY,
    invite_link TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS media_cache (
    asset_key TEXT NOT NULL,
    lang TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_id TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (asset_key, lang)
);

