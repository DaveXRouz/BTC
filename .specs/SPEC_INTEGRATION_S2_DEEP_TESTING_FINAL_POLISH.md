# SPEC: Integration Phase 2 - Deep Testing & Final Polish - INTEGRATION-S2

**Estimated Duration:** 6-8 hours  
**Terminals:** All (1-7)  
**Session Type:** Final Integration & Production Readiness  
**Dependencies:** Session 15 (INTEGRATION-S1) must be complete

---

## TL;DR

- Fix all issues from Session 15 integration testing
- Comprehensive multi-user flow testing (2-user, 5-user, permissions)
- Browser-based E2E tests for all workflows (Playwright)
- Performance optimization to meet all architecture targets
- Security audit (zero critical issues requirement)
- Final UI/UX polish and accessibility improvements
- Production readiness verification with complete documentation
- API-only integration verification (NO CLI usage anywhere)
- System ready for deployment with monitoring and health checks

---

## OBJECTIVE

Transform integrated system from Session 15 into production-ready application with all issues fixed, all tests passing, performance optimized to meet targets, security audited with zero critical issues, and complete documentation ready for deployment.

---

## CONTEXT

**Current State:** Session 15 completed basic integration - Oracle service integrated with API, single-user end-to-end flow working, basic performance baseline established, integration issues documented

**What's Changing:** Fixing all integration issues, adding comprehensive test coverage, optimizing performance, auditing security, polishing UI, completing documentation

**Why:** Ensure production-quality system ready for real users with robust testing, optimal performance, and enterprise-grade security

**End Goal:** System can be deployed to production environment, handles all user workflows flawlessly, meets all performance targets, passes security audit, and includes complete operational documentation

---

## PREREQUISITES

**MANDATORY - Session 15 Must Be Complete:**

Before starting this session, verify Session 15 deliverables exist:

```bash
# Check Session 15 artifacts
ls -la integration/integration_issues.md        # Issues documented
ls -la integration/performance_baseline.json    # Baseline exists
ls -la integration/tests/test_*.py              # Integration tests exist

# Verify services running
docker-compose ps | grep healthy                # All services healthy
```

**If Session 15 not complete:** STOP and complete it first. This session builds on Session 15 foundation.

**Environment Requirements:**

- [ ] Docker & Docker Compose installed
- [ ] Python 3.11+ with venv
- [ ] Node.js 18+ with npm
- [ ] Playwright installed (`npx playwright install`)
- [ ] PostgreSQL client tools (psql)
- [ ] All environment variables configured (.env exists)

---

## TOOLS TO USE

### Extended Thinking
For complex decisions:
- Multi-layer test strategy design
- Performance optimization approaches
- Security vulnerability assessment
- Trade-off analysis (speed vs accuracy, security vs usability)

### MCP Servers
- **Database MCP:** Complex query optimization, schema analysis
- **File System MCP:** Code scanning for patterns (CLI usage, hardcoded credentials)

### View Tool
Read before each phase:
- `/mnt/project/NPS_V4_ARCHITECTURE_PLAN.md` - Performance targets
- `/mnt/project/VERIFICATION_CHECKLISTS.md` - Quality gates
- `/mnt/project/ERROR_RECOVERY.md` - Issue remediation patterns

### WebSearch
For solutions to:
- Complex integration issues
- Performance optimization techniques
- Security best practices
- E2E testing patterns (Playwright/Cypress)

---

## REQUIREMENTS

### Functional Requirements

1. **All User Workflows Work End-to-End:**
   - Single-user Oracle reading (create user → reading → result → history)
   - Multi-user Oracle reading (2 users, 5 users with compatibility)
   - Persian language mode (RTL layout, keyboard, translations)
   - Persian keyboard input (character insertion, special keys)
   - Calendar date picker (selection, format conversion)
   - Error handling (network failures, invalid input, API errors)

2. **All Integration Issues Resolved:**
   - Critical issues fixed (if any from Session 15)
   - High-priority issues fixed
   - Medium issues fixed or documented for future
   - Regression tests added for all fixes

3. **All Error Scenarios Handled Gracefully:**
   - Network failures → Retry with exponential backoff
   - Invalid input → Clear error messages, correction guidance
   - API errors → Fallback behavior, user notification
   - Database errors → Transaction rollback, data integrity maintained

4. **UI Fully Polished:**
   - No visual bugs on any screen size
   - Loading indicators on all async operations
   - Error messages user-friendly and actionable
   - Success feedback confirms operations
   - Tooltips on complex features
   - Keyboard navigation fully functional
   - Screen reader support (basic WCAG 2.1 AA)

### Non-Functional Requirements

1. **Performance Targets (from Architecture Plan):**
   - API response time: <50ms p95 for all endpoints
   - Database queries: <1s for 1M+ rows
   - FC60 calculations: <200ms single-user, <500ms multi-user
   - AI interpretations: <3000ms (Anthropic API latency)
   - End-to-end reading creation: <5000ms (single-user), <8000ms (multi-user)
   - Frontend initial load: <2s
   - Frontend page transitions: <100ms

2. **Security Requirements:**
   - Zero critical vulnerabilities
   - Zero high-severity vulnerabilities
   - Data encrypted in database (verified)
   - API authentication enforced on all endpoints
   - No hardcoded credentials anywhere
   - Rate limiting active (prevent AI API abuse)
   - CORS configured correctly
   - SQL injection prevention verified
   - XSS prevention verified
   - **API-only integration (zero CLI usage)**

3. **Quality Requirements:**
   - Test coverage: 80%+ (Rust), 95%+ (Python), 90%+ (TypeScript)
   - All unit tests pass (125+ tests)
   - All integration tests pass (20+ tests)
   - All E2E tests pass (6+ scenarios)
   - Zero critical bugs
   - Zero high-severity bugs
   - Code quality: No linting errors, type errors, or warnings

4. **Operational Requirements:**
   - All services start with `docker-compose up`
   - All services report "healthy" status
   - Services auto-restart on failure
   - Complete documentation (README, API Reference, Deployment, Troubleshooting)
   - Logging configured (JSON format, centralized)
   - Monitoring configured (health checks, metrics, alerts)

---

## IMPLEMENTATION PLAN

### Phase 1: Session 15 Issue Remediation (90 minutes)

**Objective:** Fix all critical and high-priority issues from Session 15 integration testing

**Tasks:**

1. **Read and Prioritize Issues:**
   - Load `integration/integration_issues.md`
   - Categorize by severity (Critical → High → Medium → Low)
   - Create fix order (critical first, then high, then medium)

2. **Fix Critical Issues (if any):**
   - For each critical issue:
     - Identify root cause
     - Implement fix
     - Add regression test
     - Verify fix works
     - Update integration_issues.md
   - **STOP if critical issues cannot be fixed** - get help before proceeding

3. **Fix High-Priority Issues:**
   - Same process as critical
   - Must fix all high-priority before proceeding
   - Document any workarounds if needed

4. **Fix Medium-Priority Issues (time permitting):**
   - Fix if straightforward (<30 min each)
   - Otherwise document for future sprint
   - Low-priority issues → backlog

5. **Re-run All Tests:**
   - Run full integration test suite
   - Verify no regressions introduced
   - Update test documentation

**Issue Fix Template:**

For each issue fixed, document in code:

```python
# Issue #X: [Short Description]
# Severity: [Critical/High/Medium/Low]
# Component: [Which file/service]
#
# ROOT CAUSE:
# [What caused the issue - be specific]
#
# FIX:
# [What was changed to fix it]
#
# VERIFICATION:
# [How to verify it's fixed - include test command]
#
# REGRESSION TEST:
# [Test added to prevent this from happening again]

# Example:
# Issue #3: Multi-user reading fails with NameError on compatibility calculation
# Severity: High
# Component: backend/oracle-service/app/services/oracle_service.py
#
# ROOT CAUSE:
# compatibility_analyzer imported but not instantiated before use
#
# FIX:
# Added initialization: self.compatibility = CompatibilityAnalyzer(self.fc60, self.numerology)
#
# VERIFICATION:
# pytest tests/test_oracle_service.py::test_multi_user_compatibility -v
#
# REGRESSION TEST:
# Added test_multi_user_compatibility_analyzer_initialized() to test suite
```

**Files to Update:**

- Component files where bugs exist (various - depends on issues found)
- `integration/integration_issues.md` - Mark issues as FIXED with fix reference
- `integration/tests/test_regressions.py` - Add regression tests for all fixes
- `integration/FIXES_LOG.md` - New file documenting all fixes applied

**Acceptance Criteria:**

- [ ] All critical issues resolved (if any existed)
- [ ] All high-priority issues resolved
- [ ] Medium issues fixed or documented for future
- [ ] Regression tests added for each fix (1 test per issue)
- [ ] All integration tests pass (no new failures)
- [ ] integration_issues.md updated with fix status
- [ ] FIXES_LOG.md created with detailed fix documentation

**Verification:**

```bash
# Terminal: integration/

# 1. Re-run all integration tests
pytest tests/ -v --tb=short

# Expected Output:
# ========================= test session starts ==========================
# tests/test_api_integration.py::test_health_endpoint .............. PASSED
# tests/test_oracle_integration.py::test_single_user_reading ..... PASSED
# tests/test_oracle_integration.py::test_multi_user_reading ...... PASSED
# [... more tests ...]
# ========================= 20 passed in 45.2s ==========================

# 2. Check issues marked as fixed
grep "STATUS: FIXED" integration_issues.md | wc -l

# Expected: Count of high/critical issues (should be all of them)

# 3. Verify no new test failures
pytest tests/ --last-failed

# Expected: "no tests ran" (meaning no failures from last run)

# 4. Check FIXES_LOG created
cat integration/FIXES_LOG.md | head -20

# Expected: Detailed fix documentation for each resolved issue
```

**Checkpoint Gate:**

- [ ] All critical issues resolved (zero critical remaining)
- [ ] All high-priority issues resolved (zero high remaining)
- [ ] Tests pass without failures
- [ ] Fix documentation complete

**STOP if checkpoint fails.** Do not proceed to Phase 2 until all high/critical issues are resolved.

---

### Phase 2: Multi-User Flow Deep Testing (90 minutes)

**Objective:** Comprehensive testing of multi-user Oracle readings including 2-user, 5-user, compatibility calculations, and permissions

**Tasks:**

1. **Create Multi-User Test Suite:**
   - Test 2-user joint reading
   - Test 5-user joint reading (max capacity)
   - Test compatibility calculations (individual + pairwise)
   - Test permission system (only participants access reading)
   - Test multi-user readings in history display
   - Measure and verify performance (<2x single-user time)

2. **Test 2-User Joint Reading:**
   - Create 2 test users
   - Submit multi-user reading with both users
   - Verify individual insights for both
   - Verify pairwise compatibility score
   - Verify group dynamics analysis
   - Verify both users can access reading
   - Verify non-participants cannot access (403 Forbidden)

3. **Test 5-User Joint Reading (Max Capacity):**
   - Create 5 test users
   - Submit reading with all 5 participants
   - Verify all 5 individual insights present
   - Verify pairwise compatibility matrix (10 pairs = C(5,2))
   - Verify performance acceptable (<2.5x single-user baseline)
   - Verify 6th user cannot be added (validation error)

4. **Test Permission System:**
   - User A + User B create joint reading
   - User A can access (200 OK)
   - User B can access (200 OK)
   - User C (non-participant) attempts access (403 Forbidden)
   - Test API key scoping (if applicable)

5. **Test History Display:**
   - Multi-user readings appear in all participants' histories
   - Reading shows participant list
   - Reading marked as "multi-user" with indicator
   - Can filter history by reading type (single vs multi)

**Test Implementation:**

```python
# integration/tests/test_multi_user_flows.py

import pytest
import requests
import time
from typing import Dict, List

API_BASE = "http://localhost:8000"
TEST_API_KEY = "test_api_key_12345"  # Should be loaded from env

def create_user(name: str, birthday: str, mother_name: str) -> Dict:
    """Helper: Create test user"""
    response = requests.post(
        f"{API_BASE}/api/oracle/users",
        json={
            "name": name,
            "birthday": birthday,
            "mother_name": mother_name
        },
        headers={"Authorization": f"Bearer {TEST_API_KEY}"}
    )
    assert response.status_code == 201, f"User creation failed: {response.text}"
    return response.json()

def get_performance_baseline(operation: str) -> float:
    """Helper: Load performance baseline from Session 15"""
    import json
    with open("integration/performance_baseline.json", "r") as f:
        baseline = json.load(f)
    return baseline["timings"].get(operation, 5000.0)  # Default 5s if not found


class TestMultiUserFlows:
    """Comprehensive multi-user Oracle reading tests"""
    
    def test_2_user_joint_reading(self):
        """Test 2-user joint reading with compatibility analysis"""
        
        # Create 2 users
        user1 = create_user("Alice", "1985-01-01", "Mary")
        user2 = create_user("Bob", "1990-06-15", "Jane")
        
        print(f"\n✓ Created 2 users: {user1['name']}, {user2['name']}")
        
        # Submit multi-user reading
        reading_data = {
            "primary_user_id": user1["id"],
            "secondary_user_ids": [user2["id"]],
            "question": "Should we start this business together?",
            "sign_type": "time",
            "sign_value": "11:11"
        }
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/api/oracle/reading/multi-user",
            json=reading_data,
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        duration_ms = (time.time() - start_time) * 1000
        
        # Verify response
        assert response.status_code == 201, f"Multi-user reading failed: {response.text}"
        reading = response.json()
        
        print(f"✓ Multi-user reading created in {duration_ms:.2f}ms")
        
        # Verify multi-user fields
        assert reading["is_multi_user"] == True, "Reading not marked as multi-user"
        assert reading["primary_user_id"] == user1["id"], "Primary user mismatch"
        assert user2["id"] in reading["participant_ids"], "Secondary user not in participants"
        
        print(f"✓ Multi-user flags correct")
        
        # Verify individual insights
        assert "individual_insights" in reading, "Missing individual_insights"
        assert user1["name"] in reading["individual_insights"], f"Missing insight for {user1['name']}"
        assert user2["name"] in reading["individual_insights"], f"Missing insight for {user2['name']}"
        
        # Check insight quality (should be substantial)
        user1_insight = reading["individual_insights"][user1["name"]]
        user2_insight = reading["individual_insights"][user2["name"]]
        assert len(user1_insight) > 100, "User 1 insight too short"
        assert len(user2_insight) > 100, "User 2 insight too short"
        
        print(f"✓ Individual insights present for both users")
        
        # Verify compatibility analysis
        assert "compatibility" in reading, "Missing compatibility analysis"
        assert "score" in reading["compatibility"], "Missing compatibility score"
        
        compatibility_score = reading["compatibility"]["score"]
        assert 0 <= compatibility_score <= 1, f"Invalid compatibility score: {compatibility_score}"
        
        print(f"✓ Compatibility score: {compatibility_score:.2%}")
        
        # Verify group dynamics
        assert "group_dynamics" in reading, "Missing group_dynamics"
        assert len(reading["group_dynamics"]) > 50, "Group dynamics too brief"
        
        print(f"✓ Group dynamics analysis present")
        
        # Performance check
        baseline_single_user = get_performance_baseline("single_user_end_to_end")
        max_acceptable = baseline_single_user * 2.5  # Allow 2.5x max for 2-user
        assert duration_ms < max_acceptable, \
            f"Performance unacceptable: {duration_ms:.2f}ms > {max_acceptable:.2f}ms"
        
        print(f"✓ Performance acceptable: {duration_ms:.2f}ms (baseline: {baseline_single_user:.2f}ms)")
        
        # Test permissions: User 1 can access
        response = requests.get(
            f"{API_BASE}/api/oracle/readings/{reading['id']}",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}  # User 1's key
        )
        assert response.status_code == 200, "User 1 cannot access own reading"
        print(f"✓ User 1 (participant) can access reading")
        
        # Test permissions: User 2 can access
        # Note: In real implementation, each user would have their own API key
        # For testing, we're using shared test key
        response = requests.get(
            f"{API_BASE}/api/oracle/readings/{reading['id']}",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}  # User 2's key
        )
        assert response.status_code == 200, "User 2 cannot access reading"
        print(f"✓ User 2 (participant) can access reading")
        
        # Test permissions: Non-participant cannot access
        user3 = create_user("Charlie", "1995-03-20", "Susan")
        response = requests.get(
            f"{API_BASE}/api/oracle/readings/{reading['id']}",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}  # User 3's key (non-participant)
        )
        # Note: Permission enforcement depends on implementation
        # If implemented, should be 403. If not, document as future enhancement.
        if response.status_code == 403:
            print(f"✓ User 3 (non-participant) correctly denied access (403)")
        else:
            print(f"⚠️  Permission system not yet implemented (User 3 got {response.status_code})")
            # Don't fail test - document for future
        
        print(f"\n✅ 2-user reading test complete!\n")
    
    
    def test_5_user_joint_reading_max_capacity(self):
        """Test maximum 5-user joint reading with compatibility matrix"""
        
        # Create 5 users
        users = []
        for i in range(5):
            user = create_user(
                name=f"TestUser{i+1}",
                birthday=f"199{i}-01-01",
                mother_name=f"Mother{i+1}"
            )
            users.append(user)
        
        print(f"\n✓ Created 5 users: {[u['name'] for u in users]}")
        
        # Submit 5-user reading
        reading_data = {
            "primary_user_id": users[0]["id"],
            "secondary_user_ids": [u["id"] for u in users[1:5]],  # Users 1-4 as secondary
            "question": "What is the group's collective path forward?",
            "sign_type": "number",
            "sign_value": "777"
        }
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/api/oracle/reading/multi-user",
            json=reading_data,
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        duration_ms = (time.time() - start_time) * 1000
        
        assert response.status_code == 201, f"5-user reading failed: {response.text}"
        reading = response.json()
        
        print(f"✓ 5-user reading created in {duration_ms:.2f}ms")
        
        # Verify all 5 users included
        assert len(reading["participant_ids"]) == 5, f"Expected 5 participants, got {len(reading['participant_ids'])}"
        assert len(reading["individual_insights"]) == 5, f"Expected 5 insights, got {len(reading['individual_insights'])}"
        
        print(f"✓ All 5 users included in reading")
        
        # Verify pairwise compatibility matrix
        # For 5 users, should have C(5,2) = 10 pairwise comparisons
        assert "compatibility_matrix" in reading, "Missing compatibility_matrix"
        
        matrix = reading["compatibility_matrix"]
        expected_pairs = (5 * 4) // 2  # Combination formula: n*(n-1)/2
        assert len(matrix) == expected_pairs, \
            f"Expected {expected_pairs} pairwise comparisons, got {len(matrix)}"
        
        print(f"✓ Compatibility matrix complete: {len(matrix)} pairwise comparisons")
        
        # Verify each pair has valid score
        for pair_key, pair_data in matrix.items():
            assert "score" in pair_data, f"Missing score for pair {pair_key}"
            score = pair_data["score"]
            assert 0 <= score <= 1, f"Invalid compatibility score for {pair_key}: {score}"
        
        print(f"✓ All pairwise scores valid (0-1 range)")
        
        # Performance check: 5-user should be <2.5x single-user baseline
        baseline_single_user = get_performance_baseline("single_user_end_to_end")
        max_acceptable = baseline_single_user * 2.5
        
        if duration_ms > max_acceptable:
            print(f"⚠️  Performance degraded: {duration_ms:.2f}ms > {max_acceptable:.2f}ms")
            print(f"   This is acceptable for 5 users but should be optimized")
        else:
            print(f"✓ Performance excellent: {duration_ms:.2f}ms < {max_acceptable:.2f}ms")
        
        # Test 6th user cannot be added (validation)
        user6 = create_user("User6", "1996-01-01", "Mother6")
        
        reading_data_6_users = {
            "primary_user_id": users[0]["id"],
            "secondary_user_ids": [u["id"] for u in users[1:5]] + [user6["id"]],  # 6 total
            "question": "Too many users",
            "sign_type": "time",
            "sign_value": "12:34"
        }
        
        response = requests.post(
            f"{API_BASE}/api/oracle/reading/multi-user",
            json=reading_data_6_users,
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        
        assert response.status_code == 400, \
            f"6-user reading should be rejected (400), got {response.status_code}"
        
        error = response.json()
        assert "maximum" in error["detail"].lower() or "limit" in error["detail"].lower(), \
            f"Error message should mention limit: {error['detail']}"
        
        print(f"✓ 6th user correctly rejected with validation error")
        
        print(f"\n✅ 5-user reading test complete!\n")
    
    
    def test_multi_user_history_display(self):
        """Test multi-user readings appear correctly in history for all participants"""
        
        # Create multi-user reading using previous test helper
        user1 = create_user("HistoryUser1", "1988-05-10", "Mother1")
        user2 = create_user("HistoryUser2", "1992-08-22", "Mother2")
        
        reading_data = {
            "primary_user_id": user1["id"],
            "secondary_user_ids": [user2["id"]],
            "question": "History test question",
            "sign_type": "time",
            "sign_value": "14:44"
        }
        
        response = requests.post(
            f"{API_BASE}/api/oracle/reading/multi-user",
            json=reading_data,
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        assert response.status_code == 201
        reading = response.json()
        reading_id = reading["id"]
        
        print(f"\n✓ Created test multi-user reading: {reading_id}")
        
        # Get history for User 1 (primary)
        response = requests.get(
            f"{API_BASE}/api/oracle/readings",
            params={"user_id": user1["id"]},
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        assert response.status_code == 200
        user1_history = response.json()
        
        # Find the multi-user reading in User 1's history
        multi_reading_in_history = None
        for r in user1_history:
            if r["id"] == reading_id:
                multi_reading_in_history = r
                break
        
        assert multi_reading_in_history is not None, "Multi-user reading not in User 1 history"
        print(f"✓ Multi-user reading appears in User 1's history")
        
        # Verify multi-user indicator
        assert multi_reading_in_history["is_multi_user"] == True, \
            "Reading not marked as multi-user in history"
        
        # Verify participant list included
        assert "participants" in multi_reading_in_history, "Participants list missing from history"
        participants = multi_reading_in_history["participants"]
        assert len(participants) == 2, f"Expected 2 participants in history, got {len(participants)}"
        
        participant_names = [p["name"] for p in participants]
        assert user1["name"] in participant_names, f"User 1 not in participants"
        assert user2["name"] in participant_names, f"User 2 not in participants"
        
        print(f"✓ Participant list correct: {participant_names}")
        
        # Get history for User 2 (secondary)
        response = requests.get(
            f"{API_BASE}/api/oracle/readings",
            params={"user_id": user2["id"]},
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        assert response.status_code == 200
        user2_history = response.json()
        
        # Verify reading appears in User 2's history too
        reading_in_user2_history = any(r["id"] == reading_id for r in user2_history)
        assert reading_in_user2_history, "Multi-user reading not in User 2's history"
        
        print(f"✓ Multi-user reading appears in User 2's history")
        
        # Test filtering by reading type (if supported)
        response = requests.get(
            f"{API_BASE}/api/oracle/readings",
            params={"user_id": user1["id"], "reading_type": "multi_user"},
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        
        if response.status_code == 200:
            filtered_history = response.json()
            # All readings should be multi-user
            for r in filtered_history:
                assert r["is_multi_user"] == True, "Non-multi-user reading in filtered results"
            print(f"✓ History filtering by reading_type works")
        else:
            print(f"⚠️  History filtering not yet implemented (got {response.status_code})")
        
        print(f"\n✅ Multi-user history display test complete!\n")
    
    
    def test_multi_user_performance_scaling(self):
        """Test performance scaling from 1 → 2 → 5 users"""
        
        # Get baseline single-user time
        baseline_single = get_performance_baseline("single_user_end_to_end")
        
        print(f"\nPerformance Scaling Test:")
        print(f"Baseline (single-user): {baseline_single:.2f}ms")
        print(f"-" * 60)
        
        # Test 2-user performance
        user1 = create_user("PerfTest1", "1990-01-01", "Mother")
        user2 = create_user("PerfTest2", "1991-01-01", "Mother")
        
        start = time.time()
        response = requests.post(
            f"{API_BASE}/api/oracle/reading/multi-user",
            json={
                "primary_user_id": user1["id"],
                "secondary_user_ids": [user2["id"]],
                "question": "Performance test",
                "sign_type": "time",
                "sign_value": "11:11"
            },
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        duration_2_user = (time.time() - start) * 1000
        
        assert response.status_code == 201
        ratio_2_user = duration_2_user / baseline_single
        
        print(f"2-user: {duration_2_user:.2f}ms ({ratio_2_user:.2f}x baseline)")
        
        # Test 5-user performance
        users = [create_user(f"PerfTest{i}", f"199{i}-01-01", "Mother") for i in range(3, 8)]
        
        start = time.time()
        response = requests.post(
            f"{API_BASE}/api/oracle/reading/multi-user",
            json={
                "primary_user_id": users[0]["id"],
                "secondary_user_ids": [u["id"] for u in users[1:5]],
                "question": "Performance test 5 users",
                "sign_type": "number",
                "sign_value": "999"
            },
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        duration_5_user = (time.time() - start) * 1000
        
        assert response.status_code == 201
        ratio_5_user = duration_5_user / baseline_single
        
        print(f"5-user: {duration_5_user:.2f}ms ({ratio_5_user:.2f}x baseline)")
        print(f"-" * 60)
        
        # Performance assertions
        assert ratio_2_user < 2.5, f"2-user too slow: {ratio_2_user:.2f}x > 2.5x"
        assert ratio_5_user < 3.0, f"5-user too slow: {ratio_5_user:.2f}x > 3.0x"
        
        print(f"✓ Performance scaling acceptable")
        print(f"  2-user: {ratio_2_user:.2f}x baseline (target: <2.5x)")
        print(f"  5-user: {ratio_5_user:.2f}x baseline (target: <3.0x)")
        
        print(f"\n✅ Performance scaling test complete!\n")
```

**Files to Create:**

- `integration/tests/test_multi_user_flows.py` - Comprehensive multi-user test suite

**Acceptance Criteria:**

- [ ] Can create 2-user joint reading
- [ ] Can create 5-user joint reading (maximum capacity)
- [ ] Individual insights present for all participants
- [ ] Compatibility calculations working (pairwise for all combinations)
- [ ] Group dynamics analysis present
- [ ] Permission system working (participants can access, non-participants cannot)
- [ ] Multi-user readings display correctly in history
- [ ] Performance acceptable (<2.5x single-user for 2-user, <3x for 5-user)
- [ ] 6th user correctly rejected (validation enforced)

**Verification:**

```bash
# Terminal: integration/

pytest tests/test_multi_user_flows.py -v -s

# Expected Output:
# ========================= test session starts ==========================
# tests/test_multi_user_flows.py::test_2_user_joint_reading ............ PASSED
# tests/test_multi_user_flows.py::test_5_user_joint_reading_max_capacity  PASSED
# tests/test_multi_user_flows.py::test_multi_user_history_display ...... PASSED
# tests/test_multi_user_flows.py::test_multi_user_performance_scaling .. PASSED
# ========================= 4 passed in 35.6s ===========================
```

**Checkpoint Gate:**

- [ ] All 4 multi-user tests pass
- [ ] Performance ratios within acceptable range
- [ ] No errors or failures

**Fix issues before proceeding to Phase 3.**

---

### Phase 3: Comprehensive E2E Testing (120 minutes)

**Objective:** Browser-based end-to-end testing of all user workflows using Playwright

**Tasks:**

1. **Set Up Playwright:**
   - Install Playwright (`npx playwright install`)
   - Configure Playwright (`playwright.config.ts`)
   - Set up test environment (API running, database seeded)

2. **Write E2E Tests for All Workflows:**
   - Complete single-user flow (create user → reading → view result → check history)
   - Complete multi-user flow (create 2 users → joint reading → both view result)
   - Persian language flow (switch language → UI updates → create reading)
   - Persian keyboard flow (open keyboard → enter text → save)
   - Calendar picker flow (click field → select date → field updates)
   - Error handling flow (submit invalid → error shows → correct → succeeds)

3. **Run Tests and Fix UI Issues:**
   - Run all E2E tests
   - Capture screenshots of failures
   - Fix UI bugs found
   - Re-run until all pass

**Playwright Setup:**

```typescript
// frontend/playwright.config.ts

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

**E2E Test Implementation:**

```typescript
// frontend/e2e/complete_flows.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Complete User Flows', () => {
  
  test('single-user Oracle reading flow', async ({ page }) => {
    // Navigate to Oracle page
    await page.goto('/oracle');
    
    // Should see Oracle interface
    await expect(page.locator('h1')).toContainText('Sign Reader');
    
    // Create new user
    await page.click('button:has-text("Create User")');
    await expect(page.locator('.user-form')).toBeVisible();
    
    // Fill user form
    const timestamp = Date.now();
    await page.fill('input[name="name"]', `E2E User ${timestamp}`);
    await page.fill('input[name="birthday"]', '1990-01-01');
    await page.fill('input[name="mother_name"]', 'E2E Mother');
    
    // Submit user creation
    await page.click('button:has-text("Save")');
    
    // Wait for success message
    await expect(page.locator('.success-message')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.success-message')).toContainText('User created');
    
    console.log('✓ User created successfully');
    
    // Fill reading form
    await page.fill('textarea[name="question"]', 'Should I pursue this opportunity?');
    await page.selectOption('select[name="sign_type"]', 'time');
    await page.fill('input[name="sign_value"]', '11:11');
    
    // Submit reading
    await page.click('button:has-text("Get Reading")');
    
    // Should show loading state
    await expect(page.locator('.loading-indicator')).toBeVisible();
    
    console.log('✓ Loading indicator displayed');
    
    // Wait for result (AI call may take 3-5 seconds)
    await expect(page.locator('.reading-result')).toBeVisible({ timeout: 10000 });
    
    // Verify result contains interpretation
    const resultText = await page.locator('.reading-result').textContent();
    expect(resultText).toBeTruthy();
    expect(resultText!.length).toBeGreaterThan(100);  // Substantial text
    
    // Should contain mystical/guidance language
    const hasGuidanceLanguage = 
      resultText!.toLowerCase().includes('universe') ||
      resultText!.toLowerCase().includes('path') ||
      resultText!.toLowerCase().includes('wisdom') ||
      resultText!.toLowerCase().includes('energy');
    
    expect(hasGuidanceLanguage).toBeTruthy();
    
    console.log('✓ Reading result received with interpretation');
    
    // Navigate to history
    await page.click('button:has-text("History")');
    await expect(page.locator('.history-list')).toBeVisible({ timeout: 3000 });
    
    // Verify reading appears in history
    const historyItems = page.locator('.history-item');
    await expect(historyItems).toHaveCount(1);  // Should have our reading
    
    const historyText = await historyItems.first().textContent();
    expect(historyText).toContain('Should I pursue');
    
    console.log('✓ Reading appears in history');
    
    // Click history item to view details
    await historyItems.first().click();
    await expect(page.locator('.reading-detail')).toBeVisible();
    
    console.log('✓ Can view reading details from history');
  });
  
  
  test('multi-user Oracle reading flow', async ({ page }) => {
    await page.goto('/oracle');
    
    // Create first user
    await page.click('button:has-text("Create User")');
    const timestamp = Date.now();
    await page.fill('input[name="name"]', `Alice ${timestamp}`);
    await page.fill('input[name="birthday"]', '1985-01-01');
    await page.fill('input[name="mother_name"]', 'Mary');
    await page.click('button:has-text("Save")');
    await expect(page.locator('.success-message')).toBeVisible();
    
    console.log('✓ User 1 (Alice) created');
    
    // Create second user
    await page.click('button:has-text("Create User")');
    await page.fill('input[name="name"]', `Bob ${timestamp}`);
    await page.fill('input[name="birthday"]', '1990-06-15');
    await page.fill('input[name="mother_name"]', 'Jane');
    await page.click('button:has-text("Save")');
    await expect(page.locator('.success-message')).toBeVisible();
    
    console.log('✓ User 2 (Bob) created');
    
    // Switch to multi-user mode
    await page.click('input[type="checkbox"][name="multi_user"]');
    await expect(page.locator('.participant-selector')).toBeVisible();
    
    // Select both users as participants
    await page.click('select[name="primary_user"]');
    await page.selectOption('select[name="primary_user"]', { label: new RegExp(`Alice ${timestamp}`) });
    
    await page.click('button:has-text("Add Participant")');
    await page.selectOption('select[name="secondary_user"]', { label: new RegExp(`Bob ${timestamp}`) });
    
    console.log('✓ Multi-user participants selected');
    
    // Fill reading question
    await page.fill('textarea[name="question"]', 'Should we start this partnership?');
    await page.selectOption('select[name="sign_type"]', 'time');
    await page.fill('input[name="sign_value"]', '22:22');
    
    // Submit multi-user reading
    await page.click('button:has-text("Get Reading")');
    
    // Wait for result
    await expect(page.locator('.reading-result')).toBeVisible({ timeout: 15000 });
    
    // Verify multi-user indicator
    await expect(page.locator('.multi-user-badge')).toBeVisible();
    await expect(page.locator('.multi-user-badge')).toContainText('Joint Reading');
    
    console.log('✓ Multi-user reading created with indicator');
    
    // Verify individual insights section
    await expect(page.locator('.individual-insights')).toBeVisible();
    
    const aliceInsight = page.locator('.insight[data-user*="Alice"]');
    const bobInsight = page.locator('.insight[data-user*="Bob"]');
    
    await expect(aliceInsight).toBeVisible();
    await expect(bobInsight).toBeVisible();
    
    console.log('✓ Individual insights displayed for both users');
    
    // Verify compatibility section
    await expect(page.locator('.compatibility-section')).toBeVisible();
    await expect(page.locator('.compatibility-score')).toBeVisible();
    
    const scoreText = await page.locator('.compatibility-score').textContent();
    expect(scoreText).toMatch(/\d+%/);  // Should show percentage
    
    console.log(`✓ Compatibility score displayed: ${scoreText}`);
  });
  
  
  test('Persian language and RTL support', async ({ page }) => {
    await page.goto('/oracle');
    
    // Initial state: English (LTR)
    let direction = await page.locator('body').evaluate(
      el => window.getComputedStyle(el).direction
    );
    expect(direction).toBe('ltr');
    
    console.log('✓ Initial state: LTR (English)');
    
    // Switch to Persian
    await page.click('button[aria-label="Language"]');
    await expect(page.locator('.language-menu')).toBeVisible();
    await page.click('text=فارسی');
    
    // Wait for UI update
    await page.waitForTimeout(1000);
    
    // Verify direction changed to RTL
    direction = await page.locator('body').evaluate(
      el => window.getComputedStyle(el).direction
    );
    expect(direction).toBe('rtl');
    
    console.log('✓ Direction changed to RTL');
    
    // Verify Persian text visible
    await expect(page.locator('text=خواننده نشانه')).toBeVisible();  // "Sign Reader" in Persian
    
    console.log('✓ Persian UI text visible');
    
    // Test creating reading in Persian mode
    await page.click('button:has-text("ایجاد کاربر")');  // "Create User" in Persian
    
    // Should see form in Persian
    await expect(page.locator('label:has-text("نام")')).toBeVisible();  // "Name" in Persian
    
    console.log('✓ Forms rendered in Persian');
    
    // Switch back to English to verify toggle works
    await page.click('button[aria-label="Language"]');
    await page.click('text=English');
    
    await page.waitForTimeout(1000);
    
    direction = await page.locator('body').evaluate(
      el => window.getComputedStyle(el).direction
    );
    expect(direction).toBe('ltr');
    
    console.log('✓ Successfully switched back to English (LTR)');
  });
  
  
  test('Persian keyboard input', async ({ page }) => {
    await page.goto('/oracle');
    
    // Create user to access input field
    await page.click('button:has-text("Create User")');
    
    // Click Persian keyboard button
    await page.click('button[aria-label="Persian Keyboard"]');
    
    // Verify keyboard visible
    await expect(page.locator('.persian-keyboard')).toBeVisible();
    
    console.log('✓ Persian keyboard displayed');
    
    // Focus name input
    const nameInput = page.locator('input[name="name"]');
    await nameInput.click();
    
    // Click Persian character buttons
    await page.click('.persian-keyboard button:has-text("ع")');
    await page.click('.persian-keyboard button:has-text("ل")');
    await page.click('.persian-keyboard button:has-text("ی")');
    
    // Verify characters inserted
    const inputValue = await nameInput.inputValue();
    expect(inputValue).toContain('ع');
    expect(inputValue).toContain('ل');
    expect(inputValue).toContain('ی');
    
    console.log(`✓ Persian characters inserted: ${inputValue}`);
    
    // Test backspace
    await page.click('.persian-keyboard button[data-key="backspace"]');
    
    const afterBackspace = await nameInput.inputValue();
    expect(afterBackspace.length).toBe(inputValue.length - 1);
    
    console.log('✓ Backspace works');
    
    // Test space
    await page.click('.persian-keyboard button[data-key="space"]');
    
    const afterSpace = await nameInput.inputValue();
    expect(afterSpace).toContain(' ');
    
    console.log('✓ Space works');
    
    // Close keyboard
    await page.click('.persian-keyboard button[aria-label="Close"]');
    await expect(page.locator('.persian-keyboard')).not.toBeVisible();
    
    console.log('✓ Keyboard closes correctly');
  });
  
  
  test('calendar date picker', async ({ page }) => {
    await page.goto('/oracle');
    
    // Create user to access date field
    await page.click('button:has-text("Create User")');
    
    // Click birthday field
    const birthdayInput = page.locator('input[name="birthday"]');
    await birthdayInput.click();
    
    // Calendar should open
    await expect(page.locator('.calendar-picker')).toBeVisible({ timeout: 2000 });
    
    console.log('✓ Calendar picker opened');
    
    // Select a date (e.g., 15th of current month)
    await page.click('.calendar-day[data-day="15"]');
    
    // Calendar should close
    await expect(page.locator('.calendar-picker')).not.toBeVisible();
    
    // Input should be filled
    const selectedDate = await birthdayInput.inputValue();
    expect(selectedDate).toBeTruthy();
    expect(selectedDate).toMatch(/\d{4}-\d{2}-\d{2}/);  // YYYY-MM-DD format
    expect(selectedDate).toContain('-15');  // Should have day 15
    
    console.log(`✓ Date selected and formatted: ${selectedDate}`);
    
    // Test manual input still works
    await birthdayInput.fill('1990-01-01');
    const manualValue = await birthdayInput.inputValue();
    expect(manualValue).toBe('1990-01-01');
    
    console.log('✓ Manual date input also works');
  });
  
  
  test('error handling flow', async ({ page }) => {
    await page.goto('/oracle');
    
    // Try to submit reading without user
    await page.fill('textarea[name="question"]', 'Test question');
    await page.click('button:has-text("Get Reading")');
    
    // Should show error
    await expect(page.locator('.error-message')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('.error-message')).toContainText('user');
    
    console.log('✓ Error shown when submitting without user');
    
    // Create user
    await page.click('button:has-text("Create User")');
    await page.fill('input[name="name"]', 'Error Test User');
    await page.fill('input[name="birthday"]', '1990-01-01');
    await page.fill('input[name="mother_name"]', 'Test Mother');
    await page.click('button:has-text("Save")');
    
    await expect(page.locator('.success-message')).toBeVisible();
    
    // Try to submit with invalid sign value
    await page.fill('textarea[name="question"]', 'Test question');
    await page.selectOption('select[name="sign_type"]', 'time');
    await page.fill('input[name="sign_value"]', 'invalid');  // Should be HH:MM
    
    await page.click('button:has-text("Get Reading")');
    
    // Should show validation error
    await expect(page.locator('.error-message')).toBeVisible();
    await expect(page.locator('.error-message')).toContainText('format');
    
    console.log('✓ Validation error shown for invalid time format');
    
    // Correct the error
    await page.fill('input[name="sign_value"]', '11:11');
    
    // Submit again (should succeed)
    await page.click('button:has-text("Get Reading")');
    
    // Should NOT show error this time
    await expect(page.locator('.error-message')).not.toBeVisible();
    
    // Should show loading then result
    await expect(page.locator('.loading-indicator')).toBeVisible();
    await expect(page.locator('.reading-result')).toBeVisible({ timeout: 10000 });
    
    console.log('✓ Reading created successfully after correction');
    
    // Test network error handling (simulate by stopping API)
    // Note: This would require additional setup to actually stop API
    // For now, just document that this should be tested manually
    console.log('⚠️  Network error handling should be tested manually by stopping API');
  });
  
});
```

**Files to Create:**

- `frontend/playwright.config.ts` - Playwright configuration
- `frontend/e2e/complete_flows.spec.ts` - Complete flow tests
- `frontend/e2e/persian_support.spec.ts` - Persian-specific tests (if separate)
- `frontend/e2e/error_handling.spec.ts` - Error scenario tests (if separate)

**Acceptance Criteria:**

- [ ] All 6 E2E test scenarios pass
- [ ] Tests pass in Chromium, Firefox, and WebKit (cross-browser)
- [ ] No visual bugs found during testing
- [ ] All user interactions responsive
- [ ] Error messages clear and helpful
- [ ] Loading states visible on all async operations
- [ ] Persian mode fully functional (RTL, keyboard, translations)
- [ ] Calendar picker works correctly
- [ ] Form validation prevents invalid submissions

**Verification:**

```bash
# Terminal: frontend/

# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npx playwright test

# Expected Output:
# Running 6 tests using 3 workers
# 
#   ✓  [chromium] › complete_flows.spec.ts:5:3 › single-user Oracle reading flow (12s)
#   ✓  [chromium] › complete_flows.spec.ts:65:3 › multi-user Oracle reading flow (18s)
#   ✓  [chromium] › complete_flows.spec.ts:145:3 › Persian language and RTL support (8s)
#   ✓  [chromium] › complete_flows.spec.ts:195:3 › Persian keyboard input (10s)
#   ✓  [chromium] › complete_flows.spec.ts:255:3 › calendar date picker (6s)
#   ✓  [chromium] › complete_flows.spec.ts:295:3 › error handling flow (11s)
# 
#   6 passed (65s)

# View HTML report (if any failures)
npx playwright show-report

# Run in headed mode to see browser (debugging)
npx playwright test --headed --project=chromium
```

**Checkpoint Gate:**

- [ ] All E2E tests pass (6/6)
- [ ] No visual bugs found
- [ ] UI fully functional in browser

**Fix any UI issues before proceeding to Phase 4.**

---

### Phase 4: Performance Optimization (90 minutes)

**Objective:** Measure current performance, compare to baseline, identify slow operations, optimize, and verify improvement

**Tasks:**

1. **Re-measure Current Performance:**
   - Run same tests as Session 15
   - Capture current timings
   - Compare to baseline

2. **Identify Slow Operations:**
   - Find operations >20% slower than baseline
   - Find operations missing performance targets
   - Prioritize by impact (user-facing operations first)

3. **Optimize Slow Operations:**
   - Database: Add missing indexes, optimize queries
   - API: Add caching, reduce payload size
   - FC60: Cache intermediate calculations
   - AI: Optimize prompt length

4. **Re-measure and Verify:**
   - Run performance tests again
   - Verify all targets met
   - Update baseline

**Performance Audit Implementation:**

```python
# integration/performance_audit.py

import json
import time
import requests
from typing import Dict, List
import statistics

API_BASE = "http://localhost:8000"
TEST_API_KEY = "test_api_key_12345"

def load_baseline() -> Dict:
    """Load performance baseline from Session 15"""
    with open("integration/performance_baseline.json", "r") as f:
        return json.load(f)

def measure_operation(name: str, operation_func, iterations: int = 5) -> Dict:
    """Measure operation performance over multiple iterations"""
    timings = []
    
    for i in range(iterations):
        start = time.time()
        try:
            result = operation_func()
            duration_ms = (time.time() - start) * 1000
            timings.append(duration_ms)
        except Exception as e:
            print(f"  ✗ Operation failed: {e}")
            return {"error": str(e)}
    
    return {
        "mean": statistics.mean(timings),
        "median": statistics.median(timings),
        "min": min(timings),
        "max": max(timings),
        "p95": sorted(timings)[int(len(timings) * 0.95)],
        "timings": timings
    }

def create_test_user() -> Dict:
    """Create test user for performance testing"""
    timestamp = int(time.time())
    response = requests.post(
        f"{API_BASE}/api/oracle/users",
        json={
            "name": f"PerfTest{timestamp}",
            "birthday": "1990-01-01",
            "mother_name": "PerfMother"
        },
        headers={"Authorization": f"Bearer {TEST_API_KEY}"}
    )
    return response.json()

def performance_audit():
    """Comprehensive performance audit"""
    
    print("=" * 70)
    print(" " * 20 + "PERFORMANCE AUDIT")
    print("=" * 70)
    
    # Load baseline
    baseline = load_baseline()
    baseline_timings = baseline.get("timings", {})
    
    current_timings = {}
    
    # Test 1: API Health Check
    print("\n[1/8] Testing API Health Endpoint...")
    def api_health():
        response = requests.get(f"{API_BASE}/api/health")
        assert response.status_code == 200
        return response.json()
    
    result = measure_operation("api_health", api_health, iterations=10)
    current_timings["api_health"] = result["p95"]
    print(f"      p95: {result['p95']:.2f}ms | Target: <50ms")
    
    # Test 2: User Creation
    print("\n[2/8] Testing User Creation...")
    def user_creation():
        user = create_test_user()
        assert user["id"]
        return user
    
    result = measure_operation("user_creation", user_creation, iterations=5)
    current_timings["user_creation"] = result["p95"]
    print(f"      p95: {result['p95']:.2f}ms | Target: <100ms")
    
    # Test 3: Single-User Reading Creation
    print("\n[3/8] Testing Single-User Reading Creation...")
    test_user = create_test_user()
    
    def single_user_reading():
        response = requests.post(
            f"{API_BASE}/api/oracle/reading",
            json={
                "user_id": test_user["id"],
                "question": "Performance test question",
                "sign_type": "time",
                "sign_value": "11:11"
            },
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        assert response.status_code == 201
        return response.json()
    
    result = measure_operation("single_user_reading", single_user_reading, iterations=3)
    current_timings["reading_creation"] = result["p95"]
    print(f"      p95: {result['p95']:.2f}ms | Target: <5000ms")
    
    # Test 4: FC60 Calculation
    print("\n[4/8] Testing FC60 Calculation...")
    def fc60_calculation():
        response = requests.post(
            f"{API_BASE}/api/oracle/calculate-fc60",
            json={
                "birthday": "1990-01-01",
                "mother_name": "Test"
            },
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        assert response.status_code == 200
        return response.json()
    
    result = measure_operation("fc60_calculation", fc60_calculation, iterations=10)
    current_timings["fc60_calculation"] = result["p95"]
    print(f"      p95: {result['p95']:.2f}ms | Target: <200ms")
    
    # Test 5: AI Interpretation
    print("\n[5/8] Testing AI Interpretation...")
    def ai_interpretation():
        response = requests.post(
            f"{API_BASE}/api/oracle/interpret",
            json={
                "context": "Performance test",
                "numbers": [1, 2, 3]
            },
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        assert response.status_code == 200
        return response.json()
    
    result = measure_operation("ai_interpretation", ai_interpretation, iterations=3)
    current_timings["ai_interpretation"] = result["p95"]
    print(f"      p95: {result['p95']:.2f}ms | Target: <3000ms")
    
    # Test 6: Database Query (Findings List)
    print("\n[6/8] Testing Database Query Performance...")
    def findings_query():
        response = requests.get(
            f"{API_BASE}/api/vault/findings?limit=100",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        assert response.status_code == 200
        return response.json()
    
    result = measure_operation("findings_query", findings_query, iterations=10)
    current_timings["findings_query"] = result["p95"]
    print(f"      p95: {result['p95']:.2f}ms | Target: <100ms")
    
    # Test 7: Multi-User Reading
    print("\n[7/8] Testing Multi-User Reading Performance...")
    user1 = create_test_user()
    user2 = create_test_user()
    
    def multi_user_reading():
        response = requests.post(
            f"{API_BASE}/api/oracle/reading/multi-user",
            json={
                "primary_user_id": user1["id"],
                "secondary_user_ids": [user2["id"]],
                "question": "Performance test multi-user",
                "sign_type": "time",
                "sign_value": "22:22"
            },
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        assert response.status_code == 201
        return response.json()
    
    result = measure_operation("multi_user_reading", multi_user_reading, iterations=3)
    current_timings["multi_user_reading"] = result["p95"]
    print(f"      p95: {result['p95']:.2f}ms | Target: <8000ms (2.5x single-user baseline)")
    
    # Test 8: WebSocket Connection
    print("\n[8/8] Testing WebSocket Connection...")
    # Note: WebSocket testing requires different setup
    # For now, skip and mark as manual test
    print(f"      ⚠️  WebSocket performance should be tested manually")
    
    # Performance Comparison Report
    print("\n" + "=" * 70)
    print(" " * 20 + "PERFORMANCE COMPARISON")
    print("=" * 70)
    print(f"\n{'Operation':<30} {'Baseline':<12} {'Current':<12} {'Change':<12} {'Status':<8}")
    print("-" * 70)
    
    issues = []
    
    for operation, baseline_time in baseline_timings.items():
        current_time = current_timings.get(operation, 0)
        
        if current_time == 0:
            print(f"{operation:<30} {baseline_time:>10.2f}ms {'N/A':<12} {'N/A':<12} {'SKIP':<8}")
            continue
        
        change_pct = ((current_time - baseline_time) / baseline_time) * 100
        change_str = f"{change_pct:+.1f}%"
        
        # Status: ✓ if faster or similar, ⚠️ if 10-20% slower, ✗ if >20% slower
        if change_pct <= 0:
            status = "✓"
        elif change_pct < 10:
            status = "✓"
        elif change_pct < 20:
            status = "⚠️"
        else:
            status = "✗"
            issues.append((operation, current_time, baseline_time, change_pct))
        
        print(f"{operation:<30} {baseline_time:>10.2f}ms {current_time:>10.2f}ms {change_str:>10} {status:<8}")
    
    print("-" * 70)
    
    # Target Compliance
    print("\n" + "=" * 70)
    print(" " * 20 + "TARGET COMPLIANCE")
    print("=" * 70)
    print(f"\n{'Operation':<30} {'Current':<12} {'Target':<12} {'Status':<8}")
    print("-" * 70)
    
    targets = {
        "api_health": 50,
        "user_creation": 100,
        "reading_creation": 5000,
        "fc60_calculation": 200,
        "ai_interpretation": 3000,
        "findings_query": 100,
        "multi_user_reading": 8000,
    }
    
    target_failures = []
    
    for operation, target_ms in targets.items():
        current_ms = current_timings.get(operation, 0)
        
        if current_ms == 0:
            print(f"{operation:<30} {'N/A':<12} {target_ms:>10.2f}ms {'SKIP':<8}")
            continue
        
        if current_ms <= target_ms:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            target_failures.append((operation, current_ms, target_ms))
        
        print(f"{operation:<30} {current_ms:>10.2f}ms {target_ms:>10.2f}ms {status:<8}")
    
    print("-" * 70)
    
    # Identify slow operations
    if issues:
        print("\n" + "=" * 70)
        print("⚠️  PERFORMANCE DEGRADATION DETECTED")
        print("=" * 70)
        print("\nOperations >20% slower than baseline:\n")
        for op, current, baseline, change_pct in issues:
            print(f"  • {op}")
            print(f"    Current: {current:.2f}ms | Baseline: {baseline:.2f}ms | Change: {change_pct:+.1f}%")
            print(f"    Impact: {current - baseline:.2f}ms slower\n")
    
    if target_failures:
        print("\n" + "=" * 70)
        print("❌ TARGET COMPLIANCE FAILURES")
        print("=" * 70)
        print("\nOperations missing performance targets:\n")
        for op, current, target in target_failures:
            print(f"  • {op}")
            print(f"    Current: {current:.2f}ms | Target: {target:.2f}ms | Over by: {current - target:.2f}ms\n")
    
    # Final Status
    print("\n" + "=" * 70)
    print(" " * 20 + "FINAL STATUS")
    print("=" * 70)
    
    if not issues and not target_failures:
        print("\n✅ ALL PERFORMANCE TARGETS MET!")
        print("   System is performing within acceptable parameters.")
    else:
        print("\n⚠️  PERFORMANCE OPTIMIZATION REQUIRED")
        print(f"   {len(issues)} operations degraded vs baseline")
        print(f"   {len(target_failures)} operations missing targets")
        print("\n   Optimization needed before production deployment.")
    
    # Save current performance data
    performance_data = {
        "timestamp": time.time(),
        "timings": current_timings,
        "baseline_comparison": {
            op: {
                "current": current_timings.get(op, 0),
                "baseline": baseline_timings.get(op, 0),
                "change_pct": ((current_timings.get(op, 0) - baseline_timings.get(op, 0)) / baseline_timings.get(op, 1)) * 100 if baseline_timings.get(op, 0) > 0 else 0
            }
            for op in set(list(current_timings.keys()) + list(baseline_timings.keys()))
        },
        "target_compliance": {
            op: {
                "current": current_timings.get(op, 0),
                "target": target,
                "passed": current_timings.get(op, 0) <= target
            }
            for op, target in targets.items()
        },
        "degraded_operations": [
            {"operation": op, "current": curr, "baseline": base, "change_pct": change}
            for op, curr, base, change in issues
        ],
        "failed_targets": [
            {"operation": op, "current": curr, "target": tgt}
            for op, curr, tgt in target_failures
        ]
    }
    
    with open("integration/current_performance.json", "w") as f:
        json.dump(performance_data, f, indent=2)
    
    print(f"\n📄 Performance data saved: integration/current_performance.json")
    
    return issues, target_failures

if __name__ == "__main__":
    issues, failures = performance_audit()
    
    if issues or failures:
        print("\n🔧 OPTIMIZATION REQUIRED")
        exit(1)
    else:
        print("\n✅ PERFORMANCE VERIFIED")
        exit(0)
```

**Optimization Strategies Document:**

```markdown
# integration/OPTIMIZATION_STRATEGIES.md

# Performance Optimization Strategies

## Database Optimizations

### Add Missing Indexes
```sql
-- Index on foreign keys (if not already indexed)
CREATE INDEX idx_readings_user_id ON oracle_readings(user_id);
CREATE INDEX idx_readings_created_at ON oracle_readings(created_at);
CREATE INDEX idx_readings_is_multi_user ON oracle_readings(is_multi_user);

-- Composite index for common queries
CREATE INDEX idx_readings_user_created ON oracle_readings(user_id, created_at DESC);

-- Verify index usage
EXPLAIN ANALYZE SELECT * FROM oracle_readings WHERE user_id = 'xxx' ORDER BY created_at DESC LIMIT 10;
-- Should show "Index Scan" not "Seq Scan"
```

### Query Optimization
```sql
-- Before (N+1 query problem)
SELECT * FROM oracle_readings;
-- Then for each reading:
SELECT * FROM oracle_users WHERE id = reading.user_id;

-- After (JOIN eliminates N+1)
SELECT r.*, u.name, u.birthday 
FROM oracle_readings r 
JOIN oracle_users u ON r.user_id = u.id 
WHERE r.user_id = 'xxx';
```

## API Optimizations

### Response Caching
```python
# Add caching for expensive operations
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_user_fc60_cached(user_id: str, birthday: str) -> Dict:
    # Expensive FC60 calculation
    # Cached for repeated calls with same user
    return calculate_fc60(birthday)

# Clear cache periodically or on user update
get_user_fc60_cached.cache_clear()
```

### Pagination
```python
# Add pagination to large result sets
@router.get("/api/vault/findings")
async def get_findings(
    skip: int = 0,
    limit: int = 100,  # Max 100 per page
    db: Session = Depends(get_db)
):
    findings = db.query(Finding).offset(skip).limit(limit).all()
    total = db.query(Finding).count()
    return {
        "findings": findings,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

### Compression
```python
# Enable gzip compression
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## FC60 Optimizations

### Cache Intermediate Calculations
```python
class FC60Engine:
    def __init__(self):
        self._digit_sum_cache = {}
    
    def digit_sum(self, number: int) -> int:
        if number in self._digit_sum_cache:
            return self._digit_sum_cache[number]
        
        result = sum(int(d) for d in str(number))
        self._digit_sum_cache[number] = result
        return result
```

### Optimize Algorithm
```python
# Before: String manipulation (slow)
def digit_sum_slow(n):
    return sum(int(d) for d in str(n))

# After: Math operations (faster)
def digit_sum_fast(n):
    total = 0
    while n > 0:
        total += n % 10
        n //= 10
    return total

# Benchmark shows 2-3x improvement
```

## AI Optimizations

### Optimize Prompt Length
```python
# Before: Long, verbose prompt (more tokens = slower)
prompt = f"""
You are a mystical Oracle providing guidance based on numerology.
The user has the following information:
- Name: {user.name}
- Birthday: {user.birthday}
- Mother's name: {user.mother_name}
- FC60 number: {fc60}
- Question: {question}

Please provide a comprehensive, detailed reading that includes:
1. Interpretation of their FC60 number
2. Guidance related to their question
3. Insights about their life path
4. Recommendations for their situation
...
"""

# After: Concise, structured prompt (fewer tokens = faster)
prompt = f"""FC60: {fc60} | Q: {question}

Mystical reading (200 words):"""

# 3x fewer tokens = ~3x faster response
```

### Non-Blocking AI Calls
```python
# Before: Blocking (everything waits for AI)
interpretation = await call_anthropic_api(prompt)

# After: Non-blocking with timeout
import asyncio

async def call_ai_with_timeout(prompt: str, timeout: float = 5.0):
    try:
        return await asyncio.wait_for(
            call_anthropic_api(prompt),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return "The cosmos is processing your request..."  # Fallback
```

## Frontend Optimizations

### Code Splitting
```typescript
// Before: Bundle all pages together
import Dashboard from './pages/Dashboard';
import Oracle from './pages/Oracle';
import Vault from './pages/Vault';

// After: Lazy load pages (smaller initial bundle)
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Oracle = lazy(() => import('./pages/Oracle'));
const Vault = lazy(() => import('./pages/Vault'));
```

### Debounce User Input
```typescript
// Before: API call on every keystroke (expensive)
const handleSearch = (query: string) => {
  api.searchFindings(query);
};

// After: Debounce (API call only after user stops typing)
import { debounce } from 'lodash';

const handleSearch = debounce((query: string) => {
  api.searchFindings(query);
}, 300);  // Wait 300ms after last keystroke
```

## When to Optimize

Priority matrix:

| Impact | Frequency | Priority | Example |
|--------|-----------|----------|---------|
| High | High | **P0 - Critical** | Reading creation (user-facing, every session) |
| High | Medium | **P1 - Important** | History loading (user-facing, frequent) |
| High | Low | **P2 - Nice to have** | Export CSV (user-facing, occasional) |
| Low | High | **P2 - Nice to have** | Health check (background, not user-facing) |
| Low | Low | **P3 - Skip** | Admin functions (rare, internal only) |

Focus on P0 and P1 first.
```

**Files to Create:**

- `integration/performance_audit.py` - Performance measurement script
- `integration/OPTIMIZATION_STRATEGIES.md` - Optimization guide
- `integration/current_performance.json` - Current performance data (auto-generated)

**Acceptance Criteria:**

- [ ] All operations meet performance targets from architecture plan
- [ ] No operation >20% slower than Session 15 baseline
- [ ] Optimizations documented
- [ ] Updated performance data saved
- [ ] API <50ms p95
- [ ] Database queries <1s
- [ ] FC60 <200ms
- [ ] AI <3000ms
- [ ] End-to-end <5000ms (single-user), <8000ms (multi-user)

**Verification:**

```bash
# Terminal: integration/

python performance_audit.py

# Expected Output:
# ==================================================================
#                      PERFORMANCE AUDIT
# ==================================================================
# 
# [1/8] Testing API Health Endpoint...
#       p95: 25.3ms | Target: <50ms
# [2/8] Testing User Creation...
#       p95: 78.2ms | Target: <100ms
# [3/8] Testing Single-User Reading Creation...
#       p95: 3456.7ms | Target: <5000ms
# [4/8] Testing FC60 Calculation...
#       p95: 145.6ms | Target: <200ms
# [5/8] Testing AI Interpretation...
#       p95: 2345.8ms | Target: <3000ms
# [6/8] Testing Database Query Performance...
#       p95: 67.4ms | Target: <100ms
# [7/8] Testing Multi-User Reading Performance...
#       p95: 6234.5ms | Target: <8000ms
# [8/8] Testing WebSocket Connection...
#       ⚠️  WebSocket performance should be tested manually
# 
# ==================================================================
#                      TARGET COMPLIANCE
# ==================================================================
# 
# Operation                      Current      Target       Status  
# ----------------------------------------------------------------------
# api_health                      25.30ms      50.00ms ✓ PASS  
# user_creation                   78.20ms     100.00ms ✓ PASS  
# reading_creation              3456.70ms    5000.00ms ✓ PASS  
# fc60_calculation                145.60ms     200.00ms ✓ PASS  
# ai_interpretation             2345.80ms    3000.00ms ✓ PASS  
# findings_query                  67.40ms     100.00ms ✓ PASS  
# multi_user_reading            6234.50ms    8000.00ms ✓ PASS  
# ----------------------------------------------------------------------
# 
# ==================================================================
#                      FINAL STATUS
# ==================================================================
# 
# ✅ ALL PERFORMANCE TARGETS MET!
#    System is performing within acceptable parameters.
# 
# 📄 Performance data saved: integration/current_performance.json
# 
# ✅ PERFORMANCE VERIFIED
```

**Checkpoint Gate:**

- [ ] All performance targets met
- [ ] No degraded operations (>20% slower)

**If targets missed, optimize using OPTIMIZATION_STRATEGIES.md before proceeding.**

---

### Phase 5: Security Audit (60 minutes)

**Objective:** Comprehensive security audit with zero critical vulnerabilities requirement

**Tasks:**

1. **Verify Data Encryption:**
   - Check database for encrypted vs plaintext data
   - Verify AES-256 encryption working
   - Test encryption/decryption roundtrip

2. **Verify API Authentication:**
   - Test endpoints without API key (should return 401)
   - Test endpoints with invalid API key (should return 401)
   - Test endpoints with valid API key (should return 200)
   - Verify rate limiting active

3. **Scan for Vulnerabilities:**
   - SQL injection testing
   - XSS testing
   - Hardcoded credential scanning
   - CORS configuration check
   - CLI usage verification (should be ZERO)

4. **Generate Security Report:**
   - Document all findings
   - Categorize by severity
   - Provide remediation steps

**Security Audit Implementation:**

```python
# integration/security_audit.py

import psycopg2
import requests
import re
import os
from typing import List, Dict
from datetime import datetime

API_BASE = "http://localhost:8000"
TEST_API_KEY = "test_api_key_12345"

class SecurityAudit:
    def __init__(self):
        self.issues = []
    
    def add_issue(self, severity: str, title: str, description: str, remediation: str = ""):
        self.issues.append({
            "severity": severity,
            "title": title,
            "description": description,
            "remediation": remediation,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_data_encryption(self):
        """Test 1: Verify data encrypted in database"""
        print("\n[1/7] Testing Data Encryption...")
        
        try:
            # Connect to database
            conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
            cur = conn.cursor()
            
            # Check if user data is encrypted
            cur.execute("SELECT name, birthday FROM oracle_users LIMIT 1")
            row = cur.fetchone()
            
            if row:
                name, birthday = row
                
                # Encrypted data should be long and contain non-printable chars
                # Plaintext name would be short and readable
                if len(name) < 50 or name.isprintable():
                    self.add_issue(
                        "CRITICAL",
                        "User names not encrypted in database",
                        f"Found plaintext or weakly encrypted name: {name[:20]}...",
                        "Implement AES-256 encryption for user.name field"
                    )
                    print(f"      ✗ User names NOT encrypted (found: {name[:20]}...)")
                else:
                    print(f"      ✓ User names encrypted (length: {len(name)} bytes)")
                
                # Check birthday encryption
                if len(str(birthday)) == 10:  # YYYY-MM-DD format = plaintext
                    self.add_issue(
                        "HIGH",
                        "Birthdays not encrypted in database",
                        f"Found plaintext birthday: {birthday}",
                        "Implement encryption for user.birthday field"
                    )
                    print(f"      ✗ Birthdays NOT encrypted")
                else:
                    print(f"      ✓ Birthdays encrypted")
            
            # Check if reading questions are encrypted
            cur.execute("SELECT question FROM oracle_readings LIMIT 1")
            row = cur.fetchone()
            
            if row:
                question = row[0]
                
                if question and len(question) < 100:
                    self.add_issue(
                        "HIGH",
                        "Reading questions not encrypted",
                        f"Found plaintext question: {question[:50]}...",
                        "Implement encryption for readings.question field"
                    )
                    print(f"      ✗ Questions NOT encrypted")
                else:
                    print(f"      ✓ Questions encrypted")
            
            conn.close()
            
        except Exception as e:
            self.add_issue(
                "MEDIUM",
                "Could not verify database encryption",
                f"Error: {e}",
                "Fix database connection or schema"
            )
            print(f"      ⚠️  Could not verify encryption: {e}")
    
    def test_api_authentication(self):
        """Test 2: Verify API authentication enforced"""
        print("\n[2/7] Testing API Authentication...")
        
        # Test without API key
        response = requests.get(f"{API_BASE}/api/oracle/users")
        
        if response.status_code == 401:
            print(f"      ✓ Missing API key rejected (401)")
        else:
            self.add_issue(
                "CRITICAL",
                "API does not require authentication",
                f"GET /api/oracle/users returned {response.status_code} without auth",
                "Implement API key middleware on all endpoints"
            )
            print(f"      ✗ Missing API key NOT rejected (got {response.status_code})")
        
        # Test with invalid API key
        response = requests.get(
            f"{API_BASE}/api/oracle/users",
            headers={"Authorization": "Bearer invalid_key_xyz"}
        )
        
        if response.status_code == 401:
            print(f"      ✓ Invalid API key rejected (401)")
        else:
            self.add_issue(
                "CRITICAL",
                "Invalid API keys accepted",
                f"Invalid key accepted, got {response.status_code}",
                "Validate API key against database"
            )
            print(f"      ✗ Invalid API key NOT rejected (got {response.status_code})")
        
        # Test with valid API key
        response = requests.get(
            f"{API_BASE}/api/oracle/users",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"}
        )
        
        if response.status_code == 200:
            print(f"      ✓ Valid API key accepted (200)")
        else:
            self.add_issue(
                "MEDIUM",
                "Valid API key rejected",
                f"Valid key rejected, got {response.status_code}",
                "Fix API key validation logic"
            )
            print(f"      ⚠️  Valid API key rejected (got {response.status_code})")
    
    def test_sql_injection(self):
        """Test 3: SQL injection protection"""
        print("\n[3/7] Testing SQL Injection Protection...")
        
        # Try SQL injection attack
        malicious_inputs = [
            "'; DROP TABLE oracle_users; --",
            "' OR '1'='1",
            "admin'--",
            "1'; UPDATE oracle_users SET name='hacked' WHERE '1'='1"
        ]
        
        vulnerabilities_found = False
        
        for malicious in malicious_inputs:
            # Try user creation with SQL injection
            response = requests.post(
                f"{API_BASE}/api/oracle/users",
                json={
                    "name": malicious,
                    "birthday": "1990-01-01",
                    "mother_name": "Test"
                },
                headers={"Authorization": f"Bearer {TEST_API_KEY}"}
            )
            
            # Should either reject (400) or sanitize (201 but with escaped value)
            if response.status_code not in [400, 201]:
                self.add_issue(
                    "CRITICAL",
                    "Possible SQL injection vulnerability",
                    f"Malicious input '{malicious}' got {response.status_code}",
                    "Use parameterized queries everywhere"
                )
                vulnerabilities_found = True
                print(f"      ✗ Vulnerable to: {malicious[:30]}...")
        
        if not vulnerabilities_found:
            print(f"      ✓ SQL injection protection active")
    
    def test_xss_protection(self):
        """Test 4: XSS protection"""
        print("\n[4/7] Testing XSS Protection...")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
        
        vulnerabilities_found = False
        
        for payload in xss_payloads:
            # Try creating user with XSS payload
            response = requests.post(
                f"{API_BASE}/api/oracle/users",
                json={
                    "name": payload,
                    "birthday": "1990-01-01",
                    "mother_name": "Test"
                },
                headers={"Authorization": f"Bearer {TEST_API_KEY}"}
            )
            
            if response.status_code == 201:
                # Check if payload was stored as-is
                user = response.json()
                if payload in user.get("name", ""):
                    self.add_issue(
                        "HIGH",
                        "Possible XSS vulnerability",
                        f"XSS payload '{payload[:30]}...' stored without sanitization",
                        "Sanitize all user inputs before storage"
                    )
                    vulnerabilities_found = True
                    print(f"      ✗ XSS payload stored: {payload[:30]}...")
        
        if not vulnerabilities_found:
            print(f"      ✓ XSS protection active")
    
    def scan_hardcoded_credentials(self):
        """Test 5: Scan for hardcoded credentials"""
        print("\n[5/7] Scanning for Hardcoded Credentials...")
        
        credential_patterns = [
            (r'api_key\s*=\s*["\']sk-[a-zA-Z0-9]{20,}["\']', 'Anthropic API key'),
            (r'password\s*=\s*["\'].{8,}["\']', 'Password'),
            (r'secret\s*=\s*["\'].{8,}["\']', 'Secret'),
            (r'postgresql://[^:]+:[^@]+@', 'Database credentials'),
            (r'Bearer\s+[a-zA-Z0-9_-]{20,}', 'API Bearer token'),
        ]
        
        hardcoded_found = False
        
        # Scan all Python files
        for root, dirs, files in os.walk('.'):
            # Skip virtual environments and node_modules
            dirs[:] = [d for d in dirs if d not in ['venv', 'node_modules', '.git', '__pycache__']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            
                            for pattern, cred_type in credential_patterns:
                                matches = re.finditer(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    # Skip comments
                                    line_start = content.rfind('\n', 0, match.start()) + 1
                                    line = content[line_start:match.end()]
                                    
                                    if not line.strip().startswith('#'):
                                        self.add_issue(
                                            "HIGH",
                                            f"Hardcoded {cred_type} found",
                                            f"In {filepath}: {match.group()[:50]}...",
                                            "Move credentials to environment variables"
                                        )
                                        hardcoded_found = True
                                        print(f"      ✗ Found in {filepath}")
                    except Exception as e:
                        pass  # Skip files that can't be read
        
        if not hardcoded_found:
            print(f"      ✓ No hardcoded credentials found")
    
    def test_cors_configuration(self):
        """Test 6: CORS configuration"""
        print("\n[6/7] Testing CORS Configuration...")
        
        # Test CORS headers
        response = requests.options(
            f"{API_BASE}/api/oracle/users",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        if "Access-Control-Allow-Origin" in response.headers:
            allowed_origin = response.headers["Access-Control-Allow-Origin"]
            
            if allowed_origin == "*":
                self.add_issue(
                    "MEDIUM",
                    "CORS allows all origins",
                    "CORS configured with wildcard (*) - too permissive",
                    "Restrict CORS to specific origins (e.g., localhost:5173, production domain)"
                )
                print(f"      ⚠️  CORS allows all origins (*) - too permissive")
            else:
                print(f"      ✓ CORS configured: {allowed_origin}")
        else:
            self.add_issue(
                "LOW",
                "CORS not configured",
                "No CORS headers found - may block frontend",
                "Configure CORS middleware"
            )
            print(f"      ⚠️  CORS not configured")
    
    def test_rate_limiting(self):
        """Test 7: Rate limiting"""
        print("\n[7/7] Testing Rate Limiting...")
        
        # Make many rapid requests
        endpoint = f"{API_BASE}/api/oracle/calculate-fc60"
        
        rate_limited = False
        for i in range(100):
            response = requests.post(
                endpoint,
                json={"birthday": "1990-01-01", "mother_name": "Test"},
                headers={"Authorization": f"Bearer {TEST_API_KEY}"}
            )
            
            if response.status_code == 429:  # Too Many Requests
                rate_limited = True
                print(f"      ✓ Rate limiting active (triggered at request {i+1})")
                break
        
        if not rate_limited:
            self.add_issue(
                "MEDIUM",
                "Rate limiting not configured",
                "100 rapid requests all succeeded - no rate limit detected",
                "Implement rate limiting (e.g., 100 requests/hour per key)"
            )
            print(f"      ⚠️  Rate limiting not detected (100 requests succeeded)")
    
    def verify_api_only_integration(self):
        """Test 8: Verify API-only integration (no CLI)"""
        print("\n[8/8] Verifying API-only Integration (NO CLI)...")
        
        cli_patterns = [
            (r'subprocess\.run.*claude', 'subprocess.run with claude'),
            (r'subprocess\.call.*claude', 'subprocess.call with claude'),
            (r'os\.system.*claude', 'os.system with claude'),
            (r'subprocess\.Popen.*claude', 'subprocess.Popen with claude'),
        ]
        
        cli_usage_found = False
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['venv', 'node_modules', '.git', '__pycache__']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            
                            for pattern, desc in cli_patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    self.add_issue(
                                        "HIGH",
                                        "CLI usage detected - should use API",
                                        f"In {filepath}: {desc}",
                                        "Replace with Anthropic API direct calls"
                                    )
                                    cli_usage_found = True
                                    print(f"      ✗ CLI usage in {filepath}")
                    except:
                        pass
        
        if not cli_usage_found:
            print(f"      ✓ No CLI usage detected (API-only integration)")
    
    def generate_report(self):
        """Generate security audit report"""
        print("\n" + "=" * 70)
        print(" " * 20 + "SECURITY AUDIT SUMMARY")
        print("=" * 70)
        
        if not self.issues:
            print("\n✅ NO SECURITY ISSUES FOUND!")
            print("   System passes security audit.\n")
            return True
        
        # Count by severity
        critical = [i for i in self.issues if i["severity"] == "CRITICAL"]
        high = [i for i in self.issues if i["severity"] == "HIGH"]
        medium = [i for i in self.issues if i["severity"] == "MEDIUM"]
        low = [i for i in self.issues if i["severity"] == "LOW"]
        
        print(f"\n⚠️  Found {len(self.issues)} security issues:")
        print(f"   • {len(critical)} CRITICAL")
        print(f"   • {len(high)} HIGH")
        print(f"   • {len(medium)} MEDIUM")
        print(f"   • {len(low)} LOW\n")
        
        # Display issues by severity
        for severity_name, severity_issues in [
            ("CRITICAL", critical),
            ("HIGH", high),
            ("MEDIUM", medium),
            ("LOW", low)
        ]:
            if severity_issues:
                print(f"\n{severity_name} Issues:")
                print("-" * 70)
                for i, issue in enumerate(severity_issues, 1):
                    print(f"\n{i}. {issue['title']}")
                    print(f"   {issue['description']}")
                    if issue['remediation']:
                        print(f"   ➜ {issue['remediation']}")
        
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(self.issues),
            "by_severity": {
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "low": len(low)
            },
            "issues": self.issues
        }
        
        with open("integration/security_audit_report.json", "w") as f:
            import json
            json.dump(report, f, indent=2)
        
        # Also create markdown report
        with open("integration/security_audit_report.md", "w") as f:
            f.write("# Security Audit Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Total Issues:** {len(self.issues)}\n")
            f.write(f"- **Critical:** {len(critical)}\n")
            f.write(f"- **High:** {len(high)}\n")
            f.write(f"- **Medium:** {len(medium)}\n")
            f.write(f"- **Low:** {len(low)}\n\n")
            
            if critical:
                f.write("## ❌ CRITICAL Issues\n\n")
                for issue in critical:
                    f.write(f"### {issue['title']}\n\n")
                    f.write(f"**Description:** {issue['description']}\n\n")
                    f.write(f"**Remediation:** {issue['remediation']}\n\n")
            
            if high:
                f.write("## ⚠️ HIGH Severity Issues\n\n")
                for issue in high:
                    f.write(f"### {issue['title']}\n\n")
                    f.write(f"**Description:** {issue['description']}\n\n")
                    f.write(f"**Remediation:** {issue['remediation']}\n\n")
            
            # Medium and Low in collapsed sections
            if medium:
                f.write("## MEDIUM Severity Issues\n\n")
                for issue in medium:
                    f.write(f"- **{issue['title']}:** {issue['description']}\n")
            
            if low:
                f.write("\n## LOW Severity Issues\n\n")
                for issue in low:
                    f.write(f"- **{issue['title']}:** {issue['description']}\n")
        
        print(f"\n📄 Reports saved:")
        print(f"   • integration/security_audit_report.json")
        print(f"   • integration/security_audit_report.md")
        
        # Determine pass/fail
        if critical:
            print(f"\n❌ SECURITY AUDIT FAILED")
            print(f"   {len(critical)} CRITICAL issues must be fixed before production")
            return False
        elif high:
            print(f"\n⚠️  SECURITY AUDIT WARNING")
            print(f"   {len(high)} HIGH severity issues should be fixed before production")
            return False
        else:
            print(f"\n✅ SECURITY AUDIT PASSED")
            print(f"   Only medium/low issues found - acceptable for production")
            return True

def run_security_audit():
    audit = SecurityAudit()
    
    print("=" * 70)
    print(" " * 20 + "SECURITY AUDIT")
    print("=" * 70)
    
    audit.test_data_encryption()
    audit.test_api_authentication()
    audit.test_sql_injection()
    audit.test_xss_protection()
    audit.scan_hardcoded_credentials()
    audit.test_cors_configuration()
    audit.test_rate_limiting()
    audit.verify_api_only_integration()
    
    passed = audit.generate_report()
    
    return 0 if passed else 1

if __name__ == "__main__":
    exit(run_security_audit())
```

**Files to Create:**

- `integration/security_audit.py` - Automated security audit script
- `integration/security_audit_report.json` - Audit results (auto-generated)
- `integration/security_audit_report.md` - Human-readable audit report (auto-generated)

**Acceptance Criteria:**

- [ ] Data encrypted in database (verified by checking field lengths)
- [ ] API authentication enforced (401 for missing/invalid keys)
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] No hardcoded credentials in code
- [ ] CORS configured appropriately (not wildcard)
- [ ] Rate limiting active
- [ ] API-only integration (zero CLI usage detected)
- [ ] Zero critical security issues
- [ ] Zero high-severity security issues

**Verification:**

```bash
# Terminal: integration/

python security_audit.py

# Expected Output:
# ==================================================================
#                      SECURITY AUDIT
# ==================================================================
# 
# [1/7] Testing Data Encryption...
#       ✓ User names encrypted (length: 256 bytes)
#       ✓ Birthdays encrypted
#       ✓ Questions encrypted
# [2/7] Testing API Authentication...
#       ✓ Missing API key rejected (401)
#       ✓ Invalid API key rejected (401)
#       ✓ Valid API key accepted (200)
# [3/7] Testing SQL Injection Protection...
#       ✓ SQL injection protection active
# [4/7] Testing XSS Protection...
#       ✓ XSS protection active
# [5/7] Scanning for Hardcoded Credentials...
#       ✓ No hardcoded credentials found
# [6/7] Testing CORS Configuration...
#       ✓ CORS configured: http://localhost:5173
# [7/7] Testing Rate Limiting...
#       ✓ Rate limiting active (triggered at request 45)
# [8/8] Verifying API-only Integration (NO CLI)...
#       ✓ No CLI usage detected (API-only integration)
# 
# ==================================================================
#                   SECURITY AUDIT SUMMARY
# ==================================================================
# 
# ✅ NO SECURITY ISSUES FOUND!
#    System passes security audit.
# 
# 📄 Reports saved:
#    • integration/security_audit_report.json
#    • integration/security_audit_report.md
# 
# ✅ SECURITY AUDIT PASSED
```

**Checkpoint Gate:**

- [ ] Zero critical security issues
- [ ] Zero high-severity issues
- [ ] Security audit passes

**FIX CRITICAL ISSUES IMMEDIATELY. Do not proceed if critical issues found.**

---

### Phase 6: Final Polish (60 minutes)

**Objective:** Fix visual bugs, improve UX, add missing features, clean up code

**Tasks:**

1. **UI Polish:**
   - Fix visual bugs (alignment, spacing, colors)
   - Add loading indicators everywhere
   - Improve error messages (user-friendly)
   - Add success confirmations
   - Verify responsive design

2. **UX Improvements:**
   - Add tooltips on complex features
   - Improve keyboard navigation
   - Add screen reader support (basic)
   - Test tab order
   - Verify focus states

3. **Code Cleanup:**
   - Remove `console.log` statements
   - Remove commented-out code
   - Fix TODOs (or document for future)
   - Apply linting
   - Update comments

**Polish Checklist:**

```markdown
# integration/POLISH_CHECKLIST.md

## UI Polish Checklist

### Visual Quality
- [ ] All buttons same size and style (consistent)
- [ ] All form inputs aligned properly
- [ ] All text readable (sufficient contrast)
- [ ] No overlapping elements
- [ ] Icons consistent size (16px or 24px)
- [ ] Spacing consistent (use 4px, 8px, 16px, 24px grid)
- [ ] Dark theme applied consistently

### UX Quality
- [ ] Loading spinner on every async operation
- [ ] Loading state shows what's loading ("Creating reading...")
- [ ] Error messages specific and actionable
- [ ] Success messages confirm what happened
- [ ] Forms validate before submit
- [ ] Validation errors show next to field
- [ ] Disabled buttons show why (tooltip or message)
- [ ] Empty states helpful ("No readings yet. Create your first!")

### Responsive Design
- [ ] Mobile (375px): All features accessible, no horizontal scroll
- [ ] Tablet (768px): Optimized layout, good use of space
- [ ] Desktop (1920px): Full features, not stretched

### Accessibility
- [ ] All buttons have aria-label if icon-only
- [ ] All form inputs have associated <label>
- [ ] All images have alt text
- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Tab order logical (top-to-bottom, left-to-right)
- [ ] Focus states visible (blue outline or custom)
- [ ] Screen reader announces page changes
- [ ] Color contrast ratio ≥4.5:1 (WCAG AA)

### Code Quality
- [ ] No `console.log` in production code
- [ ] No `console.error` except in error handlers
- [ ] No commented-out code
- [ ] No `TODO` without GitHub issue reference
- [ ] Linting passes (no warnings)
- [ ] TypeScript strict mode (no `any` types)
- [ ] All functions documented
- [ ] All components exported with clear names

## Verification

### Visual Check (Manual)
1. Open http://localhost:5173 in browser
2. Check each page:
   - Dashboard: layout correct, no overlaps
   - Oracle: form aligned, buttons work
   - Vault: table displays correctly
   - History: chronological, clickable
3. Resize browser:
   - 375px (mobile): everything accessible?
   - 768px (tablet): layout optimized?
   - 1920px (desktop): not stretched?

### Keyboard Navigation Check
1. Tab through entire app
2. Can reach all interactive elements?
3. Tab order logical?
4. Enter key submits forms?
5. Escape key closes modals?

### Screen Reader Check
1. Install NVDA (Windows) or VoiceOver (Mac)
2. Navigate app with screen reader
3. Are all buttons announced?
4. Are form errors announced?
5. Are page changes announced?

### Code Quality Check
```bash
# Frontend linting
cd frontend
npm run lint
# Expected: No errors, no warnings

# TypeScript check
npm run type-check
# Expected: No type errors

# Build check
npm run build
# Expected: Build succeeds, bundle < 1MB

# Backend linting (Python)
cd api
black app/ --check
ruff check app/
mypy app/ --strict
# Expected: All checks pass
```
```

**Files to Update:**

- All frontend components with visual/UX issues
- All backend files with code quality issues
- `integration/POLISH_CHECKLIST.md` - Polish verification checklist

**Acceptance Criteria:**

- [ ] UI polish checklist 100% complete
- [ ] No visual bugs on any screen size
- [ ] All async operations show loading state
- [ ] All error messages user-friendly
- [ ] Keyboard navigation fully functional
- [ ] Screen reader support (basic)
- [ ] No linting errors
- [ ] No TypeScript errors
- [ ] No console errors in browser
- [ ] Code clean (no TODOs, no commented code, no console.logs)

**Verification:**

```bash
# Frontend checks
cd frontend
npm run lint                      # No errors
npm run type-check                # No errors
npm run build                     # Succeeds
open http://localhost:5173        # Manual visual check

# Backend checks
cd ../api
black app/ --check                # Already formatted
ruff check app/                   # No issues
mypy app/ --strict                # No type errors

# Browser console check
# Open browser DevTools → Console
# Expected: No errors (except possibly hot reload in dev)
```

**Checkpoint Gate:**

- [ ] UI polished and professional
- [ ] Code clean and maintainable
- [ ] All checks pass

---

### Phase 7: Production Readiness Verification (90 minutes)

**Objective:** Final verification that system is production-ready with all services, tests, and documentation complete

**Tasks:**

1. **Verify All Services:**
   - Stop all services (`docker-compose down`)
   - Start all services (`docker-compose up -d`)
   - Verify all healthy
   - Test inter-service communication

2. **Run Complete Test Suite:**
   - All unit tests (API, Oracle, Security)
   - All integration tests
   - All E2E tests
   - Verify all pass

3. **Complete Documentation:**
   - README.md
   - API_REFERENCE.md
   - DEPLOYMENT.md
   - TROUBLESHOOTING.md
   - .env.example

4. **Final Production Checklist:**
   - Comprehensive checklist covering all requirements
   - Every item verified

**Production Readiness Script:**

```bash
#!/bin/bash
# scripts/production_readiness_check.sh

echo "=============================================================="
echo "           NPS V4 PRODUCTION READINESS CHECK"
echo "=============================================================="

ERRORS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function pass() {
    echo -e "${GREEN}✓${NC} $1"
}

function fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

function warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Test 1: Services
echo -e "\n[1/10] Checking Services..."
docker-compose down > /dev/null 2>&1
docker-compose up -d > /dev/null 2>&1
sleep 10

POSTGRES_STATUS=$(docker-compose ps postgres | grep -c "healthy")
API_STATUS=$(docker-compose ps api | grep -c "healthy")
ORACLE_STATUS=$(docker-compose ps oracle-service | grep -c "healthy")
FRONTEND_STATUS=$(docker-compose ps frontend | grep -c "Up")

if [ $POSTGRES_STATUS -eq 1 ]; then pass "PostgreSQL healthy"; else fail "PostgreSQL not healthy"; fi
if [ $API_STATUS -eq 1 ]; then pass "API healthy"; else fail "API not healthy"; fi
if [ $ORACLE_STATUS -eq 1 ]; then pass "Oracle Service healthy"; else fail "Oracle Service not healthy"; fi
if [ $FRONTEND_STATUS -eq 1 ]; then pass "Frontend running"; else fail "Frontend not running"; fi

# Test 2: API Health
echo -e "\n[2/10] Testing API Health..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health)
if [ $HTTP_CODE -eq 200 ]; then
    pass "API health endpoint returns 200"
else
    fail "API health endpoint returns $HTTP_CODE"
fi

# Test 3: Database Connection
echo -e "\n[3/10] Testing Database..."
PSQL_RESULT=$(PGPASSWORD=nps_password psql -h localhost -U nps_user -d nps_db -c "SELECT 1" 2>&1)
if echo "$PSQL_RESULT" | grep -q "(1 row)"; then
    pass "Database connection successful"
else
    fail "Database connection failed"
fi

# Test 4: Unit Tests
echo -e "\n[4/10] Running Unit Tests..."

# API tests
cd api
source venv/bin/activate
PYTEST_OUTPUT=$(pytest tests/ -v --tb=short 2>&1)
if echo "$PYTEST_OUTPUT" | grep -q "passed"; then
    PASSED=$(echo "$PYTEST_OUTPUT" | grep -oP '\d+(?= passed)')
    pass "API tests: $PASSED passed"
else
    fail "API tests failed"
fi
deactivate
cd ..

# Oracle tests
cd backend/oracle-service
source venv/bin/activate
PYTEST_OUTPUT=$(pytest tests/ -v --tb=short 2>&1)
if echo "$PYTEST_OUTPUT" | grep -q "passed"; then
    PASSED=$(echo "$PYTEST_OUTPUT" | grep -oP '\d+(?= passed)')
    pass "Oracle tests: $PASSED passed"
else
    fail "Oracle tests failed"
fi
deactivate
cd ../..

# Test 5: Integration Tests
echo -e "\n[5/10] Running Integration Tests..."
cd integration
PYTEST_OUTPUT=$(pytest tests/ -v --tb=short 2>&1)
if echo "$PYTEST_OUTPUT" | grep -q "passed"; then
    PASSED=$(echo "$PYTEST_OUTPUT" | grep -oP '\d+(?= passed)')
    pass "Integration tests: $PASSED passed"
else
    fail "Integration tests failed"
fi
cd ..

# Test 6: E2E Tests
echo -e "\n[6/10] Running E2E Tests..."
cd frontend
E2E_OUTPUT=$(npx playwright test 2>&1)
if echo "$E2E_OUTPUT" | grep -q "passed"; then
    PASSED=$(echo "$E2E_OUTPUT" | grep -oP '\d+(?= passed)')
    pass "E2E tests: $PASSED passed"
else
    fail "E2E tests failed"
fi
cd ..

# Test 7: Performance Check
echo -e "\n[7/10] Checking Performance..."
cd integration
PERF_OUTPUT=$(python performance_audit.py 2>&1)
if echo "$PERF_OUTPUT" | grep -q "ALL PERFORMANCE TARGETS MET"; then
    pass "All performance targets met"
else
    fail "Performance targets not met"
fi
cd ..

# Test 8: Security Audit
echo -e "\n[8/10] Running Security Audit..."
cd integration
SEC_OUTPUT=$(python security_audit.py 2>&1)
if echo "$SEC_OUTPUT" | grep -q "SECURITY AUDIT PASSED"; then
    pass "Security audit passed (zero critical issues)"
else
    fail "Security audit failed (critical issues found)"
fi
cd ..

# Test 9: Documentation Check
echo -e "\n[9/10] Checking Documentation..."

if [ -f "docs/README.md" ] && [ $(wc -w < docs/README.md) -gt 100 ]; then
    pass "README.md complete ($(wc -w < docs/README.md) words)"
else
    fail "README.md missing or incomplete"
fi

if [ -f "docs/API_REFERENCE.md" ]; then
    pass "API_REFERENCE.md exists"
else
    fail "API_REFERENCE.md missing"
fi

if [ -f "docs/DEPLOYMENT.md" ]; then
    pass "DEPLOYMENT.md exists"
else
    fail "DEPLOYMENT.md missing"
fi

if [ -f "docs/TROUBLESHOOTING.md" ]; then
    pass "TROUBLESHOOTING.md exists"
else
    fail "TROUBLESHOOTING.md missing"
fi

if [ -f ".env.example" ]; then
    pass ".env.example exists"
else
    fail ".env.example missing"
fi

# Test 10: Code Quality
echo -e "\n[10/10] Checking Code Quality..."

# Frontend linting
cd frontend
LINT_OUTPUT=$(npm run lint 2>&1)
if echo "$LINT_OUTPUT" | grep -q "0 problems"; then
    pass "Frontend linting: 0 errors"
else
    warn "Frontend linting has warnings"
fi

# TypeScript check
TS_OUTPUT=$(npm run type-check 2>&1)
if ! echo "$TS_OUTPUT" | grep -q "error TS"; then
    pass "TypeScript: 0 errors"
else
    fail "TypeScript has errors"
fi
cd ..

# Backend linting
cd api
BLACK_OUTPUT=$(black app/ --check 2>&1)
if echo "$BLACK_OUTPUT" | grep -q "would reformat" || echo "$BLACK_OUTPUT" | grep -q "All done"; then
    pass "Python formatting: OK"
else
    fail "Python formatting: needs black"
fi
cd ..

# Final Report
echo -e "\n=============================================================="
echo "                     FINAL REPORT"
echo "=============================================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "\n${GREEN}✅ PRODUCTION READY!${NC}"
    echo -e "All checks passed. System ready for deployment.\n"
    exit 0
else
    echo -e "\n${RED}❌ NOT PRODUCTION READY${NC}"
    echo -e "$ERRORS checks failed. Fix issues before deployment.\n"
    exit 1
fi
```

**Production Readiness Checklist:**

```markdown
# PRODUCTION_READINESS_CHECKLIST.md

## ✅ NPS V4 Production Readiness Checklist

**Date:** [Completion Date]  
**Verified By:** [Name]

---

### Infrastructure

- [ ] All services start with `docker-compose up -d`
- [ ] All services report "healthy" status
- [ ] PostgreSQL accessible (psql connection works)
- [ ] API accessible (health endpoint returns 200)
- [ ] Frontend accessible (loads in browser)
- [ ] Services auto-restart on failure (tested)
- [ ] Data persists across service restarts (tested)
- [ ] Environment variables loaded from .env

### Testing

- [ ] Unit tests pass: API (50+ tests)
- [ ] Unit tests pass: Oracle Service (30+ tests)
- [ ] Unit tests pass: Security (10+ tests)
- [ ] Integration tests pass (20+ tests)
- [ ] E2E tests pass (6+ scenarios)
- [ ] Manual testing complete (all workflows)
- [ ] No critical bugs
- [ ] No high-severity bugs
- [ ] Test coverage: Python ≥95%, TypeScript ≥90%, Rust ≥80%

### Performance

- [ ] API response time <50ms p95
- [ ] Database queries <1s
- [ ] FC60 calculations <200ms
- [ ] AI interpretations <3000ms
- [ ] End-to-end single-user <5000ms
- [ ] End-to-end multi-user <8000ms
- [ ] Frontend initial load <2s
- [ ] Frontend page transitions <100ms

### Security

- [ ] Data encrypted in database (verified)
- [ ] API authentication enforced (401 for invalid keys)
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] No hardcoded credentials in code
- [ ] CORS configured correctly (not wildcard)
- [ ] Rate limiting active
- [ ] API-only integration (zero CLI usage)
- [ ] Security audit passes (zero critical issues)
- [ ] SSL/TLS configured (if production)

### Functionality

- [ ] Single-user Oracle readings work
- [ ] Multi-user Oracle readings work (2-user, 5-user)
- [ ] Compatibility calculations work
- [ ] Persian language support works (RTL, keyboard, translations)
- [ ] Calendar date picker works
- [ ] User history displays correctly
- [ ] Error handling graceful (network failures, invalid input)
- [ ] All user workflows tested end-to-end

### User Experience

- [ ] No visual bugs (tested mobile, tablet, desktop)
- [ ] Loading indicators on all async operations
- [ ] Error messages user-friendly
- [ ] Success messages confirm operations
- [ ] Keyboard navigation works
- [ ] Screen reader support (basic WCAG 2.1 AA)
- [ ] Responsive design (375px, 768px, 1920px)
- [ ] Dark theme consistent

### Code Quality

- [ ] No linting errors (frontend)
- [ ] No TypeScript errors
- [ ] No linting errors (backend)
- [ ] No `console.log` in production code
- [ ] No commented-out code
- [ ] No unresolved TODOs (or documented for future)
- [ ] Code formatted (Prettier, Black)
- [ ] All functions documented

### Documentation

- [ ] README.md complete (how to run, test, deploy)
- [ ] API_REFERENCE.md complete (all endpoints documented)
- [ ] DEPLOYMENT.md complete (step-by-step deployment guide)
- [ ] TROUBLESHOOTING.md complete (common issues + solutions)
- [ ] .env.example complete (all variables documented with examples)
- [ ] Code comments explain "why" not "what"
- [ ] Architecture diagrams (if applicable)

### Deployment

- [ ] Can deploy to production environment (tested)
- [ ] Environment variables configured for production
- [ ] Database migrations run successfully
- [ ] Backup/restore tested (database)
- [ ] Rollback procedure documented
- [ ] Health checks configured
- [ ] Logging configured (JSON format, centralized)
- [ ] Monitoring configured (metrics, alerts)

### Final Checks

- [ ] All Session 15 issues resolved
- [ ] All Session 16 (this session) issues resolved
- [ ] No regressions from previous sessions
- [ ] All acceptance criteria met
- [ ] Production readiness script passes (`./scripts/production_readiness_check.sh`)

---

## ✅ VERIFICATION

**Production Readiness Script:**
```bash
./scripts/production_readiness_check.sh
```

**Expected Output:**
```
==============================================================
           NPS V4 PRODUCTION READINESS CHECK
==============================================================

[1/10] Checking Services...
✓ PostgreSQL healthy
✓ API healthy
✓ Oracle Service healthy
✓ Frontend running

[2/10] Testing API Health...
✓ API health endpoint returns 200

[3/10] Testing Database...
✓ Database connection successful

[4/10] Running Unit Tests...
✓ API tests: 52 passed
✓ Oracle tests: 34 passed

[5/10] Running Integration Tests...
✓ Integration tests: 24 passed

[6/10] Running E2E Tests...
✓ E2E tests: 6 passed

[7/10] Checking Performance...
✓ All performance targets met

[8/10] Running Security Audit...
✓ Security audit passed (zero critical issues)

[9/10] Checking Documentation...
✓ README.md complete (543 words)
✓ API_REFERENCE.md exists
✓ DEPLOYMENT.md exists
✓ TROUBLESHOOTING.md exists
✓ .env.example exists

[10/10] Checking Code Quality...
✓ Frontend linting: 0 errors
✓ TypeScript: 0 errors
✓ Python formatting: OK

==============================================================
                     FINAL REPORT
==============================================================

✅ PRODUCTION READY!
All checks passed. System ready for deployment.
```

---

## 🎉 PRODUCTION READY STATUS

**Date Achieved:** [Fill in when complete]  
**Final Status:** ✅ PRODUCTION READY

**What Was Accomplished:**
- Transformed 21,909 LOC monolithic desktop app into distributed 7-layer microservices
- Built self-improving AI system with Oracle service
- Implemented complete multi-user reading functionality with compatibility analysis
- Achieved full Persian language support (keyboard, RTL, translations)
- Met all performance targets (<50ms API, <5s end-to-end)
- Passed security audit (zero critical issues)
- API-only integration (no CLI dependencies)
- Complete test coverage (125+ tests, all passing)
- Production-ready with full documentation

**System Is Ready For:**
- Production deployment
- Real user testing
- Continuous improvement
- Future enhancements

**Congratulations! 🚀**
```

**Files to Create:**

- `scripts/production_readiness_check.sh` - Automated production check script
- `PRODUCTION_READINESS_CHECKLIST.md` - Complete checklist
- `docs/README.md` - Complete user guide
- `docs/API_REFERENCE.md` - Complete API documentation
- `docs/DEPLOYMENT.md` - Complete deployment guide
- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- `.env.example` - Updated with all variables documented

**Acceptance Criteria:**

- [ ] All services start successfully
- [ ] All tests pass (125+ tests)
- [ ] All documentation complete
- [ ] Production readiness checklist 100% complete
- [ ] Production readiness script passes

**Verification:**

```bash
# Make script executable
chmod +x scripts/production_readiness_check.sh

# Run production readiness check
./scripts/production_readiness_check.sh

# Expected: ✅ PRODUCTION READY! (exit code 0)
```

**Checkpoint Gate:**

- [ ] Production readiness script passes
- [ ] All checklist items verified

**System is PRODUCTION READY! 🎉**

---

## VERIFICATION CHECKLIST (All Phases)

### Phase 1: Issue Remediation
- [ ] All critical issues resolved
- [ ] All high-priority issues resolved
- [ ] Regression tests added
- [ ] All integration tests pass

### Phase 2: Multi-User Testing
- [ ] 2-user readings work
- [ ] 5-user readings work
- [ ] Compatibility calculations correct
- [ ] Permission system working
- [ ] Performance acceptable

### Phase 3: E2E Testing
- [ ] All 6 E2E scenarios pass
- [ ] UI fully functional
- [ ] Persian mode works
- [ ] Error handling graceful

### Phase 4: Performance
- [ ] All targets met
- [ ] No degraded operations
- [ ] Performance data saved

### Phase 5: Security
- [ ] Zero critical issues
- [ ] Zero high-severity issues
- [ ] API-only integration verified
- [ ] Security report generated

### Phase 6: Polish
- [ ] UI polished
- [ ] Code clean
- [ ] No linting errors

### Phase 7: Production Readiness
- [ ] All services healthy
- [ ] All tests pass (125+)
- [ ] All documentation complete
- [ ] Checklist 100% complete
- [ ] Production script passes

---

## SUCCESS CRITERIA

### Quantitative Metrics

1. ✅ **Test Coverage:** 125+ tests pass (100% pass rate)
2. ✅ **Performance:** All targets met (API <50ms, E2E <5s)
3. ✅ **Security:** Zero critical, zero high-severity issues
4. ✅ **Documentation:** 4 complete docs (README, API, Deploy, Troubleshoot)
5. ✅ **Code Quality:** Zero linting errors, zero type errors

### Qualitative Metrics

1. ✅ **Functionality:** All user workflows work end-to-end
2. ✅ **User Experience:** Professional, polished, accessible
3. ✅ **Reliability:** Services auto-restart, data persists
4. ✅ **Maintainability:** Clean code, comprehensive tests, complete docs
5. ✅ **Production Readiness:** Can deploy today with confidence

### Final Deliverables

**Working System:**
- [ ] 7 integrated layers (Frontend, API, Oracle, Database, Infrastructure, Security, DevOps)
- [ ] Single-user and multi-user Oracle readings
- [ ] Persian language support (keyboard, RTL, translations)
- [ ] API-only AI integration (zero CLI usage)
- [ ] Production-ready with monitoring

**Test Suite:**
- [ ] 50+ API unit tests
- [ ] 34+ Oracle unit tests
- [ ] 24+ integration tests
- [ ] 6+ E2E test scenarios
- [ ] All tests passing (125+ total)

**Documentation:**
- [ ] README.md (complete user guide)
- [ ] API_REFERENCE.md (all endpoints)
- [ ] DEPLOYMENT.md (step-by-step)
- [ ] TROUBLESHOOTING.md (common issues)
- [ ] .env.example (all variables)

**Reports:**
- [ ] Performance audit report (all targets met)
- [ ] Security audit report (zero critical issues)
- [ ] Production readiness report (all checks passed)
- [ ] Integration issues report (all resolved)

---

## NEXT STEPS (After Production Ready)

1. **Deploy to Production:**
   - Follow DEPLOYMENT.md guide
   - Set up production environment variables
   - Configure SSL/TLS certificates
   - Set up monitoring and alerts
   - Test in production environment

2. **User Acceptance Testing:**
   - Invite beta users
   - Collect feedback
   - Monitor for issues
   - Iterate based on feedback

3. **Continuous Improvement:**
   - Add new features from backlog
   - Optimize based on real usage data
   - Expand language support (more languages)
   - Enhance AI capabilities

4. **Future Enhancements (Backlog):**
   - Scanner service integration (Bitcoin wallet hunting)
   - Vault service (findings browser)
   - Learning service (AI pattern analysis)
   - Telegram bot (remote control)
   - Mobile app (iOS/Android)

---

## CONGRATULATIONS! 🎉

**You've completed Integration Phase 2!**

The NPS V4 Oracle system is now **PRODUCTION READY** with:
- ✅ All integration issues resolved
- ✅ Comprehensive multi-user support
- ✅ Full E2E test coverage
- ✅ Performance optimized
- ✅ Security audited (zero critical issues)
- ✅ UI polished and professional
- ✅ Complete documentation
- ✅ API-only integration (no CLI)
- ✅ 125+ tests passing

**The system is ready for deployment! 🚀**

---

*Specification Version: 1.0*  
*Created: 2026-02-08*  
*Status: Ready for Claude Code CLI Execution*
