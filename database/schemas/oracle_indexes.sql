-- Performance indexes for Oracle tables

-- ─── Oracle Users ───

CREATE INDEX IF NOT EXISTS idx_oracle_users_created_at ON oracle_users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_users_name ON oracle_users(name);
CREATE INDEX IF NOT EXISTS idx_oracle_users_coordinates ON oracle_users USING GIST(coordinates);
CREATE INDEX IF NOT EXISTS idx_oracle_users_active ON oracle_users(id) WHERE deleted_at IS NULL;

-- ─── Oracle Readings ───

CREATE INDEX IF NOT EXISTS idx_oracle_readings_user_id ON oracle_readings(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_primary_user_id ON oracle_readings(primary_user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_created_at ON oracle_readings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_sign_type ON oracle_readings(sign_type);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_is_multi_user ON oracle_readings(is_multi_user);

-- JSONB GIN indexes for fast JSON queries
CREATE INDEX IF NOT EXISTS idx_oracle_readings_result_gin ON oracle_readings USING GIN(reading_result);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_individual_gin ON oracle_readings USING GIN(individual_results);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_compatibility_gin ON oracle_readings USING GIN(compatibility_matrix);

-- ─── Oracle Reading Users (junction table) ───

CREATE INDEX IF NOT EXISTS idx_oracle_reading_users_user_id ON oracle_reading_users(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_reading_users_reading_id ON oracle_reading_users(reading_id);

-- ─── Index Documentation ───

COMMENT ON INDEX idx_oracle_users_created_at IS 'B-tree DESC for recent-first user listing';
COMMENT ON INDEX idx_oracle_users_name IS 'B-tree for name lookup and search';
COMMENT ON INDEX idx_oracle_users_coordinates IS 'GiST for spatial distance queries on native POINT type';
COMMENT ON INDEX idx_oracle_readings_user_id IS 'B-tree FK lookup for single-user readings';
COMMENT ON INDEX idx_oracle_readings_primary_user_id IS 'B-tree FK lookup for multi-user primary asker';
COMMENT ON INDEX idx_oracle_readings_created_at IS 'B-tree DESC for chronological reading history';
COMMENT ON INDEX idx_oracle_readings_sign_type IS 'B-tree for filtering by sign type (time/name/question)';
COMMENT ON INDEX idx_oracle_readings_is_multi_user IS 'B-tree for filtering single vs multi-user readings';
COMMENT ON INDEX idx_oracle_readings_result_gin IS 'GIN for JSONB containment queries on reading results';
COMMENT ON INDEX idx_oracle_readings_individual_gin IS 'GIN for JSONB containment queries on per-user results';
COMMENT ON INDEX idx_oracle_readings_compatibility_gin IS 'GIN for JSONB containment queries on compatibility matrix';
COMMENT ON INDEX idx_oracle_reading_users_user_id IS 'B-tree for finding all readings a user participates in';
COMMENT ON INDEX idx_oracle_reading_users_reading_id IS 'B-tree for finding all users in a reading';
