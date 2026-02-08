# SPEC: DevOps Oracle Monitoring - T7-S1

**Estimated Duration:** 2-3 hours  
**Layer:** Layer 7 (DevOps/Monitoring)  
**Terminal:** Terminal 7  
**Session:** T7-S1 (DevOps Setup for Oracle)  
**Phase:** Phase 6 (DevOps/Monitoring)

---

## TL;DR
- Creating comprehensive monitoring infrastructure for Oracle service
- Structured JSON logging with rotation (10MB max, 5 backups)
- Health check endpoint (<2s response time)
- Monitoring metrics: readings/hour, response time, error rate
- Dashboard integration with real-time updates
- Telegram alerts for service down, high errors, slow responses
- Deliverables: 8 files with full test coverage

---

## OBJECTIVE

Implement production-grade monitoring, logging, and alerting infrastructure for the Oracle service to ensure system reliability, early error detection, and operational visibility.

**Success Metric:** Oracle service monitored with <5s health check response, <5% error rate, and instant Telegram alerts on failures.

---

## CONTEXT

### Current State
- Oracle service exists (Python, Layer 3B)
- Basic functionality implemented (FC60, numerology, pattern analysis)
- No structured logging
- No health monitoring
- No alerting system
- Dashboard exists but doesn't include Oracle

### What's Changing
Adding complete DevOps infrastructure for Oracle:
1. **Structured Logging** - JSON format logs for debugging and analysis
2. **Health Checks** - Oracle service health endpoint with dependency checks
3. **Monitoring Metrics** - Track performance, errors, and usage
4. **Dashboard** - Add Oracle to existing monitoring dashboard
5. **Alerts** - Telegram notifications for critical events

### Why
- **Reliability:** Early detection of failures prevents extended downtime
- **Performance:** Track Oracle response times to ensure <10s reading generation
- **Debugging:** Structured logs enable fast root cause analysis
- **Visibility:** Dashboard shows Oracle health at a glance
- **Proactive:** Alerts enable immediate response to issues

---

## PREREQUISITES

### Layer Dependencies
- [x] Layer 3B (Oracle Service) - Service must exist and be running
- [x] Layer 4 (Database) - PostgreSQL must be accessible
- [x] Layer 2 (API) - AI API integration for Oracle readings
- [ ] Layer 7 (DevOps) - Basic devops structure (will create in this spec)

### Environment Setup
```bash
# Verify Oracle service exists
ls -la backend/oracle-service/app/

# Verify Python environment
python --version  # 3.11+

# Verify PostgreSQL running
psql -h localhost -U nps_user -d nps_db -c "SELECT 1;"

# Verify dependencies installed
pip list | grep -E "flask|requests|psycopg2"
```

**Expected:**
- Oracle service directory exists
- Python 3.11+ installed
- PostgreSQL responding
- Flask, requests, psycopg2 installed

---

## TOOLS TO USE

### Extended Thinking
- Design health check logic (what dependencies to monitor)
- Design metric collection strategy (what to track, how often)
- Design alert thresholds (when to alert, severity levels)
- Trade-off analysis: Real-time vs batch metric collection

### Subagents
**Subagent 1:** Logging Infrastructure
- Task: Create `devops/logging/oracle_logger.py`
- Output: Rotating JSON logger for Oracle service

**Subagent 2:** Health Check System
- Task: Create `devops/monitoring/oracle_health.py`
- Output: Health checker with dependency verification

**Subagent 3:** Metrics Collector
- Task: Create `devops/monitoring/oracle_metrics.py`
- Output: Metrics collection and storage

**Subagent 4:** Dashboard Integration
- Task: Update `devops/dashboards/simple_dashboard.py`
- Output: Oracle stats in dashboard

**Subagent 5:** Telegram Alerts
- Task: Create `devops/alerts/oracle_alerts.py`
- Output: Alert rules for Oracle events

**Subagent 6:** Tests
- Task: Create `devops/tests/test_oracle_monitoring.py`
- Output: Comprehensive test suite

### MCP Servers
- None required (local file operations only)

### Skills
- Not applicable (infrastructure code, no document creation)

---

## REQUIREMENTS

### Functional Requirements

#### FR1: Structured Logging
1. All Oracle operations logged in JSON format
2. Log rotation: 10MB max file size, 5 backup files
3. Log levels: DEBUG, INFO, WARN, ERROR, CRITICAL
4. Fields: timestamp (ISO 8601), service_name, user_id, action, duration_ms, error (if any)
5. Centralized: All logs → `/app/logs/oracle.log`
6. No sensitive data: Private keys, API keys excluded from logs

#### FR2: Health Check Endpoint
1. Endpoint: `GET /health` on Oracle service
2. Response time: <2 seconds
3. Checks: Database connectivity, AI API reachability
4. Response format:
```json
{
  "status": "healthy" | "degraded" | "down",
  "timestamp": "2026-02-08T14:30:00Z",
  "checks": {
    "database": {"status": "ok", "latency_ms": 15},
    "ai_api": {"status": "ok", "latency_ms": 200}
  },
  "version": "4.0.0"
}
```

#### FR3: Monitoring Metrics
Track the following metrics:
1. **Performance Metrics:**
   - Reading generation time (p50, p95, p99)
   - Pattern analysis time (avg, max)
   - AI API call duration (avg, max)
   - Database query time (avg, max)

2. **Usage Metrics:**
   - Readings per hour
   - Pattern analyses per hour
   - Range suggestions generated

3. **Error Metrics:**
   - Error rate (errors per hour)
   - Error types (database, AI API, validation)
   - Failed reading attempts

#### FR4: Dashboard Integration
1. Add Oracle section to existing dashboard (`/devops/dashboards/simple_dashboard.py`)
2. Display metrics:
   - Service status (green dot = healthy, red = down)
   - Readings/hour (real-time)
   - Avg response time (last hour)
   - Error rate % (last hour)
3. Real-time updates (refresh every 5 seconds)
4. Historical graphs (last 24 hours)

#### FR5: Telegram Alerts
Alert conditions:
1. **CRITICAL:** Oracle service down
   - Trigger: Health check fails (status = "down")
   - Message: "🚨 CRITICAL: Oracle service is DOWN! Error: {error_message}"

2. **WARNING:** High error rate
   - Trigger: >5% error rate in 5-minute window
   - Message: "⚠️ WARNING: Oracle error rate {rate}% (threshold: 5%)"

3. **WARNING:** Slow responses
   - Trigger: Reading generation >10 seconds
   - Message: "⚠️ WARNING: Oracle slow response: {duration}s (threshold: 10s)"

4. **INFO:** Service recovered
   - Trigger: Service returns to healthy after being down
   - Message: "ℹ️ INFO: Oracle service recovered"

### Non-Functional Requirements

#### NFR1: Performance
- Health check: <2s response time
- Metric collection: <100ms overhead per operation
- Log writing: <10ms per log entry
- Dashboard: <1s page load time

#### NFR2: Reliability
- Logging never blocks Oracle operations
- Health checks don't affect Oracle performance
- Alerts delivered within 30 seconds of trigger

#### NFR3: Quality
- Test coverage: 95%+ for all monitoring code
- No false positive alerts (verified with tests)
- Logs parseable by standard tools (jq, grep)

---

## IMPLEMENTATION PLAN

### Phase 1: Logging Infrastructure (30 minutes)

#### Tasks

**1.1 Create Logging Module**

File: `devops/logging/oracle_logger.py`

```python
"""
Oracle Service Structured Logger

Provides JSON-formatted logging with rotation for Oracle service.
"""
import logging
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Dict, Any, Optional

class OracleJSONFormatter(logging.Formatter):
    """Custom JSON formatter for Oracle logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": "oracle",
            "message": record.getMessage(),
            "logger": record.name,
            "filename": record.filename,
            "line": record.lineno,
        }
        
        # Add custom fields from record
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'action'):
            log_data["action"] = record.action
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, 'error_type'):
            log_data["error_type"] = record.error_type
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_oracle_logger(
    log_file: str = "/app/logs/oracle.log",
    level: str = "INFO"
) -> logging.Logger:
    """
    Set up Oracle service logger with JSON formatting and rotation.
    
    Args:
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARN, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("oracle")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Rotating file handler: 10MB max, 5 backups
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10_000_000,  # 10 MB
        backupCount=5
    )
    handler.setFormatter(OracleJSONFormatter())
    
    logger.addHandler(handler)
    
    return logger


# Convenience function for logging with context
def log_operation(
    logger: logging.Logger,
    level: str,
    message: str,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    duration_ms: Optional[int] = None,
    error_type: Optional[str] = None
) -> None:
    """
    Log Oracle operation with structured context.
    
    Args:
        logger: Logger instance
        level: Log level (info, warning, error, etc.)
        message: Log message
        user_id: User ID (if applicable)
        action: Action being performed
        duration_ms: Operation duration in milliseconds
        error_type: Error type (if error)
    """
    extra = {}
    if user_id:
        extra['user_id'] = user_id
    if action:
        extra['action'] = action
    if duration_ms is not None:
        extra['duration_ms'] = duration_ms
    if error_type:
        extra['error_type'] = error_type
    
    log_method = getattr(logger, level.lower())
    log_method(message, extra=extra)
```

**1.2 Create Logging Configuration**

File: `devops/logging/config.py`

```python
"""
Centralized logging configuration for all NPS V4 services.
"""
import os
from typing import Dict

# Log directory
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")

# Logging configurations per service
LOG_CONFIGS: Dict[str, Dict] = {
    "oracle": {
        "file": f"{LOG_DIR}/oracle.log",
        "level": os.getenv("ORACLE_LOG_LEVEL", "INFO"),
        "max_bytes": 10_000_000,  # 10 MB
        "backup_count": 5
    },
    "scanner": {
        "file": f"{LOG_DIR}/scanner.log",
        "level": os.getenv("SCANNER_LOG_LEVEL", "INFO"),
        "max_bytes": 10_000_000,
        "backup_count": 5
    },
    "api": {
        "file": f"{LOG_DIR}/api.log",
        "level": os.getenv("API_LOG_LEVEL", "INFO"),
        "max_bytes": 10_000_000,
        "backup_count": 5
    }
}

def ensure_log_directory() -> None:
    """Ensure log directory exists."""
    os.makedirs(LOG_DIR, exist_ok=True)
```

**1.3 Integrate Logging into Oracle Service**

File: `backend/oracle-service/app/services/oracle_service.py` (modifications)

Add at top:
```python
import time
from devops.logging.oracle_logger import setup_oracle_logger, log_operation

# Initialize logger
logger = setup_oracle_logger()
```

Wrap existing methods with logging:
```python
async def generate_reading(self, user_id: str, query: str) -> dict:
    """Generate Oracle reading with logging."""
    start_time = time.time()
    
    try:
        log_operation(
            logger, "info",
            "Generating Oracle reading",
            user_id=user_id,
            action="generate_reading"
        )
        
        # Existing reading generation logic
        result = await self._generate_reading_impl(query)
        
        duration_ms = int((time.time() - start_time) * 1000)
        log_operation(
            logger, "info",
            "Reading generated successfully",
            user_id=user_id,
            action="generate_reading",
            duration_ms=duration_ms
        )
        
        return result
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_operation(
            logger, "error",
            f"Reading generation failed: {str(e)}",
            user_id=user_id,
            action="generate_reading",
            duration_ms=duration_ms,
            error_type=type(e).__name__
        )
        raise
```

#### Acceptance Criteria

**Phase 1 Checklist:**
- [ ] `oracle_logger.py` created with JSON formatter
- [ ] Rotating file handler configured (10MB, 5 backups)
- [ ] `config.py` created with centralized log configuration
- [ ] Oracle service integrated with logger
- [ ] All Oracle operations logged (reading, analysis, suggestions)
- [ ] Log fields include: timestamp, level, service, message, user_id, action, duration_ms
- [ ] No sensitive data in logs (verified by inspection)

#### Verification

```bash
# Phase 1 Verification (2 minutes)

# Step 1: Check logging files created
ls -la devops/logging/
# Expected: oracle_logger.py, config.py exist

# Step 2: Test logger import
cd devops
python -c "from logging.oracle_logger import setup_oracle_logger; logger = setup_oracle_logger('/tmp/test.log'); logger.info('Test'); print('✅ Logger works')"
# Expected: ✅ Logger works

# Step 3: Verify log format
cat /tmp/test.log | jq .
# Expected: Valid JSON with timestamp, level, service, message fields

# Step 4: Trigger Oracle operation and check log
curl -X POST http://localhost:8000/api/oracle/reading -H "Authorization: Bearer {key}" -d '{"query": "test"}'
tail -1 /app/logs/oracle.log | jq .
# Expected: JSON log entry with action="generate_reading", duration_ms field

# Step 5: Verify no sensitive data
grep -i "private.*key\|api.*key" /app/logs/oracle.log
# Expected: No matches (empty output)
```

**STOP if Phase 1 verification fails. Fix before Phase 2.**

---

### Phase 2: Health Check System (30 minutes)

#### Tasks

**2.1 Create Health Checker**

File: `devops/monitoring/oracle_health.py`

```python
"""
Oracle Service Health Checker

Checks Oracle service health including dependencies.
"""
import time
import asyncio
from typing import Dict, Any
from datetime import datetime
import psycopg2
import requests

class OracleHealthChecker:
    """Health checker for Oracle service."""
    
    def __init__(
        self,
        database_url: str,
        ai_api_url: str = "https://api.anthropic.com/v1/messages",
        ai_api_key: str = None
    ):
        self.database_url = database_url
        self.ai_api_url = ai_api_url
        self.ai_api_key = ai_api_key
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Health status dict with overall status and dependency checks
        """
        checks = {}
        overall_status = "healthy"
        
        # Check database
        db_check = await self._check_database()
        checks["database"] = db_check
        if db_check["status"] != "ok":
            overall_status = "degraded"
        
        # Check AI API
        ai_check = await self._check_ai_api()
        checks["ai_api"] = ai_check
        if ai_check["status"] != "ok":
            overall_status = "degraded"
        
        # If both critical dependencies down, service is down
        if db_check["status"] != "ok" and ai_check["status"] != "ok":
            overall_status = "down"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": checks,
            "version": "4.0.0"
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check PostgreSQL connectivity."""
        start = time.time()
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            
            latency_ms = int((time.time() - start) * 1000)
            return {
                "status": "ok",
                "latency_ms": latency_ms
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_ai_api(self) -> Dict[str, Any]:
        """Check AI API reachability."""
        if not self.ai_api_key:
            return {
                "status": "skipped",
                "reason": "No API key configured"
            }
        
        start = time.time()
        try:
            # Simple ping to AI API (minimal request)
            response = requests.post(
                self.ai_api_url,
                headers={
                    "x-api-key": self.ai_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "ping"}]
                },
                timeout=5
            )
            
            latency_ms = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                return {
                    "status": "ok",
                    "latency_ms": latency_ms
                }
            else:
                return {
                    "status": "error",
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Flask endpoint for health check
async def health_endpoint() -> Dict[str, Any]:
    """
    Health check endpoint for Oracle service.
    
    Usage in Flask:
        from devops.monitoring.oracle_health import health_endpoint
        
        @app.route("/health")
        async def health():
            return await health_endpoint()
    """
    import os
    
    checker = OracleHealthChecker(
        database_url=os.getenv("DATABASE_URL"),
        ai_api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    return await checker.check_health()
```

**2.2 Add Health Endpoint to Oracle Service**

File: `backend/oracle-service/app/main.py` (modifications)

```python
from flask import Flask, jsonify
from devops.monitoring.oracle_health import health_endpoint
import asyncio

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    # Run async health check
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(health_endpoint())
    loop.close()
    
    # Set HTTP status based on health status
    status_code = 200
    if result["status"] == "degraded":
        status_code = 503  # Service Unavailable
    elif result["status"] == "down":
        status_code = 503
    
    return jsonify(result), status_code
```

#### Acceptance Criteria

**Phase 2 Checklist:**
- [ ] `oracle_health.py` created with health checker
- [ ] Database connectivity check implemented
- [ ] AI API reachability check implemented
- [ ] Health endpoint added to Oracle service (`/health`)
- [ ] Response time <2 seconds (verified)
- [ ] Status codes correct (200 healthy, 503 degraded/down)
- [ ] Response format matches specification

#### Verification

```bash
# Phase 2 Verification (2 minutes)

# Step 1: Check health checker created
ls -la devops/monitoring/oracle_health.py
# Expected: File exists

# Step 2: Test health endpoint
curl http://localhost:50052/health
# Expected: JSON response with status, timestamp, checks

# Step 3: Verify response time
time curl http://localhost:50052/health
# Expected: <2 seconds total time

# Step 4: Verify all checks present
curl http://localhost:50052/health | jq '.checks | keys'
# Expected: ["ai_api", "database"]

# Step 5: Test degraded state (stop database)
docker-compose stop postgres
curl http://localhost:50052/health
# Expected: {"status": "degraded", "checks": {"database": {"status": "error"}}}
docker-compose start postgres  # Restore

# Step 6: Verify HTTP status codes
curl -w "%{http_code}" http://localhost:50052/health
# Expected: 200 (healthy) or 503 (degraded/down)
```

**STOP if Phase 2 verification fails. Fix before Phase 3.**

---

### Phase 3: Metrics Collection (40 minutes)

#### Tasks

**3.1 Create Metrics Collector**

File: `devops/monitoring/oracle_metrics.py`

```python
"""
Oracle Service Metrics Collector

Collects and stores performance and usage metrics.
"""
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
import statistics

class OracleMetrics:
    """Metrics collector for Oracle service."""
    
    def __init__(self, window_minutes: int = 60):
        """
        Initialize metrics collector.
        
        Args:
            window_minutes: Time window for metric aggregation
        """
        self.window_minutes = window_minutes
        self.window_seconds = window_minutes * 60
        
        # Time-series data (timestamp, value)
        self._reading_times: deque = deque()  # Reading generation times
        self._analysis_times: deque = deque()  # Pattern analysis times
        self._ai_call_times: deque = deque()   # AI API call times
        self._db_query_times: deque = deque()  # Database query times
        self._errors: deque = deque()          # Error events
        
        # Counters
        self._readings_count = 0
        self._analyses_count = 0
        self._suggestions_count = 0
    
    def record_reading_time(self, duration_ms: int) -> None:
        """Record reading generation time."""
        now = time.time()
        self._reading_times.append((now, duration_ms))
        self._readings_count += 1
        self._cleanup_old_data()
    
    def record_analysis_time(self, duration_ms: int) -> None:
        """Record pattern analysis time."""
        now = time.time()
        self._analysis_times.append((now, duration_ms))
        self._analyses_count += 1
        self._cleanup_old_data()
    
    def record_ai_call_time(self, duration_ms: int) -> None:
        """Record AI API call time."""
        now = time.time()
        self._ai_call_times.append((now, duration_ms))
        self._cleanup_old_data()
    
    def record_db_query_time(self, duration_ms: int) -> None:
        """Record database query time."""
        now = time.time()
        self._db_query_times.append((now, duration_ms))
        self._cleanup_old_data()
    
    def record_error(self, error_type: str) -> None:
        """Record error event."""
        now = time.time()
        self._errors.append((now, error_type))
        self._cleanup_old_data()
    
    def record_suggestion(self) -> None:
        """Record range suggestion generated."""
        self._suggestions_count += 1
    
    def get_metrics(self) -> Dict[str, any]:
        """
        Get current metrics snapshot.
        
        Returns:
            Dictionary of all current metrics
        """
        self._cleanup_old_data()
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "window_minutes": self.window_minutes,
            "performance": {
                "reading_time": self._calculate_percentiles(self._reading_times),
                "analysis_time": self._calculate_percentiles(self._analysis_times),
                "ai_call_time": self._calculate_percentiles(self._ai_call_times),
                "db_query_time": self._calculate_percentiles(self._db_query_times)
            },
            "usage": {
                "readings_per_hour": self._calculate_rate(self._readings_count),
                "analyses_per_hour": self._calculate_rate(self._analyses_count),
                "suggestions_total": self._suggestions_count
            },
            "errors": {
                "rate_percent": self._calculate_error_rate(),
                "count_last_hour": len(self._errors),
                "by_type": self._count_error_types()
            }
        }
    
    def _cleanup_old_data(self) -> None:
        """Remove data points outside time window."""
        cutoff = time.time() - self.window_seconds
        
        self._reading_times = deque(
            (t, v) for t, v in self._reading_times if t > cutoff
        )
        self._analysis_times = deque(
            (t, v) for t, v in self._analysis_times if t > cutoff
        )
        self._ai_call_times = deque(
            (t, v) for t, v in self._ai_call_times if t > cutoff
        )
        self._db_query_times = deque(
            (t, v) for t, v in self._db_query_times if t > cutoff
        )
        self._errors = deque(
            (t, v) for t, v in self._errors if t > cutoff
        )
    
    def _calculate_percentiles(
        self,
        data: deque
    ) -> Dict[str, Optional[float]]:
        """Calculate p50, p95, p99 percentiles."""
        if not data:
            return {"p50": None, "p95": None, "p99": None, "avg": None, "max": None}
        
        values = [v for _, v in data]
        values.sort()
        
        return {
            "p50": statistics.median(values),
            "p95": self._percentile(values, 0.95),
            "p99": self._percentile(values, 0.99),
            "avg": statistics.mean(values),
            "max": max(values)
        }
    
    @staticmethod
    def _percentile(values: List[float], p: float) -> float:
        """Calculate percentile."""
        k = (len(values) - 1) * p
        f = int(k)
        c = f + 1
        if c >= len(values):
            return values[-1]
        return values[f] + (k - f) * (values[c] - values[f])
    
    def _calculate_rate(self, count: int) -> float:
        """Calculate rate per hour."""
        # Convert count in window to per-hour rate
        return (count / self.window_minutes) * 60
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate as percentage."""
        total_operations = (
            len(self._reading_times) +
            len(self._analysis_times)
        )
        
        if total_operations == 0:
            return 0.0
        
        error_count = len(self._errors)
        return (error_count / total_operations) * 100
    
    def _count_error_types(self) -> Dict[str, int]:
        """Count errors by type."""
        error_types = {}
        for _, error_type in self._errors:
            error_types[error_type] = error_types.get(error_type, 0) + 1
        return error_types


# Global metrics instance
metrics = OracleMetrics(window_minutes=60)


def track_operation(operation_type: str):
    """
    Decorator to track operation metrics.
    
    Usage:
        @track_operation("reading")
        async def generate_reading(...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((time.time() - start) * 1000)
                
                if operation_type == "reading":
                    metrics.record_reading_time(duration_ms)
                elif operation_type == "analysis":
                    metrics.record_analysis_time(duration_ms)
                
                return result
            except Exception as e:
                duration_ms = int((time.time() - start) * 1000)
                metrics.record_error(type(e).__name__)
                raise
        
        return wrapper
    return decorator
```

**3.2 Integrate Metrics into Oracle Service**

File: `backend/oracle-service/app/services/oracle_service.py` (modifications)

```python
from devops.monitoring.oracle_metrics import metrics, track_operation

# Wrap methods with metric tracking
@track_operation("reading")
async def generate_reading(self, user_id: str, query: str) -> dict:
    # Existing implementation
    pass

@track_operation("analysis")
async def analyze_patterns(self, findings: list) -> dict:
    # Existing implementation
    pass
```

**3.3 Create Metrics Endpoint**

File: `backend/oracle-service/app/main.py` (modifications)

```python
from devops.monitoring.oracle_metrics import metrics

@app.route("/metrics", methods=["GET"])
def get_metrics():
    """Metrics endpoint."""
    return jsonify(metrics.get_metrics())
```

#### Acceptance Criteria

**Phase 3 Checklist:**
- [ ] `oracle_metrics.py` created with metrics collector
- [ ] Performance metrics tracked (reading time, analysis time, AI calls, DB queries)
- [ ] Usage metrics tracked (readings/hour, analyses/hour, suggestions)
- [ ] Error metrics tracked (rate %, count, by type)
- [ ] Metrics integrated into Oracle service
- [ ] Metrics endpoint accessible (`/metrics`)
- [ ] Time window working (60 minutes rolling window)
- [ ] Percentiles calculated correctly (p50, p95, p99)

#### Verification

```bash
# Phase 3 Verification (2 minutes)

# Step 1: Check metrics collector created
ls -la devops/monitoring/oracle_metrics.py
# Expected: File exists

# Step 2: Test metrics endpoint
curl http://localhost:50052/metrics
# Expected: JSON with performance, usage, errors sections

# Step 3: Trigger operations and verify metrics update
curl -X POST http://localhost:8000/api/oracle/reading -d '{"query": "test"}'
sleep 2
curl http://localhost:50052/metrics | jq '.usage.readings_per_hour'
# Expected: Non-zero value

# Step 4: Verify percentiles present
curl http://localhost:50052/metrics | jq '.performance.reading_time'
# Expected: Object with p50, p95, p99, avg, max fields

# Step 5: Verify error tracking
# Trigger error (invalid request)
curl -X POST http://localhost:8000/api/oracle/reading
curl http://localhost:50052/metrics | jq '.errors'
# Expected: Error count increased

# Step 6: Verify time window
# Wait 5 seconds, check that old data expires
sleep 5
curl http://localhost:50052/metrics | jq '.window_minutes'
# Expected: 60
```

**STOP if Phase 3 verification fails. Fix before Phase 4.**

---

### Phase 4: Dashboard Integration (30 minutes)

#### Tasks

**4.1 Update Dashboard**

File: `devops/dashboards/simple_dashboard.py` (modifications)

Add Oracle service to dashboard:

```python
from devops.monitoring.oracle_health import OracleHealthChecker
from devops.monitoring.oracle_metrics import metrics as oracle_metrics
import os

# Initialize Oracle health checker
oracle_health = OracleHealthChecker(
    database_url=os.getenv("DATABASE_URL"),
    ai_api_key=os.getenv("ANTHROPIC_API_KEY")
)

@app.route("/api/status")
async def status():
    """Get system status including Oracle."""
    # Existing services
    health = health_checker.check_all()
    db_stats = db_monitor.get_stats()
    findings_stats = db_monitor.get_findings_stats()
    
    # Add Oracle health and metrics
    oracle_health_status = await oracle_health.check_health()
    oracle_metrics_data = oracle_metrics.get_metrics()
    
    return jsonify({
        "health": health,
        "database": db_stats,
        "findings": findings_stats,
        "oracle": {
            "health": oracle_health_status,
            "metrics": oracle_metrics_data
        }
    })
```

**4.2 Update Dashboard HTML**

File: `devops/dashboards/templates/dashboard.html` (modifications)

Add Oracle section:

```html
<!-- Oracle Service Section -->
<div class="service-card">
  <h2>Oracle Service</h2>
  
  <div class="health-indicator">
    <span class="status-dot" id="oracle-status"></span>
    <span id="oracle-status-text">Checking...</span>
  </div>
  
  <div class="metrics">
    <div class="metric">
      <span class="label">Readings/Hour</span>
      <span class="value" id="oracle-readings">0</span>
    </div>
    
    <div class="metric">
      <span class="label">Avg Response Time</span>
      <span class="value" id="oracle-response-time">0ms</span>
    </div>
    
    <div class="metric">
      <span class="label">Error Rate</span>
      <span class="value" id="oracle-error-rate">0%</span>
    </div>
  </div>
  
  <div class="chart" id="oracle-response-chart"></div>
</div>

<script>
// Update Oracle metrics every 5 seconds
setInterval(async () => {
  const response = await fetch('/api/status');
  const data = await response.json();
  
  // Update health status
  const status = data.oracle.health.status;
  const statusDot = document.getElementById('oracle-status');
  const statusText = document.getElementById('oracle-status-text');
  
  statusDot.className = 'status-dot ' + status;
  statusText.textContent = status.charAt(0).toUpperCase() + status.slice(1);
  
  // Update metrics
  const metrics = data.oracle.metrics;
  document.getElementById('oracle-readings').textContent = 
    Math.round(metrics.usage.readings_per_hour);
  
  document.getElementById('oracle-response-time').textContent = 
    Math.round(metrics.performance.reading_time.avg || 0) + 'ms';
  
  document.getElementById('oracle-error-rate').textContent = 
    metrics.errors.rate_percent.toFixed(1) + '%';
  
  // Update chart (simplified - use Chart.js in production)
  updateOracleChart(metrics.performance.reading_time);
}, 5000);

function updateOracleChart(readingTime) {
  // Simplified chart update
  // In production, use Chart.js or similar library
  const chart = document.getElementById('oracle-response-chart');
  chart.innerHTML = `
    <div class="bar-chart">
      <div class="bar" style="height: ${(readingTime.p50 || 0) / 100}%">
        <span>p50: ${Math.round(readingTime.p50 || 0)}ms</span>
      </div>
      <div class="bar" style="height: ${(readingTime.p95 || 0) / 100}%">
        <span>p95: ${Math.round(readingTime.p95 || 0)}ms</span>
      </div>
      <div class="bar" style="height: ${(readingTime.p99 || 0) / 100}%">
        <span>p99: ${Math.round(readingTime.p99 || 0)}ms</span>
      </div>
    </div>
  `;
}
</script>
```

**4.3 Add CSS Styling**

File: `devops/dashboards/static/style.css` (modifications)

```css
/* Oracle Service Card */
.service-card {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
}

.health-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 10px 0;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.healthy {
  background: #00ff00;
  box-shadow: 0 0 10px #00ff00;
}

.status-dot.degraded {
  background: #ffaa00;
  box-shadow: 0 0 10px #ffaa00;
}

.status-dot.down {
  background: #ff0000;
  box-shadow: 0 0 10px #ff0000;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin: 20px 0;
}

.metric {
  text-align: center;
}

.metric .label {
  display: block;
  color: #888;
  font-size: 12px;
  margin-bottom: 5px;
}

.metric .value {
  display: block;
  color: #fff;
  font-size: 24px;
  font-weight: bold;
}

.chart {
  margin-top: 20px;
  min-height: 150px;
}

.bar-chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 150px;
}

.bar {
  flex: 1;
  background: linear-gradient(to top, #00aaff, #0066cc);
  margin: 0 5px;
  position: relative;
  min-height: 20px;
}

.bar span {
  position: absolute;
  bottom: -25px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 11px;
  color: #888;
}
```

#### Acceptance Criteria

**Phase 4 Checklist:**
- [ ] Dashboard updated to include Oracle service
- [ ] Oracle health status displayed (green/yellow/red dot)
- [ ] Metrics displayed: readings/hour, avg response time, error rate
- [ ] Dashboard updates every 5 seconds (real-time)
- [ ] Response time chart displays p50, p95, p99
- [ ] Responsive design (works on mobile + desktop)
- [ ] Dark theme consistent with existing dashboard

#### Verification

```bash
# Phase 4 Verification (2 minutes)

# Step 1: Check dashboard files updated
ls -la devops/dashboards/
# Expected: simple_dashboard.py, templates/dashboard.html, static/style.css

# Step 2: Start dashboard
cd devops/dashboards
python simple_dashboard.py &
# Expected: Dashboard running on port 9000

# Step 3: Access dashboard
curl http://localhost:9000
# Expected: HTML response with Oracle section

# Step 4: Check API endpoint includes Oracle
curl http://localhost:9000/api/status | jq '.oracle'
# Expected: Object with health and metrics

# Step 5: Visual verification
# Open http://localhost:9000 in browser
# Expected: Oracle service card visible with:
#   - Health status (green/yellow/red dot)
#   - Readings/hour metric
#   - Avg response time metric
#   - Error rate metric
#   - Response time chart (p50, p95, p99)

# Step 6: Verify real-time updates
# Wait 10 seconds, observe metrics update
# Expected: Values change as new data arrives

# Step 7: Mobile responsive check
# Resize browser window to mobile size (375px width)
# Expected: Layout adapts, all metrics visible
```

**STOP if Phase 4 verification fails. Fix before Phase 5.**

---

### Phase 5: Telegram Alerts (30 minutes)

#### Tasks

**5.1 Create Alert System**

File: `devops/alerts/oracle_alerts.py`

```python
"""
Oracle Service Telegram Alerts

Sends Telegram alerts for Oracle service events.
"""
import time
import asyncio
from typing import Dict, Any, Optional
import requests
from devops.monitoring.oracle_health import OracleHealthChecker
from devops.monitoring.oracle_metrics import metrics

class OracleAlerter:
    """Telegram alerter for Oracle service."""
    
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        check_interval_seconds: int = 30
    ):
        """
        Initialize alerter.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID to send alerts to
            check_interval_seconds: How often to check for alert conditions
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.check_interval = check_interval_seconds
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Track alert state to avoid duplicate alerts
        self._last_service_status = "healthy"
        self._last_alert_time: Dict[str, float] = {}
        
        # Alert cooldown (don't send same alert within 5 minutes)
        self.cooldown_seconds = 300
    
    def send_alert(
        self,
        severity: str,
        message: str,
        alert_key: str = None
    ) -> bool:
        """
        Send alert to Telegram.
        
        Args:
            severity: "critical", "warning", or "info"
            message: Alert message
            alert_key: Unique key for this alert (for cooldown tracking)
        
        Returns:
            True if alert sent, False if skipped (cooldown)
        """
        # Check cooldown
        if alert_key:
            last_sent = self._last_alert_time.get(alert_key, 0)
            if time.time() - last_sent < self.cooldown_seconds:
                return False  # Skip duplicate alert
        
        # Emoji mapping
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨"
        }
        
        # Format message
        formatted = f"{emoji.get(severity, '📢')} **{severity.upper()}** - Oracle Service\n\n{message}"
        
        try:
            response = requests.post(
                self.url,
                json={
                    "chat_id": self.chat_id,
                    "text": formatted,
                    "parse_mode": "Markdown"
                },
                timeout=5
            )
            
            if response.status_code == 200:
                if alert_key:
                    self._last_alert_time[alert_key] = time.time()
                return True
            else:
                print(f"Alert send failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Alert send error: {e}")
            return False
    
    async def check_and_alert(self) -> None:
        """
        Check Oracle service and send alerts if needed.
        
        This is the main monitoring loop.
        """
        import os
        
        health_checker = OracleHealthChecker(
            database_url=os.getenv("DATABASE_URL"),
            ai_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        # Check health
        health = await health_checker.check_health()
        current_status = health["status"]
        
        # Alert: Service down
        if current_status == "down" and self._last_service_status != "down":
            error_msg = "Multiple dependencies failed"
            if health["checks"]["database"]["status"] != "ok":
                error_msg = f"Database: {health['checks']['database'].get('error', 'Unknown error')}"
            elif health["checks"]["ai_api"]["status"] != "ok":
                error_msg = f"AI API: {health['checks']['ai_api'].get('error', 'Unknown error')}"
            
            self.send_alert(
                "critical",
                f"Oracle service is DOWN!\n\nError: {error_msg}",
                alert_key="service_down"
            )
        
        # Alert: Service recovered
        if current_status == "healthy" and self._last_service_status == "down":
            self.send_alert(
                "info",
                "Oracle service has recovered and is now healthy.",
                alert_key="service_recovered"
            )
        
        self._last_service_status = current_status
        
        # Check metrics
        metrics_data = metrics.get_metrics()
        
        # Alert: High error rate
        error_rate = metrics_data["errors"]["rate_percent"]
        if error_rate > 5.0:  # >5% error rate
            self.send_alert(
                "warning",
                f"High error rate detected: {error_rate:.1f}% (threshold: 5%)\n\n"
                f"Errors in last hour: {metrics_data['errors']['count_last_hour']}",
                alert_key="high_error_rate"
            )
        
        # Alert: Slow responses
        reading_time = metrics_data["performance"]["reading_time"]
        if reading_time["p95"] and reading_time["p95"] > 10000:  # >10 seconds
            self.send_alert(
                "warning",
                f"Slow Oracle responses detected!\n\n"
                f"p95 reading time: {reading_time['p95']/1000:.1f}s (threshold: 10s)\n"
                f"p99 reading time: {reading_time['p99']/1000:.1f}s",
                alert_key="slow_responses"
            )
    
    async def run_monitoring_loop(self) -> None:
        """
        Run continuous monitoring loop.
        
        Call this in a background task to enable continuous monitoring.
        """
        print(f"Oracle alerter started (checking every {self.check_interval}s)")
        
        while True:
            try:
                await self.check_and_alert()
            except Exception as e:
                print(f"Alert check error: {e}")
            
            await asyncio.sleep(self.check_interval)


# Standalone script for testing
if __name__ == "__main__":
    import os
    import sys
    
    if "--test" in sys.argv:
        # Test alert
        alerter = OracleAlerter(
            bot_token=os.getenv("NPS_BOT_TOKEN"),
            chat_id=os.getenv("NPS_CHAT_ID")
        )
        
        result = alerter.send_alert(
            "info",
            "This is a test alert from Oracle monitoring system."
        )
        
        if result:
            print("✅ Test alert sent successfully")
        else:
            print("❌ Test alert failed")
    else:
        # Run monitoring loop
        alerter = OracleAlerter(
            bot_token=os.getenv("NPS_BOT_TOKEN"),
            chat_id=os.getenv("NPS_CHAT_ID"),
            check_interval_seconds=30
        )
        
        asyncio.run(alerter.run_monitoring_loop())
```

**5.2 Add Alert Service to Infrastructure**

File: `infrastructure/docker-compose.yml` (modifications)

```yaml
services:
  # ... existing services ...
  
  oracle-alerter:
    build:
      context: ./devops/alerts
      dockerfile: Dockerfile
    container_name: nps-oracle-alerter
    environment:
      DATABASE_URL: postgresql://nps_user:${DB_PASSWORD}@postgres:5432/nps_db
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      NPS_BOT_TOKEN: ${NPS_BOT_TOKEN}
      NPS_CHAT_ID: ${NPS_CHAT_ID}
    depends_on:
      - postgres
      - oracle
    networks:
      - nps-network
    restart: unless-stopped
```

**5.3 Create Alerter Dockerfile**

File: `devops/alerts/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy alerter code
COPY oracle_alerts.py .
COPY ../monitoring/oracle_health.py ./monitoring/
COPY ../monitoring/oracle_metrics.py ./monitoring/

CMD ["python", "oracle_alerts.py"]
```

#### Acceptance Criteria

**Phase 5 Checklist:**
- [ ] `oracle_alerts.py` created with alert system
- [ ] Alert conditions implemented (service down, high error rate, slow responses)
- [ ] Cooldown mechanism prevents duplicate alerts (5 minutes)
- [ ] Service recovery alert implemented
- [ ] Docker service added for continuous monitoring
- [ ] Environment variables configured (bot token, chat ID)
- [ ] Test mode works (`--test` flag)

#### Verification

```bash
# Phase 5 Verification (2 minutes)

# Step 1: Check alert system created
ls -la devops/alerts/oracle_alerts.py
# Expected: File exists

# Step 2: Test alert sending
export NPS_BOT_TOKEN="your_bot_token"
export NPS_CHAT_ID="your_chat_id"
python devops/alerts/oracle_alerts.py --test
# Expected: ✅ Test alert sent successfully
# Check Telegram: Should receive "This is a test alert from Oracle monitoring system"

# Step 3: Test service down alert
# Stop Oracle service
docker-compose stop oracle
# Wait 35 seconds (check interval + processing)
sleep 35
# Check Telegram: Should receive "🚨 CRITICAL - Oracle service is DOWN!"

# Step 4: Test service recovery alert
docker-compose start oracle
sleep 35
# Check Telegram: Should receive "ℹ️ INFO - Oracle service has recovered"

# Step 5: Test high error rate alert
# Trigger multiple errors (invalid requests)
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/oracle/reading
done
sleep 35
# Check Telegram: Should receive "⚠️ WARNING - High error rate detected"

# Step 6: Verify cooldown works
# Trigger same condition again immediately
docker-compose stop oracle
sleep 35
# Check Telegram: Should NOT receive duplicate alert (within 5 minutes)

# Step 7: Start continuous monitoring
docker-compose up -d oracle-alerter
docker-compose logs -f oracle-alerter
# Expected: "Oracle alerter started (checking every 30s)"
```

**STOP if Phase 5 verification fails. Fix before Phase 6.**

---

### Phase 6: Testing & Documentation (20 minutes)

#### Tasks

**6.1 Create Comprehensive Tests**

File: `devops/tests/test_oracle_monitoring.py`

```python
"""
Tests for Oracle monitoring infrastructure.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from devops.logging.oracle_logger import setup_oracle_logger, OracleJSONFormatter
from devops.monitoring.oracle_health import OracleHealthChecker
from devops.monitoring.oracle_metrics import OracleMetrics, track_operation
from devops.alerts.oracle_alerts import OracleAlerter


class TestOracleLogger:
    """Test Oracle logging system."""
    
    def test_logger_setup(self, tmp_path):
        """Test logger initialization."""
        log_file = tmp_path / "test.log"
        logger = setup_oracle_logger(str(log_file), level="INFO")
        
        assert logger.name == "oracle"
        assert logger.level == 20  # INFO level
        assert len(logger.handlers) == 1
        assert logger.handlers[0].maxBytes == 10_000_000
        assert logger.handlers[0].backupCount == 5
    
    def test_json_format(self, tmp_path):
        """Test JSON log format."""
        import json
        
        log_file = tmp_path / "test.log"
        logger = setup_oracle_logger(str(log_file))
        
        logger.info("Test message", extra={"user_id": "user123", "action": "test"})
        
        with open(log_file) as f:
            log_entry = json.loads(f.read())
        
        assert log_entry["service"] == "oracle"
        assert log_entry["message"] == "Test message"
        assert log_entry["user_id"] == "user123"
        assert log_entry["action"] == "test"
        assert "timestamp" in log_entry


class TestOracleHealth:
    """Test Oracle health check system."""
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self):
        """Test health check when all dependencies healthy."""
        checker = OracleHealthChecker(
            database_url="postgresql://user:pass@localhost/db",
            ai_api_key="test_key"
        )
        
        with patch.object(checker, '_check_database', return_value={"status": "ok", "latency_ms": 10}):
            with patch.object(checker, '_check_ai_api', return_value={"status": "ok", "latency_ms": 200}):
                result = await checker.check_health()
        
        assert result["status"] == "healthy"
        assert result["checks"]["database"]["status"] == "ok"
        assert result["checks"]["ai_api"]["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self):
        """Test health check when one dependency fails."""
        checker = OracleHealthChecker(
            database_url="postgresql://user:pass@localhost/db"
        )
        
        with patch.object(checker, '_check_database', return_value={"status": "error", "error": "Connection refused"}):
            with patch.object(checker, '_check_ai_api', return_value={"status": "ok", "latency_ms": 200}):
                result = await checker.check_health()
        
        assert result["status"] == "degraded"
    
    @pytest.mark.asyncio
    async def test_health_check_down(self):
        """Test health check when all dependencies fail."""
        checker = OracleHealthChecker(
            database_url="postgresql://user:pass@localhost/db"
        )
        
        with patch.object(checker, '_check_database', return_value={"status": "error"}):
            with patch.object(checker, '_check_ai_api', return_value={"status": "error"}):
                result = await checker.check_health()
        
        assert result["status"] == "down"


class TestOracleMetrics:
    """Test Oracle metrics collection."""
    
    def test_record_reading_time(self):
        """Test recording reading time."""
        metrics = OracleMetrics(window_minutes=1)
        
        metrics.record_reading_time(500)
        metrics.record_reading_time(600)
        metrics.record_reading_time(700)
        
        result = metrics.get_metrics()
        
        assert result["performance"]["reading_time"]["avg"] == 600
        assert result["performance"]["reading_time"]["p50"] == 600
        assert result["usage"]["readings_per_hour"] > 0
    
    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        metrics = OracleMetrics(window_minutes=1)
        
        # Record operations
        metrics.record_reading_time(500)
        metrics.record_reading_time(500)
        metrics.record_reading_time(500)
        
        # Record errors
        metrics.record_error("ValueError")
        
        result = metrics.get_metrics()
        
        # 1 error out of 3 operations = 33.33%
        assert 30 < result["errors"]["rate_percent"] < 35
        assert result["errors"]["by_type"]["ValueError"] == 1
    
    def test_time_window_cleanup(self):
        """Test that old data is cleaned up."""
        metrics = OracleMetrics(window_minutes=1)  # 60 seconds window
        
        # Record old data (simulate)
        old_time = time.time() - 120  # 2 minutes ago
        metrics._reading_times.append((old_time, 500))
        
        # Record new data
        metrics.record_reading_time(600)
        
        # Cleanup should remove old data
        result = metrics.get_metrics()
        
        # Should only have 1 reading (new one)
        assert result["performance"]["reading_time"]["avg"] == 600


class TestOracleAlerter:
    """Test Oracle alerting system."""
    
    @patch('requests.post')
    def test_send_alert_success(self, mock_post):
        """Test sending alert successfully."""
        mock_post.return_value.status_code = 200
        
        alerter = OracleAlerter(
            bot_token="test_token",
            chat_id="test_chat"
        )
        
        result = alerter.send_alert("info", "Test alert")
        
        assert result is True
        mock_post.assert_called_once()
        
        # Verify message format
        call_args = mock_post.call_args
        message = call_args[1]["json"]["text"]
        assert "ℹ️" in message
        assert "INFO" in message
        assert "Test alert" in message
    
    @patch('requests.post')
    def test_alert_cooldown(self, mock_post):
        """Test alert cooldown prevents duplicates."""
        mock_post.return_value.status_code = 200
        
        alerter = OracleAlerter(
            bot_token="test_token",
            chat_id="test_chat"
        )
        
        # First alert should send
        result1 = alerter.send_alert("warning", "Test", alert_key="test_key")
        assert result1 is True
        
        # Second alert (same key) should be blocked by cooldown
        result2 = alerter.send_alert("warning", "Test", alert_key="test_key")
        assert result2 is False
        
        # Only one call should have been made
        assert mock_post.call_count == 1


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**6.2 Create README Documentation**

File: `devops/README.md`

```markdown
# NPS V4 DevOps - Oracle Monitoring

Comprehensive monitoring, logging, and alerting infrastructure for the Oracle service.

## Components

### 1. Structured Logging
**Location:** `devops/logging/oracle_logger.py`

**Features:**
- JSON-formatted logs for easy parsing
- Rotating file handler (10MB max, 5 backups)
- Log levels: DEBUG, INFO, WARN, ERROR, CRITICAL
- Custom fields: user_id, action, duration_ms

**Usage:**
```python
from devops.logging.oracle_logger import setup_oracle_logger, log_operation

logger = setup_oracle_logger()
log_operation(
    logger, "info",
    "Reading generated",
    user_id="user123",
    action="generate_reading",
    duration_ms=500
)
```

### 2. Health Checks
**Location:** `devops/monitoring/oracle_health.py`

**Endpoint:** `GET http://localhost:50052/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-08T14:30:00Z",
  "checks": {
    "database": {"status": "ok", "latency_ms": 15},
    "ai_api": {"status": "ok", "latency_ms": 200}
  }
}
```

### 3. Metrics Collection
**Location:** `devops/monitoring/oracle_metrics.py`

**Endpoint:** `GET http://localhost:50052/metrics`

**Metrics:**
- Performance: reading time (p50, p95, p99), AI call time, DB query time
- Usage: readings/hour, analyses/hour, suggestions total
- Errors: rate %, count, by type

### 4. Dashboard
**Location:** `devops/dashboards/simple_dashboard.py`

**Access:** http://localhost:9000

**Features:**
- Real-time Oracle service health
- Metrics: readings/hour, avg response time, error rate
- Response time chart (p50, p95, p99)
- Updates every 5 seconds

### 5. Telegram Alerts
**Location:** `devops/alerts/oracle_alerts.py`

**Alert Conditions:**
- 🚨 CRITICAL: Service down
- ⚠️ WARNING: High error rate (>5%)
- ⚠️ WARNING: Slow responses (>10s)
- ℹ️ INFO: Service recovered

**Cooldown:** 5 minutes (prevents alert spam)

## Setup

### 1. Environment Variables
```bash
# Required
export DATABASE_URL="postgresql://nps_user:password@localhost:5432/nps_db"
export ANTHROPIC_API_KEY="your_api_key"
export NPS_BOT_TOKEN="your_telegram_bot_token"
export NPS_CHAT_ID="your_telegram_chat_id"

# Optional
export ORACLE_LOG_LEVEL="INFO"  # DEBUG, INFO, WARN, ERROR
export LOG_DIR="/app/logs"
```

### 2. Start Services
```bash
# Start Oracle service with monitoring
docker-compose up -d oracle oracle-alerter

# Start dashboard
cd devops/dashboards
python simple_dashboard.py
```

### 3. Verify Setup
```bash
# Check health
curl http://localhost:50052/health

# Check metrics
curl http://localhost:50052/metrics

# Test alert
python devops/alerts/oracle_alerts.py --test
```

## Monitoring Workflows

### View Logs
```bash
# Real-time logs
tail -f /app/logs/oracle.log | jq .

# Find errors
grep '"level":"ERROR"' /app/logs/oracle.log | jq .

# Search by user
grep '"user_id":"user123"' /app/logs/oracle.log | jq .
```

### Check Health
```bash
# Quick health check
curl http://localhost:50052/health | jq '.status'

# Detailed health
curl http://localhost:50052/health | jq .
```

### Analyze Metrics
```bash
# Current metrics
curl http://localhost:50052/metrics | jq .

# Error rate
curl http://localhost:50052/metrics | jq '.errors.rate_percent'

# Response time
curl http://localhost:50052/metrics | jq '.performance.reading_time'
```

### Dashboard
```bash
# Access dashboard
open http://localhost:9000

# API status
curl http://localhost:9000/api/status | jq '.oracle'
```

## Testing

```bash
# Run all tests
cd devops
pytest tests/test_oracle_monitoring.py -v

# Run specific test
pytest tests/test_oracle_monitoring.py::TestOracleHealth::test_health_check_all_healthy -v

# Coverage report
pytest tests/test_oracle_monitoring.py --cov=monitoring --cov=logging --cov=alerts
```

## Troubleshooting

### No Logs Generated
```bash
# Check log directory exists
ls -la /app/logs/

# Check permissions
ls -la /app/logs/oracle.log

# Test logger directly
python -c "from devops.logging.oracle_logger import setup_oracle_logger; logger = setup_oracle_logger('/tmp/test.log'); logger.info('Test')"
```

### Health Check Fails
```bash
# Check Oracle service running
docker-compose ps oracle

# Check dependencies
psql -h localhost -U nps_user -d nps_db -c "SELECT 1"

# Test AI API
curl -H "x-api-key: $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/messages
```

### Alerts Not Sending
```bash
# Verify bot token and chat ID
echo $NPS_BOT_TOKEN
echo $NPS_CHAT_ID

# Test Telegram API
curl "https://api.telegram.org/bot$NPS_BOT_TOKEN/getMe"

# Manual alert test
python devops/alerts/oracle_alerts.py --test
```

## Performance Impact

- **Logging:** <10ms overhead per operation
- **Health checks:** <2s response time, no performance impact
- **Metrics collection:** <100ms overhead per operation
- **Alerts:** Asynchronous, no blocking

## Maintenance

### Log Rotation
- Automatic: 10MB max file size, 5 backups
- Manual cleanup: `rm /app/logs/oracle.log.*`

### Metrics Reset
```python
from devops.monitoring.oracle_metrics import metrics
metrics = OracleMetrics(window_minutes=60)  # Fresh instance
```

### Alert History
```bash
# View recent alerts
docker-compose logs oracle-alerter | grep "Alert sent"
```
```

#### Acceptance Criteria

**Phase 6 Checklist:**
- [ ] `test_oracle_monitoring.py` created with comprehensive tests
- [ ] Test coverage â‰¥95% for all monitoring code
- [ ] All tests pass (logging, health, metrics, alerts)
- [ ] README documentation created
- [ ] Setup instructions clear and tested
- [ ] Monitoring workflows documented
- [ ] Troubleshooting guide included

#### Verification

```bash
# Phase 6 Verification (2 minutes)

# Step 1: Check test file created
ls -la devops/tests/test_oracle_monitoring.py
# Expected: File exists

# Step 2: Run tests
cd devops
pytest tests/test_oracle_monitoring.py -v
# Expected: All tests pass

# Step 3: Check test coverage
pytest tests/test_oracle_monitoring.py --cov=monitoring --cov=logging --cov=alerts --cov-report=term-missing
# Expected: Coverage â‰¥95%

# Step 4: Check README created
ls -la devops/README.md
# Expected: File exists

# Step 5: Verify documentation completeness
grep -c "##" devops/README.md
# Expected: â‰¥10 (multiple sections)

# Step 6: Test documentation examples work
# Copy-paste "View Logs" example
tail -f /app/logs/oracle.log | jq . &
sleep 2
pkill tail
# Expected: Valid JSON output

# Step 7: Verify all files exist
ls -la devops/logging/oracle_logger.py
ls -la devops/monitoring/oracle_health.py
ls -la devops/monitoring/oracle_metrics.py
ls -la devops/alerts/oracle_alerts.py
ls -la devops/dashboards/simple_dashboard.py
# Expected: All files exist
```

---

## FINAL VERIFICATION CHECKLIST

### All Phases Complete
- [ ] Phase 1: Logging Infrastructure âœ… Verified
- [ ] Phase 2: Health Check System âœ… Verified
- [ ] Phase 3: Metrics Collection âœ… Verified
- [ ] Phase 4: Dashboard Integration âœ… Verified
- [ ] Phase 5: Telegram Alerts âœ… Verified
- [ ] Phase 6: Testing & Documentation âœ… Verified

### Functional Requirements Met
- [ ] FR1: Structured Logging (JSON, rotation, levels, fields) âœ…
- [ ] FR2: Health Check Endpoint (<2s, database + AI checks) âœ…
- [ ] FR3: Monitoring Metrics (performance, usage, errors) âœ…
- [ ] FR4: Dashboard Integration (status, metrics, real-time) âœ…
- [ ] FR5: Telegram Alerts (service down, high errors, slow responses) âœ…

### Non-Functional Requirements Met
- [ ] NFR1: Performance (health <2s, metrics <100ms, logs <10ms) âœ…
- [ ] NFR2: Reliability (no blocking, alerts <30s) âœ…
- [ ] NFR3: Quality (95%+ test coverage, no false positives) âœ…

### Quality Gates Passed
- [ ] Code Quality: Type hints, docstrings, error handling âœ…
- [ ] Testing: 95%+ coverage, all tests pass âœ…
- [ ] Documentation: README complete, examples work âœ…
- [ ] Architecture Alignment: Layer 7 patterns followed âœ…
- [ ] Performance: All targets met âœ…
- [ ] Security: No sensitive data in logs âœ…

---

## SUCCESS CRITERIA

1. **Structured Logging Works:**
   ```bash
   tail /app/logs/oracle.log | jq .
   # Expected: Valid JSON with timestamp, level, service, action, duration_ms
   ```

2. **Health Checks Work:**
   ```bash
   curl http://localhost:50052/health | jq '.status'
   # Expected: "healthy" (or "degraded"/"down" with details)
   ```

3. **Metrics Collection Works:**
   ```bash
   curl http://localhost:50052/metrics | jq '.usage.readings_per_hour'
   # Expected: Non-zero value after operations
   ```

4. **Dashboard Shows Oracle:**
   ```bash
   curl http://localhost:9000/api/status | jq '.oracle.health.status'
   # Expected: "healthy"
   ```

5. **Alerts Work:**
   ```bash
   python devops/alerts/oracle_alerts.py --test
   # Expected: ✅ Test alert sent + message in Telegram
   ```

6. **Tests Pass:**
   ```bash
   pytest devops/tests/test_oracle_monitoring.py -v --cov
   # Expected: All tests pass, coverage â‰¥95%
   ```

---

## HANDOFF TO NEXT SESSION

### If Session Ends Mid-Implementation

**Resume from Phase:** [Current phase number]

**Context Needed:**
- Which phases completed and verified
- Any failing tests or verification steps
- Environment variables set (bot token, chat ID)

**Verification Before Continuing:**
```bash
# Quick sanity check
curl http://localhost:50052/health  # Oracle health
curl http://localhost:9000/api/status | jq '.oracle'  # Dashboard
python devops/alerts/oracle_alerts.py --test  # Alerts
pytest devops/tests/test_oracle_monitoring.py -v  # Tests
```

---

## NEXT STEPS (After This Spec)

1. **Extend Monitoring to Other Services**
   - Create similar monitoring for Scanner service
   - Create similar monitoring for API service
   - Unified dashboard for all services

2. **Advanced Metrics**
   - Add metrics export (Prometheus format)
   - Historical data retention (database storage)
   - Advanced analytics (trends, predictions)

3. **Enhanced Alerting**
   - Alert rules engine (configurable thresholds)
   - Alert aggregation (group related alerts)
   - Multi-channel alerts (Email + Telegram + Slack)

4. **Production Hardening**
   - Log encryption for sensitive operations
   - Metrics sampling for high-volume scenarios
   - Alert rate limiting (prevent alert storms)

---

## ESTIMATED TIMELINE

- **Phase 1 (Logging):** 30 minutes
- **Phase 2 (Health Checks):** 30 minutes
- **Phase 3 (Metrics):** 40 minutes
- **Phase 4 (Dashboard):** 30 minutes
- **Phase 5 (Alerts):** 30 minutes
- **Phase 6 (Testing/Docs):** 20 minutes

**Total:** 2 hours 40 minutes

**With verification and debugging:** ~3 hours

---

## CONFIDENCE LEVEL

**High (90%)** - Well-defined requirements, clear patterns from architecture plan, standard monitoring practices.

**Risks:**
- Telegram API rate limits (mitigated by cooldown)
- Oracle service integration points (mitigated by careful testing)
- Time window edge cases (mitigated by comprehensive tests)

**Mitigation:**
- Thorough testing at each phase
- Verification steps after each phase
- Documentation of troubleshooting procedures

---

*Specification Version: 1.0*  
*Created: 2026-02-08*  
*Status: Ready for Claude Code CLI Execution*
