# VERIFICATION CHECKLISTS - NPS V4

## 🎯 PURPOSE

This document provides layer-specific verification checklists. Every deliverable MUST pass its checklist before being considered "done."

**Rule:** No task is complete without verified checklist.

---

## ✅ UNIVERSAL CHECKLIST (ALL LAYERS)

**EVERY deliverable must pass these baseline checks:**

### Code Quality
- [ ] Type hints (Python) / Types (TypeScript/Rust) present
- [ ] Docstrings/comments for non-obvious logic
- [ ] Error handling explicit (no bare except, uses Result<T,E> in Rust)
- [ ] Logging present (JSON format, appropriate levels)
- [ ] No hardcoded values (uses config/env vars)
- [ ] No TODO comments without issue tracking
- [ ] No dead code (unused imports, functions)

### Testing
- [ ] Unit tests exist for new code
- [ ] All tests pass (100% for new code)
- [ ] Coverage target met (layer-specific below)
- [ ] Integration tests for cross-component features
- [ ] Performance tests for critical paths

### Documentation
- [ ] README updated (if user-facing feature)
- [ ] API documentation complete (endpoints, parameters)
- [ ] Comments explain "why" not "what"
- [ ] Example usage provided
- [ ] Verification steps included in deliverable

### Architecture Alignment
- [ ] Follows layer separation (no cross-layer violations)
- [ ] Uses correct communication patterns (API → gRPC → Services)
- [ ] Security requirements met
- [ ] Performance targets met (see architecture plan)
- [ ] No breaking changes (or migration path documented)

### User Preferences
- [ ] Simple, clear language (no unexplained jargon)
- [ ] Measurable acceptance criteria (with numbers)
- [ ] Concrete next steps (not vague)
- [ ] 2-minute verification provided
- [ ] Swiss watch quality (robust, simple, elegant)

---

## 📋 LAYER 1: FRONTEND VERIFICATION

### React Component Checklist

**TypeScript:**
- [ ] Props typed with interface/type
- [ ] State typed (no `any` types)
- [ ] Event handlers typed
- [ ] Imports organized (React, libraries, local)

**Functionality:**
- [ ] Component renders without errors
- [ ] Props passed correctly from parent
- [ ] State updates work as expected
- [ ] Event handlers fire correctly
- [ ] Side effects cleaned up (useEffect return)

**Styling:**
- [ ] Responsive design (desktop + tablet + mobile)
- [ ] Dark theme applied (matches V3 aesthetic)
- [ ] Accessibility: WCAG 2.1 AA minimum
- [ ] Loading states displayed
- [ ] Error states handled gracefully

**Integration:**
- [ ] API calls work (error handling included)
- [ ] WebSocket updates received
- [ ] Real-time data displays correctly
- [ ] No console errors
- [ ] No console warnings (except known issues)

**Testing:**
- [ ] Component tests pass (React Testing Library)
- [ ] Coverage ≥90%
- [ ] Snapshot tests updated
- [ ] User interactions tested
- [ ] Edge cases covered

**Performance:**
- [ ] Initial load <2s
- [ ] Page transitions <100ms
- [ ] No unnecessary re-renders
- [ ] Images optimized
- [ ] Bundle size reasonable (<500KB for page)

**Verification Commands:**
```bash
cd frontend/web-ui
npm test                          # All tests pass
npm run build                     # Production build succeeds
npm run lint                      # No linting errors
npm run type-check                # No TypeScript errors
lighthouse http://localhost:5173  # Performance >90
```

---

## 📋 LAYER 2: API VERIFICATION

### FastAPI Endpoint Checklist

**Code Quality:**
- [ ] Pydantic request model defined
- [ ] Pydantic response model defined
- [ ] Type hints on all function parameters
- [ ] Docstrings for endpoint (OpenAPI description)
- [ ] Async/await used correctly

**Authentication:**
- [ ] API key required (@depends)
- [ ] Correct scope checked
- [ ] 401 returned for invalid/missing key
- [ ] 403 returned for insufficient permissions

**Error Handling:**
- [ ] HTTPException used for expected errors
- [ ] Proper status codes (400, 404, 500, etc.)
- [ ] Error messages user-friendly
- [ ] Unexpected errors caught and logged
- [ ] No sensitive data in error responses

**Business Logic:**
- [ ] Input validation complete
- [ ] Database queries parameterized (no SQL injection)
- [ ] Business rules enforced
- [ ] Results paginated (if list endpoint)
- [ ] Results sorted consistently

**Performance:**
- [ ] Response time <50ms (p95)
- [ ] Database queries optimized (uses indexes)
- [ ] No N+1 query problems
- [ ] Appropriate use of async
- [ ] Connection pooling configured

**Documentation:**
- [ ] OpenAPI schema accurate
- [ ] Example request provided
- [ ] Example response provided
- [ ] Error codes documented
- [ ] Rate limits specified

**Testing:**
- [ ] Integration tests pass
- [ ] Coverage ≥95%
- [ ] Happy path tested
- [ ] Error cases tested (400, 401, 403, 404, 500)
- [ ] Edge cases tested (empty lists, large payloads)

**Verification Commands:**
```bash
cd api
pytest tests/ -v --cov           # 95%+ coverage
curl http://localhost:8000/docs  # Swagger UI loads
ab -n 1000 http://localhost:8000/api/health  # <50ms p95
mypy app/ --strict               # No type errors
```

---

## 📋 LAYER 3: BACKEND SERVICES VERIFICATION

### Scanner Service (Rust) Checklist

**Code Quality:**
- [ ] Result<T, E> used for all fallible operations
- [ ] No .unwrap() in production code
- [ ] Error types defined (using thiserror/anyhow)
- [ ] Logging present (using tracing/log)
- [ ] No unsafe code (or justified with safety comments)

**Functionality:**
- [ ] Key generation works (random + BIP39)
- [ ] Multi-chain balance checking works
- [ ] Findings stored in PostgreSQL
- [ ] gRPC server responds correctly
- [ ] Oracle guidance applied when present

**Performance:**
- [ ] Generates ≥5000 keys/second (single thread)
- [ ] Scales linearly with threads (tested with 4 threads)
- [ ] Memory usage stable (no leaks)
- [ ] No blocking operations on async runtime
- [ ] Batch database inserts used

**Testing:**
- [ ] Unit tests pass
- [ ] Coverage ≥80%
- [ ] Integration tests pass (with test database)
- [ ] Property-based tests for crypto (if applicable)
- [ ] Benchmarks run and results documented

**Security:**
- [ ] Private keys encrypted before database storage
- [ ] No keys logged (even in debug mode)
- [ ] Random number generator cryptographically secure
- [ ] Dependencies audited (cargo audit)

**Verification Commands:**
```bash
cd backend/scanner-service
cargo test                        # All tests pass
cargo bench                       # ≥5000 keys/sec
cargo clippy -- -D warnings       # No warnings
cargo audit                       # No vulnerabilities
```

---

### Oracle Service (Python) Checklist

**Code Quality:**
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] Error handling explicit
- [ ] Logging present (JSON format)
- [ ] V3 engines migrated correctly

**Functionality:**
- [ ] FC60 engine works
- [ ] Numerology engine works
- [ ] Oracle readings generate
- [ ] Pattern analysis returns suggestions
- [ ] AI integration (Claude CLI) works

**AI Integration:**
- [ ] Claude API calls succeed
- [ ] Error handling for API failures
- [ ] Rate limiting respected
- [ ] Token usage logged
- [ ] Fallback behavior defined

**Performance:**
- [ ] Pattern analysis <5s for 1000 findings
- [ ] AI calls don't block other operations
- [ ] Database queries optimized
- [ ] Caching used where appropriate

**Testing:**
- [ ] Unit tests pass
- [ ] Coverage ≥95%
- [ ] Mocked AI responses tested
- [ ] Real AI integration tested (if API key available)
- [ ] Edge cases covered

**Verification Commands:**
```bash
cd backend/oracle-service
pytest tests/ -v --cov            # 95%+ coverage
mypy app/ --strict                # No type errors
python app/main.py analyze-patterns  # Returns valid suggestion
```

---

## 📋 LAYER 4: DATABASE VERIFICATION

### Schema Checklist

**Schema Design:**
- [ ] Primary keys defined
- [ ] Foreign keys defined
- [ ] NOT NULL constraints where appropriate
- [ ] CHECK constraints for business rules
- [ ] Default values sensible

**Indexes:**
- [ ] Primary key indexed (automatic)
- [ ] Foreign keys indexed
- [ ] Common query columns indexed
- [ ] Composite indexes for multi-column queries
- [ ] No over-indexing (impacts write performance)

**Performance:**
- [ ] Queries use indexes (verified with EXPLAIN ANALYZE)
- [ ] No sequential scans on large tables
- [ ] Partitioning used for findings table (monthly)
- [ ] Materialized views for expensive aggregates
- [ ] Vacuum/analyze scheduled

**Data Integrity:**
- [ ] Foreign key constraints enforced
- [ ] No orphaned records possible
- [ ] Cascade deletes configured correctly
- [ ] Triggers (if any) tested

**Migration:**
- [ ] Migration script runs without errors
- [ ] Migration is reversible (rollback script)
- [ ] Migration tested on copy of production data
- [ ] No data loss during migration

**Backup/Restore:**
- [ ] Backup script works
- [ ] Restore script works
- [ ] Backup tested on different machine
- [ ] Backup size reasonable
- [ ] Backup automated

**Verification Commands:**
```bash
cd database
psql -f migrations/001_initial_schema.sql  # Runs without errors
psql -c "EXPLAIN ANALYZE SELECT ..."       # Uses indexes
./scripts/backup.sh                        # Backup succeeds
./scripts/restore.sh                       # Restore succeeds
psql -c "SELECT pg_size_pretty(pg_database_size(current_database()));"  # Check size
```

---

## 📋 LAYER 5: INFRASTRUCTURE VERIFICATION

### Docker Checklist

**Dockerfile:**
- [ ] Multi-stage build used (for size)
- [ ] Base image pinned to specific version
- [ ] Security updates applied (apt update && upgrade)
- [ ] Non-root user used
- [ ] Only necessary files copied (use .dockerignore)
- [ ] Build succeeds

**docker-compose:**
- [ ] All services defined
- [ ] Dependencies specified (depends_on)
- [ ] Health checks configured
- [ ] Volumes for persistent data
- [ ] Networks configured
- [ ] Environment variables documented (.env.example)

**Deployment:**
- [ ] All services start (`docker-compose up -d`)
- [ ] All services healthy (`docker-compose ps`)
- [ ] Services can communicate
- [ ] Volumes persist data across restarts
- [ ] Environment variables loaded correctly

**Networking:**
- [ ] Services accessible from expected ports
- [ ] Internal services NOT exposed externally
- [ ] Reverse proxy configured (if using)
- [ ] SSL/TLS working (if production)

**Resource Management:**
- [ ] Memory limits set
- [ ] CPU limits set (if needed)
- [ ] No resource contention
- [ ] Logs rotated

**Verification Commands:**
```bash
cd infrastructure
docker-compose config              # Validates config
docker-compose build               # All images build
docker-compose up -d               # All services start
docker-compose ps                  # All "healthy"
curl http://localhost:8000/api/health  # API accessible
docker stats                       # Check resource usage
```

---

## 📋 LAYER 6: SECURITY VERIFICATION

### API Key System Checklist

**Key Generation:**
- [ ] Keys are cryptographically random
- [ ] Keys are long enough (≥32 bytes)
- [ ] Keys stored as hash (SHA-256 minimum)
- [ ] Original key shown only once
- [ ] Scopes assigned correctly

**Authentication:**
- [ ] Invalid key rejected (401)
- [ ] Expired key rejected (401)
- [ ] Insufficient scope rejected (403)
- [ ] Rate limiting applied
- [ ] Brute force protection (account lockout)

**Encryption:**
- [ ] Private keys encrypted (AES-256)
- [ ] Encryption keys stored securely (env vars, not code)
- [ ] No plaintext sensitive data in logs
- [ ] No plaintext sensitive data in database
- [ ] Encryption tested (encrypt → decrypt roundtrip)

**SSL/TLS:**
- [ ] Certificates generated
- [ ] Certificates valid (not expired)
- [ ] HTTPS enforced (HTTP redirects)
- [ ] Strong cipher suites only
- [ ] Certificate auto-renewal configured

**Audit Logging:**
- [ ] All auth attempts logged
- [ ] All privileged operations logged
- [ ] Logs tamper-evident
- [ ] Logs retained for compliance period
- [ ] Anomaly detection active

**Verification Commands:**
```bash
cd security
python scripts/generate_api_key.py --name "Test" --scopes admin  # Key generated
curl -H "Authorization: Bearer wrong_key" http://localhost:8000/api/health  # 401
curl -H "Authorization: Bearer valid_key" http://localhost:8000/api/health  # 200
psql -c "SELECT private_key_encrypted FROM findings LIMIT 1;"  # Encrypted (not plaintext)
openssl s_client -connect localhost:443  # SSL working
```

---

## 📋 LAYER 7: DEVOPS/MONITORING VERIFICATION

### Logging Checklist

**Log Format:**
- [ ] JSON structured
- [ ] Timestamp included (ISO 8601)
- [ ] Log level included
- [ ] Service name included
- [ ] Request ID included (for tracing)
- [ ] No sensitive data logged

**Log Levels:**
- [ ] DEBUG for development
- [ ] INFO for normal operations
- [ ] WARN for recoverable errors
- [ ] ERROR for unexpected errors
- [ ] CRITICAL for system failures

**Log Management:**
- [ ] Logs rotated (max size 10MB)
- [ ] Old logs archived
- [ ] Logs centralized (all services → one location)
- [ ] Logs searchable (can use grep/jq)

**Verification Commands:**
```bash
cd devops
tail -f volumes/logs/api.log | jq .  # Valid JSON
grep ERROR volumes/logs/*.log         # Find errors
```

---

### Monitoring Checklist

**Health Checks:**
- [ ] API health endpoint works
- [ ] Scanner health check works
- [ ] Oracle health check works
- [ ] Database health check works
- [ ] All health checks <5s response time

**Metrics:**
- [ ] Scanner speed tracked (keys/sec)
- [ ] API response times tracked
- [ ] Database query times tracked
- [ ] Memory usage tracked
- [ ] Disk usage tracked

**Alerts:**
- [ ] Service down alert works
- [ ] High error rate alert works
- [ ] Disk space alert works (>80% usage)
- [ ] Memory alert works (>80% usage)
- [ ] Telegram bot delivers alerts

**Dashboard:**
- [ ] Dashboard accessible
- [ ] Dashboard shows all services
- [ ] Dashboard updates in real-time
- [ ] Dashboard shows historical data
- [ ] Dashboard responsive (mobile-friendly)

**Verification Commands:**
```bash
cd devops
python monitoring/health_checker.py    # All healthy
python monitoring/db_monitor.py        # Stats displayed
curl http://localhost:9000             # Dashboard loads
python alerts/telegram_alerts.py --test  # Alert delivered
```

---

## 🎯 PHASE-SPECIFIC VERIFICATION

### Phase 1: API + Database (Foundation)

**Before moving to Phase 2:**
- [ ] All API endpoints return 200 for valid requests
- [ ] All database tables created
- [ ] All migrations run successfully
- [ ] API tests: 50+ passing, coverage ≥95%
- [ ] Database can handle 1000 inserts/sec
- [ ] Health endpoint returns all services "up"

**Verification:**
```bash
pytest api/tests/ -v --cov         # 50+ tests, 95%+ coverage
psql -c "SELECT COUNT(*) FROM findings;"  # Table accessible
ab -n 10000 http://localhost:8000/api/health  # <50ms p95
```

---

### Phase 2: Scanner + Oracle Services

**Before moving to Phase 3:**
- [ ] Scanner generates ≥5000 keys/sec
- [ ] Oracle returns valid suggestions
- [ ] Scanner applies Oracle guidance
- [ ] Findings stored in database (encrypted)
- [ ] gRPC communication works
- [ ] Tests: 80%+ coverage (Rust), 95%+ (Python)

**Verification:**
```bash
cargo bench                        # 5000+ keys/sec
python oracle-service/app/main.py analyze-patterns  # Valid suggestion
psql -c "SELECT COUNT(*) FROM findings WHERE balance_btc > 0;"  # Findings exist
```

---

### Phase 3: Frontend

**Before moving to Phase 4:**
- [ ] All 6 pages render without errors
- [ ] API integration works (all endpoints)
- [ ] WebSocket updates work
- [ ] Responsive on mobile + desktop
- [ ] Dark theme applied
- [ ] Tests: 90%+ coverage

**Verification:**
```bash
npm test                          # 90%+ coverage
npm run build                     # Production build succeeds
lighthouse http://localhost:5173  # Performance >90
```

---

### Phase 4: Infrastructure

**Before moving to Phase 5:**
- [ ] All services start with `docker-compose up`
- [ ] All services report "healthy"
- [ ] Inter-service communication works
- [ ] Data persists across restarts
- [ ] Environment variables loaded

**Verification:**
```bash
docker-compose up -d              # All services start
docker-compose ps                 # All healthy
curl http://localhost:8000/api/health  # API accessible
docker-compose restart postgres   # Data persists
```

---

### Phase 5: Security

**Before moving to Phase 6:**
- [ ] API key auth works
- [ ] Encryption works (roundtrip test)
- [ ] SSL/TLS configured
- [ ] Audit logging active
- [ ] No critical vulnerabilities (cargo audit, safety check)

**Verification:**
```bash
curl -H "Authorization: Bearer invalid" http://localhost:8000/api/health  # 401
psql -c "SELECT private_key_encrypted FROM findings LIMIT 1;"  # Encrypted
cargo audit && safety check       # No vulnerabilities
```

---

### Phase 6: DevOps/Monitoring

**Before moving to Phase 7:**
- [ ] All services log to centralized location
- [ ] Health checks work for all services
- [ ] Dashboard accessible
- [ ] Telegram alerts work
- [ ] Logs rotated

**Verification:**
```bash
python devops/monitoring/health_checker.py  # All healthy
curl http://localhost:9000        # Dashboard loads
python devops/alerts/telegram_alerts.py --test  # Alert sent
```

---

### Phase 7: Integration Testing

**Before declaring V4 production-ready:**
- [ ] Scanner finds wallets → stores in database
- [ ] Oracle analyzes → suggests ranges
- [ ] Scanner applies Oracle guidance
- [ ] AI model learns over time
- [ ] Web UI controls all functions
- [ ] Telegram bot works (all commands)
- [ ] Load test passes (10K scans/sec sustained)
- [ ] Disaster recovery tested (backup → restore)

**Verification:**
```bash
# Run integration test script (see architecture plan Phase 7)
./tests/integration_test.sh       # All checks pass
```

---

## 📊 QUALITY SCORE CARD

Use this to grade deliverables:

| Category | Weight | Score (0-100) |
|----------|--------|---------------|
| Code Quality | 20% | ___/100 |
| Testing | 25% | ___/100 |
| Documentation | 10% | ___/100 |
| Architecture Alignment | 20% | ___/100 |
| Performance | 15% | ___/100 |
| Security | 10% | ___/100 |
| **TOTAL** | 100% | **___/100** |

**Passing Grade:** ≥80/100  
**Excellent Grade:** ≥90/100  
**Swiss Watch Grade:** ≥95/100

---

**Remember:** Verification is not optional. It's the definition of "done." 🚀

*Version: 1.0*  
*Last Updated: 2026-02-08*
