-- Migration 011: Widen columns for encrypted data + add soft-delete support
-- Applied by: T6-S1 Security Oracle Layer

BEGIN;

-- Guard: skip if already applied
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '011') THEN
        RAISE NOTICE 'Migration 011 already applied, skipping';
        RETURN;
    END IF;

    -- Widen mother_name columns: VARCHAR(200) is too short for ENC4: ciphertext
    ALTER TABLE oracle_users ALTER COLUMN mother_name TYPE TEXT;
    ALTER TABLE oracle_users ALTER COLUMN mother_name_persian TYPE TEXT;

    -- Add deleted_at for soft-delete (ORM expects it, init.sql didn't include it)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'oracle_users' AND column_name = 'deleted_at'
    ) THEN
        ALTER TABLE oracle_users ADD COLUMN deleted_at TIMESTAMPTZ;
    END IF;

    -- Track migration
    INSERT INTO schema_migrations (version, name)
    VALUES ('011', '011_security_columns');
END $$;

COMMIT;
