DROP TRIGGER IF EXISTS trg_oracle_readings_search ON oracle_readings;
DROP FUNCTION IF EXISTS oracle_readings_search_update();
DROP INDEX IF EXISTS idx_oracle_readings_search;
DROP INDEX IF EXISTS idx_oracle_readings_favorite;
DROP INDEX IF EXISTS idx_oracle_readings_deleted;
DROP INDEX IF EXISTS idx_oracle_readings_stats;
ALTER TABLE oracle_readings
  DROP COLUMN IF EXISTS search_vector,
  DROP COLUMN IF EXISTS deleted_at,
  DROP COLUMN IF EXISTS is_favorite;
