-- Oracle Reading Users — Many-to-many for multi-user readings

CREATE TABLE IF NOT EXISTS oracle_reading_users (
    reading_id BIGINT NOT NULL REFERENCES oracle_readings(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (reading_id, user_id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE oracle_reading_users IS 'Junction table for multi-user readings (many-to-many)';
COMMENT ON COLUMN oracle_reading_users.is_primary IS 'TRUE if this user is the primary asker';
