-- Migration 021: Performance indexes
-- Date: 2026-02-14
-- Session: 44
-- Description: Add composite and partial indexes for query performance

BEGIN;

-- oracle_users: partial index for soft-delete filter (used in every query)
CREATE INDEX IF NOT EXISTS idx_oracle_users_active
  ON oracle_users(id) WHERE deleted_at IS NULL;

-- oracle_users: search by name (used in list endpoint LIKE query)
CREATE INDEX IF NOT EXISTS idx_oracle_users_name_lower
  ON oracle_users(LOWER(name) varchar_pattern_ops);

-- oracle_users: search by persian name
CREATE INDEX IF NOT EXISTS idx_oracle_users_name_persian_lower
  ON oracle_users(LOWER(name_persian) varchar_pattern_ops)
  WHERE name_persian IS NOT NULL;

-- oracle_users: ordering for paginated list
CREATE INDEX IF NOT EXISTS idx_oracle_users_active_created
  ON oracle_users(created_at DESC) WHERE deleted_at IS NULL;

-- oracle_readings: filter by sign_type + ordering
CREATE INDEX IF NOT EXISTS idx_oracle_readings_sign_type_created
  ON oracle_readings(sign_type, created_at DESC);

-- oracle_readings: user-specific reading lookup
CREATE INDEX IF NOT EXISTS idx_oracle_readings_user_created
  ON oracle_readings(user_id, created_at DESC) WHERE user_id IS NOT NULL;

-- oracle_audit_log: filter by action + ordering
CREATE INDEX IF NOT EXISTS idx_oracle_audit_log_action_created
  ON oracle_audit_log(action, created_at DESC);

-- oracle_audit_log: filter by resource
CREATE INDEX IF NOT EXISTS idx_oracle_audit_log_resource
  ON oracle_audit_log(resource_type, resource_id)
  WHERE resource_id IS NOT NULL;

-- oracle_daily_readings: user + date lookup
CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_user_date
  ON oracle_daily_readings(user_id, reading_date);

COMMIT;
