-- Rollback for Migration 010: Oracle Domain Schema
-- Drops all Oracle tables in reverse dependency order.
--
-- Usage: psql -U nps -d nps -f 010_oracle_schema_rollback.sql

BEGIN;

-- Drop in reverse dependency order (junction first, then dependents, then base)
DROP TABLE IF EXISTS oracle_reading_users CASCADE;
DROP TABLE IF EXISTS oracle_audit_log CASCADE;
DROP TABLE IF EXISTS oracle_readings CASCADE;
DROP TABLE IF EXISTS oracle_users CASCADE;

-- Remove migration record
DELETE FROM schema_migrations WHERE version = '010';

COMMIT;
