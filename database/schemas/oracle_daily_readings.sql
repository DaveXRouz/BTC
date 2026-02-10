-- Oracle Daily Readings — Auto-generated one reading per user per day
-- UNIQUE constraint on (user_id, reading_date) ensures exactly one daily reading
-- reading_result stores full framework output JSONB
-- daily_insights stores suggested_activities, energy_forecast, lucky_hours (Session 7)

CREATE TABLE IF NOT EXISTS oracle_daily_readings (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
    reading_date DATE NOT NULL,

    -- Framework output
    reading_result JSONB NOT NULL,
    daily_insights JSONB,

    -- Calculation metadata
    numerology_system VARCHAR(20) NOT NULL DEFAULT 'pythagorean'
        CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad')),
    confidence_score DOUBLE PRECISION DEFAULT 0,
    framework_version VARCHAR(20),

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One daily reading per user per day
    UNIQUE(user_id, reading_date)
);

COMMENT ON TABLE oracle_daily_readings IS 'Auto-generated daily readings, one per user per day';
COMMENT ON COLUMN oracle_daily_readings.reading_result IS 'Full framework output JSONB (numerology, fc60_stamp, moon, etc.)';
COMMENT ON COLUMN oracle_daily_readings.daily_insights IS 'Suggested activities, energy forecast, lucky hours (populated in Session 7)';
COMMENT ON COLUMN oracle_daily_readings.confidence_score IS 'Denormalized from reading_result for quick sorting/filtering';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_user_date
    ON oracle_daily_readings(user_id, reading_date DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_date
    ON oracle_daily_readings(reading_date DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_result_gin
    ON oracle_daily_readings(reading_result) USING GIN;
