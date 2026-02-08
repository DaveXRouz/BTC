# SUBAGENT PATTERNS - NPS V4

## 🎯 PURPOSE

This playbook provides detailed patterns for coordinating multiple subagents to handle complex, multi-component tasks in parallel. Subagents enable efficient work distribution and context management.

**Key Principle:** One subagent = one focused task with clear inputs/outputs.

---

## 📋 WHEN TO USE SUBAGENTS

### Decision Matrix

| Scenario | Use Subagents? | Why |
|----------|----------------|-----|
| Creating 1 file (<100 lines) | ❌ No | Simple, direct response faster |
| Creating 2-3 related files | ⚠️ Maybe | If files are independent |
| Creating 4+ files | ✅ Yes | Parallel execution more efficient |
| Multi-layer task | ✅ Yes | Layer separation benefits |
| Large prompt (>8000 tokens) | ✅ Yes | Context management |
| Independent sub-tasks | ✅ Yes | No coordination overhead |
| Complex coordination needed | ⚠️ Careful | Ensure clear interfaces |
| Time-sensitive task | ✅ Yes | Parallel = faster |

---

## 🏗️ CORE PATTERNS

### Pattern 1: Layer Separation

**Use Case:** Creating files across multiple NPS V4 layers

**Example Task:** "Create health check endpoint (API) + database schema + tests"

**Subagent Structure:**
```
Subagent 1: API Layer
- Task: Create /api/app/routers/health.py
- Input: Database schema design (from Subagent 2)
- Output: FastAPI endpoint code
- Acceptance: Endpoint returns 200 with service statuses

Subagent 2: Database Layer  
- Task: Create /database/schemas/health_checks.sql
- Input: None (independent)
- Output: PostgreSQL schema for health tracking
- Acceptance: Schema creates without errors

Subagent 3: Testing Layer
- Task: Create /api/tests/test_health.py
- Input: Endpoint code (from Subagent 1)
- Output: Integration tests
- Acceptance: All tests pass (5/5)
```

**Coordination Flow:**
```
Subagent 2 (Database) → Completes first (no dependencies)
    ↓
Subagent 1 (API) → Uses Subagent 2 output
    ↓
Subagent 3 (Tests) → Uses Subagent 1 output
    ↓
Main Agent → Integrates all outputs + verifies
```

**Prompt Template:**
```markdown
# Subagent 1: API Health Endpoint

You are Subagent 1 for NPS V4 API Layer (Layer 2).

## CONTEXT
Creating health check endpoint that queries database and returns service status.
Database schema created by Subagent 2.

## YOUR TASK
Create `/api/app/routers/health.py` with:
- GET /api/health endpoint
- Queries: PostgreSQL, Scanner service, Oracle service
- Returns: JSON with status for each service
- Response time: <50ms target

## DEPENDENCIES
- Database schema: Provided by Subagent 2 (health_checks table)
- Use existing database connection from `app/database/connection.py`

## OUTPUT FORMAT
Complete Python file with:
- FastAPI router
- Pydantic response model
- Database queries
- Error handling
- Logging (JSON format)

## ACCEPTANCE CRITERIA
- [ ] Endpoint returns 200 status
- [ ] Response includes all 3 service statuses
- [ ] Uses existing DB connection pool
- [ ] Logs all health checks
- [ ] No hardcoded values

## VERIFICATION
```bash
uvicorn app.main:app --reload
curl http://localhost:8000/api/health
# Expected: {"status": "healthy", "services": {...}}
```
```

---

### Pattern 2: Phase Parallelization

**Use Case:** Multiple independent phases that can run simultaneously

**Example Task:** "Implement Scanner + Oracle services in parallel"

**Subagent Structure:**
```
Subagent 1: Scanner Service (Rust)
- Phase: Core scanning logic
- Dependencies: None
- Duration: 45 minutes
- Output: scanner-service/src/scanner/mod.rs

Subagent 2: Oracle Service (Python)
- Phase: Pattern analysis logic
- Dependencies: None  
- Duration: 30 minutes
- Output: oracle-service/app/services/pattern_service.py

Subagent 3: gRPC Interface (Proto)
- Phase: Communication protocol
- Dependencies: None
- Duration: 15 minutes
- Output: shared/proto/scanner.proto + oracle.proto
```

**Coordination Flow:**
```
All subagents start SIMULTANEOUSLY
    ↓
Each completes independently
    ↓
Main Agent → Integrates + creates communication layer
```

**Prompt Template:**
```markdown
# Subagent 2: Oracle Pattern Analysis Service

You are Subagent 2 for NPS V4 Oracle Service (Layer 3B).

## CONTEXT
Oracle service analyzes patterns in successful wallet findings to suggest lucky ranges for Scanner.
Working in parallel with Scanner service (Subagent 1).

## YOUR TASK
Create `/backend/oracle-service/app/services/pattern_service.py` with:
- Function: analyze_patterns(findings: List[Finding]) -> RangeSuggestion
- Analyzes: Numerology scores, FC60 signatures, private key ranges
- Returns: Weighted range suggestion with reasoning

## DEPENDENCIES
None - this is independent logic

## OUTPUT FORMAT
Complete Python file with:
- Type hints
- Docstrings
- Error handling
- Logging
- Unit tests

## ACCEPTANCE CRITERIA
- [ ] Function accepts list of findings
- [ ] Returns valid RangeSuggestion object
- [ ] Confidence score calculated (0.0-1.0)
- [ ] Reasoning string generated
- [ ] Unit tests pass (10/10)

## VERIFICATION
```bash
pytest tests/test_pattern_service.py -v
# Expected: 10/10 tests pass
```
```

---

### Pattern 3: Component Splitting

**Use Case:** Large component broken into smaller independent pieces

**Example Task:** "Create complete Dashboard page with 4 widgets"

**Subagent Structure:**
```
Subagent 1: TerminalCard Component
- Task: Create src/components/TerminalCard.tsx
- Input: None (self-contained)
- Output: Reusable terminal status card

Subagent 2: HealthDots Component
- Task: Create src/components/HealthDots.tsx
- Input: None (self-contained)
- Output: Service health indicator

Subagent 3: StatsSummary Component
- Task: Create src/components/StatsSummary.tsx
- Input: None (self-contained)
- Output: Scan statistics display

Subagent 4: Dashboard Page
- Task: Create src/pages/Dashboard.tsx
- Input: All 3 components (from Subagents 1-3)
- Output: Complete dashboard page
```

**Coordination Flow:**
```
Subagents 1, 2, 3 → Run in parallel (no dependencies)
    ↓
All complete
    ↓
Subagent 4 → Composes components into page
    ↓
Main Agent → Tests integration + responsive design
```

---

### Pattern 4: Feature Slicing

**Use Case:** Same feature across multiple layers

**Example Task:** "Implement 'pause scan' feature across all layers"

**Subagent Structure:**
```
Subagent 1: API Endpoint
- Task: POST /api/scanner/pause
- Layer: API (Layer 2)
- Output: FastAPI endpoint + Pydantic models

Subagent 2: Scanner Logic
- Task: pause() method in Scanner service
- Layer: Backend (Layer 3)
- Output: Rust pause implementation

Subagent 3: Database Schema
- Task: Add pause_state to sessions table
- Layer: Database (Layer 4)
- Output: Migration script

Subagent 4: Frontend UI
- Task: Pause button in Scanner page
- Layer: Frontend (Layer 1)
- Output: React component + API integration

Subagent 5: Tests
- Task: Integration tests for pause feature
- Layer: Testing
- Output: End-to-end test
```

**Coordination Flow:**
```
Subagent 3 (Database) → Completes first
    ↓
Subagents 1 + 2 → Use database schema
    ↓
Subagent 4 → Uses API endpoint
    ↓
Subagent 5 → Tests entire flow
    ↓
Main Agent → Verifies cross-layer integration
```

---

## 🔧 SUBAGENT COORDINATION TEMPLATES

### Template 1: Independent Subagents (Parallel)

```markdown
# TASK: [Overall task description]

## COORDINATION STRATEGY
All subagents work independently in parallel.
No dependencies between subagents.

---

# SUBAGENT 1: [Name]
You are Subagent 1 for [specific component].

**Task:** [Specific sub-task]
**Input:** None (independent)
**Output:** [Specific deliverable]
**Acceptance:** [Measurable criteria]
**Verification:** [Test command]

---

# SUBAGENT 2: [Name]
You are Subagent 2 for [specific component].

**Task:** [Specific sub-task]
**Input:** None (independent)
**Output:** [Specific deliverable]
**Acceptance:** [Measurable criteria]
**Verification:** [Test command]

---

[Repeat for all subagents]

---

# MAIN AGENT: Integration

Once all subagents complete:
1. Verify each subagent output
2. Integrate outputs
3. Run cross-component tests
4. Provide final verification
```

---

### Template 2: Sequential Subagents (Pipeline)

```markdown
# TASK: [Overall task description]

## COORDINATION STRATEGY
Subagents execute in sequence, each using previous output.

---

# SUBAGENT 1: [Name] (FOUNDATION)
You are Subagent 1 for [specific component].

**Task:** [Specific sub-task]
**Input:** None (first in pipeline)
**Output:** [Specific deliverable]
**Provides for:** Subagent 2 (what they need)
**Acceptance:** [Measurable criteria]
**Verification:** [Test command]

---

# SUBAGENT 2: [Name] (BUILDS ON 1)
You are Subagent 2 for [specific component].

**Task:** [Specific sub-task]
**Input:** [Output from Subagent 1]
**Output:** [Specific deliverable]
**Provides for:** Subagent 3 (what they need)
**Acceptance:** [Measurable criteria]
**Verification:** [Test command]

---

[Continue pipeline]

---

# MAIN AGENT: Verification

After pipeline completes:
1. Verify end-to-end flow
2. Test integration points
3. Check performance
4. Provide final verification
```

---

### Template 3: Hub-and-Spoke (One coordinator, many workers)

```markdown
# TASK: [Overall task description]

## COORDINATION STRATEGY
Subagent 1 is coordinator, others are specialized workers.

---

# SUBAGENT 1: [Coordinator Name] (HUB)
You are the coordinator for this multi-component task.

**Task:** [Coordination responsibilities]
**Manages:** Subagents 2, 3, 4, 5
**Provides:** Shared context/interfaces
**Integrates:** All worker outputs
**Acceptance:** [Integration criteria]

---

# SUBAGENT 2: [Worker Name] (SPOKE)
You are a specialized worker for [specific component].

**Task:** [Specific sub-task]
**Reports to:** Subagent 1
**Uses:** Shared interfaces from Subagent 1
**Output:** [Specific deliverable]
**Acceptance:** [Measurable criteria]

---

[Repeat for all workers]

---

# MAIN AGENT: Final Verification

After coordinator integrates:
1. Verify coordinator output
2. Test all integrations
3. Check consistency
4. Provide final verification
```

---

## ⚠️ COMMON COORDINATION PITFALLS

### Pitfall 1: Unclear Dependencies

**❌ Wrong:**
```markdown
Subagent 1: Create API endpoint
Subagent 2: Create tests
[No mention of dependencies]
```

**✅ Correct:**
```markdown
Subagent 1: Create API endpoint
- Output: api/app/routers/scanner.py

Subagent 2: Create tests
- Input: api/app/routers/scanner.py (from Subagent 1)
- Waits for: Subagent 1 completion
```

---

### Pitfall 2: Duplicate Work

**❌ Wrong:**
```markdown
Subagent 1: Create health endpoint
Subagent 2: Create health endpoint (different implementation)
[Both do the same work]
```

**✅ Correct:**
```markdown
Subagent 1: Create health endpoint
Subagent 2: Create health tests for endpoint (from Subagent 1)
[Clear division of labor]
```

---

### Pitfall 3: Missing Integration Step

**❌ Wrong:**
```markdown
Subagent 1: Creates Component A
Subagent 2: Creates Component B
[Main agent assumes they work together]
```

**✅ Correct:**
```markdown
Subagent 1: Creates Component A
Subagent 2: Creates Component B
Main Agent: 
1. Integrates A + B
2. Tests integration
3. Verifies components communicate correctly
```

---

## 🎯 NPS V4 SPECIFIC PATTERNS

### Pattern: API + Database + Tests

**Scenario:** Creating new API endpoint with database backing

```markdown
# SUBAGENT 1: Database Schema
Create /database/schemas/[table].sql
- No dependencies
- Runs first

# SUBAGENT 2: API Endpoint  
Create /api/app/routers/[endpoint].py
- Uses schema from Subagent 1
- Runs second

# SUBAGENT 3: Tests
Create /api/tests/test_[endpoint].py
- Uses endpoint from Subagent 2
- Runs third

# MAIN AGENT
1. Run migration (Subagent 1 output)
2. Start API (Subagent 2 output)
3. Run tests (Subagent 3 output)
4. Verify all pass
```

---

### Pattern: Scanner + Oracle + gRPC

**Scenario:** Implementing cross-service communication

```markdown
# SUBAGENT 1: gRPC Protocol
Create /shared/proto/[service].proto
- No dependencies
- Runs first

# SUBAGENT 2: Scanner gRPC Client
Create /scanner-service/src/grpc/client.rs
- Uses proto from Subagent 1
- Runs second

# SUBAGENT 3: Oracle gRPC Server
Create /oracle-service/app/grpc/server.py
- Uses proto from Subagent 1
- Runs second (parallel with Subagent 2)

# MAIN AGENT
1. Compile proto (Subagent 1)
2. Test client → server communication
3. Verify data flows correctly
```

---

### Pattern: Frontend Component Suite

**Scenario:** Creating multiple related React components

```markdown
# SUBAGENT 1: Base Component
Create /src/components/BaseCard.tsx
- Reusable card component
- No dependencies

# SUBAGENT 2: TerminalCard (extends Base)
Create /src/components/TerminalCard.tsx
- Uses BaseCard from Subagent 1
- Scanner terminal display

# SUBAGENT 3: StatsCard (extends Base)
Create /src/components/StatsCard.tsx
- Uses BaseCard from Subagent 1
- Statistics display

# SUBAGENT 4: Dashboard Page
Create /src/pages/Dashboard.tsx
- Uses TerminalCard + StatsCard
- Composes into page

# MAIN AGENT
1. Build component library
2. Test individual components
3. Test composed page
4. Verify responsive design
```

---

## 📊 SUBAGENT EFFECTIVENESS MATRIX

| Task Complexity | Subagents | Time Saved | Quality Gain |
|-----------------|-----------|------------|--------------|
| 1-2 files | 0 (direct) | 0% | Baseline |
| 3-5 files | 2-3 | 30-40% | +20% (focused) |
| 6-10 files | 4-6 | 50-60% | +40% (parallel) |
| 11+ files | 7+ | 60-70% | +60% (specialized) |
| Multi-layer | Layer count | 40-50% | +50% (separation) |

---

## 🔄 SUBAGENT HANDOFF PROTOCOL

### Step 1: Main Agent Preparation
```markdown
1. Analyze task complexity
2. Identify sub-tasks
3. Determine dependencies
4. Create subagent prompts
5. Specify coordination strategy
```

### Step 2: Subagent Execution
```markdown
Each subagent:
1. Reads own prompt completely
2. Verifies inputs available
3. Executes task
4. Provides output + verification
5. Reports completion to main agent
```

### Step 3: Main Agent Integration
```markdown
1. Collect all subagent outputs
2. Verify each output independently
3. Test integration points
4. Run cross-component tests
5. Provide final verification
6. Create handoff pack
```

---

## 📚 QUICK REFERENCE

**Most Common NPS V4 Subagent Patterns:**

| Task | Pattern | Subagents | Strategy |
|------|---------|-----------|----------|
| New API endpoint + DB + tests | Layer Separation | 3 | Sequential |
| Multiple React components | Component Splitting | 4-5 | Parallel → Compose |
| Scanner + Oracle services | Phase Parallelization | 2-3 | Parallel |
| Full feature (all layers) | Feature Slicing | 5-7 | Mixed |
| Complex integration | Hub-and-Spoke | 3-5 | Coordinator |

---

**Remember:** Subagents are for complexity management, not simple tasks. Use wisely. 🚀

*Version: 1.0*  
*Last Updated: 2026-02-08*
