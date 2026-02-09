# RECIPES.md — Common Task Step-by-Step

> Step-by-step instructions for tasks that come up repeatedly.
> Follow these exactly to maintain consistency across the project.

---

## Recipe 1: Add a New API Endpoint

**When:** You need a new REST endpoint in FastAPI.

### Steps:

1. **Define the Pydantic models** (request + response):

   ```
   api/app/models/[feature].py
   ```

   - Request model with validation
   - Response model with example values
   - Add to `api/app/models/__init__.py` exports

2. **Create the router**:

   ```
   api/app/routers/[feature].py
   ```

   - Import models
   - Add auth dependency: `Depends(get_current_user)`
   - Add proper HTTP status codes
   - Add OpenAPI tags and descriptions

3. **Register the router** in `api/app/main.py`:

   ```python
   from app.routers import feature
   app.include_router(feature.router, prefix="/api", tags=["feature"])
   ```

4. **Add service logic** (if complex):

   ```
   api/app/services/[feature]_service.py
   ```

5. **Write tests**:

   ```
   api/tests/test_[feature].py
   ```

   - Test success case (200)
   - Test validation failure (422)
   - Test auth failure (401)
   - Test not found (404)

6. **Run verification**:

   ```bash
   cd api && python3 -m pytest tests/test_[feature].py -v
   curl http://localhost:8000/docs  # Check Swagger
   ```

7. **Update frontend API client** (if frontend needs this endpoint):
   ```
   frontend/src/services/api.ts
   ```

---

## Recipe 2: Add a New React Component

**When:** You need a new UI component.

### Steps:

1. **Create the component**:

   ```
   frontend/src/components/[folder]/[ComponentName].tsx
   ```

   - Follow template from `.claude/templates.md`
   - Include `useTranslation()` for any text
   - Support RTL with `dir` attribute
   - Use Tailwind classes

2. **Add translations**:

   ```
   frontend/src/locales/en.json  → add English strings
   frontend/src/locales/fa.json  → add Persian strings
   ```

3. **Add TypeScript types** (if new data shapes):

   ```
   frontend/src/types/index.ts
   ```

4. **Write tests**:

   ```
   frontend/src/components/[folder]/__tests__/[ComponentName].test.tsx
   ```

   - Render test
   - Interaction test
   - RTL test (if applicable)

5. **Run verification**:
   ```bash
   cd frontend && npm test -- --run [ComponentName]
   cd frontend && npm run build  # No type errors
   ```

---

## Recipe 3: Add a New Oracle Engine

**When:** You need a new calculation engine (e.g., new numerology system).

### Steps:

1. **Check legacy reference** (if engine existed in legacy version):

   ```
   .archive/v3/engines/[engine_name].py
   ```

   - Note all functions and their outputs
   - Create test vectors from legacy output

2. **Create the engine**:

   ```
   services/oracle/oracle_service/engines/[engine_name].py
   ```

   - Follow Python template from `.claude/templates.md`
   - Zero external dependencies (pure Python preferred)
   - Type hints on everything
   - Docstrings with math formulas

3. **Write comprehensive tests**:

   ```
   services/oracle/tests/test_[engine_name].py
   ```

   - Test all public functions
   - Test with legacy test vectors (output must match exactly)
   - Test edge cases (zero, negative, very large numbers)
   - Test Persian input (if applicable)

4. **Add to engine registry** (if the oracle service has one):

   ```
   services/oracle/oracle_service/engines/__init__.py
   ```

5. **Run verification**:

   ```bash
   cd services/oracle && python3 -m pytest tests/test_[engine_name].py -v
   ```

6. **Update algorithm documentation**:
   ```
   logic/[ALGORITHM_NAME].md  # or update existing doc
   ```

---

## Recipe 4: Add a New Database Table

**When:** You need to store new data in PostgreSQL.

### Steps:

1. **Design the schema** — think about:
   - Primary key (UUID or serial?)
   - Foreign keys (which tables?)
   - Indexes (what queries will run?)
   - Constraints (NOT NULL, CHECK, UNIQUE)
   - Timestamps (created_at, updated_at)
   - Soft delete (deleted_at TIMESTAMPTZ?)

2. **Create migration file**:

   ```
   database/migrations/[NNN]_[description].sql
   ```

   - Wrap in BEGIN/COMMIT
   - Add indexes
   - Add verification query comment

3. **Create rollback file**:

   ```
   database/migrations/[NNN]_[description]_rollback.sql
   ```

4. **Add schema file** (for reference):

   ```
   database/schemas/[table_name].sql
   ```

5. **Create ORM model**:

   ```
   api/app/orm/[table_name].py
   ```

   - SQLAlchemy model matching the schema exactly
   - Add to `api/app/orm/__init__.py`

6. **Create Pydantic model** (for API):

   ```
   api/app/models/[feature].py
   ```

   - Request model (what API accepts)
   - Response model (what API returns)
   - Don't expose internal fields (encrypted data, hashes)

7. **Run migration**:

   ```bash
   docker-compose exec postgres psql -U nps -d nps -f /path/to/migration.sql
   ```

8. **Write tests**:

   ```
   integration/tests/test_database.py  # Add tests for new table
   ```

   - Test INSERT
   - Test SELECT with index
   - Test constraints (violate them, expect errors)
   - Test rollback migration

---

## Recipe 5: Add Translation Support to a Feature

**When:** A feature needs English + Persian text.

### Steps:

1. **Add English strings**:

   ```
   frontend/src/locales/en.json
   ```

   ```json
   {
     "feature": {
       "title": "Feature Title",
       "description": "Feature description text",
       "button_submit": "Submit",
       "error_required": "This field is required"
     }
   }
   ```

2. **Add Persian strings**:

   ```
   frontend/src/locales/fa.json
   ```

   ```json
   {
     "feature": {
       "title": "عنوان ویژگی",
       "description": "متن توضیح ویژگی",
       "button_submit": "ارسال",
       "error_required": "این فیلد الزامی است"
     }
   }
   ```

3. **Use in component**:

   ```tsx
   const { t, i18n } = useTranslation();
   const isRTL = i18n.language === "fa";

   return (
     <div dir={isRTL ? "rtl" : "ltr"}>
       <h1>{t("feature.title")}</h1>
       <p>{t("feature.description")}</p>
     </div>
   );
   ```

4. **Handle Persian numbers** (if displaying numbers):

   ```tsx
   import { toPersianDigits } from "../utils/persianFormatter";

   const displayNum = isRTL ? toPersianDigits(count) : count;
   ```

5. **Test both languages**:
   ```tsx
   it("displays Persian text in FA mode", () => {
     // Mock i18n to return 'fa'
     // Verify RTL dir attribute
     // Verify Persian strings render
   });
   ```

---

## Recipe 6: Fix a Bug

**When:** Something is broken and needs fixing.

### Steps:

1. **Reproduce** — confirm the bug exists:

   ```bash
   # Run the failing test or replicate the issue
   ```

2. **Write a failing test** that captures the bug:

   ```python
   def test_bug_description():
       """Regression test for [bug description]."""
       result = broken_function(trigger_input)
       assert result == expected  # This should FAIL before fix
   ```

3. **Find the root cause** — read the code, add debug logging if needed

4. **Fix the code** — minimal change that fixes the issue

5. **Verify the test passes**:

   ```bash
   pytest test_file.py::test_bug_description -v
   ```

6. **Run ALL tests** — make sure fix didn't break anything:

   ```bash
   make test
   ```

7. **Commit** with message: `[layer] fix: description of bug (#session)`

---

## Recipe 7: Add a New Reading Type (Oracle)

**When:** Adding one of the 5 reading types (Time, Name, Question, Daily, Multi-user).

### Steps:

1. **Define the reading flow**:
   - What inputs are needed?
   - Which engines are used? (FC60, numerology, zodiac)
   - What calculations produce the reading?
   - What does the AI interpretation prompt look like?

2. **Create/update Oracle engine code**:

   ```
   services/oracle/oracle_service/engines/[reading_type].py
   ```

3. **Create/update solver**:

   ```
   services/oracle/oracle_service/solvers/[reading_type]_solver.py
   ```

4. **Add API endpoint**:
   - Model: `api/app/models/oracle.py` (add request/response)
   - Router: `api/app/routers/oracle.py` (add route)
   - Service: `api/app/services/oracle_reading.py` (add logic)

5. **Add frontend form + results display**:
   - Form: `frontend/src/components/oracle/[ReadingType]Form.tsx`
   - Results: integrated into `ReadingResults.tsx`
   - Translations: both `en.json` and `fa.json`

6. **Write tests at every layer**:
   - Engine tests (math verification)
   - API tests (endpoint + validation)
   - Frontend tests (form + display)
   - Integration test (end-to-end flow)

7. **Verify against legacy** (if reading type existed):
   - Same inputs → same calculation outputs
   - AI interpretation can differ (improved), but math must match

---

## Recipe 8: Deploy to Production

**When:** Ready to deploy a version.

### Steps:

1. **Run production readiness check**:

   ```bash
   ./scripts/production_readiness_check.sh
   ```

2. **Run full test suite**:

   ```bash
   make test
   python3 -m pytest integration/tests/ -v -s
   cd frontend && npx playwright test
   ```

3. **Run security audit**:

   ```bash
   python3 integration/scripts/security_audit.py
   pip-audit
   npm audit
   ```

4. **Run performance audit**:

   ```bash
   python3 integration/scripts/perf_audit.py
   ```

5. **Build production images**:

   ```bash
   docker-compose build
   docker-compose up -d
   docker-compose ps  # All services "healthy"
   ```

6. **Verify live**:

   ```bash
   curl http://localhost:8000/api/health
   curl http://localhost:5173  # Frontend loads
   ```

7. **Backup current database** (before deploying schema changes):

   ```bash
   make backup
   ```

8. **Tag the release**:
   ```bash
   git tag v4.X.Y -m "Release description"
   git push origin v4.X.Y
   ```
