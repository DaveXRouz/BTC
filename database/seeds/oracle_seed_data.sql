-- Oracle Seed Data — Development/testing only
-- 4 users (3 Persian + 1 framework test vector) + 5 readings (3 single + 2 multi-user)
-- + oracle_settings for all users
--
-- Usage: psql -U nps -d nps -f oracle_seed_data.sql
-- Idempotent: safe to re-run (truncates Oracle tables first)

BEGIN;

-- ─── Clean slate (Oracle tables only) ───

TRUNCATE oracle_daily_readings, oracle_settings, oracle_reading_users, oracle_audit_log, oracle_readings, oracle_users
    RESTART IDENTITY CASCADE;

-- ═══════════════════════════════════════════════════════════════════
-- Users
-- ═══════════════════════════════════════════════════════════════════

INSERT INTO oracle_users (id, name, name_persian, birthday, mother_name, mother_name_persian, gender, heart_rate_bpm, timezone_hours, timezone_minutes, country, city, coordinates)
VALUES
    (1, 'Hamzeh', 'حمزه', '1990-03-21', 'Fatemeh', 'فاطمه', 'male', 72, 3, 30, 'Iran', 'Tehran', POINT(51.3890, 35.6892)),
    (2, 'Sara', 'سارا', '1995-07-14', 'Maryam', 'مریم', 'female', 68, 3, 30, 'Iran', 'Isfahan', POINT(51.6776, 32.6546)),
    (3, 'Ali', 'علی', '1988-11-02', 'Zahra', 'زهرا', 'male', 75, 3, 30, 'Iran', 'Shiraz', POINT(52.5836, 29.5918));

-- Framework test vector: "Test User" born 2000-01-01, Life Path = 4 (1+1+2+0+0+0 = 4)
-- Age on 2026-02-11: 26 years | Birth weekday: Saturday (JDN 2451545)
INSERT INTO oracle_users (id, name, name_persian, birthday, mother_name, mother_name_persian, gender, heart_rate_bpm, timezone_hours, timezone_minutes)
VALUES (100, 'Test User', 'کاربر آزمایشی', '2000-01-01', 'Test Mother', 'مادر آزمایشی', NULL, NULL, 0, 0);

-- Reset sequence to next available ID
SELECT setval('oracle_users_id_seq', (SELECT MAX(id) FROM oracle_users));

-- ═══════════════════════════════════════════════════════════════════
-- User Settings (preferences)
-- ═══════════════════════════════════════════════════════════════════

INSERT INTO oracle_settings (user_id, language, theme, numerology_system, default_timezone_hours, default_timezone_minutes)
VALUES
    (1, 'fa', 'dark', 'auto', 3, 30),
    (2, 'fa', 'light', 'auto', 3, 30),
    (3, 'fa', 'light', 'abjad', 3, 30),
    (100, 'en', 'light', 'pythagorean', 0, 0)
ON CONFLICT (user_id) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════
-- Readings — Single-user (one per sign_type)
-- ═══════════════════════════════════════════════════════════════════

-- Reading 1: Time-based reading for Hamzeh
INSERT INTO oracle_readings (id, user_id, is_multi_user, question, question_persian, sign_type, sign_value, reading_result, ai_interpretation, ai_interpretation_persian)
VALUES (1, 1, FALSE,
    'What does today hold for me?',
    'امروز چه چیزی برای من دارد؟',
    'time',
    '14:30',
    '{"fc60_value": 42, "numerology": {"life_path": 7, "expression": 3}, "cosmic_score": 0.85, "elements": {"fire": 0.3, "water": 0.5, "earth": 0.1, "air": 0.1}}',
    'The cosmic alignment at 14:30 reveals strong water energy. Your life path 7 resonates with deep introspection today.',
    'هم‌ترازی کیهانی در ساعت ۱۴:۳۰ انرژی قوی آب را نشان می‌دهد. مسیر زندگی ۷ شما با تعمق عمیق امروز هم‌خوانی دارد.'
);

-- Reading 2: Name-based reading for Sara
INSERT INTO oracle_readings (id, user_id, is_multi_user, question, question_persian, sign_type, sign_value, reading_result, ai_interpretation, ai_interpretation_persian)
VALUES (2, 2, FALSE,
    'What is the energy of my name?',
    'انرژی اسم من چیست؟',
    'name',
    'Sara',
    '{"fc60_value": 18, "numerology": {"name_number": 5, "soul_urge": 1}, "letter_values": {"S": 3, "a": 1, "r": 2, "a2": 1}, "vibration": "high"}',
    'The name Sara carries vibration number 5 — freedom, adventure, and change. Your soul urge 1 drives independence.',
    'نام سارا ارتعاش عدد ۵ را حمل می‌کند — آزادی، ماجراجویی و تغییر. اشتیاق روح ۱ شما استقلال را هدایت می‌کند.'
);

-- Reading 3: Question-based reading for Ali
INSERT INTO oracle_readings (id, user_id, is_multi_user, question, question_persian, sign_type, sign_value, reading_result, ai_interpretation, ai_interpretation_persian)
VALUES (3, 3, FALSE,
    'Should I change my career path?',
    'آیا باید مسیر شغلی‌ام را تغییر دهم؟',
    'question',
    'career_change',
    '{"fc60_value": 33, "numerology": {"question_number": 9, "answer_vibration": 6}, "answer": "yes", "confidence": 0.72, "timing": "within_3_months"}',
    'The Oracle sees transformation energy (33) in your question. Number 9 signals completion of a cycle. Change is favored.',
    'اوراکل انرژی تحول (۳۳) را در سوال شما می‌بیند. عدد ۹ نشان‌دهنده تکمیل یک چرخه است. تغییر مورد حمایت است.'
);

-- ═══════════════════════════════════════════════════════════════════
-- Readings — Multi-user (2 readings with junction table entries)
-- ═══════════════════════════════════════════════════════════════════

-- Reading 4: Compatibility reading between Hamzeh and Sara
INSERT INTO oracle_readings (id, user_id, is_multi_user, primary_user_id, question, question_persian, sign_type, sign_value, reading_result, ai_interpretation, ai_interpretation_persian, individual_results, compatibility_matrix, combined_energy)
VALUES (4, NULL, TRUE, 1,
    'What is our compatibility?',
    'سازگاری ما چقدر است؟',
    'name',
    'Hamzeh+Sara',
    '{"fc60_combined": 60, "harmony_score": 0.78}',
    'Hamzeh and Sara share a deep water-earth connection. The combined FC60 value of 60 indicates a complete cycle of harmony.',
    'حمزه و سارا ارتباط عمیق آب-خاک دارند. مقدار ترکیبی FC60 شصت نشان‌دهنده یک چرخه کامل هماهنگی است.',
    '[{"user_id": 1, "fc60_value": 42, "life_path": 7}, {"user_id": 2, "fc60_value": 18, "life_path": 5}]',
    '{"user_1_2": {"score": 0.78, "strengths": ["communication", "trust"], "challenges": ["routine"]}}',
    '{"total_energy": 60, "dominant_element": "water", "balance": 0.82}'
);

-- Reading 5: Group reading for all three users
INSERT INTO oracle_readings (id, user_id, is_multi_user, primary_user_id, question, question_persian, sign_type, sign_value, reading_result, ai_interpretation, ai_interpretation_persian, individual_results, compatibility_matrix, combined_energy)
VALUES (5, NULL, TRUE, 1,
    'What is the energy of our group?',
    'انرژی گروه ما چیست؟',
    'time',
    '2024-01-15T10:00:00',
    '{"fc60_combined": 93, "group_harmony": 0.65, "dominant_number": 3}',
    'The trio forms a creative triangle. Number 3 dominates — expression, joy, and social connection are your strengths.',
    'این سه‌نفره یک مثلث خلاقانه تشکیل می‌دهند. عدد ۳ غالب است — بیان، شادی و ارتباط اجتماعی نقاط قوت شماست.',
    '[{"user_id": 1, "fc60_value": 42, "role": "visionary"}, {"user_id": 2, "fc60_value": 18, "role": "communicator"}, {"user_id": 3, "fc60_value": 33, "role": "transformer"}]',
    '{"user_1_2": {"score": 0.78}, "user_1_3": {"score": 0.71}, "user_2_3": {"score": 0.69}}',
    '{"total_energy": 93, "dominant_element": "fire", "balance": 0.65, "group_number": 3}'
);

-- Reset sequence to next available ID
SELECT setval('oracle_readings_id_seq', (SELECT MAX(id) FROM oracle_readings));

-- ═══════════════════════════════════════════════════════════════════
-- Junction table entries for multi-user readings
-- ═══════════════════════════════════════════════════════════════════

-- Reading 4: Hamzeh (primary) + Sara
INSERT INTO oracle_reading_users (reading_id, user_id, is_primary) VALUES
    (4, 1, TRUE),
    (4, 2, FALSE);

-- Reading 5: Hamzeh (primary) + Sara + Ali
INSERT INTO oracle_reading_users (reading_id, user_id, is_primary) VALUES
    (5, 1, TRUE),
    (5, 2, FALSE),
    (5, 3, FALSE);

COMMIT;
