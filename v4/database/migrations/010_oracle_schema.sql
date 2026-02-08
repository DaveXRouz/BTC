-- Migration 010: Oracle Domain Schema
-- Creates oracle_users, oracle_readings, oracle_reading_users, oracle_audit_log
-- with all indexes, comments, and triggers.
--
-- Usage: psql -U nps -d nps -f 010_oracle_schema.sql
-- Rollback: psql -U nps -d nps -f 010_oracle_schema_rollback.sql

BEGIN;

-- ─── Prerequisites ───

-- Ensure update_updated_at() function exists (safe if already present)
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Ensure schema_migrations table exists
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(20) PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Guard: Prevent duplicate application ───

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '010') THEN
        RAISE EXCEPTION 'Migration 010 already applied. Use rollback first if re-applying.';
    END IF;
END $$;

-- ═══════════════════════════════════════════════════════════════════
-- Tables
-- ═══════════════════════════════════════════════════════════════════

-- ─── Oracle Users ───

CREATE TABLE IF NOT EXISTS oracle_users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    name_persian VARCHAR(200),
    birthday DATE NOT NULL,
    mother_name VARCHAR(200) NOT NULL,
    mother_name_persian VARCHAR(200),
    country VARCHAR(100),
    city VARCHAR(100),
    coordinates POINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT oracle_readings_sign_type_check CHECK (sign_type IN ('time', 'name', 'question')),
    CONSTRAINT oracle_readings_user_check CHECK (
        (is_multi_user = FALSE AND user_id IS NOT NULL) OR
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

-- ═══════════════════════════════════════════════════════════════════
-- Indexes
-- ═══════════════════════════════════════════════════════════════════

-- Oracle Users
CREATE INDEX IF NOT EXISTS idx_oracle_users_created_at ON oracle_users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_users_name ON oracle_users(name);
CREATE INDEX IF NOT EXISTS idx_oracle_users_coordinates ON oracle_users USING GIST(coordinates);

-- Oracle Readings
CREATE INDEX IF NOT EXISTS idx_oracle_readings_user_id ON oracle_readings(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_primary_user_id ON oracle_readings(primary_user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_created_at ON oracle_readings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_sign_type ON oracle_readings(sign_type);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_is_multi_user ON oracle_readings(is_multi_user);

-- JSONB GIN indexes
CREATE INDEX IF NOT EXISTS idx_oracle_readings_result_gin ON oracle_readings USING GIN(reading_result);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_individual_gin ON oracle_readings USING GIN(individual_results);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_compatibility_gin ON oracle_readings USING GIN(compatibility_matrix);

-- Oracle Reading Users
CREATE INDEX IF NOT EXISTS idx_oracle_reading_users_user_id ON oracle_reading_users(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_reading_users_reading_id ON oracle_reading_users(reading_id);

-- Oracle Audit Log
CREATE INDEX IF NOT EXISTS idx_oracle_audit_timestamp ON oracle_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_audit_user ON oracle_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_audit_action ON oracle_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_oracle_audit_success ON oracle_audit_log(success);

-- ═══════════════════════════════════════════════════════════════════
-- Index Comments
-- ═══════════════════════════════════════════════════════════════════

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

-- ═══════════════════════════════════════════════════════════════════
-- Trigger
-- ═══════════════════════════════════════════════════════════════════

CREATE TRIGGER oracle_users_updated_at
    BEFORE UPDATE ON oracle_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ═══════════════════════════════════════════════════════════════════
-- Record migration
-- ═══════════════════════════════════════════════════════════════════

INSERT INTO schema_migrations (version, name)
VALUES ('010', 'Oracle domain schema: users, readings, reading_users, audit_log');

COMMIT;
