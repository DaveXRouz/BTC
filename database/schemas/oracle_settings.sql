-- Oracle Settings — User preferences for Oracle service
-- One settings row per user (UNIQUE on user_id)
-- Language: 'en' (English) or 'fa' (Persian/Farsi)
-- Theme: 'light', 'dark', or 'auto'
-- Numerology system: 'pythagorean', 'chaldean', 'abjad', or 'auto' (auto-detect in Session 8)

CREATE TABLE IF NOT EXISTS oracle_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,

    -- Display preferences
    language VARCHAR(10) NOT NULL DEFAULT 'en' CHECK(language IN ('en', 'fa')),
    theme VARCHAR(20) NOT NULL DEFAULT 'light' CHECK(theme IN ('light', 'dark', 'auto')),

    -- Calculation preferences
    numerology_system VARCHAR(20) NOT NULL DEFAULT 'auto'
        CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad', 'auto')),

    -- Timezone defaults (used when user doesn't specify per-reading)
    default_timezone_hours INTEGER DEFAULT 0
        CHECK(default_timezone_hours >= -12 AND default_timezone_hours <= 14),
    default_timezone_minutes INTEGER DEFAULT 0
        CHECK(default_timezone_minutes >= 0 AND default_timezone_minutes <= 59),

    -- Feature toggles
    daily_reading_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    notifications_enabled BOOLEAN NOT NULL DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One settings row per user
    UNIQUE(user_id)
);

COMMENT ON TABLE oracle_settings IS 'User preferences for Oracle service (language, theme, numerology system)';
COMMENT ON COLUMN oracle_settings.language IS 'UI locale: en (English) or fa (Persian/Farsi with RTL)';
COMMENT ON COLUMN oracle_settings.numerology_system IS 'auto = detect from name script; pythagorean/chaldean for Latin, abjad for Arabic/Persian';
COMMENT ON COLUMN oracle_settings.daily_reading_enabled IS 'Controls whether cron generates daily readings for this user';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_oracle_settings_user_id ON oracle_settings(user_id);

-- Auto-update updated_at (requires update_updated_at() from init.sql)
CREATE TRIGGER oracle_settings_updated_at
    BEFORE UPDATE ON oracle_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
