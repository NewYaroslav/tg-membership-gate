CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    locale VARCHAR(8)
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

CREATE TABLE IF NOT EXISTS members (
    id SERIAL PRIMARY KEY,
    membership_id TEXT UNIQUE NOT NULL,
    telegram_id BIGINT UNIQUE REFERENCES users(telegram_id),
    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMP,
    warn_sent_at TIMESTAMP,
    grace_notified_at TIMESTAMP,
    post_join_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_members_membership_id ON members(membership_id);
CREATE INDEX IF NOT EXISTS idx_members_telegram_id ON members(telegram_id);
CREATE INDEX IF NOT EXISTS idx_members_expires_at ON members(expires_at);
CREATE INDEX IF NOT EXISTS idx_members_confirmed ON members(is_confirmed);
CREATE INDEX IF NOT EXISTS idx_members_banned ON members(is_banned);

CREATE OR REPLACE FUNCTION trg_members_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER members_updated_at
BEFORE UPDATE ON members
FOR EACH ROW EXECUTE FUNCTION trg_members_updated_at();

CREATE TABLE IF NOT EXISTS admins (
    telegram_id BIGINT PRIMARY KEY,
    is_top_level BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_admins_telegram_id ON admins(telegram_id);

CREATE TABLE IF NOT EXISTS join_invite_links (
    chat_id BIGINT PRIMARY KEY,
    invite_link TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS media_cache (
    asset_key TEXT NOT NULL,
    lang TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_id TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (asset_key, lang)
);

