-- Oracle Readings — FC60, numerology, and AI interpretations
-- Supports single-user and multi-user (compatibility) readings

CREATE TABLE IF NOT EXISTS oracle_readings (
    id BIGSERIAL PRIMARY KEY,

    -- Single-user vs multi-user
    user_id INTEGER REFERENCES oracle_users(id) ON DELETE CASCADE,
    is_multi_user BOOLEAN NOT NULL DEFAULT FALSE,
    primary_user_id INTEGER REFERENCES oracle_users(id) ON DELETE SET NULL,

    -- Question data
    question TEXT NOT NULL,
    question_persian TEXT,

    -- Sign type and value
    sign_type VARCHAR(20) NOT NULL,
    sign_value VARCHAR(100) NOT NULL,

    -- FC60 calculation results (complex data as JSON)
    reading_result JSONB,

    -- AI interpretation
    ai_interpretation TEXT,
    ai_interpretation_persian TEXT,

    -- Multi-user specific fields
    individual_results JSONB,
    compatibility_matrix JSONB,
    combined_energy JSONB,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT oracle_readings_sign_type_check CHECK (sign_type IN ('time', 'name', 'question')),
    CONSTRAINT oracle_readings_user_check CHECK (
        (is_multi_user = FALSE AND user_id IS NOT NULL) OR
        (is_multi_user = TRUE AND primary_user_id IS NOT NULL)
    )
);

COMMENT ON TABLE oracle_readings IS 'Oracle readings with FC60, numerology, and AI interpretations';
COMMENT ON COLUMN oracle_readings.reading_result IS 'Full FC60 calculation results as JSONB';
COMMENT ON COLUMN oracle_readings.individual_results IS 'Per-user results for multi-user readings (JSONB array)';
COMMENT ON COLUMN oracle_readings.compatibility_matrix IS 'User compatibility scores (JSONB)';
COMMENT ON COLUMN oracle_readings.sign_type IS 'Type of sign: time, name, or question';
