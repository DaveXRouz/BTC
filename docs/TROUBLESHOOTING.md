# NPS Troubleshooting Guide

## Database Issues

### "relation 'oracle_users' does not exist"

The schema hasn't been applied. Run:

```bash
docker compose exec postgres psql -U nps -d nps -f /docker-entrypoint-initdb.d/init.sql
```

### "column 'deleted_at' does not exist"

Your schema is outdated (pre-S2). Re-run init.sql — it now includes the `deleted_at` column.

### "check constraint oracle_readings_sign_type_check violated"

Your schema has the old constraint. The S2 fix expanded it to include `'reading'`, `'multi_user'`, and `'daily'`. Re-run init.sql.

### "check constraint oracle_readings_user_check violated"

Your schema has the old constraint requiring `user_id IS NOT NULL` for single-user readings. The S2 fix relaxes this to allow anonymous readings. Re-run init.sql.

### Connection refused on port 5432

PostgreSQL isn't running:

```bash
docker compose up -d postgres
# Verify: docker compose ps
```

### "password authentication failed"

Check `POSTGRES_PASSWORD` in `.env` matches what was used when creating the database.

## Encryption Issues

### "ENC4: prefix not found"

Encryption is optional. If `NPS_ENCRYPTION_KEY` is not set, data is stored in plaintext. To enable:

```bash
# Generate keys
python3 -c "import secrets; print(secrets.token_hex(32))"
# Add to .env:
# NPS_ENCRYPTION_KEY=<generated_key>
# NPS_ENCRYPTION_SALT=<generated_salt>
```

### "Failed to decrypt field"

The encryption key has changed since the data was written. You need the original key to decrypt existing data. Legacy data uses `ENC:` prefix (PBKDF2), current uses `ENC4:` prefix (AES-256-GCM).

## CORS Issues

### "Access-Control-Allow-Origin" errors in browser

Add your frontend URL to `API_CORS_ORIGINS` in `.env`:

```bash
API_CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://your-domain.com
```

### Preflight (OPTIONS) requests failing

Ensure the API server is handling CORS middleware correctly. Check FastAPI CORS configuration in `api/app/main.py`.

## Import Errors

### "ModuleNotFoundError: No module named 'engines'"

The legacy engine import path isn't configured. The API uses a sys.path shim. Ensure:

1. `services/oracle/oracle_service/engines/` directory exists
2. `__init__.py` files exist in all intermediate directories

### "ModuleNotFoundError: No module named 'oracle_service'"

Same issue — the path shim in `oracle_reading.py` needs the oracle service directory structure.

## API Issues

### 401 Unauthorized on all endpoints

Check your auth token:

```bash
# Using legacy auth (from .env)
curl -H "Authorization: Bearer YOUR_API_SECRET_KEY" http://localhost:8000/api/oracle/users
```

### 403 Forbidden

Your token is valid but lacks the required scope. Legacy API_SECRET_KEY grants admin (all scopes). JWT tokens and API keys may have limited scopes.

### 422 Validation Error

Request body doesn't match the Pydantic model. Check the Swagger docs at `/docs` for the expected format.

### 500 Internal Server Error

Check API logs:

```bash
docker compose logs api --tail 50
# Or for local development:
# The uvicorn console output shows the traceback
```

## Frontend Issues

### Blank page at localhost:5173

1. Check Vite dev server is running: `cd frontend && npm run dev`
2. Check browser console for errors
3. Verify API proxy in `vite.config.ts` points to correct API URL

### API calls failing from frontend

The Vite dev server proxies `/api` requests to the API server. Ensure:

1. API is running on port 8000
2. `vite.config.ts` has the proxy configured
3. No CORS issues (check browser console)

## Redis Issues

### "Redis connection refused"

Redis is optional. The app degrades gracefully without it. To start:

```bash
docker compose up -d redis
```

### Redis not caching

Redis caching is connected but currently unused (reserved for future phases).

## Performance Issues

### Slow readings (> 5 seconds)

Legacy engines are pure Python computation. For the Oracle reading endpoint:

- FC60 encoding: ~10ms
- Numerology: ~5ms
- Oracle interpretation: ~50ms
- DB write: ~20ms

If consistently slow, check:

1. Database connection pool exhaustion
2. Network latency to PostgreSQL
3. Disk I/O on the DB server

### Run performance audit

```bash
python3 integration/scripts/perf_audit.py
```

## Common Patterns

### Fresh install workflow

```bash
cp .env.example .env
# Edit .env
docker compose up -d postgres redis
docker compose exec postgres psql -U nps -d nps -f /docker-entrypoint-initdb.d/init.sql
cd api && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000 &
cd ../frontend && npm install && npm run dev
```

### Reset database

```bash
docker compose exec postgres psql -U nps -d nps -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec postgres psql -U nps -d nps -f /docker-entrypoint-initdb.d/init.sql
```

### Check integration health

```bash
python3 integration/scripts/validate_env.py
```
