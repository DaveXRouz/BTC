# ERROR RECOVERY PLAYBOOK - NPS V4

## 🎯 PURPOSE

This playbook provides systematic approaches to debugging and recovering from errors across all NPS V4 layers. When something breaks, follow these patterns.

**Rule:** Don't guess. Follow the systematic debugging process.

---

## 🚨 GENERAL ERROR RECOVERY PROCESS

### Step 1: IDENTIFY (What broke?)

```
1. Read error message completely
2. Identify which layer failed
   - Frontend error → Layer 1
   - API error → Layer 2
   - Service error → Layer 3
   - Database error → Layer 4
   - Docker error → Layer 5
   - Auth/encryption error → Layer 6
   - Monitoring error → Layer 7

3. Determine error severity
   - CRITICAL: System down, data loss risk
   - HIGH: Feature broken, affects users
   - MEDIUM: Degraded performance
   - LOW: Non-critical issue
```

---

### Step 2: ISOLATE (Where exactly?)

```
1. Reproduce error consistently
   - Document exact steps to reproduce
   - Note any environmental factors

2. Create minimal reproduction
   - Strip away unrelated code
   - Reduce to smallest failing case

3. Check dependencies
   - Is this layer's dependencies healthy?
   - Test each dependency independently
```

---

### Step 3: DIAGNOSE (Why did it break?)

```
1. Check logs (JSON format)
   - ERROR level messages
   - Stack traces
   - Recent changes before error

2. Use extended_thinking
   - Analyze root cause
   - Consider multiple hypotheses
   - Rule out unlikely causes

3. Search conversation history
   - conversation_search("error message")
   - Has this happened before?
   - How was it fixed last time?
```

---

### Step 4: FIX (How to resolve?)

```
1. Implement minimal fix
   - Don't refactor while fixing
   - One change at a time
   - Test after each change

2. Verify fix works
   - Run all relevant tests
   - Check no new errors introduced
   - Verify performance unchanged

3. Document root cause
   - Add comment explaining fix
   - Update this playbook if new pattern
```

---

### Step 5: PREVENT (How to avoid future?)

```
1. Add test for this error
   - Regression test
   - Edge case coverage

2. Update documentation
   - Known issues section
   - Troubleshooting guide

3. Consider architecture improvement
   - Can we make this impossible?
   - Better error handling?
```

---

## 🛠️ LAYER-SPECIFIC ERROR PATTERNS

### LAYER 1: FRONTEND ERRORS

#### Error: Component won't render

**Symptoms:**
- Blank page
- Console error: "Cannot read property 'X' of undefined"

**Diagnosis:**
```bash
# Check browser console
F12 → Console tab

# Look for:
- Missing imports
- Undefined props
- State initialization issues
```

**Common Causes:**
1. **Props not passed from parent**
   ```typescript
   // BAD: Parent doesn't pass required prop
   <Dashboard />  // Missing 'data' prop
   
   // GOOD:
   <Dashboard data={data} />
   ```

2. **State not initialized**
   ```typescript
   // BAD: undefined initial state
   const [data, setData] = useState();
   
   // GOOD:
   const [data, setData] = useState<DataType | null>(null);
   ```

3. **Async data not handled**
   ```typescript
   // BAD: Renders before data loads
   return <div>{data.name}</div>
   
   // GOOD:
   if (!data) return <Loading />;
   return <div>{data.name}</div>;
   ```

**Fix:**
```bash
1. Add null checks
2. Initialize state properly
3. Handle loading states
4. Test with React DevTools
```

---

#### Error: API calls failing

**Symptoms:**
- Network errors in console
- CORS errors
- 401/403 responses

**Diagnosis:**
```bash
# Check Network tab
F12 → Network tab → Filter: XHR

# Look for:
- Request URL (correct?)
- Request headers (API key included?)
- Response status (what error code?)
```

**Common Causes:**
1. **Missing API key**
   ```typescript
   // BAD: No Authorization header
   fetch('/api/scanner/start')
   
   // GOOD:
   fetch('/api/scanner/start', {
     headers: { 'Authorization': `Bearer ${apiKey}` }
   })
   ```

2. **Wrong base URL**
   ```typescript
   // BAD: Hardcoded localhost
   const API_URL = 'http://localhost:8000';
   
   // GOOD: Environment variable
   const API_URL = import.meta.env.VITE_API_URL;
   ```

3. **CORS not configured**
   ```python
   # In FastAPI (Layer 2)
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

**Fix:**
```bash
1. Verify API is running (curl http://localhost:8000/api/health)
2. Check API key in request headers
3. Add CORS middleware (Layer 2)
4. Test with curl first, then browser
```

---

### LAYER 2: API ERRORS

#### Error: 500 Internal Server Error

**Symptoms:**
- API returns 500
- No specific error message

**Diagnosis:**
```bash
# Check API logs
tail -f volumes/logs/api.log | jq .

# Look for:
- Exception stack traces
- Database errors
- Validation failures
```

**Common Causes:**
1. **Unhandled exception**
   ```python
   # BAD: No error handling
   @app.get("/api/scanner/stats")
   async def get_stats():
       stats = db.query(...)  # Could fail
       return stats
   
   # GOOD:
   @app.get("/api/scanner/stats")
   async def get_stats():
       try:
           stats = db.query(...)
           return stats
       except SQLAlchemyError as e:
           logger.error("Database query failed", exc_info=True)
           raise HTTPException(status_code=500, detail="Internal server error")
   ```

2. **Database connection failed**
   ```python
   # Check database connection
   from sqlalchemy import text
   
   try:
       db.execute(text("SELECT 1"))
   except Exception as e:
       logger.error(f"Database connection failed: {e}")
   ```

3. **Missing environment variable**
   ```python
   # BAD: No default, crashes if not set
   DATABASE_URL = os.environ["DATABASE_URL"]
   
   # GOOD: Explicit error
   DATABASE_URL = os.environ.get("DATABASE_URL")
   if not DATABASE_URL:
       raise ValueError("DATABASE_URL environment variable not set")
   ```

**Fix:**
```bash
1. Add try/except around risky operations
2. Check database connection (psql -h localhost -U nps_user)
3. Verify environment variables loaded (printenv | grep NPS)
4. Add specific error responses (not just 500)
```

---

#### Error: 401 Unauthorized

**Symptoms:**
- All API calls return 401
- Even with valid API key

**Diagnosis:**
```bash
# Test API key manually
curl -H "Authorization: Bearer YOUR_KEY" http://localhost:8000/api/health

# Check database
psql -c "SELECT * FROM api_keys;"
```

**Common Causes:**
1. **API key not in database**
   ```bash
   # Generate new key
   python security/scripts/generate_api_key.py --name "Test" --scopes admin
   ```

2. **Wrong key hash algorithm**
   ```python
   # Ensure both generation and validation use same algorithm
   import hashlib
   key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
   ```

3. **Middleware not applied**
   ```python
   # Ensure auth middleware is in endpoint
   from app.security.auth import validate_api_key
   
   @app.get("/api/scanner/start", dependencies=[Depends(validate_api_key)])
   ```

**Fix:**
```bash
1. Verify key exists in database
2. Check key_hash generation matches validation
3. Apply auth middleware to all protected endpoints
4. Test with known-good key
```

---

### LAYER 3: BACKEND SERVICE ERRORS

#### Error: Scanner service crash

**Symptoms:**
- Scanner service exits unexpectedly
- No keys generated

**Diagnosis:**
```bash
# Check scanner logs
docker logs nps-scanner

# Check for:
- Panic messages
- Connection errors
- Resource exhaustion
```

**Common Causes:**
1. **Database connection pool exhausted**
   ```rust
   // Increase pool size
   let pool = PgPoolOptions::new()
       .max_connections(20)  // Increase from default 5
       .connect(&database_url)
       .await?;
   ```

2. **Unwrap on None/Err**
   ```rust
   // BAD: Panics if Oracle not available
   let guidance = oracle_client.get_suggestion().unwrap();
   
   // GOOD: Handle gracefully
   let guidance = match oracle_client.get_suggestion().await {
       Ok(g) => Some(g),
       Err(e) => {
           warn!("Oracle unavailable: {}", e);
           None
       }
   };
   ```

3. **Memory leak**
   ```bash
   # Monitor memory usage
   docker stats nps-scanner
   
   # If memory grows unbounded:
   # Check for:
   # - Unclosed database connections
   # - Growing vectors without bounds
   # - Leaked file handles
   ```

**Fix:**
```bash
1. Add Result<T,E> error handling (no unwrap)
2. Increase connection pool size
3. Profile memory usage (valgrind, heaptrack)
4. Add graceful degradation (Oracle unavailable → continue with random)
```

---

#### Error: Oracle service timeout

**Symptoms:**
- Oracle service doesn't respond
- API calls to Oracle hang

**Diagnosis:**
```bash
# Check Oracle logs
docker logs nps-oracle

# Check for:
- AI API timeouts
- Database query hangs
- Deadlocks
```

**Common Causes:**
1. **AI API call hanging**
   ```python
   # BAD: No timeout
   response = await anthropic_client.messages.create(...)
   
   # GOOD: Add timeout
   import asyncio
   
   try:
       response = await asyncio.wait_for(
           anthropic_client.messages.create(...),
           timeout=30.0
       )
   except asyncio.TimeoutError:
       logger.error("AI API call timed out")
       raise HTTPException(status_code=504, detail="Oracle timeout")
   ```

2. **Database query too slow**
   ```bash
   # Check slow queries
   psql -c "SELECT query, mean_exec_time FROM pg_stat_statements WHERE mean_exec_time > 1000 ORDER BY mean_exec_time DESC LIMIT 10;"
   
   # Add indexes if needed
   ```

3. **Deadlock**
   ```python
   # Check for deadlocks
   # In PostgreSQL logs, look for:
   # "deadlock detected"
   
   # Fix by:
   # - Consistent lock ordering
   # - Shorter transactions
   ```

**Fix:**
```bash
1. Add timeouts to all external calls
2. Optimize slow database queries
3. Use connection pooling properly
4. Add circuit breaker for failing services
```

---

### LAYER 4: DATABASE ERRORS

#### Error: Connection refused

**Symptoms:**
- Can't connect to PostgreSQL
- "Connection refused" error

**Diagnosis:**
```bash
# Is PostgreSQL running?
docker-compose ps postgres

# Can you connect locally?
psql -h localhost -U nps_user -d nps_db

# Check network
docker network ls
docker network inspect nps-network
```

**Common Causes:**
1. **PostgreSQL not started**
   ```bash
   docker-compose up -d postgres
   ```

2. **Wrong connection string**
   ```python
   # BAD: Wrong host
   DATABASE_URL = "postgresql://nps_user:password@localhost:5432/nps_db"
   
   # GOOD: Docker service name
   DATABASE_URL = "postgresql://nps_user:password@postgres:5432/nps_db"
   ```

3. **Port not exposed**
   ```yaml
   # In docker-compose.yml
   postgres:
     ports:
       - "5432:5432"  # Make sure this is present
   ```

**Fix:**
```bash
1. Start PostgreSQL (docker-compose up -d postgres)
2. Fix connection string (use service name, not localhost)
3. Check port mapping in docker-compose.yml
4. Test connection: psql -h localhost -U nps_user -d nps_db
```

---

#### Error: Query timeout

**Symptoms:**
- Queries take >10 seconds
- Application hangs

**Diagnosis:**
```bash
# Check active queries
psql -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"

# Check locks
psql -c "SELECT * FROM pg_locks WHERE NOT granted;"

# Explain query plan
psql -c "EXPLAIN ANALYZE YOUR_QUERY;"
```

**Common Causes:**
1. **Missing index**
   ```sql
   -- Check if query uses indexes
   EXPLAIN ANALYZE SELECT * FROM findings WHERE chain = 'btc';
   
   -- If sequential scan, add index
   CREATE INDEX idx_findings_chain ON findings(chain);
   ```

2. **Table bloat (needs vacuum)**
   ```bash
   # Run vacuum
   psql -c "VACUUM ANALYZE findings;"
   
   # Set up automatic vacuum
   ALTER TABLE findings SET (autovacuum_enabled = true);
   ```

3. **Too many rows returned**
   ```python
   # BAD: No limit
   findings = db.query(Finding).all()
   
   # GOOD: Paginate
   findings = db.query(Finding).limit(100).offset(page * 100).all()
   ```

**Fix:**
```bash
1. Add indexes for common query patterns
2. Run VACUUM ANALYZE regularly
3. Add pagination to all list queries
4. Use EXPLAIN ANALYZE to verify query plans
```

---

### LAYER 5: INFRASTRUCTURE ERRORS

#### Error: Container won't start

**Symptoms:**
- `docker-compose up` fails
- Container exits immediately

**Diagnosis:**
```bash
# Check container logs
docker-compose logs [service-name]

# Check container status
docker-compose ps

# Inspect container
docker inspect nps-api
```

**Common Causes:**
1. **Dependency not ready**
   ```yaml
   # BAD: No health check
   api:
     depends_on:
       - postgres
   
   # GOOD: Wait for healthy
   api:
     depends_on:
       postgres:
         condition: service_healthy
   ```

2. **Environment variable missing**
   ```bash
   # Check .env file exists
   ls -la .env
   
   # Check variables loaded
   docker-compose config | grep DATABASE_URL
   ```

3. **Port already in use**
   ```bash
   # Find process using port
   lsof -i :8000
   
   # Kill process or change port
   ```

**Fix:**
```bash
1. Add health checks to dependencies
2. Verify .env file present and correct
3. Change conflicting ports
4. Check Dockerfile CMD/ENTRYPOINT syntax
```

---

#### Error: Services can't communicate

**Symptoms:**
- API can't reach Scanner/Oracle
- "Connection refused" between services

**Diagnosis:**
```bash
# Check network
docker network ls
docker network inspect nps-network

# Test connectivity
docker exec nps-api ping scanner
docker exec nps-api curl http://scanner:50051/health
```

**Common Causes:**
1. **Not on same network**
   ```yaml
   # All services must be on same network
   services:
     api:
       networks:
         - nps-network
     scanner:
       networks:
         - nps-network
   
   networks:
     nps-network:
       driver: bridge
   ```

2. **Wrong service name**
   ```python
   # BAD: Using localhost
   SCANNER_URL = "http://localhost:50051"
   
   # GOOD: Using service name
   SCANNER_URL = "http://scanner:50051"
   ```

3. **Port not exposed internally**
   ```yaml
   # Expose port to other services (no need to publish)
   scanner:
     expose:
       - "50051"
   ```

**Fix:**
```bash
1. Ensure all services on same Docker network
2. Use service names (not localhost) in inter-service calls
3. Expose ports with 'expose' (not 'ports' unless external access needed)
```

---

### LAYER 6: SECURITY ERRORS

#### Error: Encryption/decryption fails

**Symptoms:**
- Can't decrypt private keys
- "Invalid padding" error

**Diagnosis:**
```bash
# Check encryption key
printenv NPS_MASTER_PASSWORD

# Test encryption roundtrip
python -c "from security.encryption import encrypt_dict, decrypt_dict; data = {'key': 'value'}; encrypted = encrypt_dict(data, 'password'); print(decrypt_dict(encrypted, 'password'))"
```

**Common Causes:**
1. **Wrong password used**
   ```python
   # Encryption and decryption must use same password
   encrypted = encrypt_dict(data, password1)
   decrypted = decrypt_dict(encrypted, password2)  # WRONG PASSWORD
   ```

2. **Password changed**
   ```bash
   # If master password changed, re-encrypt all data
   python security/scripts/rotate_master_key.py \
     --old-password "old" \
     --new-password "new"
   ```

3. **Encryption library version mismatch**
   ```bash
   # Check cryptography version
   pip list | grep cryptography
   
   # Ensure same version on all instances
   ```

**Fix:**
```bash
1. Verify master password consistent across all services
2. If password changed, run key rotation script
3. Pin cryptography library version in requirements.txt
4. Test encryption roundtrip in CI/CD
```

---

### LAYER 7: MONITORING ERRORS

#### Error: Health checks failing

**Symptoms:**
- Dashboard shows services "down"
- But services appear to work

**Diagnosis:**
```bash
# Test health endpoints manually
curl http://localhost:8000/api/health
curl http://scanner:50051/health
curl http://oracle:50052/health

# Check health check timeout
python -c "import time; import requests; start = time.time(); requests.get('http://localhost:8000/api/health'); print(f'{time.time() - start}s')"
```

**Common Causes:**
1. **Timeout too short**
   ```python
   # BAD: 1s timeout
   response = requests.get(url, timeout=1)
   
   # GOOD: 5s timeout
   response = requests.get(url, timeout=5)
   ```

2. **Health check calls external service**
   ```python
   # BAD: Health check depends on external API
   @app.get("/health")
   async def health():
       claude_api_status = await check_claude_api()  # Could fail
       return {"status": "healthy" if claude_api_status else "down"}
   
   # GOOD: Health check only checks internal state
   @app.get("/health")
   async def health():
       db_ok = await check_database()
       return {"status": "healthy" if db_ok else "degraded"}
   ```

3. **Race condition on startup**
   ```yaml
   # Health check runs before service ready
   # Add interval + retries
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
     interval: 10s
     timeout: 5s
     retries: 5
     start_period: 30s  # Wait 30s before first check
   ```

**Fix:**
```bash
1. Increase health check timeout
2. Health checks should only check critical internal state
3. Add start_period to allow service initialization
4. Log all health check failures for debugging
```

---

## 🔄 ERROR RECOVERY TEMPLATES

### Template 1: Service Won't Start

```markdown
## SERVICE WON'T START

**Service:** [service-name]
**Error:** [error message]

**Diagnosis:**
1. Check logs: `docker-compose logs [service-name]`
2. Check dependencies: Are required services healthy?
3. Check environment: Are env vars loaded?

**Common Fixes:**
- [ ] Dependency not healthy → Add health check + wait
- [ ] Env var missing → Check .env file
- [ ] Port conflict → Change port or kill process
- [ ] Syntax error → Check Dockerfile/docker-compose.yml

**Resolution:**
[Document what actually fixed it]
```

---

### Template 2: Performance Degradation

```markdown
## PERFORMANCE DEGRADATION

**Component:** [component-name]
**Metric:** [metric-name] (current: X, target: Y)

**Diagnosis:**
1. Profile: [tool used, results]
2. Bottleneck: [identified bottleneck]
3. Resource usage: CPU/Memory/Disk

**Common Fixes:**
- [ ] Database query slow → Add index, optimize query
- [ ] Memory leak → Fix leaked resources
- [ ] CPU-bound → Parallelize or optimize algorithm
- [ ] I/O-bound → Add caching, use async

**Resolution:**
[Document optimization + benchmark results]
```

---

### Template 3: Data Inconsistency

```markdown
## DATA INCONSISTENCY

**Symptom:** [describe inconsistency]
**Tables affected:** [table names]

**Diagnosis:**
1. Check constraints: `psql -c "\d+ table_name"`
2. Find orphaned records: [query used]
3. Transaction isolation: [check current level]

**Common Fixes:**
- [ ] Missing foreign key → Add constraint + clean data
- [ ] Race condition → Use transaction isolation
- [ ] Concurrent updates → Add optimistic locking
- [ ] Migration error → Rollback + fix migration

**Resolution:**
[Document fix + data cleanup steps]
```

---

## 📊 ERROR PRIORITY MATRIX

| Severity | Impact | Response Time | Escalation |
|----------|--------|---------------|------------|
| **CRITICAL** | System down, data loss risk | Immediate | Wake up team |
| **HIGH** | Feature broken, affects users | <1 hour | Notify lead |
| **MEDIUM** | Degraded performance | <4 hours | Fix in sprint |
| **LOW** | Non-critical issue | <1 day | Backlog |

---

## 🎯 PREVENTION CHECKLIST

After fixing any error:

- [ ] Added test to prevent regression
- [ ] Updated relevant playbook with new pattern
- [ ] Documented root cause in code comments
- [ ] Checked for similar issues elsewhere
- [ ] Improved error messages for future diagnosis
- [ ] Added monitoring/alerting if applicable
- [ ] Reviewed architecture to prevent class of errors

---

**Remember:** Every error is a learning opportunity. Document it well. 🚀

*Version: 1.0*  
*Last Updated: 2026-02-08*
