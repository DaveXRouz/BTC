# SPEC: Infrastructure Docker - T5-S1 (Oracle Service & docker-compose)

**Estimated Duration:** 2-3 hours  
**Layer:** Layer 5 (Infrastructure)  
**Terminal:** Terminal 5  
**Phase:** Phase 4 (Infrastructure Setup)  
**Session:** T5-S1

---

## 🎯 TL;DR

- Creating Oracle service Dockerfile (Python 3.11+)
- Updating docker-compose.yml to include Oracle service
- Configuring health checks for all services
- Setting up environment variables for Oracle integration
- Establishing service dependency chain: postgres → oracle → api → frontend
- Implementing volume management for logs and persistent data
- Verification: All services start healthy with `docker-compose up -d`

---

## 📋 OBJECTIVE

Create production-ready Docker infrastructure for Oracle service and update orchestration to support full NPS V4 stack with proper health checks, dependency management, and security isolation.

---

## 🔍 CONTEXT

### Current State
- Terminal 3 (Backend Services) completed Oracle service Python code
- Terminal 4 (Database) completed PostgreSQL setup
- Infrastructure directory structure partially exists
- Need to containerize Oracle service and integrate into docker-compose

### What's Changing
- Adding `infrastructure/Dockerfiles/oracle.Dockerfile`
- Updating `infrastructure/docker-compose.yml` with Oracle service definition
- Updating `infrastructure/.env.example` with Oracle environment variables
- Adding health check endpoints and startup dependencies
- Configuring volume mounts for Oracle logs

### Why
Oracle service must run as isolated container to:
- Enable independent scaling and deployment
- Provide consistent environment across dev/prod
- Facilitate gRPC communication with API and Scanner
- Support AI integration with Anthropic API securely
- Allow health monitoring and automatic restart

---

## ✅ PREREQUISITES

### Required Completions
- [x] Terminal 3 (Oracle service code) - Located in `backend/oracle-service/`
  - Verified: `app/main.py` exists with gRPC server
  - Verified: `requirements.txt` with dependencies
  - Verified: `app/engines/` contains FC60, numerology, oracle modules
- [x] Terminal 4 (Database) - PostgreSQL running
  - Verified: Database schema created with `insights`, `oracle_suggestions` tables
  - Verified: `docker-compose.yml` contains postgres service definition

### System Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- Minimum 8GB RAM available
- Ports available: 50052 (Oracle gRPC), 5432 (Postgres), 8000 (API)

### Verification of Prerequisites
```bash
# Check Docker
docker --version               # Should be 20.10+
docker-compose --version       # Should be 2.0+

# Check Oracle service code exists
ls -la backend/oracle-service/app/
# Expected: main.py, engines/, services/, grpc/

# Check requirements.txt exists
cat backend/oracle-service/requirements.txt
# Expected: anthropic, psycopg2-binary, grpcio, etc.

# Check PostgreSQL running
docker ps | grep postgres
# Expected: nps-postgres container running
```

---

## 🛠️ TOOLS TO USE

### Primary Tools
- **create_file**: For Dockerfile, docker-compose updates, .env.example
- **extended_thinking**: For health check design and startup ordering
- **bash_tool**: For Docker build testing and verification

### Skills
- None required (standard Docker configuration)

### Subagents
- Not needed (coherent single-file specifications)

---

## 📋 REQUIREMENTS

### Functional Requirements

#### FR-1: Oracle Service Dockerfile
- Python 3.11+ base image (debian-slim for smaller size)
- Install system dependencies for PostgreSQL driver
- Install Python dependencies from requirements.txt
- Copy Oracle service code to `/app`
- Expose gRPC port 50052
- Run as non-root user for security
- Health check endpoint via HTTP (separate from gRPC)
- **Acceptance:** `docker build -f oracle.Dockerfile . --tag nps-oracle:latest` succeeds

#### FR-2: docker-compose Oracle Service
- Service named `oracle`
- Depends on `postgres` with health check wait
- Environment variables from .env file
- Volume mount for `/app/logs` (persistent logging)
- Network: `nps-network` (shared with other services)
- Restart policy: `unless-stopped`
- Resource limits: 1 CPU, 1GB memory (Oracle is lightweight)
- **Acceptance:** `docker-compose config` validates yaml syntax

#### FR-3: Environment Variables
- `ANTHROPIC_API_KEY` - Claude API key for AI integration
- `DATABASE_URL` - PostgreSQL connection string
- `GRPC_PORT` - Oracle gRPC port (50052)
- `NPS_MASTER_PASSWORD` - Encryption key for vault data
- `LOG_LEVEL` - Python logging level (INFO default)
- **Acceptance:** All variables documented in .env.example with descriptions

#### FR-4: Health Checks
- Oracle health check: HTTP GET /health on port 8052 (separate from gRPC)
- Postgres health check: `pg_isready` command
- API health check: HTTP GET /api/health
- Scanner health check: gRPC health probe on 50051
- **Acceptance:** `docker-compose ps` shows all services "healthy"

#### FR-5: Startup Ordering
- Order: postgres → oracle → scanner → api → web-ui
- Each service waits for dependency health check before starting
- Postgres must be healthy before Oracle attempts connection
- Oracle must start before API (API calls Oracle via gRPC)
- **Acceptance:** Services start in correct order without connection errors

### Non-Functional Requirements

#### NFR-1: Performance
- Container startup time <30 seconds
- Docker image size <500MB for Oracle
- Health check response <2 seconds
- Graceful shutdown <10 seconds
- **Acceptance:** Measured with `time docker-compose up -d`

#### NFR-2: Security
- Oracle runs as non-root user (uid 1000)
- Secrets passed via environment variables (not in Dockerfile)
- No hardcoded API keys in any files
- Logs directory permissions: 755 (readable by container user)
- **Acceptance:** `docker exec nps-oracle whoami` returns non-root user

#### NFR-3: Observability
- Oracle logs to stdout (captured by Docker)
- Logs also written to volume-mounted `/app/logs/oracle.log`
- JSON structured logging format
- Log rotation configured (10MB max, 5 backups)
- **Acceptance:** `docker logs nps-oracle` shows JSON logs

#### NFR-4: Maintainability
- Multi-stage Dockerfile (builder + runtime stages)
- Clear comments in docker-compose.yml
- .env.example has description for every variable
- Volume paths clearly documented
- **Acceptance:** Another developer can understand setup from comments alone

---

## 📝 IMPLEMENTATION PLAN

### Phase 1: Oracle Dockerfile (Duration: 45 minutes)

#### Tasks
1. Create `infrastructure/Dockerfiles/oracle.Dockerfile`
   - Use Python 3.11-slim-bookworm base
   - Install PostgreSQL client libraries (libpq-dev)
   - Create app user (non-root)
   - Copy requirements.txt and install dependencies
   - Copy Oracle service code
   - Set working directory and user
   - Expose port 50052 (gRPC)
   - Health check command
   - CMD to run Oracle service

2. Test Dockerfile build
   - Build image: `docker build -f oracle.Dockerfile -t nps-oracle:test .`
   - Verify image size <500MB
   - Test container run (will fail without env vars - expected)

**Files to Create:**
- `infrastructure/Dockerfiles/oracle.Dockerfile` (60 lines)

**Verification:**
```bash
cd infrastructure
docker build -f Dockerfiles/oracle.Dockerfile \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t nps-oracle:test \
  ../backend/oracle-service

# Expected output: Successfully built [image-id]
# Check image size
docker images nps-oracle:test
# Expected: SIZE column shows <500MB
```

**Checkpoint 1:**
- [ ] Dockerfile builds successfully
- [ ] Image size <500MB
- [ ] No security warnings from docker scan
- [ ] Multi-stage build uses cache effectively

**STOP if checkpoint fails** - Fix Dockerfile before proceeding

---

### Phase 2: Update docker-compose.yml (Duration: 30 minutes)

#### Tasks
1. Add Oracle service definition to `infrastructure/docker-compose.yml`
   - Service name: `oracle`
   - Build context: `./backend/oracle-service`
   - Dockerfile: `../../infrastructure/Dockerfiles/oracle.Dockerfile`
   - Container name: `nps-oracle`
   - Environment variables (from .env):
     - `DATABASE_URL`
     - `GRPC_PORT=50052`
     - `ANTHROPIC_API_KEY`
     - `NPS_MASTER_PASSWORD`
     - `LOG_LEVEL=INFO`
   - Depends on: `postgres` (with `service_healthy` condition)
   - Volumes: `./volumes/logs:/app/logs`
   - Networks: `nps-network`
   - Restart: `unless-stopped`
   - Resource limits: `cpus: '1'`, `memory: 1G`
   - Health check: HTTP probe on port 8052

2. Update API service dependencies
   - Add `oracle: condition: service_started` to API depends_on
   - Verify `ORACLE_SERVICE_URL: oracle:50052` in API environment

**Files to Modify:**
- `infrastructure/docker-compose.yml` (+40 lines)

**Verification:**
```bash
cd infrastructure
docker-compose config
# Expected: No errors, valid YAML output

# Verify Oracle service present
docker-compose config --services | grep oracle
# Expected: oracle

# Check dependency chain
docker-compose config | grep -A 5 "depends_on:"
# Expected: postgres → oracle, postgres+oracle → api
```

**Checkpoint 2:**
- [ ] docker-compose.yml syntax valid
- [ ] Oracle service defined with all required fields
- [ ] Dependency chain correct (postgres → oracle → api)
- [ ] Environment variables properly mapped

**STOP if checkpoint fails** - Fix docker-compose.yml before proceeding

---

### Phase 3: Environment Variables (Duration: 15 minutes)

#### Tasks
1. Update `infrastructure/.env.example` with Oracle variables
   - Add `ANTHROPIC_API_KEY` with description
   - Add `ORACLE_GRPC_PORT=50052` with description
   - Add comments explaining each variable's purpose
   - Add security warning for API key

2. Create development .env from template (for testing)
   - Copy .env.example to .env
   - Add placeholder values (will be replaced in testing)

**Files to Modify:**
- `infrastructure/.env.example` (+10 lines)

**Files to Create:**
- `infrastructure/.env` (copy of .env.example with test values)

**Verification:**
```bash
cd infrastructure

# Check .env.example has Oracle variables
grep ANTHROPIC_API_KEY .env.example
# Expected: ANTHROPIC_API_KEY=your_claude_api_key_here

grep ORACLE .env.example
# Expected: Comments about Oracle service

# Verify .env created (not committed to git)
test -f .env && echo "✓ .env exists" || echo "✗ .env missing"
```

**Checkpoint 3:**
- [ ] .env.example contains all Oracle variables
- [ ] Each variable has clear description comment
- [ ] .env file created for local testing
- [ ] .env added to .gitignore (if not already)

**STOP if checkpoint fails** - Add missing variables

---

### Phase 4: Health Checks Implementation (Duration: 30 minutes)

#### Tasks
1. Add health check to Oracle Dockerfile
   - Create simple HTTP health endpoint in Oracle service (port 8052)
   - Health check command in Dockerfile: `curl -f http://localhost:8052/health`
   - Interval: 10s, Timeout: 5s, Retries: 3, Start period: 30s

2. Add health checks to docker-compose.yml services
   - Oracle: HTTP check on port 8052
   - Postgres: Already has `pg_isready` check (verify it's present)
   - API: HTTP check on port 8000/api/health
   - Scanner: gRPC health check on port 50051 (if applicable)

3. Create health check script: `infrastructure/scripts/health-check.sh`
   - Checks all services via docker-compose ps
   - Parses "healthy" status for each service
   - Returns 0 if all healthy, 1 if any unhealthy

**Files to Modify:**
- `infrastructure/Dockerfiles/oracle.Dockerfile` (+5 lines for HEALTHCHECK)
- `backend/oracle-service/app/main.py` (+20 lines for HTTP health endpoint)
- `infrastructure/docker-compose.yml` (+health check configs)

**Files to Create:**
- `infrastructure/scripts/health-check.sh` (40 lines)

**Verification:**
```bash
cd infrastructure

# Build and start Oracle service only (with postgres)
docker-compose up -d postgres
sleep 15  # Wait for postgres healthy
docker-compose up -d oracle
sleep 30  # Wait for Oracle startup

# Check Oracle health
docker inspect nps-oracle --format='{{.State.Health.Status}}'
# Expected: healthy (after start_period)

# Run health check script
chmod +x scripts/health-check.sh
./scripts/health-check.sh
# Expected: All services healthy (postgres + oracle)
```

**Checkpoint 4:**
- [ ] Oracle Dockerfile has HEALTHCHECK instruction
- [ ] Oracle service exposes HTTP /health endpoint
- [ ] docker-compose.yml has health checks for all services
- [ ] health-check.sh script works and returns correct status

**STOP if checkpoint fails** - Fix health check implementation

---

### Phase 5: Integration Testing (Duration: 30 minutes)

#### Tasks
1. Start full stack with docker-compose
   - Run `docker-compose up -d`
   - Monitor logs for each service
   - Verify startup order: postgres → oracle → scanner → api → web-ui

2. Verify inter-service communication
   - Test Oracle gRPC endpoint from API container
   - Verify Oracle can connect to PostgreSQL
   - Check Oracle logs for successful initialization

3. Test Oracle AI integration (if API key provided)
   - Trigger Oracle pattern analysis endpoint
   - Verify Claude API called successfully
   - Check Oracle logs for AI responses

4. Verify data persistence
   - Stop and restart Oracle service
   - Verify logs persist in volume
   - Check database connection re-established

**Verification:**
```bash
cd infrastructure

# Start all services
docker-compose up -d

# Wait for all services healthy (max 2 minutes)
timeout 120 bash -c 'until [ "$(docker-compose ps --filter "status=running" | grep -c healthy)" -eq 5 ]; do sleep 5; done'

# Verify all services running and healthy
docker-compose ps
# Expected: 5 services (postgres, oracle, scanner, api, web-ui) all "healthy"

# Check Oracle logs
docker logs nps-oracle --tail 50
# Expected: "Oracle service started", "gRPC server listening on 50052", "Connected to database"

# Test Oracle gRPC from API container (requires grpcurl)
docker exec nps-api curl http://oracle:8052/health
# Expected: {"status": "healthy", "service": "oracle"}

# Test Oracle → PostgreSQL connection
docker exec nps-oracle psql "${DATABASE_URL}" -c "SELECT COUNT(*) FROM oracle_suggestions;"
# Expected: Count of suggestions (could be 0)

# Test data persistence
docker-compose restart oracle
sleep 20
docker logs nps-oracle --tail 20 | grep "Connected to database"
# Expected: Log line showing successful reconnection

# Verify log volume
ls -lah volumes/logs/
# Expected: oracle.log file present with size > 0
```

**Checkpoint 5:**
- [ ] All 5 services start and reach "healthy" status
- [ ] Oracle logs show successful initialization
- [ ] Oracle can connect to PostgreSQL
- [ ] Oracle gRPC server responding on port 50052
- [ ] Logs persist in volume across restarts
- [ ] No error messages in any service logs

**STOP if checkpoint fails** - Debug service communication issues

---

## 🎯 VERIFICATION CHECKLIST

### Infrastructure (Layer 5)
- [ ] Oracle Dockerfile builds successfully (<30s build time)
- [ ] Oracle Docker image size <500MB
- [ ] docker-compose.yml syntax valid (docker-compose config passes)
- [ ] All 5 services defined in docker-compose.yml
- [ ] Environment variables documented in .env.example
- [ ] .env file created with placeholder values
- [ ] Health checks configured for all services
- [ ] Service dependency chain correct (postgres → oracle → api)

### Container Orchestration
- [ ] All services start with `docker-compose up -d`
- [ ] All services reach "healthy" status within 2 minutes
- [ ] Inter-service communication works (API → Oracle gRPC)
- [ ] Oracle connects to PostgreSQL successfully
- [ ] Log volumes mounted and writable
- [ ] Data persists across service restarts
- [ ] Graceful shutdown works (`docker-compose down`)

### Security
- [ ] Oracle runs as non-root user (verified with `whoami`)
- [ ] No API keys in Dockerfile or docker-compose.yml (only .env)
- [ ] Secrets passed via environment variables
- [ ] Network isolation via docker network
- [ ] Resource limits set (prevent DOS)

### Observability
- [ ] Oracle logs to stdout (visible with `docker logs`)
- [ ] Logs written to volume (`volumes/logs/oracle.log`)
- [ ] JSON structured logging format
- [ ] Health check endpoint responds <2s
- [ ] health-check.sh script works

### Performance
- [ ] Container startup time <30 seconds (measured)
- [ ] Health check response time <2 seconds
- [ ] Oracle service ready to accept gRPC calls within 30s
- [ ] Resource usage within limits (1 CPU, 1GB RAM)

---

## ✅ SUCCESS CRITERIA

1. **Docker Build Success**
   - Oracle Dockerfile builds without errors in <30 seconds
   - Resulting image size <500MB
   - No security vulnerabilities reported by `docker scan`
   - Multi-stage build reduces final image size by 30%+

2. **Service Orchestration**
   - All 5 services start with `docker-compose up -d`
   - All services reach "healthy" status within 2 minutes
   - Startup order correct: postgres → oracle → scanner → api → web-ui
   - No error messages in any service logs

3. **Oracle Service Functionality**
   - Oracle gRPC server listening on port 50052
   - Oracle HTTP health endpoint responds on port 8052
   - Oracle successfully connects to PostgreSQL
   - Oracle AI integration works (if API key provided)
   - Pattern analysis endpoint functional

4. **Data Persistence**
   - Logs persist in `volumes/logs/oracle.log`
   - Log rotation configured (10MB max, 5 backups)
   - Data survives container restart
   - Volume permissions correct (readable by Oracle container)

5. **Inter-Service Communication**
   - API can reach Oracle via gRPC (oracle:50052)
   - Oracle can query PostgreSQL database
   - Oracle can call Anthropic API (if key provided)
   - Health checks work across all services

---

## 📂 DELIVERABLES

### Created Files
1. `infrastructure/Dockerfiles/oracle.Dockerfile` (60 lines)
   - Python 3.11 base with Oracle service
   - Multi-stage build for optimization
   - Health check configuration
   - Non-root user setup

2. `infrastructure/scripts/health-check.sh` (40 lines)
   - Checks all service health statuses
   - Returns 0 for all healthy, 1 otherwise
   - Colored output for readability

3. `infrastructure/.env` (development only, not committed)
   - Copy of .env.example with test values

### Modified Files
1. `infrastructure/docker-compose.yml` (+40 lines)
   - Oracle service definition
   - Updated API dependencies
   - Health check configurations

2. `infrastructure/.env.example` (+10 lines)
   - ANTHROPIC_API_KEY
   - ORACLE_GRPC_PORT
   - Descriptive comments

3. `backend/oracle-service/app/main.py` (+20 lines)
   - HTTP health endpoint on port 8052
   - Returns JSON health status

### File Structure
```
infrastructure/
├── docker-compose.yml          # Updated with Oracle service
├── .env.example                # Updated with Oracle variables
├── .env                        # Created for local dev (gitignored)
├── Dockerfiles/
│   └── oracle.Dockerfile       # NEW: Oracle container definition
└── scripts/
    └── health-check.sh         # NEW: Health monitoring script

backend/oracle-service/
└── app/
    └── main.py                 # Modified: Added HTTP health endpoint
```

---

## 🔄 HANDOFF TO NEXT SESSION

### If Session Ends Mid-Implementation

**Resume from Phase:** [Current Phase Number]

**Context Needed:**
- Which Dockerfile phase was completed
- Whether docker-compose.yml was updated
- If .env.example was modified
- Current test status

**Verification Before Continuing:**
```bash
# Check what exists
ls infrastructure/Dockerfiles/oracle.Dockerfile  # Should exist
grep "oracle:" infrastructure/docker-compose.yml  # Should be present
grep "ANTHROPIC_API_KEY" infrastructure/.env.example  # Should be documented

# Verify can build
docker build -f infrastructure/Dockerfiles/oracle.Dockerfile \
  -t nps-oracle:test backend/oracle-service
```

### State Checkpoints
- **After Phase 1:** Oracle Dockerfile built successfully
- **After Phase 2:** docker-compose.yml updated and validated
- **After Phase 3:** Environment variables documented
- **After Phase 4:** Health checks implemented
- **After Phase 5:** Full stack tested and working

---

## 🎯 NEXT STEPS (After This Spec)

### Immediate (Terminal 5 continuation)
1. **T5-S2: Nginx Reverse Proxy**
   - Create nginx.conf for API routing
   - SSL/TLS certificate setup
   - Rate limiting configuration
   - Estimated: 2 hours

2. **T5-S3: Deployment Scripts**
   - Create deploy.sh (automated deployment)
   - Create rollback.sh (version rollback)
   - Backup/restore automation
   - Estimated: 1.5 hours

### Next Terminal (Terminal 6 - Security)
1. **T6-S1: API Key Authentication**
   - Generate API key script
   - FastAPI middleware integration
   - Database storage for keys
   - Estimated: 2.5 hours

### Integration Testing
1. **End-to-End Stack Test**
   - Scanner → Oracle → API → Frontend flow
   - Verify AI learning loop
   - Performance benchmarking
   - Estimated: 3 hours

---

## 📚 REFERENCE DOCUMENTATION

### Architecture Plan
- Layer 5 Section: Lines 650-881 in `NPS_V4_ARCHITECTURE_PLAN.md`
- docker-compose.yml example: Lines 682-815
- Environment variables: Lines 817-838

### Verification Checklists
- Layer 5 Verification: `VERIFICATION_CHECKLISTS.md` lines 430-489
- Phase 4 Verification: Lines 562-577

### Related Specifications
- Terminal 3 (Oracle service code) - prerequisite
- Terminal 4 (Database) - prerequisite
- Terminal 2 (API) - will consume Oracle via gRPC

---

## 🔍 EXTENDED THINKING NOTES

### Health Check Design Decision

**Question:** Should Oracle have HTTP health check or gRPC health check?

**Analysis:**
- gRPC health check protocol exists (`grpc.health.v1.Health`)
- HTTP simpler for Docker HEALTHCHECK (curl available)
- Docker expects shell command for health check
- gRPC requires `grpcurl` tool (not in base image)

**Trade-offs:**
| Approach | Pros | Cons |
|----------|------|------|
| HTTP | Simple, curl built-in, fast | Extra HTTP server needed |
| gRPC | Native protocol, reuses server | Requires grpcurl, complex |

**Decision:** HTTP health check on separate port (8052)

**Reasoning:**
- Simpler Docker HEALTHCHECK command
- No additional tools needed in image
- Industry standard (Kubernetes also uses HTTP)
- Can check both HTTP and gRPC separately if needed

**Implementation:**
```python
# In Oracle main.py
from aiohttp import web

async def health_check(request):
    return web.json_response({"status": "healthy", "service": "oracle"})

app = web.Application()
app.router.add_get('/health', health_check)
web.run_app(app, port=8052)
```

### Startup Order Decision

**Question:** What's the optimal startup order for services?

**Analysis:**
- Database must be first (everyone depends on it)
- Oracle needs database for insights storage
- Scanner needs database for findings storage
- API needs both Oracle and Scanner for gRPC calls
- Frontend only needs API

**Dependency Graph:**
```
postgres (foundation)
  ├─→ oracle (needs DB for insights)
  ├─→ scanner (needs DB for findings)
  └─→ api (needs DB + oracle + scanner)
       └─→ web-ui (needs API only)
```

**Decision:** postgres → (oracle + scanner in parallel) → api → web-ui

**Reasoning:**
- Oracle and Scanner can start in parallel (both only need postgres)
- API must wait for both Oracle and Scanner (calls them via gRPC)
- Frontend waits for API only
- Maximizes parallel startup for speed

**Implementation:**
```yaml
oracle:
  depends_on:
    postgres:
      condition: service_healthy

scanner:
  depends_on:
    postgres:
      condition: service_healthy

api:
  depends_on:
    postgres:
      condition: service_healthy
    oracle:
      condition: service_started
    scanner:
      condition: service_started
```

### Resource Limits Decision

**Question:** What CPU and memory limits for Oracle service?

**Analysis:**
- Oracle is Python + AI calls (mostly network I/O bound)
- Pattern analysis is computationally light (numerology)
- AI calls are blocking but infrequent (<1/min)
- Database queries are simple (indexed lookups)

**Workload Estimate:**
- Pattern analysis: 100ms CPU time per 1000 findings
- AI API call: 5s wall time but <10ms CPU (network wait)
- Database queries: <5ms each
- Expected QPS: <5 requests/sec

**Decision:** 1 CPU, 1GB memory

**Reasoning:**
- Oracle is not CPU-intensive (AI calls are network I/O)
- 1 CPU enough for <10 QPS with room to spare
- 1GB memory covers Python runtime + model loading
- Prevents resource exhaustion if Oracle bugs out
- Can scale horizontally if needed (multiple containers)

**Alternative Considered:**
- 0.5 CPU: Too restrictive, AI processing might queue
- 2 CPU: Wasteful, Oracle doesn't use it
- 2GB memory: Unnecessary, 1GB is generous for this workload

---

## ⚠️ KNOWN ISSUES & WARNINGS

### Issue 1: Anthropic API Key Required

**Problem:** Oracle service won't fully function without valid Anthropic API key

**Impact:** 
- AI pattern analysis will fail
- Range suggestions will fallback to random
- No learning loop advancement

**Workaround:**
- Oracle starts and runs without API key
- Logs warning about missing key
- Returns mock suggestions until key provided

**Permanent Fix:**
- Obtain Anthropic API key
- Add to .env file
- Restart Oracle service

### Issue 2: Volume Permissions

**Problem:** Log volume might not be writable by container user

**Impact:**
- Oracle can't write to `/app/logs/oracle.log`
- Logs only visible via `docker logs` (not persistent)

**Workaround:**
```bash
# Fix permissions before starting
mkdir -p volumes/logs
chmod 755 volumes/logs
chown -R 1000:1000 volumes/logs  # Match Oracle container user
```

**Permanent Fix:**
- Add volume permission setup to deploy.sh script
- Document in README.md

### Issue 3: Health Check False Positives

**Problem:** Health check might report "healthy" before service ready

**Impact:**
- API starts calling Oracle before it's ready
- Initial gRPC calls might fail (then retry and succeed)

**Workaround:**
- Extended start_period (30s) gives Oracle time to initialize
- API has retry logic for gRPC calls

**Permanent Fix:**
- Improve health check to verify:
  - Database connection established
  - gRPC server listening
  - AI client initialized

---

## 📊 ESTIMATED METRICS

### Build Metrics
- Docker build time: 25-30 seconds (first build)
- Docker build time: 5-10 seconds (cached)
- Image size: 350-450MB
- Build cache hit rate: 80%+ (after first build)

### Runtime Metrics
- Container startup time: 15-25 seconds
- Time to healthy status: 25-30 seconds
- Health check response time: <500ms
- Memory usage: 200-400MB (well under 1GB limit)
- CPU usage: <10% of 1 CPU (idle)

### Performance Benchmarks
- Pattern analysis (1000 findings): <5 seconds
- AI API call latency: 2-8 seconds (network dependent)
- Database query latency: <50ms
- gRPC request handling: <10ms (excluding AI call)

---

## 🎓 CONFIDENCE LEVEL

**High (90%)** - Standard Docker configuration with clear requirements

**Reasoning:**
- Docker and docker-compose are well-understood technologies
- Oracle service code already exists (Terminal 3 completed)
- Architecture plan provides detailed specifications
- Health check pattern is industry standard
- No complex custom networking or orchestration needed

**Risks:**
- Anthropic API key availability (medium risk - can work without)
- Volume permission issues (low risk - easily fixed)
- Resource limits might need tuning (low risk - conservative defaults)

**Mitigation:**
- Comprehensive verification steps at each phase
- Health checks catch startup failures immediately
- Logs provide detailed debugging information
- Rollback to previous state easy with docker-compose

---

## ✅ FINAL CHECKLIST

Before declaring this specification complete:

- [x] All phases have clear tasks and verification steps
- [x] Success criteria are measurable (numbers, timings, commands)
- [x] Verification commands are copy-paste ready
- [x] Extended thinking documented for key decisions
- [x] Known issues identified with workarounds
- [x] Handoff information complete for session continuity
- [x] Next steps prioritized and estimated
- [x] Confidence level stated with reasoning
- [x] All deliverables listed with file paths
- [x] Prerequisites verified before implementation
- [x] Resource limits justified with analysis
- [x] Health check strategy explained
- [x] Security considerations addressed

---

**Specification Status:** ✅ READY FOR EXECUTION  
**Claude Code CLI Compatible:** ✅ YES  
**Estimated Total Duration:** 2-3 hours  
**Complexity:** Medium  
**Risk Level:** Low

**Approved for Terminal 5 Session 1 execution.**

---

*Specification Version: 1.0*  
*Created: 2026-02-08*  
*Last Updated: 2026-02-08*  
*Author: Claude (NPS V4 Architecture Team)*
