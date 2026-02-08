# NPS V4 - CLAUDE CODE STARTUP PROTOCOL
**Version:** 1.0  
**Date:** 2026-02-08  
**Purpose:** Automatic workflow initialization for Claude Code CLI sessions

---

## 🎯 CRITICAL INSTRUCTION

**YOU ARE CLAUDE CODE CLI WORKING ON NPS V4 PROJECT.**

Before ANY action, you MUST execute this 5-stage startup workflow:

```
INIT → MEMORY → CURRENT STATE → TASK → GATE
```

**This is non-negotiable.** Every session starts here.

---

## 📋 WORKFLOW EXECUTION SEQUENCE

### STAGE 1: INIT 🚀

**Purpose:** Load project context and establish baseline understanding

**Mandatory Actions:**
1. **Read Architecture Plan**
   ```bash
   view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md
   ```
   - Identify: 7-layer architecture
   - Note: Current phase in build sequence
   - Understand: Scanner ↔ Oracle collaboration pattern

2. **Read Skills Playbook**
   ```bash
   view /mnt/project/SKILLS_PLAYBOOK.md
   ```
   - Identify: Available skills for task type
   - Note: Skill combination patterns
   - Prepare: Skill reading list

3. **Read Tool Orchestration**
   ```bash
   view /mnt/project/TOOL_ORCHESTRATION_MATRIX.md
   ```
   - Identify: Which tools apply to this session
   - Note: Complexity level (Simple/Medium/Complex)
   - Prepare: Tool usage strategy

4. **Check Project Structure**
   ```bash
   ls -la .
   find . -type d -maxdepth 2
   ```
   - Identify: Which layers exist
   - Note: Project organization
   - Detect: Missing components

**Output:** Create `/tmp/init_status.json`
```json
{
  "architecture_loaded": true,
  "skills_identified": ["skill1", "skill2"],
  "tools_selected": ["tool1", "tool2"],
  "project_structure": {
    "frontend": "exists|missing",
    "api": "exists|missing",
    "backend": "exists|missing",
    "database": "exists|missing",
    "infrastructure": "exists|missing",
    "security": "exists|missing",
    "devops": "exists|missing"
  },
  "init_timestamp": "2026-02-08T10:30:00Z"
}
```

**Checkpoint:** STOP if any mandatory file is missing. Request file upload.

---

### STAGE 2: MEMORY 🧠

**Purpose:** Load session history and accumulated knowledge

**Mandatory Actions:**

1. **Check for Session Handoff**
   ```bash
   # Look for previous session handoff
   find . -name "SESSION_HANDOFF*.md" -type f | sort -r | head -1
   ```
   
   **If handoff exists:**
   - Read entire handoff document
   - Extract: Last completed phase
   - Extract: In-progress work status
   - Extract: Known blockers
   - Extract: Next priority actions
   
   **If no handoff:**
   - Check git log for recent commits
   - Analyze code for TODO/FIXME comments
   - Identify incomplete features (stub functions, empty files)

2. **Check Git History**
   ```bash
   git log --oneline -10
   git status
   git diff HEAD~1 (if applicable)
   ```
   - Identify: Recent changes
   - Note: Current branch
   - Detect: Uncommitted work

3. **Load Learning Data**
   ```bash
   # Check for accumulated patterns
   find . -name "LESSONS_LEARNED*.md" -type f
   find . -name "ERROR_RECOVERY*.md" -type f
   ```
   - Extract: Successful patterns
   - Extract: Failed approaches
   - Extract: Known gotchas

4. **Scan for Context Clues**
   ```bash
   # Find all README files
   find . -name "README*.md" -type f
   
   # Find all TODO files
   grep -r "TODO\|FIXME\|HACK" --include="*.py" --include="*.rs" --include="*.ts" | head -20
   ```

**Output:** Create `/tmp/memory_status.json`
```json
{
  "session_handoff_found": true,
  "last_session_date": "2026-02-07",
  "completed_phases": ["Phase 1", "Phase 2A"],
  "in_progress": {
    "phase": "Phase 2B",
    "status": "65% complete",
    "next_step": "Complete Oracle pattern analysis tests"
  },
  "blockers": [
    {
      "type": "decision_needed",
      "description": "Oracle caching strategy",
      "options": ["LRU cache", "Time-based cache"]
    }
  ],
  "git_status": {
    "branch": "feature/oracle-service",
    "uncommitted_changes": 3,
    "last_commit": "feat: add pattern analysis service"
  },
  "memory_timestamp": "2026-02-08T10:31:00Z"
}
```

**Checkpoint:** STOP if critical blocker exists. Present to user first.

---

### STAGE 3: CURRENT STATE 📊

**Purpose:** Determine exact project state and validate completeness

**Mandatory Actions:**

1. **Phase Detection**
   
   For each layer, check for key deliverables:
   
   ```bash
   # Phase 1: API + Database
   [ -d "api/app/routers" ] && echo "API: STARTED"
   [ -f "database/migrations/001_initial_schema.sql" ] && echo "Database: STARTED"
   
   # Phase 2: Backend Services
   [ -d "backend/scanner-service/src" ] && echo "Scanner: STARTED"
   [ -d "backend/oracle-service/app" ] && echo "Oracle: STARTED"
   
   # Phase 3: Frontend
   [ -d "frontend/web-ui/src" ] && echo "Frontend: STARTED"
   
   # Phase 4: Infrastructure
   [ -f "docker-compose.yml" ] && echo "Infrastructure: STARTED"
   
   # Phase 5: Security
   [ -d "security/auth" ] && echo "Security: STARTED"
   
   # Phase 6: DevOps
   [ -d "devops/monitoring" ] && echo "DevOps: STARTED"
   
   # Phase 7: Integration
   [ -d "tests/integration" ] && echo "Integration: STARTED"
   ```

2. **Quality Verification**
   
   ```bash
   # Run existing tests
   if [ -d "api/tests" ]; then
     cd api && pytest tests/ -v --tb=short || echo "API TESTS: SOME FAILING"
   fi
   
   if [ -d "backend/scanner-service" ]; then
     cd backend/scanner-service && cargo test || echo "SCANNER TESTS: SOME FAILING"
   fi
   
   # Check for syntax errors
   find . -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | grep -v "^$"
   ```

3. **Dependency Check**
   
   ```bash
   # Python dependencies
   if [ -f "api/requirements.txt" ]; then
     pip freeze | diff - api/requirements.txt || echo "API: Dependencies mismatch"
   fi
   
   # Rust dependencies
   if [ -f "backend/scanner-service/Cargo.toml" ]; then
     cd backend/scanner-service && cargo check || echo "Scanner: Dependency issues"
   fi
   
   # Node dependencies
   if [ -f "frontend/web-ui/package.json" ]; then
     cd frontend/web-ui && npm ls || echo "Frontend: Dependency issues"
   fi
   ```

4. **Environment Verification**
   
   ```bash
   # Check required environment variables
   if [ -f ".env.example" ]; then
     echo "Checking .env completeness..."
     diff <(grep -v '^#' .env.example | cut -d= -f1) <(grep -v '^#' .env | cut -d= -f1) || echo "ENV: Missing variables"
   fi
   ```

**Output:** Create `/tmp/current_state.json`
```json
{
  "phase_completion": {
    "phase_1": {
      "api": "100%",
      "database": "100%",
      "verified": true,
      "tests_passing": "45/50"
    },
    "phase_2": {
      "scanner": "100%",
      "oracle": "65%",
      "verified": false,
      "tests_passing": "12/18"
    },
    "phase_3": {
      "frontend": "0%",
      "verified": false
    }
  },
  "failing_tests": [
    "api/tests/test_oracle.py::test_suggest_range",
    "backend/oracle-service/tests/test_pattern_service.py::test_analyze_patterns"
  ],
  "missing_dependencies": [],
  "environment_issues": ["ORACLE_AI_TIMEOUT not set"],
  "next_logical_phase": "Complete Phase 2B (Oracle service testing)",
  "state_timestamp": "2026-02-08T10:32:00Z"
}
```

**Checkpoint:** STOP if any Phase X verification failed. Cannot proceed to Phase X+1.

---

### STAGE 4: TASK 🎯

**Purpose:** Determine next action based on context

**Decision Algorithm:**

```python
def determine_next_task(memory, current_state, user_input=None):
    """
    Priority order:
    1. User explicit instruction (if provided)
    2. Critical blocker from memory
    3. Failing tests from current state
    4. In-progress work from memory
    5. Next logical phase from current state
    """
    
    if user_input and user_input.is_explicit_instruction:
        return Task(
            type="user_directed",
            description=user_input.instruction,
            priority="P0"
        )
    
    if memory.blockers and any(b.type == "critical" for b in memory.blockers):
        return Task(
            type="resolve_blocker",
            description=memory.blockers[0].description,
            priority="P1"
        )
    
    if current_state.failing_tests:
        return Task(
            type="fix_tests",
            description=f"Fix {len(current_state.failing_tests)} failing tests",
            tests=current_state.failing_tests,
            priority="P1"
        )
    
    if memory.in_progress and memory.in_progress.status < "90%":
        return Task(
            type="continue_work",
            description=memory.in_progress.next_step,
            priority="P2"
        )
    
    return Task(
        type="next_phase",
        description=current_state.next_logical_phase,
        priority="P3"
    )
```

**Mandatory Actions:**

1. **Analyze User Input**
   - If user provided specific instruction → Use it
   - If user said "continue" → Use memory + current state
   - If user uploaded ZIP → Full project analysis first

2. **Identify Task Type**
   - Fix (something broken)
   - Continue (something started)
   - Create (something new)
   - Optimize (something slow)
   - Document (something undocumented)

3. **Scope Definition**
   - Affected layers: [List]
   - Affected files: [Estimate]
   - Dependencies: [List]
   - Estimated complexity: Simple | Medium | Complex
   - Estimated duration: [Hours]

4. **Tool Selection**
   Based on complexity:
   - **Simple:** No special tools
   - **Medium:** Extended thinking + 1-2 skills
   - **Complex:** Extended thinking + subagents + all applicable skills

**Output:** Create `/tmp/task_definition.json`
```json
{
  "task_id": "TASK_2026_02_08_001",
  "type": "fix_tests",
  "description": "Fix 5 failing Oracle service tests",
  "priority": "P1",
  "scope": {
    "layers": ["Layer 2 (API)", "Layer 3B (Oracle)"],
    "estimated_files": 3,
    "estimated_changes": "50-100 lines",
    "dependencies": ["PostgreSQL running", "Test fixtures updated"],
    "complexity": "medium",
    "duration_estimate": "1-2 hours"
  },
  "tools_required": {
    "extended_thinking": true,
    "skills": ["product-self-knowledge"],
    "subagents": false,
    "mcp_servers": ["database_mcp"]
  },
  "acceptance_criteria": [
    "All 5 tests pass (pytest tests/test_*.py)",
    "Test coverage remains ≥95%",
    "No breaking changes to other components"
  ],
  "task_timestamp": "2026-02-08T10:33:00Z"
}
```

**Checkpoint:** If task is high-stakes (architecture, security, cost), ASK USER before proceeding.

---

### STAGE 5: GATE ✅

**Purpose:** Validate prerequisites and get approval before execution

**Mandatory Checks:**

1. **Prerequisite Verification**
   
   ```bash
   # Check all dependencies are met
   for dep in ${TASK_DEPENDENCIES[@]}; do
     check_dependency "$dep" || GATE_FAILED=true
   done
   ```
   
   Common prerequisites:
   - Previous phase verified ✅
   - Required services running (PostgreSQL, etc.)
   - Required tools available (pytest, cargo, npm)
   - Environment variables set
   - No uncommitted breaking changes

2. **Risk Assessment**
   
   ```python
   risk_level = calculate_risk(
       affects_multiple_layers=True,
       changes_database_schema=False,
       affects_security=False,
       performance_impact="low",
       breaking_changes=False
   )
   # risk_level: "low" | "medium" | "high"
   ```

3. **User Approval** (if needed)
   
   **Require approval if:**
   - Risk level: High
   - Affects: Database schema
   - Affects: Security layer
   - Affects: Multiple layers simultaneously
   - Decision: Multiple valid approaches exist
   
   **Approval format:**
   ```markdown
   ## ⚠️ GATE CHECKPOINT - APPROVAL REQUIRED
   
   **Task:** [Description]
   **Risk Level:** [High/Medium/Low]
   **Affected Layers:** [List]
   **Changes:** [Summary]
   
   **Impact:**
   - Performance: [Impact]
   - Security: [Impact]
   - Breaking changes: [Yes/No]
   
   **Approach:**
   [Detailed approach with reasoning]
   
   **Alternatives considered:**
   1. Option A - [Pros/Cons]
   2. Option B - [Pros/Cons]
   
   **Recommendation:** [Option X] because [reasoning]
   
   **Proceed?** [Waiting for user confirmation]
   ```

4. **Verification Checklist**
   
   ```markdown
   Before execution, confirm:
   
   - [ ] Architecture plan read and understood
   - [ ] Applicable skills identified and read
   - [ ] Tools selected appropriately for complexity
   - [ ] Task scoped with measurable acceptance criteria
   - [ ] Prerequisites verified (all dependencies met)
   - [ ] Risk assessed and approved (if high-risk)
   - [ ] Verification steps prepared (2-minute check ready)
   - [ ] Handoff plan prepared (for session end)
   ```

**Output:** Create `/tmp/gate_approval.json`
```json
{
  "gate_status": "APPROVED",
  "prerequisites_met": true,
  "risk_level": "medium",
  "user_approval_required": false,
  "user_approval_received": null,
  "checklist_complete": true,
  "ready_to_execute": true,
  "gate_timestamp": "2026-02-08T10:34:00Z"
}
```

**Checkpoint:** STOP if gate status is not "APPROVED". Resolve issues first.

---

## 🚀 POST-GATE: EXECUTION PHASE

**Once gate is approved, proceed with:**

1. **Extended Thinking** (if applicable)
   - Analyze approach
   - Consider trade-offs
   - Document decision rationale

2. **Skill Reading** (if applicable)
   - Read all identified SKILL.md files
   - Follow patterns exactly

3. **Subagent Coordination** (if applicable)
   - Spawn subagents for parallel work
   - Define clear coordination points
   - Collect and verify outputs

4. **Implementation**
   - Create files
   - Write code
   - Run tests
   - Verify acceptance criteria

5. **Quality Verification**
   - Run verification checklist
   - Document results
   - Update metrics

6. **Session Handoff**
   - Create handoff document (if session ending)
   - Update current state files
   - Commit changes (if appropriate)

---

## 📁 PROJECT ROOT FILE STRUCTURE

**Required files in project root:**

```
/project-root/
├── .workflow/                          # Workflow state files
│   ├── init_status.json                # Stage 1 output
│   ├── memory_status.json              # Stage 2 output
│   ├── current_state.json              # Stage 3 output
│   ├── task_definition.json            # Stage 4 output
│   └── gate_approval.json              # Stage 5 output
│
├── .sessions/                          # Session history
│   ├── SESSION_HANDOFF_2026_02_07.md   # Previous session
│   └── SESSION_HANDOFF_2026_02_08.md   # Current session
│
├── .lessons/                           # Accumulated knowledge
│   ├── LESSONS_LEARNED.md              # Successful patterns
│   └── GOTCHAS.md                      # Known issues
│
└── PROJECT_STATE.md                    # Human-readable status
```

**Auto-create on first run:**

```bash
mkdir -p .workflow .sessions .lessons
touch PROJECT_STATE.md
```

---

## 🔄 CONTINUOUS WORKFLOW LOOP

**Every time Claude Code CLI starts:**

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  NEW SESSION DETECTED                           │
│                                                 │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│                                                 │
│  STAGE 1: INIT                                  │
│  ✓ Read architecture plan                       │
│  ✓ Read skills playbook                         │
│  ✓ Read tool orchestration                      │
│  ✓ Check project structure                      │
│  ✓ Create /tmp/init_status.json                 │
│                                                 │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│                                                 │
│  STAGE 2: MEMORY                                │
│  ✓ Load session handoff (if exists)             │
│  ✓ Check git history                            │
│  ✓ Load lessons learned                         │
│  ✓ Scan for context clues                       │
│  ✓ Create /tmp/memory_status.json               │
│                                                 │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│                                                 │
│  STAGE 3: CURRENT STATE                         │
│  ✓ Detect phase completion                      │
│  ✓ Run quality verification                     │
│  ✓ Check dependencies                           │
│  ✓ Verify environment                           │
│  ✓ Create /tmp/current_state.json               │
│                                                 │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│                                                 │
│  STAGE 4: TASK                                  │
│  ✓ Analyze user input (if any)                  │
│  ✓ Apply decision algorithm                     │
│  ✓ Define task scope                            │
│  ✓ Select tools                                 │
│  ✓ Create /tmp/task_definition.json             │
│                                                 │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│                                                 │
│  STAGE 5: GATE                                  │
│  ✓ Verify prerequisites                         │
│  ✓ Assess risk                                  │
│  ✓ Request approval (if high-risk)              │
│  ✓ Complete checklist                           │
│  ✓ Create /tmp/gate_approval.json               │
│                                                 │
└─────────────────────────────────────────────────┘
                     ↓
             ┌───────┴────────┐
             │                │
             ├─ APPROVED? ────┤
             │                │
             └───────┬────────┘
                     ↓ YES
┌─────────────────────────────────────────────────┐
│                                                 │
│  EXECUTION PHASE                                │
│  → Extended thinking                            │
│  → Read skills                                  │
│  → Spawn subagents (if needed)                  │
│  → Implement                                    │
│  → Verify                                       │
│  → Create handoff                               │
│                                                 │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│                                                 │
│  SESSION END                                    │
│  ✓ Handoff document created                     │
│  ✓ State files updated                          │
│  ✓ Ready for next session                       │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 📊 SUCCESS METRICS

**Every workflow execution should produce:**

1. **State Files** (5 JSON files in .workflow/)
2. **Handoff Document** (if session ends)
3. **Measurable Progress** (phase completion %)
4. **Quality Evidence** (test results, verification output)

**Workflow is successful when:**
- ✅ All 5 stages completed sequentially
- ✅ All checkpoints passed
- ✅ Gate approved (user or automatic)
- ✅ Execution phase completed with verification
- ✅ Handoff created for continuity

---

## ⚠️ FAILURE MODES & RECOVERY

### Failure Mode 1: Missing Architecture Files

**Symptom:** Cannot read `/mnt/project/NPS_V4_ARCHITECTURE_PLAN.md`

**Recovery:**
```
HALT WORKFLOW
Request user to upload project knowledge files:
- NPS_V4_ARCHITECTURE_PLAN.md
- SKILLS_PLAYBOOK.md
- TOOL_ORCHESTRATION_MATRIX.md
- VERIFICATION_CHECKLISTS.md
- ERROR_RECOVERY.md
```

### Failure Mode 2: Checkpoint Failed

**Symptom:** Phase X verification shows critical failures

**Recovery:**
```
HALT WORKFLOW
Present checkpoint status to user:
- What failed
- Why it matters
- Options to resolve
- Recommended next step

DO NOT PROCEED to next phase until resolved.
```

### Failure Mode 3: High-Risk Gate Without Approval

**Symptom:** Gate assessment shows high-risk, no user approval

**Recovery:**
```
HALT WORKFLOW
Present gate approval request (formatted as above)
WAIT for user response
DO NOT auto-approve high-risk gates
```

---

## 🎯 FIRST RUN INITIALIZATION

**When running for the first time on a project:**

1. **Detect First Run**
   ```bash
   if [ ! -d ".workflow" ]; then
     echo "FIRST RUN DETECTED"
     FIRST_RUN=true
   fi
   ```

2. **Initialize Project Structure**
   ```bash
   mkdir -p .workflow .sessions .lessons
   touch .lessons/LESSONS_LEARNED.md
   touch .lessons/GOTCHAS.md
   ```

3. **Create Initial State**
   ```bash
   cat > PROJECT_STATE.md << 'EOF'
   # NPS V4 Project State
   **Last Updated:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
   
   ## Current Phase
   Phase 0: Project initialization
   
   ## Completed Milestones
   - [x] Project structure created
   - [x] Workflow system initialized
   
   ## In Progress
   - [ ] Architecture setup pending
   
   ## Next Actions
   1. Review architecture plan
   2. Begin Phase 1 (API + Database)
   EOF
   ```

4. **Proceed with normal workflow**
   ```
   → STAGE 1: INIT
   ```

---

## 📖 REFERENCE GUIDE

### Quick Commands

**Check workflow status:**
```bash
cat .workflow/gate_approval.json | jq .gate_status
```

**View current task:**
```bash
cat .workflow/task_definition.json | jq .description
```

**Check phase completion:**
```bash
cat .workflow/current_state.json | jq .phase_completion
```

**Resume from last session:**
```bash
cat .sessions/SESSION_HANDOFF_$(ls -t .sessions/ | head -1) | grep "Next Priority"
```

### File Locations Reference

| Component | Location |
|-----------|----------|
| Architecture Plan | `/mnt/project/NPS_V4_ARCHITECTURE_PLAN.md` |
| Skills Playbook | `/mnt/project/SKILLS_PLAYBOOK.md` |
| Tool Orchestration | `/mnt/project/TOOL_ORCHESTRATION_MATRIX.md` |
| Verification Checklists | `/mnt/project/VERIFICATION_CHECKLISTS.md` |
| Error Recovery | `/mnt/project/ERROR_RECOVERY.md` |
| Session Handoff Template | `/mnt/project/SESSION_HANDOFF_TEMPLATE.md` |
| Subagent Patterns | `/mnt/project/SUBAGENT_PATTERNS.md` |

---

## ✅ COMPLIANCE VERIFICATION

**Before claiming workflow complete, verify:**

- [ ] STAGE 1 (INIT): init_status.json created
- [ ] STAGE 2 (MEMORY): memory_status.json created
- [ ] STAGE 3 (CURRENT STATE): current_state.json created
- [ ] STAGE 4 (TASK): task_definition.json created
- [ ] STAGE 5 (GATE): gate_approval.json created with status "APPROVED"
- [ ] All checkpoints passed (no HALT conditions triggered)
- [ ] Execution phase completed (if gate approved)
- [ ] Verification run (acceptance criteria checked)
- [ ] Handoff created (if session ending)

---

## 🏆 FINAL INSTRUCTION

**YOU MUST EXECUTE THIS WORKFLOW ON EVERY SESSION START.**

No exceptions. No shortcuts. This ensures:
- ✅ 100% context loading
- ✅ No duplicated work
- ✅ No regression
- ✅ Swiss watch precision
- ✅ Perfect continuity between sessions

**The workflow is the foundation of NPS V4 quality.**

Start now. Init → Memory → Current State → Task → Gate.

🚀

---

*Version: 1.0*  
*Status: Production Ready*  
*Compliance: 100% Mandatory*
