CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    membership_id TEXT UNIQUE NOT NULL,
    telegram_id INTEGER UNIQUE,
    username TEXT,
    full_name TEXT,
    is_confirmed INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0,
    expires_at TEXT,
    warn_sent_at TEXT,
    grace_notified_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_members_membership_id ON members(membership_id);
CREATE INDEX IF NOT EXISTS idx_members_telegram_id ON members(telegram_id);

CREATE TRIGGER IF NOT EXISTS trg_members_updated_at
AFTER UPDATE ON members
FOR EACH ROW
BEGIN
    UPDATE members SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS admins (
    telegram_id INTEGER PRIMARY KEY,
    is_top_level INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_admins_telegram_id ON admins(telegram_id);

CREATE TABLE IF NOT EXISTS join_invite_links (
    chat_id INTEGER PRIMARY KEY,
    invite_link TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

