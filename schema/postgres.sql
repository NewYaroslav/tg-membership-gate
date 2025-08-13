CREATE TABLE IF NOT EXISTS allowed_emails (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    is_banned INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_allowed_email ON allowed_emails(email);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    full_name TEXT,
    email_id BIGINT REFERENCES allowed_emails(id),
    is_authorized INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_topic TEXT,
    last_message TEXT,
    request_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_email_id ON users(email_id);

CREATE OR REPLACE FUNCTION trg_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION trg_update_timestamp();

CREATE TABLE IF NOT EXISTS admins (
    telegram_id BIGINT PRIMARY KEY,
    is_top_level INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_admins_telegram_id ON admins(telegram_id);
