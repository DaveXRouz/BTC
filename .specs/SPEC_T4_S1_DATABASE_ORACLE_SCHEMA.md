# SPEC: Database Oracle Schema - T4-S1
**Estimated Duration:** 2-3 hours
**Layer:** Layer 4 (Database)
**Terminal:** Terminal 4
**Dependencies:** None (foundation layer)

## TL;DR
- Creating complete PostgreSQL schema for Oracle system rebuild
- 3 tables: oracle_users, oracle_readings, oracle_reading_users (junction)
- Supports single-user and multi-user readings with Persian language (RTL)
- Performance optimized with indexes + optional partitioning
- Includes migrations (versioned, reversible), seed data, backup/restore scripts
- Foundation for Terminals 1, 2, 3, 6 to build upon

## OBJECTIVE
Create production-ready PostgreSQL database schema for NPS V4 Oracle system supporting user profiles, readings (single and multi-user), FC60 calculations, numerology analysis, and AI interpretations in both English and Persian languages.

## CONTEXT
**Current State:** No Oracle database schema exists in NPS V4

**What's Changing:** Creating complete database foundation for Oracle rebuild

**Why:** Oracle system needs centralized storage for:
- User profiles (English + Persian names, birthdates, locations)
- Readings (questions, FC60 signs, numerology, AI interpretations)
- Multi-user compatibility readings (joint readings for 2+ people)
- Historical reading data for AI learning

**Architecture Alignment:** 
- Layer 4 (Database) creates foundation
- Layer 2 (API) will query this schema
- Layer 3 (Backend Oracle service) will populate this schema
- Layer 1 (Frontend) will display this data

## PREREQUISITES
- [ ] PostgreSQL 15+ installed and running
- [ ] Database created: nps_db
- [ ] User created: nps_user with appropriate permissions
- [ ] PostGIS extension available (for geographic POINT type)
- [ ] psql command-line tool accessible

**Verification:**
```bash
psql --version
# Expected: psql (PostgreSQL) 15.x or higher

psql -h localhost -U nps_user -d nps_db -c "SELECT version();"
# Expected: PostgreSQL 15.x on [platform]

psql -h localhost -U nps_user -d nps_db -c "CREATE EXTENSION IF NOT EXISTS postgis; SELECT PostGIS_version();"
# Expected: PostGIS version string
```

## TOOLS TO USE
- **Extended Thinking:** For schema design decisions (indexes, partitioning, JSONB structure)
- **View:** Read /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md (Layer 4 section) before starting
- **View:** Read /mnt/project/VERIFICATION_CHECKLISTS.md (Database checklist) for quality gates
- **bash_tool:** For testing SQL scripts, running migrations, verifying performance

## REQUIREMENTS

### Functional Requirements
1. Store user profiles with English and Persian names (Unicode UTF-8)
2. Store user birthdates (DATE type) and mother names (for numerology)
3. Store geographic location data (country, city, coordinates)
4. Support single-user readings (1 user asks question)
5. Support multi-user readings (2+ users, joint compatibility readings)
6. Store reading questions in English and Persian
7. Store FC60 sign results (time/name/question based)
8. Store complex FC60 calculation results as JSONB
9. Store AI interpretations in English and Persian
10. Link readings to users (one-to-many for single, many-to-many for multi)

### Non-Functional Requirements
1. **Performance:** Queries under 1 second for 1M+ rows
2. **Scalability:** Support millions of readings over time
3. **Data Integrity:** Foreign key constraints enforced, no orphaned records
4. **Backup:** Daily backups possible within 5 minutes
5. **Query Efficiency:** All common queries use indexes
6. **Text Encoding:** Full Unicode UTF-8 support for Persian RTL text
7. **Maintainability:** Clear table/column names, documented schema

## IMPLEMENTATION PLAN

### Phase 1: Core Tables Creation (60 minutes)

**Tasks:**
1. Create oracle_users table with all fields
2. Create oracle_readings table with all fields  
3. Create oracle_reading_users junction table
4. Add primary keys and foreign keys
5. Add check constraints (data validation)
6. Test table creation on clean database

**Files to Create:**
- `database/schemas/oracle_users.sql`
- `database/schemas/oracle_readings.sql`
- `database/schemas/oracle_reading_users.sql`

**Oracle Users Table Schema:**
```sql
-- database/schemas/oracle_users.sql
-- User profiles for Oracle readings
-- Supports English and Persian names, birthdates, mother names, locations

CREATE TABLE IF NOT EXISTS oracle_users (
    id SERIAL PRIMARY KEY,
    
    -- User identification (English)
    name VARCHAR(200) NOT NULL,
    name_persian VARCHAR(200),
    
    -- Numerology data
    birthday DATE NOT NULL,
    mother_name VARCHAR(200) NOT NULL,
    mother_name_persian VARCHAR(200),
    
    -- Location data (optional)
    country VARCHAR(100),
    city VARCHAR(100),
    coordinates POINT,  -- PostGIS POINT type (longitude, latitude)
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT oracle_users_birthday_check CHECK (birthday <= CURRENT_DATE),
    CONSTRAINT oracle_users_name_check CHECK (LENGTH(name) >= 2)
);

-- Comments for documentation
COMMENT ON TABLE oracle_users IS 'User profiles for Oracle readings with English and Persian name support';
COMMENT ON COLUMN oracle_users.coordinates IS 'PostGIS POINT type: POINT(longitude, latitude)';
COMMENT ON COLUMN oracle_users.name_persian IS 'Persian/Farsi name (RTL text, UTF-8)';
COMMENT ON COLUMN oracle_users.mother_name IS 'Mother name for numerology calculations';
```

**Oracle Readings Table Schema:**
```sql
-- database/schemas/oracle_readings.sql
-- Oracle readings with FC60, numerology, and AI interpretations
-- Supports single-user and multi-user (compatibility) readings

CREATE TABLE IF NOT EXISTS oracle_readings (
    id BIGSERIAL PRIMARY KEY,
    
    -- Single-user vs multi-user
    user_id INTEGER REFERENCES oracle_users(id) ON DELETE CASCADE,  -- For single-user readings
    is_multi_user BOOLEAN NOT NULL DEFAULT FALSE,
    primary_user_id INTEGER REFERENCES oracle_users(id) ON DELETE SET NULL,  -- Primary asker in multi-user
    
    -- Question data
    question TEXT NOT NULL,
    question_persian TEXT,
    
    -- Sign type and value
    sign_type VARCHAR(20) NOT NULL,  -- 'time', 'name', 'question'
    sign_value VARCHAR(100) NOT NULL,  -- '11:11', 'John Doe', or question text
    
    -- FC60 calculation results (complex data as JSON)
    reading_result JSONB,  -- Full FC60 calculation: {fc60: {...}, numerology: {...}, cosmic: {...}}
    
    -- AI interpretation
    ai_interpretation TEXT,
    ai_interpretation_persian TEXT,
    
    -- Multi-user specific fields
    individual_results JSONB,  -- Array of per-user results for multi-user readings
    compatibility_matrix JSONB,  -- Compatibility scores between users
    combined_energy JSONB,  -- Joint energy calculations
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT oracle_readings_sign_type_check CHECK (sign_type IN ('time', 'name', 'question')),
    CONSTRAINT oracle_readings_user_check CHECK (
        (is_multi_user = FALSE AND user_id IS NOT NULL) OR
        (is_multi_user = TRUE AND primary_user_id IS NOT NULL)
    )
);

-- Comments for documentation
COMMENT ON TABLE oracle_readings IS 'Oracle readings with FC60, numerology, and AI interpretations';
COMMENT ON COLUMN oracle_readings.reading_result IS 'Full FC60 calculation results as JSONB';
COMMENT ON COLUMN oracle_readings.individual_results IS 'Per-user results for multi-user readings (JSONB array)';
COMMENT ON COLUMN oracle_readings.compatibility_matrix IS 'User compatibility scores (JSONB)';
COMMENT ON COLUMN oracle_readings.sign_type IS 'Type of sign: time, name, or question';
```

**Oracle Reading Users Junction Table Schema:**
```sql
-- database/schemas/oracle_reading_users.sql
-- Many-to-many relationship between readings and users
-- Supports multi-user compatibility readings

CREATE TABLE IF NOT EXISTS oracle_reading_users (
    reading_id BIGINT NOT NULL REFERENCES oracle_readings(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,  -- Is this user the primary asker?
    
    -- Primary key (composite)
    PRIMARY KEY (reading_id, user_id),
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Comments for documentation
COMMENT ON TABLE oracle_reading_users IS 'Junction table for multi-user readings (many-to-many)';
COMMENT ON COLUMN oracle_reading_users.is_primary IS 'TRUE if this user is the primary asker';
```

**Acceptance Criteria:**
- [ ] All 3 tables created without errors
- [ ] Foreign key constraints work (cascade deletes)
- [ ] Check constraints prevent invalid data
- [ ] Can insert sample data into all tables
- [ ] Single-user reading can be inserted
- [ ] Multi-user reading can be inserted with junction records

**Verification:**
```bash
cd database

# Create tables
psql -h localhost -U nps_user -d nps_db -f schemas/oracle_users.sql
psql -h localhost -U nps_user -d nps_db -f schemas/oracle_readings.sql
psql -h localhost -U nps_user -d nps_db -f schemas/oracle_reading_users.sql

# Verify tables exist
psql -h localhost -U nps_user -d nps_db -c "\dt oracle_*"
# Expected: oracle_users, oracle_readings, oracle_reading_users

# Test single-user reading insert
psql -h localhost -U nps_user -d nps_db << EOF
INSERT INTO oracle_users (name, birthday, mother_name) 
VALUES ('Test User', '1990-01-01', 'Test Mother');

INSERT INTO oracle_readings (user_id, question, sign_type, sign_value)
VALUES (1, 'Test question?', 'time', '11:11');
EOF
# Expected: INSERT 0 1 (twice)

# Test multi-user reading insert
psql -h localhost -U nps_user -d nps_db << EOF
INSERT INTO oracle_users (name, birthday, mother_name) 
VALUES ('User 2', '1985-05-15', 'Mother 2');

INSERT INTO oracle_readings (is_multi_user, primary_user_id, question, sign_type, sign_value)
VALUES (TRUE, 1, 'Should we collaborate?', 'question', 'Should we collaborate?')
RETURNING id;

INSERT INTO oracle_reading_users (reading_id, user_id, is_primary)
VALUES 
  (2, 1, TRUE),
  (2, 2, FALSE);
EOF
# Expected: Successfully inserts multi-user reading

# Test foreign key cascade
psql -h localhost -U nps_user -d nps_db -c "DELETE FROM oracle_users WHERE id = 2;"
psql -h localhost -U nps_user -d nps_db -c "SELECT COUNT(*) FROM oracle_reading_users WHERE user_id = 2;"
# Expected: 0 (cascade delete worked)
```

**Checkpoint:**
- [ ] All tables exist and functional
- [ ] Foreign keys enforce referential integrity
- [ ] Cascade deletes work as expected
- [ ] Check constraints prevent invalid data
- [ ] Can insert both single-user and multi-user readings

**🚨 STOP if checkpoint fails - fix before Phase 2**

---

### Phase 2: Indexes & Performance Optimization (30 minutes)

**Tasks:**
1. Create indexes on foreign keys (automatic for PK, manual for FK)
2. Create indexes on commonly queried fields (user_id, created_at)
3. Create GIN indexes on JSONB fields (for fast JSON queries)
4. Test index usage with EXPLAIN ANALYZE
5. Document index rationale in comments

**Files to Create:**
- `database/schemas/oracle_indexes.sql`

**Index Strategy:**
```sql
-- database/schemas/oracle_indexes.sql
-- Performance indexes for Oracle tables
-- All indexes support common query patterns

-- Oracle Users Indexes
CREATE INDEX IF NOT EXISTS idx_oracle_users_created_at ON oracle_users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_users_name ON oracle_users(name);
CREATE INDEX IF NOT EXISTS idx_oracle_users_coordinates ON oracle_users USING GIST(coordinates);  -- Spatial index

-- Oracle Readings Indexes
CREATE INDEX IF NOT EXISTS idx_oracle_readings_user_id ON oracle_readings(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_primary_user_id ON oracle_readings(primary_user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_created_at ON oracle_readings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_sign_type ON oracle_readings(sign_type);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_is_multi_user ON oracle_readings(is_multi_user);

-- JSONB GIN indexes for fast JSON queries
CREATE INDEX IF NOT EXISTS idx_oracle_readings_result_gin ON oracle_readings USING GIN(reading_result);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_individual_gin ON oracle_readings USING GIN(individual_results);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_compatibility_gin ON oracle_readings USING GIN(compatibility_matrix);

-- Oracle Reading Users Indexes (junction table)
CREATE INDEX IF NOT EXISTS idx_oracle_reading_users_user_id ON oracle_reading_users(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_reading_users_reading_id ON oracle_reading_users(reading_id);

-- Comments for documentation
COMMENT ON INDEX idx_oracle_readings_result_gin IS 'GIN index for fast JSONB queries on reading_result';
COMMENT ON INDEX idx_oracle_users_coordinates IS 'GIST spatial index for geographic queries';
```

**Acceptance Criteria:**
- [ ] All indexes created without errors
- [ ] EXPLAIN ANALYZE shows index usage for common queries
- [ ] Query performance meets targets (<1s for 1M rows)
- [ ] GIN indexes speed up JSONB queries
- [ ] GIST index speeds up geographic queries

**Verification:**
```bash
cd database

# Create indexes
psql -h localhost -U nps_user -d nps_db -f schemas/oracle_indexes.sql

# Verify indexes exist
psql -h localhost -U nps_user -d nps_db -c "\di oracle_*"
# Expected: List of all indexes

# Test index usage on user_id query
psql -h localhost -U nps_user -d nps_db -c "EXPLAIN ANALYZE SELECT * FROM oracle_readings WHERE user_id = 1;"
# Expected: Index Scan using idx_oracle_readings_user_id

# Test index usage on created_at query
psql -h localhost -U nps_user -d nps_db -c "EXPLAIN ANALYZE SELECT * FROM oracle_readings WHERE created_at > NOW() - INTERVAL '7 days';"
# Expected: Index Scan using idx_oracle_readings_created_at

# Test JSONB GIN index usage
psql -h localhost -U nps_user -d nps_db << EOF
UPDATE oracle_readings 
SET reading_result = '{"fc60": "Water Ox", "score": 85}'::jsonb 
WHERE id = 1;

EXPLAIN ANALYZE SELECT * FROM oracle_readings WHERE reading_result @> '{"fc60": "Water Ox"}'::jsonb;
EOF
# Expected: Bitmap Index Scan using idx_oracle_readings_result_gin
```

**Checkpoint:**
- [ ] All indexes created successfully
- [ ] Indexes are being used by queries (verified with EXPLAIN)
- [ ] JSONB queries use GIN indexes
- [ ] Geographic queries use GIST index
- [ ] Performance meets targets

**🚨 STOP if checkpoint fails - investigate why indexes not used**

---

### Phase 3: Migrations (Versioned Schema Management) (20 minutes)

**Tasks:**
1. Create combined migration script (010_oracle_schema.sql)
2. Create rollback script (010_oracle_schema_rollback.sql)
3. Test migration on clean database
4. Test rollback restores to pre-migration state
5. Make migration idempotent (can run multiple times safely)
6. Version migration properly

**Files to Create:**
- `database/migrations/010_oracle_schema.sql`
- `database/migrations/010_oracle_schema_rollback.sql`

**Migration Script (Up):**
```sql
-- database/migrations/010_oracle_schema.sql
-- Migration: Oracle System Schema
-- Version: 010
-- Description: Create oracle_users, oracle_readings, oracle_reading_users tables with indexes
-- Author: NPS V4 Database Team
-- Date: 2026-02-08

BEGIN;

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create tables (idempotent with IF NOT EXISTS)
\i ../schemas/oracle_users.sql
\i ../schemas/oracle_readings.sql
\i ../schemas/oracle_reading_users.sql

-- Create indexes
\i ../schemas/oracle_indexes.sql

-- Migration metadata
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO schema_migrations (version, description)
VALUES (10, 'Oracle System Schema - users, readings, indexes')
ON CONFLICT (version) DO NOTHING;

COMMIT;
```

**Rollback Script (Down):**
```sql
-- database/migrations/010_oracle_schema_rollback.sql
-- Rollback: Oracle System Schema
-- Version: 010
-- Reverts: 010_oracle_schema.sql

BEGIN;

-- Drop indexes first
DROP INDEX IF EXISTS idx_oracle_users_created_at;
DROP INDEX IF EXISTS idx_oracle_users_name;
DROP INDEX IF EXISTS idx_oracle_users_coordinates;
DROP INDEX IF EXISTS idx_oracle_readings_user_id;
DROP INDEX IF EXISTS idx_oracle_readings_primary_user_id;
DROP INDEX IF EXISTS idx_oracle_readings_created_at;
DROP INDEX IF EXISTS idx_oracle_readings_sign_type;
DROP INDEX IF EXISTS idx_oracle_readings_is_multi_user;
DROP INDEX IF EXISTS idx_oracle_readings_result_gin;
DROP INDEX IF EXISTS idx_oracle_readings_individual_gin;
DROP INDEX IF EXISTS idx_oracle_readings_compatibility_gin;
DROP INDEX IF EXISTS idx_oracle_reading_users_user_id;
DROP INDEX IF EXISTS idx_oracle_reading_users_reading_id;

-- Drop tables (CASCADE to handle foreign keys)
DROP TABLE IF EXISTS oracle_reading_users CASCADE;
DROP TABLE IF EXISTS oracle_readings CASCADE;
DROP TABLE IF EXISTS oracle_users CASCADE;

-- Remove migration metadata
DELETE FROM schema_migrations WHERE version = 10;

COMMIT;
```

**Acceptance Criteria:**
- [ ] Migration runs without errors on clean database
- [ ] Migration is idempotent (can run multiple times)
- [ ] Rollback completely removes all Oracle tables and indexes
- [ ] Rollback restores to pre-migration state
- [ ] Migration metadata tracked in schema_migrations table
- [ ] Uses PostgreSQL transactions (BEGIN/COMMIT)

**Verification:**
```bash
cd database

# Test migration on clean database
psql -h localhost -U nps_user -d nps_db -f migrations/010_oracle_schema.sql
# Expected: All commands execute successfully

# Verify tables created
psql -h localhost -U nps_user -d nps_db -c "\dt oracle_*"
# Expected: 3 tables listed

# Verify migration tracked
psql -h localhost -U nps_user -d nps_db -c "SELECT * FROM schema_migrations WHERE version = 10;"
# Expected: 1 row with version 10

# Test idempotency (run again)
psql -h localhost -U nps_user -d nps_db -f migrations/010_oracle_schema.sql
# Expected: No errors (IF NOT EXISTS prevents duplicates)

# Test rollback
psql -h localhost -U nps_user -d nps_db -f migrations/010_oracle_schema_rollback.sql
# Expected: All commands execute successfully

# Verify tables removed
psql -h localhost -U nps_user -d nps_db -c "\dt oracle_*"
# Expected: No tables listed

# Verify migration metadata removed
psql -h localhost -U nps_user -d nps_db -c "SELECT * FROM schema_migrations WHERE version = 10;"
# Expected: 0 rows
```

**Checkpoint:**
- [ ] Migration runs cleanly
- [ ] Rollback works correctly
- [ ] Idempotency verified
- [ ] Migration versioning working
- [ ] No data loss on rollback

**🚨 STOP if checkpoint fails - fix migration/rollback logic**

---

### Phase 4: Seed Data (Sample Users & Readings) (30 minutes)

**Tasks:**
1. Create seed data script with 3 sample users
2. Create 5 sample readings (mix of single and multi-user)
3. Demonstrate all features (Persian text, JSONB, multi-user)
4. Ensure data loads correctly
5. Test queries on seed data

**Files to Create:**
- `database/seed/oracle_seed_data.sql`

**Seed Data Script:**
```sql
-- database/seed/oracle_seed_data.sql
-- Sample data for Oracle system testing
-- 3 users (English, Persian, Mixed) + 5 readings (single + multi-user)

BEGIN;

-- Clean existing data (for idempotency)
TRUNCATE oracle_reading_users, oracle_readings, oracle_users RESTART IDENTITY CASCADE;

-- Sample Users
INSERT INTO oracle_users (name, name_persian, birthday, mother_name, mother_name_persian, country, city, coordinates) VALUES
-- User 1: Full English
('Alice Johnson', NULL, '1985-03-15', 'Mary Johnson', NULL, 'United States', 'New York', POINT(-74.006, 40.7128)),

-- User 2: Full Persian
('علی رضایی', 'Ali Rezaei', '1990-05-20', 'مریم احمدی', 'Maryam Ahmadi', 'Iran', 'Tehran', POINT(51.4215, 35.6944)),

-- User 3: Mixed (English + Persian)
('Sara Khani', 'سارا خانی', '1992-08-10', 'Fatima', 'فاطمه', 'Canada', 'Toronto', POINT(-79.3832, 43.6532));

-- Sample Readings

-- Reading 1: Single-user, time sign, full FC60 result
INSERT INTO oracle_readings (
    user_id, 
    is_multi_user, 
    question, 
    question_persian,
    sign_type, 
    sign_value,
    reading_result,
    ai_interpretation,
    ai_interpretation_persian
) VALUES (
    1,
    FALSE,
    'Should I change jobs?',
    NULL,
    'time',
    '11:11',
    '{
        "fc60": {
            "sign": "Water Ox",
            "element": "Water",
            "animal": "Ox",
            "energy": "Yin"
        },
        "numerology": {
            "life_path": 7,
            "expression": 11,
            "soul_urge": 3
        },
        "cosmic_alignment": 87.5
    }'::jsonb,
    'The Water Ox energy suggests stability and patience. This is a time for careful consideration rather than impulsive action. Your life path number 7 indicates a need for introspection before major decisions.',
    NULL
);

-- Reading 2: Single-user, Persian question, name sign
INSERT INTO oracle_readings (
    user_id,
    is_multi_user,
    question,
    question_persian,
    sign_type,
    sign_value,
    reading_result,
    ai_interpretation,
    ai_interpretation_persian
) VALUES (
    2,
    FALSE,
    'Will my business succeed?',
    'آیا کسب و کار من موفق خواهد شد؟',
    'name',
    'علی رضایی',
    '{
        "fc60": {
            "sign": "Fire Horse",
            "element": "Fire",
            "animal": "Horse",
            "energy": "Yang"
        },
        "numerology": {
            "life_path": 5,
            "expression": 8,
            "soul_urge": 1
        },
        "cosmic_alignment": 92.3
    }'::jsonb,
    'Fire Horse brings dynamic energy and forward momentum. Your expression number 8 indicates strong business acumen.',
    'اسب آتش انرژی پویا و حرکت رو به جلو می‌آورد. شماره بیان شما ۸ نشان‌دهنده هوش تجاری قوی است.'
);

-- Reading 3: Single-user, question sign
INSERT INTO oracle_readings (
    user_id,
    is_multi_user,
    question,
    question_persian,
    sign_type,
    sign_value,
    reading_result
) VALUES (
    3,
    FALSE,
    'Should I move to a new city?',
    'آیا باید به شهر جدیدی نقل مکان کنم؟',
    'question',
    'Should I move to a new city?',
    '{
        "fc60": {
            "sign": "Wood Dragon",
            "element": "Wood",
            "animal": "Dragon",
            "energy": "Yang"
        },
        "numerology": {
            "life_path": 9,
            "expression": 6,
            "soul_urge": 2
        },
        "cosmic_alignment": 78.9
    }'::jsonb
);

-- Reading 4: Multi-user (compatibility reading between users 1 and 2)
INSERT INTO oracle_readings (
    is_multi_user,
    primary_user_id,
    question,
    question_persian,
    sign_type,
    sign_value,
    reading_result,
    individual_results,
    compatibility_matrix,
    combined_energy,
    ai_interpretation
) VALUES (
    TRUE,
    1,
    'Should we start a business together?',
    'آیا باید با هم کسب و کار راه‌اندازی کنیم؟',
    'time',
    '04:44',
    '{
        "fc60": {
            "sign": "Earth Rabbit",
            "element": "Earth",
            "animal": "Rabbit",
            "energy": "Yin"
        },
        "cosmic_alignment": 85.7
    }'::jsonb,
    '[
        {
            "user_id": 1,
            "name": "Alice Johnson",
            "individual_sign": "Water Ox",
            "strengths": ["stability", "patience", "reliability"]
        },
        {
            "user_id": 2,
            "name": "Ali Rezaei",
            "individual_sign": "Fire Horse",
            "strengths": ["dynamism", "leadership", "innovation"]
        }
    ]'::jsonb,
    '{
        "alice_ali": {
            "compatibility_score": 82,
            "strengths": ["complementary_elements", "balanced_energies"],
            "challenges": ["pace_differences", "communication_styles"]
        }
    }'::jsonb,
    '{
        "combined_sign": "Earth Rabbit",
        "synergy_level": 85.7,
        "recommended_roles": {
            "alice": "operations_finance",
            "ali": "strategy_growth"
        }
    }'::jsonb,
    'Water Ox and Fire Horse create a powerful balance. Alice''s stability complements Ali''s dynamism. Together you form Earth Rabbit energy - grounded yet creative. Compatibility: 82%. Recommended: Alice handles operations/finance, Ali drives strategy/growth.'
);

-- Reading 4 junction records
INSERT INTO oracle_reading_users (reading_id, user_id, is_primary) VALUES
(4, 1, TRUE),   -- Alice is primary asker
(4, 2, FALSE);  -- Ali is participant

-- Reading 5: Multi-user (3-way reading - all users)
INSERT INTO oracle_readings (
    is_multi_user,
    primary_user_id,
    question,
    sign_type,
    sign_value,
    reading_result,
    individual_results,
    combined_energy
) VALUES (
    TRUE,
    2,
    'Should we form a partnership for this project?',
    'question',
    'Should we form a partnership for this project?',
    '{
        "fc60": {
            "sign": "Metal Tiger",
            "element": "Metal",
            "animal": "Tiger",
            "energy": "Yang"
        },
        "cosmic_alignment": 76.4
    }'::jsonb,
    '[
        {"user_id": 1, "name": "Alice Johnson", "individual_sign": "Water Ox"},
        {"user_id": 2, "name": "Ali Rezaei", "individual_sign": "Fire Horse"},
        {"user_id": 3, "name": "Sara Khani", "individual_sign": "Wood Dragon"}
    ]'::jsonb,
    '{
        "combined_sign": "Metal Tiger",
        "group_synergy": 76.4,
        "optimal_structure": "trio_balanced",
        "timing": "favorable_but_needs_planning"
    }'::jsonb
);

-- Reading 5 junction records
INSERT INTO oracle_reading_users (reading_id, user_id, is_primary) VALUES
(5, 2, TRUE),   -- Ali is primary asker
(5, 1, FALSE),  -- Alice is participant
(5, 3, FALSE);  -- Sara is participant

COMMIT;

-- Verification queries
SELECT 'Users created:' as status, COUNT(*) as count FROM oracle_users;
SELECT 'Readings created:' as status, COUNT(*) as count FROM oracle_readings;
SELECT 'Single-user readings:' as status, COUNT(*) as count FROM oracle_readings WHERE is_multi_user = FALSE;
SELECT 'Multi-user readings:' as status, COUNT(*) as count FROM oracle_readings WHERE is_multi_user = TRUE;
SELECT 'Junction records:' as status, COUNT(*) as count FROM oracle_reading_users;
```

**Acceptance Criteria:**
- [ ] Seed data loads without errors
- [ ] 3 users created (English, Persian, Mixed)
- [ ] 5 readings created (3 single-user, 2 multi-user)
- [ ] Persian text displays correctly (UTF-8 encoding)
- [ ] JSONB data stored and queryable
- [ ] Multi-user readings properly linked via junction table
- [ ] Can query all sample data successfully

**Verification:**
```bash
cd database

# Load seed data
psql -h localhost -U nps_user -d nps_db -f seed/oracle_seed_data.sql
# Expected: Summary counts at end

# Verify user count
psql -h localhost -U nps_user -d nps_db -c "SELECT COUNT(*) FROM oracle_users;"
# Expected: 3

# Verify readings count
psql -h localhost -U nps_user -d nps_db -c "SELECT COUNT(*) FROM oracle_readings;"
# Expected: 5

# Verify multi-user readings
psql -h localhost -U nps_user -d nps_db -c "SELECT id, question, is_multi_user FROM oracle_readings WHERE is_multi_user = TRUE;"
# Expected: 2 rows (readings 4 and 5)

# Verify junction table
psql -h localhost -U nps_user -d nps_db << EOF
SELECT 
    r.id, 
    r.question,
    u.name,
    ru.is_primary
FROM oracle_readings r
JOIN oracle_reading_users ru ON r.id = ru.reading_id
JOIN oracle_users u ON ru.user_id = u.id
WHERE r.id = 4;
EOF
# Expected: 2 rows (Alice as primary, Ali as participant)

# Test Persian text rendering
psql -h localhost -U nps_user -d nps_db -c "SELECT name_persian, mother_name_persian FROM oracle_users WHERE id = 2;"
# Expected: Persian characters displayed correctly

# Test JSONB query
psql -h localhost -U nps_user -d nps_db -c "SELECT question, reading_result->>'fc60' as fc60_sign FROM oracle_readings WHERE id = 1;"
# Expected: Question + JSON extract of FC60 sign

# Test geographic query
psql -h localhost -U nps_user -d nps_db -c "SELECT name, city, ST_AsText(coordinates) as coords FROM oracle_users WHERE city = 'Tehran';"
# Expected: Ali's record with coordinates
```

**Checkpoint:**
- [ ] Seed data complete and accessible
- [ ] All user types represented (English, Persian, Mixed)
- [ ] All reading types demonstrated (single, multi-user)
- [ ] JSONB queries work
- [ ] Persian text displays correctly
- [ ] Junction table links correct

**🚨 STOP if checkpoint fails - review data integrity**

---

### Phase 5: Backup/Restore Scripts (30 minutes)

**Tasks:**
1. Create backup script using pg_dump
2. Create restore script using pg_restore
3. Create usage README documentation
4. Test backup creates valid dump file
5. Test restore recovers data correctly
6. Document backup frequency recommendations

**Files to Create:**
- `database/scripts/backup_oracle.sh`
- `database/scripts/restore_oracle.sh`
- `database/scripts/README.md`

**Backup Script:**
```bash
#!/bin/bash
# database/scripts/backup_oracle.sh
# Backup Oracle system tables (users, readings, junction)
# Usage: ./backup_oracle.sh [backup_directory]

set -e  # Exit on error

# Configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-nps_user}
DB_NAME=${DB_NAME:-nps_db}
BACKUP_DIR=${1:-./backups}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/oracle_backup_$TIMESTAMP.dump"

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Backup Oracle tables
echo "Starting Oracle backup..."
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "Output: $BACKUP_FILE"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  --table=oracle_users \
  --table=oracle_readings \
  --table=oracle_reading_users \
  --format=custom \
  --compress=9 \
  --file="$BACKUP_FILE" \
  --verbose

# Verify backup file created
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup completed successfully!"
    echo "File: $BACKUP_FILE"
    echo "Size: $BACKUP_SIZE"
    
    # Create latest symlink
    ln -sf "$(basename "$BACKUP_FILE")" "$BACKUP_DIR/oracle_backup_latest.dump"
    echo "Latest backup symlink updated"
else
    echo "❌ Backup failed - file not created"
    exit 1
fi

# Cleanup old backups (keep last 30 days)
echo "Cleaning old backups (>30 days)..."
find "$BACKUP_DIR" -name "oracle_backup_*.dump" -type f -mtime +30 -delete
echo "Cleanup complete"

exit 0
```

**Restore Script:**
```bash
#!/bin/bash
# database/scripts/restore_oracle.sh
# Restore Oracle system from backup
# Usage: ./restore_oracle.sh <backup_file>

set -e  # Exit on error

# Configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-nps_user}
DB_NAME=${DB_NAME:-nps_db}
BACKUP_FILE=$1

# Validate arguments
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 backups/oracle_backup_20260208_143022.dump"
    echo "Or use: $0 backups/oracle_backup_latest.dump"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Warning
echo "⚠️  WARNING: This will DELETE existing Oracle data and restore from backup!"
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "Backup: $BACKUP_FILE"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Drop existing Oracle tables (clean slate)
echo "Dropping existing Oracle tables..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
DROP TABLE IF EXISTS oracle_reading_users CASCADE;
DROP TABLE IF EXISTS oracle_readings CASCADE;
DROP TABLE IF EXISTS oracle_users CASCADE;
EOF

# Restore from backup
echo "Restoring from backup..."
pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  --format=custom \
  --verbose \
  "$BACKUP_FILE"

# Verify restoration
echo "Verifying restoration..."
USERS_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM oracle_users;")
READINGS_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM oracle_readings;")
JUNCTION_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM oracle_reading_users;")

echo "✅ Restore completed successfully!"
echo "Users: $USERS_COUNT"
echo "Readings: $READINGS_COUNT"
echo "Junction records: $JUNCTION_COUNT"

exit 0
```

**README Documentation:**
```markdown
# Oracle Database Scripts

## Backup & Restore Scripts

### backup_oracle.sh
Creates compressed backup of Oracle system tables.

**Usage:**
```bash
# Default backup to ./backups/
./scripts/backup_oracle.sh

# Custom backup directory
./scripts/backup_oracle.sh /path/to/backups/
```

**Environment Variables:**
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_USER` - Database user (default: nps_user)
- `DB_NAME` - Database name (default: nps_db)

**What it backs up:**
- oracle_users (user profiles)
- oracle_readings (readings with FC60/AI data)
- oracle_reading_users (junction table)

**Features:**
- Compressed format (pg_dump custom format, level 9)
- Automatic timestamping
- Latest backup symlink
- Auto-cleanup of old backups (>30 days)

**Output:**
- Backup file: `backups/oracle_backup_YYYYMMDD_HHMMSS.dump`
- Symlink: `backups/oracle_backup_latest.dump`

### restore_oracle.sh
Restores Oracle system from backup.

**Usage:**
```bash
# Restore from specific backup
./scripts/restore_oracle.sh backups/oracle_backup_20260208_143022.dump

# Restore from latest backup
./scripts/restore_oracle.sh backups/oracle_backup_latest.dump
```

**⚠️ WARNING:** Restore DELETES existing Oracle data before restoring!

**Safety:**
- Prompts for confirmation before proceeding
- Validates backup file exists
- Verifies restoration with row counts

## Recommended Backup Schedule

**Production:**
- Daily: Automated backup at 2 AM (cron)
- Weekly: Off-site backup copy (Friday)
- Monthly: Long-term archive

**Development:**
- Before schema changes: Manual backup
- Before major data imports: Manual backup

**Cron Example (Daily 2 AM):**
```bash
0 2 * * * cd /path/to/nps-v4/database && ./scripts/backup_oracle.sh /mnt/backups/oracle/ >> /var/log/oracle_backup.log 2>&1
```

## Testing Backups

Regularly test restore process:
```bash
# 1. Create test database
createdb -U nps_user nps_db_test

# 2. Restore to test database
DB_NAME=nps_db_test ./scripts/restore_oracle.sh backups/oracle_backup_latest.dump

# 3. Verify data
psql -U nps_user -d nps_db_test -c "SELECT COUNT(*) FROM oracle_users;"

# 4. Cleanup
dropdb -U nps_user nps_db_test
```
```

**Acceptance Criteria:**
- [ ] Backup script creates valid dump file
- [ ] Backup file is compressed (smaller than raw SQL)
- [ ] Restore script restores data correctly
- [ ] Restore script prompts for confirmation (safety)
- [ ] Scripts have error handling (set -e)
- [ ] Scripts are executable (chmod +x)
- [ ] README documents usage clearly
- [ ] Automated cleanup removes old backups

**Verification:**
```bash
cd database/scripts

# Make scripts executable
chmod +x backup_oracle.sh restore_oracle.sh

# Test backup
./backup_oracle.sh
# Expected: Backup file created in ./backups/

# Verify backup file
ls -lh backups/oracle_backup_*.dump
# Expected: File exists with reasonable size

# Delete some data (to test restore)
psql -h localhost -U nps_user -d nps_db -c "DELETE FROM oracle_users WHERE id = 3;"
psql -h localhost -U nps_user -d nps_db -c "SELECT COUNT(*) FROM oracle_users;"
# Expected: 2 (down from 3)

# Test restore
./restore_oracle.sh backups/oracle_backup_latest.dump
# Type "yes" when prompted
# Expected: Restoration summary with counts

# Verify data restored
psql -h localhost -U nps_user -d nps_db -c "SELECT COUNT(*) FROM oracle_users;"
# Expected: 3 (restored)

psql -h localhost -U nps_user -d nps_db -c "SELECT name FROM oracle_users WHERE id = 3;"
# Expected: Sara Khani (data restored)

# Test backup to custom directory
mkdir -p /tmp/oracle_test_backups
./backup_oracle.sh /tmp/oracle_test_backups
ls /tmp/oracle_test_backups/
# Expected: Backup file exists

# Cleanup
rm -rf /tmp/oracle_test_backups
```

**Checkpoint:**
- [ ] Backup/restore scripts working
- [ ] Backup creates valid PostgreSQL dump
- [ ] Restore recovers all data correctly
- [ ] Scripts handle errors gracefully
- [ ] Documentation clear and complete
- [ ] Tested on real data

**🚨 STOP if checkpoint fails - backup/restore is critical**

---

## VERIFICATION CHECKLIST

Run ALL these checks before declaring session complete:

### Schema Validation
- [ ] All 3 tables exist: `psql -c "\dt oracle_*"`
- [ ] All foreign keys defined: `psql -c "\d oracle_readings"`
- [ ] All indexes created: `psql -c "\di oracle_*"`
- [ ] Check constraints work: Try inserting invalid data (should fail)

### Data Integrity
- [ ] Can insert user: `INSERT INTO oracle_users (...) VALUES (...)`
- [ ] Can insert single-user reading
- [ ] Can insert multi-user reading with junction records
- [ ] Foreign key prevents orphaned readings (delete user → readings cascade)
- [ ] Unique constraint on (reading_id, user_id) prevents duplicates
- [ ] Check constraint prevents is_multi_user=FALSE with NULL user_id

### Performance
- [ ] Query with user_id uses index (verify with EXPLAIN)
- [ ] Query with created_at uses index
- [ ] JSONB query uses GIN index
- [ ] Geographic query uses GIST index (if PostGIS available)
- [ ] All queries complete in under 1 second with seed data

### Migrations
- [ ] Migration runs cleanly: `psql -f migrations/010_oracle_schema.sql`
- [ ] Migration is idempotent (run twice without errors)
- [ ] Rollback works: `psql -f migrations/010_oracle_schema_rollback.sql`
- [ ] After rollback, no Oracle tables remain

### Seed Data
- [ ] Seed data loads without errors
- [ ] 3 users in database
- [ ] 5 readings in database (3 single, 2 multi-user)
- [ ] Persian text displays correctly (no garbled characters)
- [ ] JSONB data queries work

### Backup/Restore
- [ ] Backup script creates dump file
- [ ] Dump file is compressed (reasonable size)
- [ ] Restore script restores data completely
- [ ] Restored data matches original (row counts, content)
- [ ] Old backups auto-deleted (>30 days)

### Documentation
- [ ] README.md in scripts/ explains usage
- [ ] SQL comments explain table purposes
- [ ] Migration versioning documented
- [ ] Backup schedule recommendations provided

### Integration Readiness
- [ ] Layer 2 (API) can query these tables
- [ ] Layer 3 (Backend) can insert readings
- [ ] Layer 1 (Frontend) can display users/readings
- [ ] Layer 6 (Security) can use user_id for encryption

## SUCCESS CRITERIA

Must achieve ALL of these:

1. ✅ All 3 tables created with proper schema and constraints
2. ✅ Foreign key relationships enforced (cascade deletes work)
3. ✅ Indexes improve query performance (verified with EXPLAIN ANALYZE)
4. ✅ Migration system functional (up and down, idempotent)
5. ✅ Seed data demonstrates all features (English, Persian, single, multi-user)
6. ✅ Backup/restore tested and working (data restored correctly)
7. ✅ Can insert 10,000 readings in under 10 seconds
8. ✅ Queries remain fast with seed data (all under 1s)
9. ✅ Zero SQL errors in any script
10. ✅ Persian text encoding works (UTF-8, no corruption)
11. ✅ JSONB queries functional (can filter by JSON content)
12. ✅ PostGIS coordinates work (geographic queries possible)

**Quality Score Target:** 95/100 (Swiss Watch Grade)

## NEXT STEPS (After Session Complete)

**Immediate Next Actions:**
1. **Terminal 2 (API):** Can now build Oracle endpoints using this schema
   - POST /api/oracle/reading (create reading)
   - GET /api/oracle/users (list users)
   - GET /api/oracle/readings/{id} (get reading details)

2. **Terminal 3 (Backend):** Oracle service can query/insert to these tables
   - FC60 calculations → store in reading_result JSONB
   - AI interpretations → store in ai_interpretation fields
   - Multi-user compatibility → use junction table

3. **Terminal 1 (Frontend):** Can display users and readings
   - User profile page
   - Reading history page
   - Multi-user reading visualization

4. **Terminal 6 (Security):** Can use oracle_users for encryption keys
   - User-specific encryption contexts
   - Reading access control

**Documentation to Update:**
- API specification: Add Oracle endpoints
- Frontend requirements: Add Oracle UI pages
- Backend integration: Oracle service database access

**Performance Optimization (Future):**
- Consider partitioning oracle_readings if >1M rows (by created_at)
- Add materialized view for reading statistics
- Implement read replicas for high-traffic queries

## HANDOFF NOTES

### Files Created
```
database/
├── schemas/
│   ├── oracle_users.sql              (User profiles table)
│   ├── oracle_readings.sql           (Readings table)
│   ├── oracle_reading_users.sql      (Junction table)
│   └── oracle_indexes.sql            (Performance indexes)
├── migrations/
│   ├── 010_oracle_schema.sql         (Migration up)
│   └── 010_oracle_schema_rollback.sql (Migration down)
├── seed/
│   └── oracle_seed_data.sql          (Sample users + readings)
└── scripts/
    ├── backup_oracle.sh              (Backup script)
    ├── restore_oracle.sh             (Restore script)
    └── README.md                     (Usage documentation)
```

### Database State After Session
- ✅ 3 tables created (oracle_users, oracle_readings, oracle_reading_users)
- ✅ 12+ indexes created (foreign keys, dates, JSONB, coordinates)
- ✅ 3 users seeded (English, Persian, Mixed)
- ✅ 5 readings seeded (3 single-user, 2 multi-user)
- ✅ Migration version 10 tracked in schema_migrations
- ✅ Backup created and tested

### Known Issues
None expected. If PostGIS extension unavailable:
- Coordinates column will fail (POINT type requires PostGIS)
- Workaround: Use VARCHAR(50) for coordinates as "lat,lng" string
- Update spatial index to regular B-tree index

### Resume Instructions
If session interrupted:
1. Check last completed phase checkpoint
2. Verify database state: `psql -c "\dt oracle_*"`
3. Continue from next incomplete phase
4. Re-run verification checklist before declaring complete

### Performance Benchmarks
With seed data (5 readings):
- Single-user reading insert: ~5ms
- Multi-user reading insert: ~10ms (includes junction records)
- Query by user_id: ~2ms (using index)
- JSONB query: ~3ms (using GIN index)

Target for 1M readings:
- Insert: <10ms per reading
- Query with index: <100ms
- JSONB query: <500ms

## EXTENDED THINKING GUIDANCE

**For Claude Code CLI with Extended Thinking:**

When implementing this spec, use extended thinking for:

1. **Schema Design Decisions:**
   - Should coordinates be PostGIS POINT or VARCHAR?
   - Should reading_result be JSONB or TEXT?
   - Should we partition oracle_readings table now or later?

2. **Index Strategy:**
   - Which queries will be most common?
   - Are GIN indexes worth the write performance cost?
   - Should we add composite indexes (e.g., user_id + created_at)?

3. **Multi-User Reading Design:**
   - Is junction table best approach vs array of user_ids?
   - How to handle primary user designation?
   - Should compatibility scores be JSONB or separate table?

4. **Performance vs Simplicity Trade-offs:**
   - Partitioning adds complexity but improves query speed
   - JSONB flexible but harder to query than normalized tables
   - Materialized views fast but need refresh management

5. **Persian Text Handling:**
   - Does PostgreSQL UTF-8 default handle RTL text correctly?
   - Should we store both English and Persian (redundant) or just one?
   - Do we need special indexes for Persian text search?

**Recommended Thinking Outputs:**
- Clear decision with rationale
- Trade-offs acknowledged
- Future optimization paths noted
- Performance impact estimated
- Rollback plan if decision fails

---

*End of Specification*

**Ready for Claude Code CLI Execution** ✅
