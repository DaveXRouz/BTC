-- Rollback Migration 012: Framework Alignment
-- Removes all additions from migration 012
-- Idempotent: safe to run if migration was never applied

DO $$
BEGIN
    -- Guard: skip if not applied
    IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '012') THEN
        RAISE NOTICE 'Migration 012 not applied, nothing to rollback.';
        RETURN;
    END IF;

    -- Drop new tables (reverse order of creation)
    DROP TABLE IF EXISTS oracle_daily_readings CASCADE;
    DROP TABLE IF EXISTS oracle_settings CASCADE;

    -- Drop new indexes on oracle_readings
    DROP INDEX IF EXISTS idx_oracle_readings_numerology_system;

    -- Remove columns from oracle_readings (reverse order of addition)
    ALTER TABLE oracle_readings DROP COLUMN IF EXISTS numerology_system;
    ALTER TABLE oracle_readings DROP COLUMN IF EXISTS reading_mode;
    ALTER TABLE oracle_readings DROP COLUMN IF EXISTS framework_version;

    -- Remove columns from oracle_users (reverse order of addition)
    ALTER TABLE oracle_users DROP COLUMN IF EXISTS timezone_minutes;
    ALTER TABLE oracle_users DROP COLUMN IF EXISTS timezone_hours;
    ALTER TABLE oracle_users DROP COLUMN IF EXISTS heart_rate_bpm;
    ALTER TABLE oracle_users DROP COLUMN IF EXISTS gender;

    -- Remove migration record
    DELETE FROM schema_migrations WHERE version = '012';

    RAISE NOTICE 'Migration 012 rolled back successfully.';
END $$;
