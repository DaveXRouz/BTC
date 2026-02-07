-- NPS V4 — Seed admin user (development only)
-- Password: admin (bcrypt hash, DO NOT use in production)
INSERT INTO users (username, password_hash, role)
VALUES ('admin', '$2b$12$placeholder_hash_replace_me', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Default learning data for admin
INSERT INTO learning_data (user_id, xp, level)
SELECT id, 0, 1 FROM users WHERE username = 'admin'
ON CONFLICT (user_id) DO NOTHING;
