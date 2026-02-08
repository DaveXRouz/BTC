-- Oracle Users — User profiles for Oracle readings
-- Supports English and Persian names, birthdates, mother names, locations

CREATE TABLE IF NOT EXISTS oracle_users (
    id SERIAL PRIMARY KEY,

    -- User identification
    name VARCHAR(200) NOT NULL,
    name_persian VARCHAR(200),

    -- Numerology data
    birthday DATE NOT NULL,
    mother_name VARCHAR(200) NOT NULL,
    mother_name_persian VARCHAR(200),

    -- Location data (optional)
    country VARCHAR(100),
    city VARCHAR(100),
    coordinates POINT,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT oracle_users_birthday_check CHECK (birthday <= CURRENT_DATE),
    CONSTRAINT oracle_users_name_check CHECK (LENGTH(name) >= 2)
);

COMMENT ON TABLE oracle_users IS 'User profiles for Oracle readings with English and Persian name support';
COMMENT ON COLUMN oracle_users.coordinates IS 'PostgreSQL geometric POINT type: (longitude, latitude)';
COMMENT ON COLUMN oracle_users.name_persian IS 'Persian/Farsi name (RTL text, UTF-8)';
COMMENT ON COLUMN oracle_users.mother_name IS 'Mother name for numerology calculations';

COMMENT ON COLUMN oracle_users.deleted_at IS 'Soft-delete timestamp; NULL means active';

-- Partial unique index: prevent duplicate name+birthday among active (non-deleted) users
CREATE UNIQUE INDEX IF NOT EXISTS idx_oracle_users_name_birthday_active
    ON oracle_users(name, birthday) WHERE deleted_at IS NULL;

-- Auto-update updated_at on row modification (requires update_updated_at() from init.sql)
CREATE TRIGGER oracle_users_updated_at
    BEFORE UPDATE ON oracle_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
