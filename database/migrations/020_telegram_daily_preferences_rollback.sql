-- Rollback migration 020: Remove telegram_daily_preferences table.

DROP TABLE IF EXISTS telegram_daily_preferences CASCADE;
