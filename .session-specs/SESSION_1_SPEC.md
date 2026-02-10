# SESSION 1 SPEC — Database Schema Audit & Alignment

**Block:** Foundation (Sessions 1-5)
**Estimated Duration:** 3-4 hours
**Complexity:** High
**Dependencies:** None — this is the starting point

---

## TL;DR

- Audit existing 15-table PostgreSQL schema against framework's `MasterOrchestrator` output model
- Add 4 missing columns to `oracle_users` (gender, heart_rate_bpm, timezone_hours, timezone_minutes)
- Add 3 missing columns to `oracle_readings` (framework_version, reading_mode, numerology_system)
- Create 2 new tables: `oracle_settings` (user preferences) and `oracle_daily_readings` (daily auto-readings)
- Write migration 012 (up + rollback), update seed data with framework test vectors, verify Persian UTF-8

---

## OBJECTIVES

1. **Complete schema audit** — Document every gap between the existing 15 tables and the framework's data requirements
2. **Add missing columns** to `oracle_users` and `oracle_readings` so the framework has all inputs/outputs it needs
3. **Create `oracle_settings` table** for user preferences (language, theme, numerology system, timezone)
4. **Create `oracle_daily_readings` table** for auto-generated daily readings (one per user per day)
5. **Write idempotent migration 012** with clean rollback, update seeds with framework test vectors, verify Persian text integrity

---

## PREREQUISITES

- [ ] PostgreSQL schemas exist in `database/schemas/` and `database/init.sql`
- [ ] Migrations 010 and 011 exist in `database/migrations/`
- [ ] Framework is available at `numerology_ai_framework/` (for output structure reference)
- Verification:
  ```bash
  test -f database/init.sql && test -f database/schemas/oracle_users.sql && test -f database/schemas/oracle_readings.sql && echo "Schema files OK"
  test -f database/migrations/010_oracle_schema.sql && test -f database/migrations/011_security_columns.sql && echo "Migrations OK"
  test -f numerology_ai_framework/synthesis/master_orchestrator.py && echo "Framework OK"
  ```

---

## SCHEMA GAP ANALYSIS

### `oracle_users` — 4 Missing Columns

The framework's `MasterOrchestrator.generate_reading()` requires these parameters that have no corresponding column:

| Missing Column     | Type        | Framework Parameter | Why Needed                                             |
| ------------------ | ----------- | ------------------- | ------------------------------------------------------ |
| `gender`           | VARCHAR(20) | `gender`            | Polarity data (+gender_polarity in numerology profile) |
| `heart_rate_bpm`   | INTEGER     | `actual_bpm`        | Heartbeat engine rhythm analysis (+5% confidence)      |
| `timezone_hours`   | INTEGER     | `tz_hours`          | FC60 stamp timezone adjustment                         |
| `timezone_minutes` | INTEGER     | `tz_minutes`        | FC60 stamp timezone fine adjustment                    |

**Existing columns that map correctly:**

- `name` → `full_name`
- `birthday` → `birth_day`, `birth_month`, `birth_year` (extract from DATE)
- `mother_name` → `mother_name`
- `coordinates` → `latitude`, `longitude` (extract from POINT)

### `oracle_readings` — 3 Missing Columns

| Missing Column      | Type        | Purpose                                                             |
| ------------------- | ----------- | ------------------------------------------------------------------- |
| `framework_version` | VARCHAR(20) | Track which framework version generated the reading (e.g., "1.0.0") |
| `reading_mode`      | VARCHAR(20) | 'full' or 'stamp_only' — which framework mode was used              |
| `numerology_system` | VARCHAR(20) | 'pythagorean', 'chaldean', or 'abjad' — which system was used       |

**Existing `reading_result` JSONB column** is already sufficient to store the full framework output dict (keys: numerology, fc60_stamp, moon, ganzhi, heartbeat, location, patterns, current, birth, person, confidence, synthesis, translation). No structural change needed — just ensure nothing truncates it.

### New Tables Needed

1. **`oracle_settings`** — User preferences (language, theme, default numerology system, default timezone)
2. **`oracle_daily_readings`** — One auto-generated reading per user per day, with UNIQUE constraint on (user_id, reading_date)

---

## FILES TO CREATE

- `database/schemas/oracle_settings.sql` — New table definition
- `database/schemas/oracle_daily_readings.sql` — New table definition
- `database/migrations/012_framework_alignment.sql` — Migration up
- `database/migrations/012_framework_alignment_rollback.sql` — Migration down

## FILES TO MODIFY

- `database/schemas/oracle_users.sql` — Add 4 columns (gender, heart_rate_bpm, timezone_hours, timezone_minutes)
- `database/schemas/oracle_readings.sql` — Add 3 columns (framework_version, reading_mode, numerology_system)
- `database/seeds/oracle_seed_data.sql` — Add framework test vector user + update existing users with new columns
- `database/init.sql` — Add references to new tables (oracle_settings, oracle_daily_readings)

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Schema Modifications — oracle_users (~45 min)

**Tasks:**

1. Add 4 columns to `database/schemas/oracle_users.sql`:

   ```sql
   gender VARCHAR(20) CHECK(gender IN ('male', 'female') OR gender IS NULL),
   heart_rate_bpm INTEGER CHECK(heart_rate_bpm IS NULL OR (heart_rate_bpm >= 30 AND heart_rate_bpm <= 220)),
   timezone_hours INTEGER DEFAULT 0 CHECK(timezone_hours >= -12 AND timezone_hours <= 14),
   timezone_minutes INTEGER DEFAULT 0 CHECK(timezone_minutes >= 0 AND timezone_minutes <= 59)
   ```

2. Constraints rationale:
   - `gender`: NULL allowed (optional field, +polarity if provided). Only 'male'/'female' per framework's `_gender_polarity()` method
   - `heart_rate_bpm`: Normal resting range 30-220 BPM (covers bradycardia to extreme tachycardia)
   - `timezone_hours`: -12 (Baker Island) to +14 (Line Islands) — full range of real UTC offsets
   - `timezone_minutes`: 0-59 for half-hour/quarter-hour timezone offsets (e.g., India +5:30, Nepal +5:45)

3. All 4 columns are nullable/defaulted — backward compatible with existing data

**Checkpoint:**

- [ ] Schema file has 4 new columns with CHECK constraints
- [ ] Existing column definitions unchanged
- Verify: `grep -c "gender\|heart_rate_bpm\|timezone_hours\|timezone_minutes" database/schemas/oracle_users.sql` — should return 4+

🚨 STOP if checkpoint fails

---

### Phase 2: Schema Modifications — oracle_readings (~30 min)

**Tasks:**

1. Add 3 columns to `database/schemas/oracle_readings.sql`:

   ```sql
   framework_version VARCHAR(20) DEFAULT NULL,
   reading_mode VARCHAR(20) DEFAULT 'full' CHECK(reading_mode IN ('full', 'stamp_only')),
   numerology_system VARCHAR(20) DEFAULT 'pythagorean' CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad'))
   ```

2. Add index for numerology_system filtering:

   ```sql
   CREATE INDEX idx_oracle_readings_numerology_system ON oracle_readings(numerology_system);
   ```

3. Constraints rationale:
   - `framework_version`: NULL for legacy readings generated before framework integration
   - `reading_mode`: 'full' default — most readings are full; 'stamp_only' for quick FC60 lookups
   - `numerology_system`: 'pythagorean' default — matches framework's default parameter

**Checkpoint:**

- [ ] Schema file has 3 new columns with CHECK constraints
- [ ] New index defined for numerology_system
- Verify: `grep -c "framework_version\|reading_mode\|numerology_system" database/schemas/oracle_readings.sql` — should return 3+

🚨 STOP if checkpoint fails

---

### Phase 3: New Tables — oracle_settings & oracle_daily_readings (~60 min)

**Tasks:**

1. Create `database/schemas/oracle_settings.sql`:

   ```sql
   CREATE TABLE IF NOT EXISTS oracle_settings (
       id SERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
       language VARCHAR(10) NOT NULL DEFAULT 'en' CHECK(language IN ('en', 'fa')),
       theme VARCHAR(20) NOT NULL DEFAULT 'light' CHECK(theme IN ('light', 'dark', 'auto')),
       numerology_system VARCHAR(20) NOT NULL DEFAULT 'auto'
           CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad', 'auto')),
       default_timezone_hours INTEGER DEFAULT 0
           CHECK(default_timezone_hours >= -12 AND default_timezone_hours <= 14),
       default_timezone_minutes INTEGER DEFAULT 0
           CHECK(default_timezone_minutes >= 0 AND default_timezone_minutes <= 59),
       daily_reading_enabled BOOLEAN NOT NULL DEFAULT TRUE,
       notifications_enabled BOOLEAN NOT NULL DEFAULT FALSE,
       created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       UNIQUE(user_id)
   );
   ```

   - One settings row per user (UNIQUE on user_id)
   - `language`: 'en' or 'fa' (English/Persian) — controls UI locale and AI response language
   - `theme`: 'light', 'dark', 'auto' — frontend display theme
   - `numerology_system`: 'auto' default — Session 8 adds auto-detection logic
   - `daily_reading_enabled`: Controls whether cron generates daily readings for this user
   - Trigger for `updated_at` auto-update

2. Create `database/schemas/oracle_daily_readings.sql`:

   ```sql
   CREATE TABLE IF NOT EXISTS oracle_daily_readings (
       id BIGSERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
       reading_date DATE NOT NULL,
       reading_result JSONB NOT NULL,
       daily_insights JSONB,
       numerology_system VARCHAR(20) NOT NULL DEFAULT 'pythagorean'
           CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad')),
       confidence_score DOUBLE PRECISION DEFAULT 0,
       framework_version VARCHAR(20),
       created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       UNIQUE(user_id, reading_date)
   );
   ```

   - UNIQUE on (user_id, reading_date) — exactly one daily reading per user per day
   - `reading_result`: Full framework output JSONB
   - `daily_insights`: Separate JSONB for suggested_activities, energy_forecast, lucky_hours, etc. (Session 7)
   - `confidence_score`: Denormalized from reading_result for quick sorting/filtering

3. Add indexes:

   ```sql
   -- oracle_settings
   CREATE INDEX idx_oracle_settings_user_id ON oracle_settings(user_id);

   -- oracle_daily_readings
   CREATE INDEX idx_oracle_daily_readings_user_date ON oracle_daily_readings(user_id, reading_date DESC);
   CREATE INDEX idx_oracle_daily_readings_date ON oracle_daily_readings(reading_date DESC);
   CREATE INDEX idx_oracle_daily_readings_result_gin ON oracle_daily_readings(reading_result) USING GIN;
   ```

4. Add `update_updated_at` trigger for `oracle_settings` (reuse existing function from init.sql).

**Checkpoint:**

- [ ] Both new schema files exist and have valid SQL
- [ ] `oracle_settings` has UNIQUE(user_id) constraint
- [ ] `oracle_daily_readings` has UNIQUE(user_id, reading_date) constraint
- [ ] Indexes defined for both tables
- Verify: `test -f database/schemas/oracle_settings.sql && test -f database/schemas/oracle_daily_readings.sql && echo "New schemas OK"`

🚨 STOP if checkpoint fails

---

### Phase 4: Migration 012 — Framework Alignment (~45 min)

**Tasks:**

1. Create `database/migrations/012_framework_alignment.sql`:

   ```sql
   -- Migration 012: Framework Alignment
   -- Adds columns needed by numerology_ai_framework to oracle_users and oracle_readings
   -- Creates oracle_settings and oracle_daily_readings tables

   DO $$
   BEGIN
       -- Guard: skip if already applied
       IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '012') THEN
           RAISE NOTICE 'Migration 012 already applied, skipping.';
           RETURN;
       END IF;

       -- 1. Add columns to oracle_users
       ALTER TABLE oracle_users ADD COLUMN IF NOT EXISTS gender VARCHAR(20)
           CHECK(gender IN ('male', 'female') OR gender IS NULL);
       ALTER TABLE oracle_users ADD COLUMN IF NOT EXISTS heart_rate_bpm INTEGER
           CHECK(heart_rate_bpm IS NULL OR (heart_rate_bpm >= 30 AND heart_rate_bpm <= 220));
       ALTER TABLE oracle_users ADD COLUMN IF NOT EXISTS timezone_hours INTEGER DEFAULT 0
           CHECK(timezone_hours >= -12 AND timezone_hours <= 14);
       ALTER TABLE oracle_users ADD COLUMN IF NOT EXISTS timezone_minutes INTEGER DEFAULT 0
           CHECK(timezone_minutes >= 0 AND timezone_minutes <= 59);

       -- 2. Add columns to oracle_readings
       ALTER TABLE oracle_readings ADD COLUMN IF NOT EXISTS framework_version VARCHAR(20);
       ALTER TABLE oracle_readings ADD COLUMN IF NOT EXISTS reading_mode VARCHAR(20) DEFAULT 'full'
           CHECK(reading_mode IN ('full', 'stamp_only'));
       ALTER TABLE oracle_readings ADD COLUMN IF NOT EXISTS numerology_system VARCHAR(20) DEFAULT 'pythagorean'
           CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad'));

       -- 3. Add index for numerology_system
       CREATE INDEX IF NOT EXISTS idx_oracle_readings_numerology_system
           ON oracle_readings(numerology_system);

       -- 4. Create oracle_settings table
       CREATE TABLE IF NOT EXISTS oracle_settings (
           id SERIAL PRIMARY KEY,
           user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
           language VARCHAR(10) NOT NULL DEFAULT 'en' CHECK(language IN ('en', 'fa')),
           theme VARCHAR(20) NOT NULL DEFAULT 'light' CHECK(theme IN ('light', 'dark', 'auto')),
           numerology_system VARCHAR(20) NOT NULL DEFAULT 'auto'
               CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad', 'auto')),
           default_timezone_hours INTEGER DEFAULT 0
               CHECK(default_timezone_hours >= -12 AND default_timezone_hours <= 14),
           default_timezone_minutes INTEGER DEFAULT 0
               CHECK(default_timezone_minutes >= 0 AND default_timezone_minutes <= 59),
           daily_reading_enabled BOOLEAN NOT NULL DEFAULT TRUE,
           notifications_enabled BOOLEAN NOT NULL DEFAULT FALSE,
           created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
           updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
           UNIQUE(user_id)
       );

       -- 5. Create oracle_daily_readings table
       CREATE TABLE IF NOT EXISTS oracle_daily_readings (
           id BIGSERIAL PRIMARY KEY,
           user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
           reading_date DATE NOT NULL,
           reading_result JSONB NOT NULL,
           daily_insights JSONB,
           numerology_system VARCHAR(20) NOT NULL DEFAULT 'pythagorean'
               CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad')),
           confidence_score DOUBLE PRECISION DEFAULT 0,
           framework_version VARCHAR(20),
           created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
           UNIQUE(user_id, reading_date)
       );

       -- 6. Indexes for new tables
       CREATE INDEX IF NOT EXISTS idx_oracle_settings_user_id
           ON oracle_settings(user_id);
       CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_user_date
           ON oracle_daily_readings(user_id, reading_date DESC);
       CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_date
           ON oracle_daily_readings(reading_date DESC);
       CREATE INDEX IF NOT EXISTS idx_oracle_daily_readings_result_gin
           ON oracle_daily_readings(reading_result) USING GIN;

       -- 7. Trigger for oracle_settings updated_at
       CREATE TRIGGER oracle_settings_updated_at
           BEFORE UPDATE ON oracle_settings
           FOR EACH ROW EXECUTE FUNCTION update_updated_at();

       -- 8. Record migration
       INSERT INTO schema_migrations (version, name)
       VALUES ('012', 'Framework alignment: user columns, reading columns, settings, daily readings');

       RAISE NOTICE 'Migration 012 applied successfully.';
   END $$;
   ```

2. Create `database/migrations/012_framework_alignment_rollback.sql`:

   ```sql
   -- Rollback Migration 012: Framework Alignment
   DO $$
   BEGIN
       -- Guard: skip if not applied
       IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '012') THEN
           RAISE NOTICE 'Migration 012 not applied, nothing to rollback.';
           RETURN;
       END IF;

       -- Drop new tables (reverse order)
       DROP TABLE IF EXISTS oracle_daily_readings CASCADE;
       DROP TABLE IF EXISTS oracle_settings CASCADE;

       -- Drop new indexes on oracle_readings
       DROP INDEX IF EXISTS idx_oracle_readings_numerology_system;

       -- Remove columns from oracle_readings
       ALTER TABLE oracle_readings DROP COLUMN IF EXISTS numerology_system;
       ALTER TABLE oracle_readings DROP COLUMN IF EXISTS reading_mode;
       ALTER TABLE oracle_readings DROP COLUMN IF EXISTS framework_version;

       -- Remove columns from oracle_users
       ALTER TABLE oracle_users DROP COLUMN IF EXISTS timezone_minutes;
       ALTER TABLE oracle_users DROP COLUMN IF EXISTS timezone_hours;
       ALTER TABLE oracle_users DROP COLUMN IF EXISTS heart_rate_bpm;
       ALTER TABLE oracle_users DROP COLUMN IF EXISTS gender;

       -- Remove migration record
       DELETE FROM schema_migrations WHERE version = '012';

       RAISE NOTICE 'Migration 012 rolled back successfully.';
   END $$;
   ```

3. Migration is fully idempotent — can run twice without error (guards + IF NOT EXISTS).

**Checkpoint:**

- [ ] Migration file has valid SQL syntax
- [ ] Rollback reverses ALL changes from migration
- [ ] Both files have guard clauses for idempotency
- Verify: `test -f database/migrations/012_framework_alignment.sql && test -f database/migrations/012_framework_alignment_rollback.sql && echo "Migration files OK"`

🚨 STOP if checkpoint fails

---

### Phase 5: Seed Data & init.sql Updates (~45 min)

**Tasks:**

1. Update `database/seeds/oracle_seed_data.sql`:

   Add framework test vector user:

   ```sql
   -- Framework test vector: "Test User" born 2000-01-01, Life Path = 4
   INSERT INTO oracle_users (id, name, name_persian, birthday, mother_name, gender, heart_rate_bpm, timezone_hours, timezone_minutes)
   VALUES (100, 'Test User', 'کاربر آزمایشی', '2000-01-01', 'Test Mother', NULL, NULL, 0, 0)
   ON CONFLICT DO NOTHING;
   ```

   Update existing 3 seed users with new columns:

   ```sql
   -- Hamzeh: male, 72 BPM resting, Tehran UTC+3:30
   UPDATE oracle_users SET gender = 'male', heart_rate_bpm = 72, timezone_hours = 3, timezone_minutes = 30
   WHERE id = 1;

   -- Sara: female, 68 BPM, Isfahan UTC+3:30
   UPDATE oracle_users SET gender = 'female', heart_rate_bpm = 68, timezone_hours = 3, timezone_minutes = 30
   WHERE id = 2;

   -- Ali: male, 75 BPM, Shiraz UTC+3:30
   UPDATE oracle_users SET gender = 'male', heart_rate_bpm = 75, timezone_hours = 3, timezone_minutes = 30
   WHERE id = 3;
   ```

   Add settings for all users:

   ```sql
   INSERT INTO oracle_settings (user_id, language, theme, numerology_system)
   VALUES
       (1, 'fa', 'dark', 'auto'),
       (2, 'fa', 'light', 'auto'),
       (3, 'fa', 'light', 'abjad'),
       (100, 'en', 'light', 'pythagorean')
   ON CONFLICT (user_id) DO NOTHING;
   ```

2. Update `database/init.sql` to include new table creation after existing Oracle tables:

   Add after the oracle_audit_log section:

   ```sql
   -- Oracle Settings (user preferences)
   \i schemas/oracle_settings.sql

   -- Oracle Daily Readings (auto-generated)
   \i schemas/oracle_daily_readings.sql
   ```

   Note: Only add the `\i` references if init.sql uses `\i` includes. If init.sql has inline SQL, add the CREATE TABLE statements inline instead. Check the actual init.sql pattern first.

3. Verify framework test vector:
   - "Test User" born 2000-01-01 → Life Path: 1+1+2+0+0+0 = 4 (matches framework expectation)
   - Age on 2026-02-09: 26 years
   - Birth weekday: Saturday (JDN 2451545, (2451545+1)%7 = 0 = Saturday)

**Checkpoint:**

- [ ] Test vector user (id=100) inserted with correct birthdate
- [ ] Existing users updated with gender, heart_rate_bpm, timezone
- [ ] Settings rows created for all users
- [ ] init.sql references new schema files
- Verify: `grep -c "Test User" database/seeds/oracle_seed_data.sql` — should return 1+

🚨 STOP if checkpoint fails

---

### Phase 6: Persian Text Verification & Final Validation (~30 min)

**Tasks:**

1. Verify Persian text in seed data is valid UTF-8:
   - `حمزه` (Hamzeh), `سارا` (Sara), `علی` (Ali) — names
   - `فاطمه` (Fatemeh), `مریم` (Maryam), `زهرا` (Zahra) — mother names
   - `کاربر آزمایشی` (Test User) — framework test vector

2. Verify all SQL files parse without syntax errors:

   ```bash
   # Check SQL syntax (basic validation — look for unclosed quotes, mismatched parens)
   python3 -c "
   import re
   files = [
       'database/schemas/oracle_users.sql',
       'database/schemas/oracle_readings.sql',
       'database/schemas/oracle_settings.sql',
       'database/schemas/oracle_daily_readings.sql',
       'database/migrations/012_framework_alignment.sql',
       'database/migrations/012_framework_alignment_rollback.sql',
       'database/seeds/oracle_seed_data.sql',
   ]
   for f in files:
       content = open(f).read()
       # Check balanced parens
       assert content.count('(') == content.count(')'), f'{f}: unbalanced parentheses'
       # Check no bare tab characters in SQL (style)
       print(f'  OK: {f}')
   print('All SQL files valid')
   "
   ```

3. Cross-reference framework parameter mapping:

   | Framework Parameter | oracle_users Column                     | Extraction                                          |
   | ------------------- | --------------------------------------- | --------------------------------------------------- |
   | `full_name`         | `name`                                  | Direct                                              |
   | `birth_day`         | `birthday`                              | `EXTRACT(DAY FROM birthday)`                        |
   | `birth_month`       | `birthday`                              | `EXTRACT(MONTH FROM birthday)`                      |
   | `birth_year`        | `birthday`                              | `EXTRACT(YEAR FROM birthday)`                       |
   | `mother_name`       | `mother_name`                           | Direct                                              |
   | `gender`            | `gender`                                | Direct (NEW)                                        |
   | `latitude`          | `coordinates`                           | `coordinates[0]` — note: POINT is (x,y) = (lon,lat) |
   | `longitude`         | `coordinates`                           | `coordinates[1]` — reversed in POINT type           |
   | `actual_bpm`        | `heart_rate_bpm`                        | Direct (NEW)                                        |
   | `tz_hours`          | `timezone_hours`                        | Direct (NEW)                                        |
   | `tz_minutes`        | `timezone_minutes`                      | Direct (NEW)                                        |
   | `numerology_system` | via `oracle_settings.numerology_system` | Join or app-level                                   |

   **Important note on coordinates:** PostgreSQL POINT stores `(x, y)`. The existing seed data uses `POINT(longitude, latitude)` format (e.g., `POINT(51.3890, 35.6892)` for Tehran = lon 51.39, lat 35.69). The framework bridge (Session 6) must extract `coordinates[0]` as longitude and `coordinates[1]` as latitude. Document this in the schema file as a comment.

4. Verify no naming conflicts with existing `readings` table (from init.sql) vs `oracle_readings` (from schemas/). They are separate tables — `readings` is legacy v4, `oracle_readings` is the Oracle domain table. Both coexist.

**Checkpoint:**

- [ ] All Persian strings are valid UTF-8 (no mojibake)
- [ ] All SQL files have balanced parentheses
- [ ] Framework parameter mapping is complete — no gaps
- [ ] POINT coordinate ordering documented
- Verify: `python3 -c "open('database/seeds/oracle_seed_data.sql').read().encode('utf-8'); print('UTF-8 OK')"`

🚨 STOP if checkpoint fails

---

## TESTS TO WRITE

This session modifies SQL files only — no Python test files created. Verification is SQL-based:

| Test                               | Method                                                       | Verifies                                                 |
| ---------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------- |
| Tables exist                       | `\dt oracle_*` in psql                                       | All 6 oracle\_\* tables present                          |
| New columns on oracle_users        | `\d oracle_users`                                            | gender, heart_rate_bpm, timezone_hours, timezone_minutes |
| New columns on oracle_readings     | `\d oracle_readings`                                         | framework_version, reading_mode, numerology_system       |
| oracle_settings structure          | `\d oracle_settings`                                         | All columns, UNIQUE(user_id), CHECK constraints          |
| oracle_daily_readings structure    | `\d oracle_daily_readings`                                   | All columns, UNIQUE(user_id, reading_date)               |
| Gender CHECK constraint            | `INSERT ... gender='invalid'`                                | Should fail                                              |
| heart_rate_bpm CHECK constraint    | `INSERT ... heart_rate_bpm=0`                                | Should fail (below 30)                                   |
| timezone_hours CHECK constraint    | `INSERT ... timezone_hours=15`                               | Should fail (above 14)                                   |
| reading_mode CHECK constraint      | `INSERT ... reading_mode='invalid'`                          | Should fail                                              |
| numerology_system CHECK constraint | `INSERT ... numerology_system='tarot'`                       | Should fail                                              |
| Settings UNIQUE constraint         | Duplicate user_id INSERT                                     | Should fail                                              |
| Daily readings UNIQUE constraint   | Duplicate (user_id, reading_date) INSERT                     | Should fail                                              |
| Framework test vector              | `SELECT * FROM oracle_users WHERE id=100`                    | Name='Test User', birthday='2000-01-01'                  |
| Persian text round-trip            | `SELECT name_persian FROM oracle_users WHERE id=1`           | Returns 'حمزه' uncorrupted                               |
| Seed data completeness             | `SELECT gender, heart_rate_bpm FROM oracle_users WHERE id=1` | 'male', 72                                               |
| Migration idempotency              | Run migration 012 twice                                      | No error on second run                                   |
| Rollback clean                     | Run rollback, verify columns/tables gone                     | All additions removed                                    |
| Index existence                    | `\di idx_oracle_*`                                           | All new indexes present                                  |
| Cascade delete                     | Delete oracle_user → settings/daily_readings rows gone       | FK CASCADE works                                         |

**Note:** These tests will be run against a live PostgreSQL instance (Docker). If Docker is not running, tests are verified by SQL syntax review + manual inspection of the migration file logic.

---

## ACCEPTANCE CRITERIA

- [ ] `oracle_users` has 4 new columns: gender, heart_rate_bpm, timezone_hours, timezone_minutes
- [ ] `oracle_readings` has 3 new columns: framework_version, reading_mode, numerology_system
- [ ] `oracle_settings` table exists with UNIQUE(user_id) and all preference columns
- [ ] `oracle_daily_readings` table exists with UNIQUE(user_id, reading_date)
- [ ] Migration 012 applies cleanly (no errors)
- [ ] Migration 012 is idempotent (runs twice without error)
- [ ] Rollback 012 removes all additions cleanly
- [ ] Framework test vector user (id=100, "Test User", 2000-01-01) in seed data
- [ ] Existing seed users updated with gender, BPM, timezone values
- [ ] Persian text in seed data is valid UTF-8
- [ ] All CHECK constraints enforce valid values
- [ ] POINT coordinate order documented (longitude, latitude)
- [ ] init.sql updated to reference new schema files
- Verify all:
  ```bash
  test -f database/schemas/oracle_settings.sql && \
  test -f database/schemas/oracle_daily_readings.sql && \
  test -f database/migrations/012_framework_alignment.sql && \
  test -f database/migrations/012_framework_alignment_rollback.sql && \
  grep -q "gender" database/schemas/oracle_users.sql && \
  grep -q "framework_version" database/schemas/oracle_readings.sql && \
  grep -q "Test User" database/seeds/oracle_seed_data.sql && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                          | Expected Behavior                                                          |
| ------------------------------------------------- | -------------------------------------------------------------------------- |
| Migration 012 run before 010/011                  | Fails — oracle_users/oracle_readings don't exist yet. Must apply in order. |
| Migration 012 run twice                           | No error — guard clause skips if already applied                           |
| Rollback run when 012 not applied                 | No error — guard clause skips                                              |
| INSERT with gender='nonbinary'                    | CHECK constraint rejects — only 'male'/'female'/NULL allowed               |
| INSERT with heart_rate_bpm=250                    | CHECK constraint rejects — max 220                                         |
| INSERT with timezone_hours=15                     | CHECK constraint rejects — max 14                                          |
| INSERT duplicate oracle_settings for same user    | UNIQUE(user_id) rejects                                                    |
| INSERT duplicate daily reading for same user+date | UNIQUE(user_id, reading_date) rejects                                      |
| Delete oracle_user with settings/daily_readings   | CASCADE deletes related rows (FK ON DELETE CASCADE)                        |
| Large JSONB in reading_result                     | No size limit on JSONB — framework output (~5-10KB) is fine                |
| NULL coordinates in oracle_users                  | Location-related framework fields get NULL — framework handles gracefully  |

---

## HANDOFF

**Created:**

- `database/schemas/oracle_settings.sql`
- `database/schemas/oracle_daily_readings.sql`
- `database/migrations/012_framework_alignment.sql`
- `database/migrations/012_framework_alignment_rollback.sql`

**Modified:**

- `database/schemas/oracle_users.sql` (4 new columns)
- `database/schemas/oracle_readings.sql` (3 new columns)
- `database/seeds/oracle_seed_data.sql` (test vector + updated users + settings)
- `database/init.sql` (references to new tables)

**Next session needs:**

- **Session 2 (Authentication System Hardening)** depends on:
  - `users` table existing (from init.sql — already present)
  - `oracle_audit_log` table existing (already present)
  - Session 1 schema being stable — Session 2 adds auth columns and migration 013
- **Session 3 (User Profile Management)** depends on:
  - `oracle_users` table with all columns including the 4 new ones from this session
  - `oracle_settings` table for user preferences
  - API endpoints will read/write these columns
- **Session 6 (Framework Bridge)** depends on:
  - All `oracle_users` columns mapping to framework parameters — this session ensures that mapping is complete
  - `oracle_readings` columns for storing framework output metadata (version, mode, system)
- **Session 7 (Reading Types)** depends on:
  - `oracle_daily_readings` table for daily reading storage
  - `oracle_settings.daily_reading_enabled` flag for cron control
