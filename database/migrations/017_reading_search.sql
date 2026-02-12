-- Migration 017: Reading search, favorites, and soft delete
-- Depends on: 010_oracle_schema.sql

-- 1. Add new columns
ALTER TABLE oracle_readings
  ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;

-- 2. Auto-populate search_vector trigger
CREATE OR REPLACE FUNCTION oracle_readings_search_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.question, '')), 'A') ||
    setweight(to_tsvector('simple', COALESCE(NEW.question_persian, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.ai_interpretation, '')), 'B') ||
    setweight(to_tsvector('simple', COALESCE(NEW.ai_interpretation_persian, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.sign_value, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_oracle_readings_search
  BEFORE INSERT OR UPDATE ON oracle_readings
  FOR EACH ROW EXECUTE FUNCTION oracle_readings_search_update();

-- 3. Indexes
CREATE INDEX IF NOT EXISTS idx_oracle_readings_search ON oracle_readings USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_favorite ON oracle_readings(is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX IF NOT EXISTS idx_oracle_readings_deleted ON oracle_readings(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_oracle_readings_stats ON oracle_readings(sign_type, created_at) WHERE deleted_at IS NULL;

-- 4. Backfill existing rows
UPDATE oracle_readings SET search_vector =
  setweight(to_tsvector('english', COALESCE(question, '')), 'A') ||
  setweight(to_tsvector('simple', COALESCE(question_persian, '')), 'A') ||
  setweight(to_tsvector('english', COALESCE(ai_interpretation, '')), 'B') ||
  setweight(to_tsvector('simple', COALESCE(ai_interpretation_persian, '')), 'B') ||
  setweight(to_tsvector('english', COALESCE(sign_value, '')), 'C')
WHERE search_vector IS NULL;
