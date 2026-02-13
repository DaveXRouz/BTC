-- Rollback migration 021: Performance indexes
-- Session: 44

BEGIN;

DROP INDEX IF EXISTS idx_oracle_users_active;
DROP INDEX IF EXISTS idx_oracle_users_name_lower;
DROP INDEX IF EXISTS idx_oracle_users_name_persian_lower;
DROP INDEX IF EXISTS idx_oracle_users_active_created;
DROP INDEX IF EXISTS idx_oracle_readings_sign_type_created;
DROP INDEX IF EXISTS idx_oracle_readings_user_created;
DROP INDEX IF EXISTS idx_oracle_audit_log_action_created;
DROP INDEX IF EXISTS idx_oracle_audit_log_resource;
DROP INDEX IF EXISTS idx_oracle_daily_readings_user_date;

COMMIT;
