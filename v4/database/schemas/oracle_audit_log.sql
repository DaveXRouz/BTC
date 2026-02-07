-- Oracle Audit Log — Security event tracking

CREATE TABLE IF NOT EXISTS oracle_audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id INTEGER REFERENCES oracle_users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id BIGINT,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    ip_address VARCHAR(45),
    api_key_hash VARCHAR(64),
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_oracle_audit_timestamp ON oracle_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_audit_user ON oracle_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_audit_action ON oracle_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_oracle_audit_success ON oracle_audit_log(success);

COMMENT ON TABLE oracle_audit_log IS 'Audit trail for Oracle security events';
