-- Migration 012: Framework Alignment
-- Adds columns needed by numerology_ai_framework to oracle_users and oracle_readings
-- Creates oracle_settings and oracle_daily_readings tables
-- Idempotent: safe to run multiple times (guard clause + IF NOT EXISTS)

DO $$
BEGIN
    -- Guard: skip if already applied
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '012') THEN
        RAISE NOTICE 'Migration 012 already applied, skipping.';
        RETURN;
    END IF;

    -- 1. Add columns to oracle_users (framework input parameters)
    ALTER TABLE oracle_users ADD COLUMN IF NOT EXISTS gender VARCHAR(20)
        CHECK(gender IN ('male', 'female') OR gender IS NULL);
    ALTER TABLE oracle_users ADD COLUMN IF NOT EXISTS heart_rate_bpm INTEGER
        CHECK(heart_rate_bpm IS NULL OR (heart_rate_bpm >= 30 AND heart_rate_bpm <= 220));
    ALTER TABLE oracle_users ADD COLUMN IF NOT EXISTS timezone_hours INTEGER DEFAULT 0
        CHECK(timezone_hours >= -12 AND timezone_hours <= 14);
    ALTER TABLE oracle_users ADD COLUMN IF NOT EXISTS timezone_minutes INTEGER DEFAULT 0
        CHECK(timezone_minutes >= 0 AND timezone_minutes <= 59);

    -- 2. Add columns to oracle_readings (framework output metadata)
    ALTER TABLE oracle_readings ADD COLUMN IF NOT EXISTS framework_version VARCHAR(20);
    ALTER TABLE oracle_readings ADD COLUMN IF NOT EXISTS reading_mode VARCHAR(20) DEFAULT 'full'
        CHECK(reading_mode IN ('full', 'stamp_only'));
    ALTER TABLE oracle_readings ADD COLUMN IF NOT EXISTS numerology_system VARCHAR(20) DEFAULT 'pythagorean'
        CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad'));

    -- 3. Add index for numerology_system filtering
    CREATE INDEX IF NOT EXISTS idx_oracle_readings_numerology_system
        ON oracle_readings(numerology_system);

    -- 4. Create oracle_settings table (user preferences)
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

    -- 5. Create oracle_daily_readings table (one per user per day)
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

    -- 6. Indexes for new tables
    CREATE INDEX IF NOT EXISTS idx_oracle_settings_user_id
        ON oracle_settings(user_id);
    CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_user_date
        ON oracle_daily_readings(user_id, reading_date DESC);
    CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_date
        ON oracle_daily_readings(reading_date DESC);
    CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_result_gin
        ON oracle_daily_readings(reading_result) USING GIN;

    -- 7. Trigger for oracle_settings updated_at
    CREATE TRIGGER oracle_settings_updated_at
        BEFORE UPDATE ON oracle_settings
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();

    -- 8. Record migration
    INSERT INTO schema_migrations (version, name)
    VALUES ('012', 'Framework alignment: user columns, reading columns, settings, daily readings');

    RAISE NOTICE 'Migration 012 applied successfully.';
END $$;
