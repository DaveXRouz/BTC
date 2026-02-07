-- NPS V4 — PostgreSQL Schema
-- Run: psql -U nps -d nps -f init.sql

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── Users & Auth ───

CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        VARCHAR(100) UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,           -- bcrypt hash
    salt            BYTEA,                   -- per-user encryption salt
    role            VARCHAR(20) DEFAULT 'user',  -- 'admin', 'user', 'readonly'
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    last_login      TIMESTAMPTZ,
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS api_keys (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash        TEXT NOT NULL,            -- SHA-256 hash of the API key
    name            VARCHAR(100) NOT NULL,
    scopes          TEXT[] DEFAULT '{}',      -- e.g. {'scanner:read', 'oracle:write'}
    rate_limit      INTEGER DEFAULT 60,       -- requests per minute
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    last_used       TIMESTAMPTZ,
    is_active       BOOLEAN DEFAULT TRUE
);

-- ─── Sessions (before findings, which references it) ───

CREATE TABLE IF NOT EXISTS sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    terminal_id     VARCHAR(100),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    mode            VARCHAR(20) NOT NULL DEFAULT 'both',
    chains          TEXT[] DEFAULT '{btc,eth}',
    settings        JSONB DEFAULT '{}',
    stats           JSONB DEFAULT '{}',
    checkpoint      JSONB,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    duration_secs   DOUBLE PRECISION,
    status          VARCHAR(20) DEFAULT 'running',
    v3_session_id   VARCHAR(200),
    migrated_from   VARCHAR(20) DEFAULT 'v4'
);

CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_started ON sessions(started_at);

-- ─── Findings (Vault) ───

CREATE TABLE IF NOT EXISTS findings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID REFERENCES sessions(id) ON DELETE SET NULL,
    address         TEXT NOT NULL,
    chain           VARCHAR(20) NOT NULL DEFAULT 'btc',
    balance         NUMERIC(30, 18) DEFAULT 0,
    score           DOUBLE PRECISION DEFAULT 0,
    -- Sensitive fields: AES-256-GCM encrypted
    private_key_enc TEXT,
    seed_phrase_enc TEXT,
    wif_enc         TEXT,
    extended_private_key_enc TEXT,
    -- Metadata
    source          VARCHAR(50),
    puzzle_number   INTEGER,
    score_breakdown JSONB,
    metadata        JSONB DEFAULT '{}',
    -- Timestamps
    found_at        TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    -- V3 migration tracking
    v3_session      VARCHAR(200),
    migrated_from   VARCHAR(20) DEFAULT 'v4'
);

CREATE INDEX idx_findings_chain ON findings(chain);
CREATE INDEX idx_findings_balance ON findings(balance) WHERE balance > 0;
CREATE INDEX idx_findings_session ON findings(session_id);
CREATE INDEX idx_findings_found_at ON findings(found_at);
CREATE INDEX idx_findings_score ON findings(score);

-- ─── Oracle Readings ───

CREATE TABLE IF NOT EXISTS readings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    reading_type    VARCHAR(30) NOT NULL,
    input_data      JSONB NOT NULL,
    result          JSONB NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_readings_type ON readings(reading_type);
CREATE INDEX idx_readings_user ON readings(user_id);
CREATE INDEX idx_readings_created ON readings(created_at);

-- ─── Learning System ───

CREATE TABLE IF NOT EXISTS learning_data (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    xp              INTEGER DEFAULT 0,
    level           INTEGER DEFAULT 1,
    model           VARCHAR(50) DEFAULT 'sonnet',
    total_learn_calls   INTEGER DEFAULT 0,
    total_keys_scanned  BIGINT DEFAULT 0,
    total_hits          INTEGER DEFAULT 0,
    auto_adjustments    JSONB,
    last_learn          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS insights (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    learning_id     UUID REFERENCES learning_data(id) ON DELETE CASCADE,
    insight_type    VARCHAR(30) NOT NULL,
    content         TEXT NOT NULL,
    source          VARCHAR(50),
    session_id      UUID REFERENCES sessions(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_insights_user ON insights(user_id);
CREATE INDEX idx_insights_type ON insights(insight_type);

-- ─── Oracle Suggestions ───

CREATE TABLE IF NOT EXISTS oracle_suggestions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    suggestion_type VARCHAR(50) NOT NULL,
    suggestion      JSONB NOT NULL,
    accepted        BOOLEAN,
    session_id      UUID REFERENCES sessions(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Health & Audit Logs ───

CREATE TABLE IF NOT EXISTS health_checks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint_name   VARCHAR(100) NOT NULL,
    endpoint_url    TEXT NOT NULL,
    healthy         BOOLEAN NOT NULL,
    response_ms     INTEGER,
    checked_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_health_endpoint ON health_checks(endpoint_name);
CREATE INDEX idx_health_checked ON health_checks(checked_at);

CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(50),
    resource_id     UUID,
    details         JSONB,
    ip_address      INET,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_created ON audit_log(created_at);

-- ─── Functions ───

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER learning_data_updated_at BEFORE UPDATE ON learning_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
