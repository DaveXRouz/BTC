-- Migration 020: Add telegram_daily_preferences table for daily auto-insight delivery.

CREATE TABLE IF NOT EXISTS telegram_daily_preferences (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL UNIQUE,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    daily_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    delivery_time TIME NOT NULL DEFAULT '08:00:00',
    timezone_offset_minutes INTEGER NOT NULL DEFAULT 0,
    last_delivered_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telegram_daily_enabled
    ON telegram_daily_preferences(daily_enabled) WHERE daily_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_telegram_daily_chat_id
    ON telegram_daily_preferences(chat_id);
