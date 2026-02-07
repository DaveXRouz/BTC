-- Performance indexes for Oracle tables

-- Oracle Users
CREATE INDEX IF NOT EXISTS idx_oracle_users_created_at ON oracle_users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_users_name ON oracle_users(name);

-- Oracle Readings
CREATE INDEX IF NOT EXISTS idx_oracle_readings_user_id ON oracle_readings(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_primary_user_id ON oracle_readings(primary_user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_created_at ON oracle_readings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_sign_type ON oracle_readings(sign_type);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_is_multi_user ON oracle_readings(is_multi_user);

-- JSONB GIN indexes for fast JSON queries
CREATE INDEX IF NOT EXISTS idx_oracle_readings_result_gin ON oracle_readings USING GIN(reading_result);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_individual_gin ON oracle_readings USING GIN(individual_results);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_compatibility_gin ON oracle_readings USING GIN(compatibility_matrix);

-- Oracle Reading Users (junction table)
CREATE INDEX IF NOT EXISTS idx_oracle_reading_users_user_id ON oracle_reading_users(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_reading_users_reading_id ON oracle_reading_users(reading_id);
