CREATE TABLE IF NOT EXISTS members (
    id SERIAL PRIMARY KEY,
    membership_id TEXT UNIQUE NOT NULL,
    telegram_id BIGINT UNIQUE,
    username TEXT,
    full_name TEXT,
    is_confirmed BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP,
    warn_sent_at TIMESTAMP,
    grace_notified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_members_membership_id ON members(membership_id);
CREATE INDEX IF NOT EXISTS idx_members_telegram_id ON members(telegram_id);

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
    is_top_level BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_admins_telegram_id ON admins(telegram_id);

CREATE TABLE IF NOT EXISTS join_invite_links (
    chat_id BIGINT PRIMARY KEY,
    invite_link TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

