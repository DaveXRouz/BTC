-- Rollback migration 019: drop telegram_links table
-- Session 33

DROP INDEX IF EXISTS idx_telegram_links_chat_id;
DROP INDEX IF EXISTS idx_telegram_links_user_id;
DROP TABLE IF EXISTS telegram_links;
