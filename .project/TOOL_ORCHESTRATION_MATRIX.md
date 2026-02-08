# TOOL ORCHESTRATION MATRIX - NPS V4

## 🎯 PURPOSE

This matrix provides systematic guidance on which tools to use for every scenario in NPS V4 development. Think of this as your "which tool for which job" reference.

**Rule:** Always consult this matrix before starting ANY task.

---

## 🛠️ AVAILABLE TOOLS

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **view** | Read files/directories | Always (architecture plan, skills, playbooks) |
| **Skills** | Pre-built best practices | File creation (docx, pptx, React, API) |
| **Subagents** | Parallel execution | Multi-file tasks (3+ files) |
| **extended_thinking** | Complex decisions | Architecture, trade-offs, security |
| **ask_user** | Interactive clarification | High-stakes, ambiguous, multiple approaches |
| **conversation_search** | Find past context | Continuing from previous session |
| **MCP servers** | External integration | Database ops, file mgmt, Git |
| **bash_tool** | Execute commands | Testing, verification, deployment |
| **create_file** | Create new files | All file creation |
| **str_replace** | Edit existing files | Modifications, bug fixes |

---

## 📋 DECISION MATRIX BY SCENARIO

### Scenario 1: Starting New Task

```
ALWAYS START WITH:
1. view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md
2. Identify layer(s) involved
3. Check this matrix for layer-specific tools
4. Proceed with selected tools
```

| If... | Use Tools |
|-------|-----------|
| First time seeing this task type | view (architecture plan) → ask_user (confirm approach) |
| Continuing from previous session | conversation_search → view (architecture plan) |
| User uploaded ZIP | bash_tool (extract) → view (analyze structure) → ask_user (verify state) |
| Task involves files | view (check applicable skills) |
| Task is complex (multiple layers) | extended_thinking → subagents |

---

### Scenario 2: Creating Documents

| Document Type | Tools to Use | Order |
|---------------|--------------|-------|
| **Word Document** | view → docx skill → create_file | 1. Read skill 2. Create file 3. Verify |
| **PDF** | view → pdf skill → create_file | 1. Read skill 2. Create file 3. Verify |
| **Presentation** | view → pptx skill → create_file | 1. Read skill 2. Create file 3. Verify |
| **Spreadsheet** | view → xlsx skill → create_file | 1. Read skill 2. Create file 3. Verify |
| **Technical Spec (MD)** | view → doc-coauthoring skill → create_file | 1. Read skill 2. Co-author 3. Create |
| **API Documentation** | view → product-self-knowledge → docx skill | 1. Verify API 2. Document 3. Create |

**Example:**
```markdown
Task: "Create NPS V4 API specification document"

Tools Used:
1. view /mnt/skills/examples/doc-coauthoring/SKILL.md (read skill)
2. view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md (get API details)
3. create_file (produce MD specification)
4. ask_user (verify structure before writing)
```

---

### Scenario 3: Building Frontend (Layer 1)

| Task | Tools to Use | Details |
|------|--------------|---------|
| **Single Component** | view (frontend-design skill) → create_file | Simple React component |
| **Multiple Components** | view (frontend-design) → subagents (one per component) | 3+ components in parallel |
| **Themed UI** | view (frontend-design + theme-factory) → create_file | Apply consistent theme |
| **Complex Multi-Page App** | view (web-artifacts-builder) → subagents → extended_thinking | Architecture planning needed |
| **Anthropic Branding** | view (brand-guidelines + frontend-design) → create_file | Use Anthropic colors |

**Example:**
```markdown
Task: "Create Dashboard page with 4 widgets"

Tools Used:
1. view /mnt/skills/public/frontend-design/SKILL.md
2. view /mnt/skills/examples/theme-factory/SKILL.md
3. extended_thinking (decide component hierarchy)
4. subagents (4 subagents, one per widget)
5. create_file (compose dashboard page)
```

---

### Scenario 4: Building API (Layer 2)

| Task | Tools to Use | Details |
|------|--------------|---------|
| **Single Endpoint** | view (architecture plan) → create_file | Straightforward REST endpoint |
| **Endpoint + Tests** | view (architecture plan) → subagents (endpoint + tests) | Parallel creation |
| **Claude API Integration** | view (product-self-knowledge) → create_file | Anthropic API patterns |
| **Complex API Design** | extended_thinking (design decisions) → subagents | Multiple endpoints + auth |
| **MCP Server** | view (mcp-builder) → create_file | MCP server creation |

**Example:**
```markdown
Task: "Create /api/scanner/start endpoint with authentication"

Tools Used:
1. view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md (Layer 2 section)
2. view /mnt/skills/public/product-self-knowledge/SKILL.md (API patterns)
3. extended_thinking (design auth flow)
4. subagents:
   - Subagent 1: Create endpoint
   - Subagent 2: Create tests
5. bash_tool (run tests for verification)
```

---

### Scenario 5: Building Backend Services (Layer 3)

| Task | Tools to Use | Details |
|------|--------------|---------|
| **Rust Scanner** | view (architecture plan) → create_file + bash_tool (cargo test) | Performance-critical code |
| **Python Oracle** | view (architecture plan) → create_file + bash_tool (pytest) | AI integration |
| **gRPC Interface** | view (mcp-builder optional) → subagents (proto + clients) | Cross-service comm |
| **Performance Optimization** | extended_thinking (strategy) → bash_tool (benchmark) | Profiling + optimization |
| **AI Integration** | view (product-self-knowledge) → create_file | Claude CLI patterns |

**Example:**
```markdown
Task: "Implement Scanner service with Oracle integration"

Tools Used:
1. view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md (Layer 3 section)
2. extended_thinking (decide communication pattern: gRPC vs HTTP)
3. subagents:
   - Subagent 1: Scanner service (Rust)
   - Subagent 2: Oracle service (Python)
   - Subagent 3: gRPC proto definitions
4. bash_tool (cargo test && pytest)
```

---

### Scenario 6: Database Work (Layer 4)

| Task | Tools to Use | Details |
|------|--------------|---------|
| **Schema Creation** | view (architecture plan) → create_file | SQL schema files |
| **Migration Script** | view (architecture plan) → create_file + bash_tool (psql) | Versioned migrations |
| **Complex Query** | MCP (database) → bash_tool (EXPLAIN ANALYZE) | Performance optimization |
| **Backup/Restore** | bash_tool (pg_dump/pg_restore) → create_file (script) | Automation scripts |
| **Index Design** | extended_thinking (query patterns) → create_file | Performance tuning |

**Example:**
```markdown
Task: "Create findings table with partitioning"

Tools Used:
1. view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md (Layer 4 section)
2. extended_thinking (design partitioning strategy: monthly vs yearly)
3. create_file (001_findings_table.sql)
4. bash_tool (psql -f 001_findings_table.sql)
5. bash_tool (psql -c "EXPLAIN SELECT ..." - verify indexes work)
```

---

### Scenario 7: Infrastructure (Layer 5)

| Task | Tools to Use | Details |
|------|--------------|---------|
| **Dockerfile** | view (architecture plan) → create_file | Per-service containers |
| **docker-compose** | view (architecture plan) → create_file + bash_tool (compose up) | Orchestration |
| **Deployment Script** | bash_tool (test commands) → create_file (deploy.sh) | Automation |
| **Health Checks** | view (architecture plan) → create_file + bash_tool (curl) | Service monitoring |
| **Environment Config** | view (architecture plan) → create_file (.env.example) | Configuration mgmt |

**Example:**
```markdown
Task: "Create docker-compose.yml for all services"

Tools Used:
1. view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md (Layer 5 section)
2. extended_thinking (design service dependencies and startup order)
3. create_file (docker-compose.yml)
4. bash_tool (docker-compose config - validate)
5. bash_tool (docker-compose up -d - test)
6. bash_tool (docker-compose ps - verify all healthy)
```

---

### Scenario 8: Security (Layer 6)

| Task | Tools to Use | Details |
|------|--------------|---------|
| **API Key Generation** | view (architecture plan) → create_file (script) + bash_tool (test) | Authentication |
| **Encryption** | view (V3 security.py) → create_file (reuse patterns) | AES-256 encryption |
| **SSL/TLS Setup** | view (architecture plan) → bash_tool (openssl) → create_file | Certificate mgmt |
| **Audit Logging** | view (architecture plan) → create_file | Security events |
| **Vulnerability Check** | bash_tool (safety check) → extended_thinking (mitigation) | Security review |

**Example:**
```markdown
Task: "Implement API key authentication for FastAPI"

Tools Used:
1. view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md (Layer 6 section)
2. view /mnt/project/VERIFICATION_CHECKLISTS.md (security checklist)
3. extended_thinking (design key storage: hash vs encryption)
4. subagents:
   - Subagent 1: Generate API key script
   - Subagent 2: FastAPI middleware
   - Subagent 3: Tests
5. bash_tool (pytest - verify auth works)
```

---

### Scenario 9: DevOps/Monitoring (Layer 7)

| Task | Tools to Use | Details |
|------|--------------|---------|
| **Logging Setup** | view (architecture plan) → create_file (config.py) | JSON structured logs |
| **Health Monitoring** | view (architecture plan) → create_file + bash_tool (test) | Service health checks |
| **Dashboard** | view (frontend-design) → create_file (simple Flask app) | Monitoring UI |
| **Alerts** | view (architecture plan) → create_file (Telegram bot) | Alert system |
| **Log Analysis** | bash_tool (jq queries) → create_file (analysis script) | Log processing |

**Example:**
```markdown
Task: "Create health monitoring dashboard"

Tools Used:
1. view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md (Layer 7 section)
2. view /mnt/skills/public/frontend-design/SKILL.md (if web UI)
3. subagents:
   - Subagent 1: Health checker service
   - Subagent 2: Simple web UI
   - Subagent 3: Telegram alerter
4. bash_tool (test health checks)
```

---

## 🔄 MULTI-LAYER WORKFLOWS

### Workflow 1: Complete Feature (All Layers)

**Example:** "Implement 'export findings to CSV' feature"

```markdown
# LAYER 4: Database
Tools: view + create_file
Output: Export SQL query

# LAYER 2: API
Tools: view + create_file
Output: GET /api/vault/export/csv endpoint

# LAYER 3: Backend (if needed)
Tools: view + create_file
Output: CSV generation logic

# LAYER 1: Frontend
Tools: view (frontend-design) + create_file
Output: Export button in Vault page

# LAYER 7: DevOps
Tools: view + create_file
Output: Export logging

# COORDINATION
Tools: subagents (one per layer) → extended_thinking (integration)
Main Agent: Integrates all layers + tests end-to-end
```

---

### Workflow 2: Performance Optimization

**Example:** "Optimize Scanner service for 10,000 keys/sec"

```markdown
# ANALYSIS
Tools: 
- bash_tool (cargo bench - baseline)
- extended_thinking (identify bottlenecks)

# OPTIMIZATION
Tools:
- view (architecture plan - check targets)
- str_replace (modify Rust code)
- bash_tool (cargo bench - verify improvement)

# VERIFICATION
Tools:
- bash_tool (cargo test - ensure no breakage)
- extended_thinking (analyze trade-offs)

# DOCUMENTATION
Tools:
- str_replace (update comments with optimizations)
- create_file (performance benchmark results)
```

---

### Workflow 3: Bug Fix

**Example:** "Fix failing test in API layer"

```markdown
# REPRODUCTION
Tools:
- bash_tool (pytest -v - identify exact failure)
- view (read test code)
- view (read implementation code)

# ANALYSIS
Tools:
- extended_thinking (understand root cause)
- bash_tool (add debug logging if needed)

# FIX
Tools:
- str_replace (modify code)
- bash_tool (pytest - verify fix)

# REGRESSION CHECK
Tools:
- bash_tool (pytest --cov - full suite)
- view (VERIFICATION_CHECKLISTS.md - quality gates)

# DOCUMENTATION
Tools:
- str_replace (add comment explaining fix)
- conversation_search (check if similar issue before)
```

---

## ⚠️ ANTI-PATTERNS (What NOT to Do)

### Anti-Pattern 1: Skipping view Tool

**❌ Wrong:**
```markdown
User: "Create a presentation about NPS V4"
AI: [Immediately creates slides without reading pptx skill]
```

**✅ Correct:**
```markdown
User: "Create a presentation about NPS V4"
AI: 
1. view /mnt/skills/public/pptx/SKILL.md
2. view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md
3. [Then create slides following skill patterns]
```

---

### Anti-Pattern 2: Wrong Tool for Job

**❌ Wrong:**
```markdown
Task: "Create complex multi-component React app"
Tools: Just create_file (no skills, no subagents)
Result: Generic, low-quality output
```

**✅ Correct:**
```markdown
Task: "Create complex multi-component React app"
Tools:
1. view (web-artifacts-builder skill)
2. extended_thinking (architecture design)
3. subagents (component splitting)
4. create_file (per subagent)
Result: Production-grade, well-architected app
```

---

### Anti-Pattern 3: No Verification

**❌ Wrong:**
```markdown
Tools: create_file
[No bash_tool to test]
[No verification steps]
```

**✅ Correct:**
```markdown
Tools:
1. create_file (implementation)
2. bash_tool (run tests)
3. bash_tool (check performance)
4. Provide verification checklist
```

---

## 📊 TOOL SELECTION FLOWCHART

```
START: New Task
    ↓
Read Architecture Plan
(view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md)
    ↓
What type of task?
    ↓
┌─────────────────────────────────────────────┐
│ FILE CREATION                               │
│ → Check Skills Playbook                     │
│ → view applicable SKILL.md                  │
│ → Use create_file                           │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ MULTI-FILE (3+)                             │
│ → Use subagents                             │
│ → Coordinate with clear dependencies        │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ COMPLEX DECISION                            │
│ → Use extended_thinking                     │
│ → Consider trade-offs                       │
│ → Document reasoning                        │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ UNCLEAR/AMBIGUOUS                           │
│ → Use ask_user                              │
│ → Present 2-3 options                       │
│ → Get confirmation before proceeding        │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ VERIFICATION NEEDED                         │
│ → Use bash_tool                             │
│ → Run tests                                 │
│ → Check performance                         │
│ → Verify against checklist                  │
└─────────────────────────────────────────────┘
    ↓
COMPLETE: All tools used appropriately
```

---

## 🎯 QUICK REFERENCE TABLE

| Scenario | Primary Tool | Secondary Tools | Verification |
|----------|--------------|-----------------|--------------|
| Create Word doc | docx skill | view | bash_tool (open file) |
| Build React UI | frontend-design | theme-factory, subagents | bash_tool (npm test) |
| API endpoint | product-self-knowledge | subagents (tests), extended_thinking | bash_tool (pytest) |
| Rust service | - | extended_thinking (design), subagents | bash_tool (cargo test) |
| Database schema | - | extended_thinking (indexes), MCP (if complex) | bash_tool (psql) |
| Docker setup | - | extended_thinking (dependencies) | bash_tool (docker-compose) |
| Security feature | - | extended_thinking (threat model), V3 code review | bash_tool (security tests) |
| Monitoring | frontend-design (if UI) | bash_tool (test health checks) | bash_tool (curl) |
| Bug fix | view, str_replace | bash_tool (reproduce), extended_thinking | bash_tool (regression tests) |
| High-stakes decision | ask_user | extended_thinking (options analysis) | User confirmation |

---

## 📚 TOOL USAGE STATISTICS (Learn from Patterns)

Based on NPS V4 requirements, expected tool usage distribution:

| Tool | Usage % | Most Common Scenarios |
|------|---------|----------------------|
| view | 100% | Every task starts with architecture plan |
| create_file | 80% | Most tasks create files |
| bash_tool | 75% | Verification is mandatory |
| Skills | 60% | Document creation, UI building, API work |
| Subagents | 40% | Multi-file tasks (3+ files) |
| extended_thinking | 30% | Complex decisions, architecture, trade-offs |
| ask_user | 20% | High-stakes decisions, ambiguous requirements |
| str_replace | 15% | Bug fixes, modifications |
| conversation_search | 10% | Session continuity |
| MCP servers | 5% | Specialized database/Git operations |

---

**Remember:** The right tool for the right job = Swiss watch precision. 🚀

*Version: 1.0*  
*Last Updated: 2026-02-08*
