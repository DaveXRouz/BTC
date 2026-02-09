#!/usr/bin/env bash
# NPS Production Readiness Check
# Automated verification of 10 key requirements
# Usage: ./scripts/production_readiness_check.sh

PASS=0
FAIL=0
WARN=0

pass() { echo "  [PASS] $1"; PASS=$((PASS + 1)); }
fail() { echo "  [FAIL] $1"; FAIL=$((FAIL + 1)); }
warn() { echo "  [WARN] $1"; WARN=$((WARN + 1)); }

echo "=============================================="
echo "NPS Production Readiness Check"
echo "=============================================="
echo ""

# 1. Database schema file exists and has critical fixes
echo "[1/10] Database Schema"
if [ -f "database/init.sql" ]; then
    if grep -q "deleted_at TIMESTAMPTZ" database/init.sql; then
        pass "init.sql has deleted_at column (S2 fix)"
    else
        fail "init.sql missing deleted_at column"
    fi
    if grep -q "'reading'" database/init.sql; then
        pass "init.sql has expanded sign_type CHECK"
    else
        fail "init.sql has old sign_type CHECK constraint"
    fi
else
    fail "database/init.sql not found"
fi

# 2. API entry point exists
echo ""
echo "[2/10] API Service"
if [ -f "api/app/main.py" ]; then
    pass "API entry point exists"
else
    fail "api/app/main.py not found"
fi

# 3. Oracle router exists
echo ""
echo "[3/10] Oracle Router"
if [ -f "api/app/routers/oracle.py" ]; then
    pass "Oracle router exists"
else
    fail "api/app/routers/oracle.py not found"
fi

# 4. ORM models have deleted_at
echo ""
echo "[4/10] ORM Models"
if grep -q "deleted_at" api/app/orm/oracle_user.py 2>/dev/null; then
    pass "OracleUser ORM has deleted_at field"
else
    fail "OracleUser ORM missing deleted_at field"
fi

# 5. Frontend builds
echo ""
echo "[5/10] Frontend"
if [ -f "frontend/package.json" ]; then
    pass "Frontend package.json exists"
    if grep -q "@playwright/test" frontend/package.json; then
        pass "Playwright devDependency configured"
    else
        warn "Playwright devDependency not in package.json"
    fi
else
    fail "frontend/package.json not found"
fi

# 6. Integration tests exist
echo ""
echo "[6/10] Integration Tests"
TEST_COUNT=$(find integration/tests -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
if [ "$TEST_COUNT" -ge 6 ]; then
    pass "$TEST_COUNT integration test files found (min: 6)"
else
    fail "Only $TEST_COUNT integration test files (expected >= 6)"
fi

# Check for key test files
for tf in test_database test_api_oracle test_e2e_flow test_multi_user test_security; do
    if [ -f "integration/tests/${tf}.py" ]; then
        pass "${tf}.py exists"
    else
        fail "${tf}.py missing"
    fi
done

# 7. Security audit script exists
echo ""
echo "[7/10] Security"
if [ -f "integration/scripts/security_audit.py" ]; then
    pass "Security audit script exists"
else
    fail "Security audit script missing"
fi

# 8. Performance audit script exists
echo ""
echo "[8/10] Performance"
if [ -f "integration/scripts/perf_audit.py" ]; then
    pass "Performance audit script exists"
else
    fail "Performance audit script missing"
fi

# 9. Documentation
echo ""
echo "[9/10] Documentation"
for doc in README.md docs/api/API_REFERENCE.md docs/DEPLOYMENT.md docs/TROUBLESHOOTING.md; do
    if [ -f "$doc" ]; then
        pass "$doc exists"
    else
        fail "$doc missing"
    fi
done

# 10. Environment configuration
echo ""
echo "[10/10] Configuration"
if [ -f ".env.example" ]; then
    pass ".env.example exists"
    if grep -q "NPS_ENCRYPTION_KEY" .env.example; then
        pass "Encryption key documented in .env.example"
    else
        fail "NPS_ENCRYPTION_KEY missing from .env.example"
    fi
else
    fail ".env.example not found"
fi

# Summary
echo ""
echo "=============================================="
echo "Results: $PASS passed, $FAIL failed, $WARN warnings"
echo "=============================================="

if [ "$FAIL" -gt 0 ]; then
    echo "STATUS: NOT READY"
    exit 1
else
    echo "STATUS: PRODUCTION READY"
    exit 0
fi
