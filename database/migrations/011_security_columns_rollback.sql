-- Rollback migration 011: Revert column widening

BEGIN;

ALTER TABLE oracle_users ALTER COLUMN mother_name TYPE VARCHAR(200);
ALTER TABLE oracle_users ALTER COLUMN mother_name_persian TYPE VARCHAR(200);
-- Note: deleted_at column is kept — dropping it would lose soft-delete state

DELETE FROM schema_migrations WHERE version = '011';

COMMIT;
