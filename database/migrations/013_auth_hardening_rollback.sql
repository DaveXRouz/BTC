-- Rollback Migration 013: Auth Hardening
DO $$
BEGIN
    -- Guard: skip if not applied
    IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '013') THEN
        RAISE NOTICE 'Migration 013 not applied, nothing to rollback.';
        RETURN;
    END IF;

    -- Drop indexes
    DROP INDEX IF EXISTS idx_users_locked;
    DROP INDEX IF EXISTS idx_users_refresh_token;

    -- Drop role constraint
    ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;

    -- Remove columns (reverse order of addition)
    ALTER TABLE users DROP COLUMN IF EXISTS refresh_token_hash;
    ALTER TABLE users DROP COLUMN IF EXISTS locked_until;
    ALTER TABLE users DROP COLUMN IF EXISTS failed_attempts;

    -- Remove migration record
    DELETE FROM schema_migrations WHERE version = '013';

    RAISE NOTICE 'Migration 013 rolled back successfully.';
END $$;
