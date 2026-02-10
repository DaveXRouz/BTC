-- Migration 013: Authentication System Hardening
-- Adds brute-force protection columns, refresh token storage, and moderator role

DO $$
BEGIN
    -- Guard: skip if already applied
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '013') THEN
        RAISE NOTICE 'Migration 013 already applied, skipping.';
        RETURN;
    END IF;

    -- 1. Add brute-force protection columns to users
    ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_attempts INTEGER NOT NULL DEFAULT 0;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;

    -- 2. Add refresh token hash column
    ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token_hash TEXT;

    -- 3. Update role constraint to include 'moderator'
    -- Add explicit CHECK constraint for the 4 valid roles
    ALTER TABLE users ADD CONSTRAINT users_role_check
        CHECK (role IN ('admin', 'moderator', 'user', 'readonly'));

    -- 4. Index for refresh token lookup (used during token refresh)
    CREATE INDEX IF NOT EXISTS idx_users_refresh_token
        ON users(refresh_token_hash) WHERE refresh_token_hash IS NOT NULL;

    -- 5. Index for locked accounts (used during login to check lockout)
    CREATE INDEX IF NOT EXISTS idx_users_locked
        ON users(locked_until) WHERE locked_until IS NOT NULL;

    -- 6. Record migration
    INSERT INTO schema_migrations (version, name)
    VALUES ('013', 'Auth hardening: brute-force protection, refresh tokens, moderator role');

    RAISE NOTICE 'Migration 013 applied successfully.';
END $$;
