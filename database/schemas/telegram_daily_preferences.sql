-- Telegram daily auto-insight preferences table.
-- Stores per-user opt-in status, preferred delivery time, and timezone offset.

CREATE TABLE IF NOT EXISTS telegram_daily_preferences (
    id SERIAL PRIMARY KEY,

    -- Link to Telegram user (chat_id is the unique Telegram identifier)
    chat_id BIGINT NOT NULL UNIQUE,

    -- Link to NPS user (nullable if user hasn't linked yet)
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,

    -- Daily delivery settings
    daily_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    delivery_time TIME NOT NULL DEFAULT '08:00:00',
    timezone_offset_minutes INTEGER NOT NULL DEFAULT 0,

    -- Delivery tracking
    last_delivered_date DATE,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telegram_daily_enabled
    ON telegram_daily_preferences(daily_enabled) WHERE daily_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_telegram_daily_chat_id
    ON telegram_daily_preferences(chat_id);
