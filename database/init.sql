-- NPS — PostgreSQL Schema
-- Run: psql -U nps -d nps -f init.sql

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── Schema Migrations Tracking ───

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(20) PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE schema_migrations IS 'Tracks applied database migrations for version control';

-- ─── Functions ───

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

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
    -- legacy migration tracking
    v3_session      VARCHAR(200),
    migrated_from   VARCHAR(20) DEFAULT 'v4'
);

CREATE INDEX idx_findings_chain ON findings(chain);
CREATE INDEX idx_findings_balance ON findings(balance) WHERE balance > 0;
CREATE INDEX idx_findings_session ON findings(session_id);
CREATE INDEX idx_findings_found_at ON findings(found_at);
CREATE INDEX idx_findings_score ON findings(score);

-- ─── Oracle Readings (main schema) ───

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

-- ─── Triggers (main V4 tables) ───

CREATE TRIGGER users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER learning_data_updated_at BEFORE UPDATE ON learning_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ═══════════════════════════════════════════════════════════════════
-- Oracle Domain Tables (dedicated schema for Oracle service)
-- ═══════════════════════════════════════════════════════════════════

-- ─── Oracle Users ───

CREATE TABLE IF NOT EXISTS oracle_users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    name_persian VARCHAR(200),
    birthday DATE NOT NULL,
    mother_name VARCHAR(200) NOT NULL,
    mother_name_persian VARCHAR(200),
    gender VARCHAR(20) CHECK(gender IN ('male', 'female') OR gender IS NULL),
    heart_rate_bpm INTEGER CHECK(heart_rate_bpm IS NULL OR (heart_rate_bpm >= 30 AND heart_rate_bpm <= 220)),
    timezone_hours INTEGER DEFAULT 0 CHECK(timezone_hours >= -12 AND timezone_hours <= 14),
    timezone_minutes INTEGER DEFAULT 0 CHECK(timezone_minutes >= 0 AND timezone_minutes <= 59),
    country VARCHAR(100),
    city VARCHAR(100),
    coordinates POINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT oracle_users_birthday_check CHECK (birthday <= CURRENT_DATE),
    CONSTRAINT oracle_users_name_check CHECK (LENGTH(name) >= 2)
);

COMMENT ON TABLE oracle_users IS 'User profiles for Oracle readings with English and Persian name support';
COMMENT ON COLUMN oracle_users.coordinates IS 'PostgreSQL geometric POINT type: (longitude, latitude)';
COMMENT ON COLUMN oracle_users.name_persian IS 'Persian/Farsi name (RTL text, UTF-8)';
COMMENT ON COLUMN oracle_users.mother_name IS 'Mother name for numerology calculations';

-- ─── Oracle Readings ───

CREATE TABLE IF NOT EXISTS oracle_readings (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES oracle_users(id) ON DELETE CASCADE,
    is_multi_user BOOLEAN NOT NULL DEFAULT FALSE,
    primary_user_id INTEGER REFERENCES oracle_users(id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    question_persian TEXT,
    sign_type VARCHAR(20) NOT NULL,
    sign_value VARCHAR(100) NOT NULL,
    reading_result JSONB,
    ai_interpretation TEXT,
    ai_interpretation_persian TEXT,
    individual_results JSONB,
    compatibility_matrix JSONB,
    combined_energy JSONB,
    framework_version VARCHAR(20) DEFAULT NULL,
    reading_mode VARCHAR(20) DEFAULT 'full' CHECK(reading_mode IN ('full', 'stamp_only')),
    numerology_system VARCHAR(20) DEFAULT 'pythagorean' CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT oracle_readings_sign_type_check CHECK (sign_type IN ('time', 'name', 'question', 'reading', 'multi_user', 'daily')),
    CONSTRAINT oracle_readings_user_check CHECK (
        (is_multi_user = FALSE) OR
        (is_multi_user = TRUE AND primary_user_id IS NOT NULL)
    )
);

COMMENT ON TABLE oracle_readings IS 'Oracle readings with FC60, numerology, and AI interpretations';
COMMENT ON COLUMN oracle_readings.reading_result IS 'Full FC60 calculation results as JSONB';
COMMENT ON COLUMN oracle_readings.individual_results IS 'Per-user results for multi-user readings (JSONB array)';
COMMENT ON COLUMN oracle_readings.compatibility_matrix IS 'User compatibility scores (JSONB)';
COMMENT ON COLUMN oracle_readings.sign_type IS 'Type of sign: time, name, or question';

-- ─── Oracle Reading Users (junction for multi-user) ───

CREATE TABLE IF NOT EXISTS oracle_reading_users (
    reading_id BIGINT NOT NULL REFERENCES oracle_readings(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (reading_id, user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE oracle_reading_users IS 'Junction table for multi-user readings (many-to-many)';
COMMENT ON COLUMN oracle_reading_users.is_primary IS 'TRUE if this user is the primary asker';

-- ─── Oracle Audit Log ───

CREATE TABLE IF NOT EXISTS oracle_audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id INTEGER REFERENCES oracle_users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id BIGINT,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    ip_address VARCHAR(45),
    api_key_hash VARCHAR(64),
    details JSONB
);

COMMENT ON TABLE oracle_audit_log IS 'Audit trail for Oracle security events';

CREATE INDEX IF NOT EXISTS idx_oracle_audit_timestamp ON oracle_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_audit_user ON oracle_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_audit_action ON oracle_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_oracle_audit_success ON oracle_audit_log(success);

-- ─── Oracle Indexes ───

CREATE INDEX IF NOT EXISTS idx_oracle_users_created_at ON oracle_users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_users_name ON oracle_users(name);
CREATE INDEX IF NOT EXISTS idx_oracle_users_coordinates ON oracle_users USING GIST(coordinates);
CREATE INDEX IF NOT EXISTS idx_oracle_users_active ON oracle_users(deleted_at) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_oracle_readings_user_id ON oracle_readings(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_primary_user_id ON oracle_readings(primary_user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_created_at ON oracle_readings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_sign_type ON oracle_readings(sign_type);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_is_multi_user ON oracle_readings(is_multi_user);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_result_gin ON oracle_readings USING GIN(reading_result);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_individual_gin ON oracle_readings USING GIN(individual_results);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_compatibility_gin ON oracle_readings USING GIN(compatibility_matrix);

CREATE INDEX IF NOT EXISTS idx_oracle_reading_users_user_id ON oracle_reading_users(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_reading_users_reading_id ON oracle_reading_users(reading_id);

-- ─── Oracle Index Comments ───

COMMENT ON INDEX idx_oracle_users_created_at IS 'B-tree DESC for recent-first user listing';
COMMENT ON INDEX idx_oracle_users_name IS 'B-tree for name lookup and search';
COMMENT ON INDEX idx_oracle_users_coordinates IS 'GiST for spatial distance queries on native POINT type';
COMMENT ON INDEX idx_oracle_readings_user_id IS 'B-tree FK lookup for single-user readings';
COMMENT ON INDEX idx_oracle_readings_primary_user_id IS 'B-tree FK lookup for multi-user primary asker';
COMMENT ON INDEX idx_oracle_readings_created_at IS 'B-tree DESC for chronological reading history';
COMMENT ON INDEX idx_oracle_readings_sign_type IS 'B-tree for filtering by sign type (time/name/question)';
COMMENT ON INDEX idx_oracle_readings_is_multi_user IS 'B-tree for filtering single vs multi-user readings';
COMMENT ON INDEX idx_oracle_readings_result_gin IS 'GIN for JSONB containment queries on reading results';
COMMENT ON INDEX idx_oracle_readings_individual_gin IS 'GIN for JSONB containment queries on per-user results';
COMMENT ON INDEX idx_oracle_readings_compatibility_gin IS 'GIN for JSONB containment queries on compatibility matrix';
COMMENT ON INDEX idx_oracle_reading_users_user_id IS 'B-tree for finding all readings a user participates in';
COMMENT ON INDEX idx_oracle_reading_users_reading_id IS 'B-tree for finding all users in a reading';

-- ─── Oracle Trigger ───

CREATE TRIGGER oracle_users_updated_at
    BEFORE UPDATE ON oracle_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ═══════════════════════════════════════════════════════════════════
-- Oracle Settings & Daily Readings (Session 1: Framework Alignment)
-- ═══════════════════════════════════════════════════════════════════

-- ─── Oracle Settings (user preferences) ───

CREATE TABLE IF NOT EXISTS oracle_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL DEFAULT 'en' CHECK(language IN ('en', 'fa')),
    theme VARCHAR(20) NOT NULL DEFAULT 'light' CHECK(theme IN ('light', 'dark', 'auto')),
    numerology_system VARCHAR(20) NOT NULL DEFAULT 'auto'
        CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad', 'auto')),
    default_timezone_hours INTEGER DEFAULT 0
        CHECK(default_timezone_hours >= -12 AND default_timezone_hours <= 14),
    default_timezone_minutes INTEGER DEFAULT 0
        CHECK(default_timezone_minutes >= 0 AND default_timezone_minutes <= 59),
    daily_reading_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    notifications_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);

COMMENT ON TABLE oracle_settings IS 'User preferences for Oracle service (language, theme, numerology system)';

CREATE INDEX IF NOT EXISTS idx_oracle_settings_user_id ON oracle_settings(user_id);

CREATE TRIGGER oracle_settings_updated_at
    BEFORE UPDATE ON oracle_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─── Oracle Daily Readings (auto-generated, one per user per day) ───

CREATE TABLE IF NOT EXISTS oracle_daily_readings (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
    reading_date DATE NOT NULL,
    reading_result JSONB NOT NULL,
    daily_insights JSONB,
    numerology_system VARCHAR(20) NOT NULL DEFAULT 'pythagorean'
        CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad')),
    confidence_score DOUBLE PRECISION DEFAULT 0,
    framework_version VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, reading_date)
);

COMMENT ON TABLE oracle_daily_readings IS 'Auto-generated daily readings, one per user per day';

CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_user_date
    ON oracle_daily_readings(user_id, reading_date DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_date
    ON oracle_daily_readings(reading_date DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_result_gin
    ON oracle_daily_readings(reading_result) USING GIN;

-- ─── Oracle Readings: numerology_system index ───

CREATE INDEX IF NOT EXISTS idx_oracle_readings_numerology_system
    ON oracle_readings(numerology_system);
