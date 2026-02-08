# SPEC: API Oracle Reading Endpoints - T2-S2

**Estimated Duration:** 3-4 hours  
**Layer:** Layer 2 (API)  
**Terminal:** Terminal 2 (API Development)  
**Session:** T2-S2 (Oracle Reading Operations)  
**Phase:** Phase 1 (Foundation - API Layer)

---

## TL;DR

- Creating 3 REST endpoints + 1 WebSocket for Oracle readings
- Single-user context (no multi-tenant yet - simplification for V4 launch)
- Real-time WebSocket updates during FC60 calculations (progress indicators)
- Integration with Terminal 3 Backend FC60 service via function calls
- Question encryption before database storage (privacy/security)
- Comprehensive test suite: 95%+ coverage, <50ms p95 response time
- Full OpenAPI documentation auto-generated

---

## OBJECTIVE

Build FastAPI endpoints that enable users to request Oracle readings (FC60 numerology + cosmic timing analysis) with real-time progress updates, secure storage, and seamless integration with Backend FC60 engine.

**Success Metric:** User submits question → receives formatted FC60 reading with interpretation → reading stored encrypted in database → retrievable via history endpoint

---

## CONTEXT

### Current State

- Terminal 4 (Database): `oracle_readings` table exists (from T4-S1)
- Terminal 6 (Security): Encryption module ready (AES-256)
- Terminal 3 Session 1: FC60 core engine implemented (fc60.py)
- Terminal 2 Session 1: Health endpoint + auth middleware complete

### What's Changing

Adding Oracle-specific functionality:
1. **Reading creation** - User asks question, gets FC60 analysis
2. **Reading history** - User retrieves past readings
3. **Real-time updates** - WebSocket streams progress during calculation
4. **Encrypted storage** - Questions stored securely in database

### Why

Oracle readings are core NPS V4 feature. Users interact with FC60 numerology system through API (not CLI). This enables:
- Web UI integration (Terminal 1 can call these endpoints)
- Historical analysis (track Oracle guidance over time)
- Learning system (Terminal 7 can analyze reading patterns)

---

## PREREQUISITES

**MUST be completed before starting:**

- [x] Terminal 4: `oracle_readings` table created
  - Verified: `psql -c "SELECT * FROM oracle_readings LIMIT 1;"`
- [x] Terminal 6: Encryption module available
  - Verified: `python -c "from security.encryption import encrypt_text"`
- [x] Terminal 3 Session 1: FC60 engine functional
  - Verified: `python -c "from backend.oracle_service.app.engines.fc60 import FC60Engine; fc60 = FC60Engine()"`
- [x] Terminal 2 Session 1: Auth middleware working
  - Verified: `curl -H "Authorization: Bearer test_key" http://localhost:8000/api/health`

**Environment Variables:**
- `NPS_MASTER_PASSWORD` - For encryption (set in .env)
- `DATABASE_URL` - PostgreSQL connection
- `API_SECRET_KEY` - FastAPI secret

---

## TOOLS TO USE

### Extended Thinking
Use for:
- Designing WebSocket message flow (when to send updates, what data)
- Error handling strategy (FC60 calculation fails, database errors)
- Response model structure (how to format FC60 output for frontend)

### Subagents
Use 3 subagents for parallel work:
1. **Subagent 1:** Pydantic models (request/response schemas)
2. **Subagent 2:** Endpoint implementation (business logic)
3. **Subagent 3:** WebSocket manager + integration tests

### Skills
- Read `/mnt/skills/public/product-self-knowledge/SKILL.md` before implementing
  - FastAPI best practices
  - Async patterns
  - WebSocket handling

---

## REQUIREMENTS

### Functional Requirements

1. **FR-1: Create Reading**
   - Endpoint: `POST /api/oracle/reading`
   - Input: Question (string, 1-500 chars), optional timestamp
   - Process: Call FC60 engine → Store encrypted → Return reading
   - Output: Reading ID, FC60 signature, interpretation, timing
   - Real-time: WebSocket sends progress updates ("Calculating numerology...", "Analyzing cosmic alignment...")

2. **FR-2: Get Reading History**
   - Endpoint: `GET /api/oracle/readings?user_id={id}&limit={n}&offset={m}`
   - Input: User ID (from auth), pagination params
   - Process: Query database → Decrypt questions → Return list
   - Output: Array of readings with metadata

3. **FR-3: Get Specific Reading**
   - Endpoint: `GET /api/oracle/readings/{id}`
   - Input: Reading ID (UUID)
   - Process: Query database → Decrypt → Return if owned by user
   - Output: Full reading object

4. **FR-4: Real-Time Progress**
   - Endpoint: `ws://localhost:8000/ws/oracle`
   - Flow: Client connects → Server streams progress during FC60 calculation → Final result pushed
   - Messages: `{"type": "progress", "message": "Step 1/5..."}`, `{"type": "complete", "reading": {...}}`

### Non-Functional Requirements

1. **Performance**
   - API response time: <50ms p95 (excluding FC60 calculation time)
   - FC60 calculation: <2s for simple readings, <5s for complex
   - WebSocket message latency: <100ms
   - Database query time: <10ms

2. **Security**
   - API key authentication required (scope: `oracle_read`)
   - Questions encrypted with AES-256 before storage
   - Reading IDs are UUIDs (non-sequential, non-guessable)
   - No plaintext sensitive data in logs
   - Rate limiting: 10 readings per minute per user

3. **Quality**
   - Test coverage: 95%+
   - Type hints: 100% (mypy strict mode)
   - OpenAPI documentation: Complete
   - Error messages: User-friendly, actionable

---

## IMPLEMENTATION PLAN

### Phase 1: Pydantic Models (Duration: 30 min)

**Subagent 1 Task:**

Create `/api/app/models/oracle.py` with:

1. **OracleReadingRequest** (input validation)
```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class OracleReadingRequest(BaseModel):
    question: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="User's question for Oracle"
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="Optional specific time for reading (default: now)"
    )
    
    @validator('question')
    def validate_question(cls, v):
        # Remove excessive whitespace
        v = ' '.join(v.split())
        if len(v) < 1:
            raise ValueError('Question cannot be empty')
        return v

    class Config:
        schema_extra = {
            "example": {
                "question": "What should I focus on today?",
                "timestamp": "2026-02-08T10:30:00Z"
            }
        }
```

2. **OracleReadingResponse** (output structure)
```python
from uuid import UUID

class OracleReadingResponse(BaseModel):
    id: UUID
    user_id: str
    question: str  # Decrypted
    fc60_signature: str  # e.g., "Water Ox"
    numerology_score: int  # 0-100
    cosmic_alignment: float  # 0.0 to 100.0
    interpretation: str  # Human-readable wisdom
    timing: str  # e.g., "Favorable moment for new beginnings"
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_123",
                "question": "What should I focus on today?",
                "fc60_signature": "Water Ox",
                "numerology_score": 78,
                "cosmic_alignment": 82.5,
                "interpretation": "Strong alignment with creative pursuits...",
                "timing": "Current moment favors introspection and planning",
                "created_at": "2026-02-08T10:30:00Z"
            }
        }
```

3. **OracleReadingListResponse** (pagination)
```python
class OracleReadingListResponse(BaseModel):
    readings: List[OracleReadingResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
```

4. **WebSocketProgressMessage** (real-time updates)
```python
class WebSocketProgressMessage(BaseModel):
    type: str  # "progress", "complete", "error"
    message: Optional[str]
    reading: Optional[OracleReadingResponse]
    error: Optional[str]
```

**Verification:**
```bash
cd api
python -c "from app.models.oracle import OracleReadingRequest; req = OracleReadingRequest(question='Test'); print(req)"
# Expected: OracleReadingRequest(question='Test', timestamp=None)
```

**Checkpoint:**
- [ ] All Pydantic models import without errors
- [ ] Validation works (try invalid inputs)
- [ ] Example schemas match expected structure

**STOP if checkpoint fails** - Fix models before proceeding

---

### Phase 2: Endpoint Implementation (Duration: 90 min)

**Subagent 2 Task:**

Create `/api/app/routers/oracle.py` with:

1. **POST /api/oracle/reading**
```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.models.oracle import OracleReadingRequest, OracleReadingResponse
from app.dependencies import get_current_user, get_db
from app.services.oracle_service import OracleService
from app.websockets.manager import ConnectionManager
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/oracle", tags=["oracle"])
manager = ConnectionManager()

@router.post("/reading", response_model=OracleReadingResponse)
async def create_reading(
    request: OracleReadingRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user),
    db = Depends(get_db)
) -> OracleReadingResponse:
    """
    Create new Oracle reading using FC60 numerology.
    
    **Process:**
    1. Validate request
    2. Call FC60 engine (with progress updates via WebSocket)
    3. Encrypt question
    4. Store in database
    5. Return formatted reading
    
    **WebSocket Updates:**
    - Connect to ws://localhost:8000/ws/oracle before calling this endpoint
    - Progress messages stream during calculation
    - Final result pushed when complete
    
    **Rate Limit:** 10 readings per minute
    """
    try:
        # Initialize Oracle service
        oracle_service = OracleService(db)
        
        # Generate reading (this calls FC60 engine)
        reading = await oracle_service.create_reading(
            user_id=user.id,
            question=request.question,
            timestamp=request.timestamp or datetime.utcnow(),
            ws_manager=manager  # For progress updates
        )
        
        return reading
        
    except ValueError as e:
        # Invalid input
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected error
        logger.error("Reading creation failed", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail="Reading creation failed")
```

2. **GET /api/oracle/readings** (history)
```python
@router.get("/readings", response_model=OracleReadingListResponse)
async def get_readings(
    limit: int = 20,
    offset: int = 0,
    user = Depends(get_current_user),
    db = Depends(get_db)
) -> OracleReadingListResponse:
    """
    Get user's reading history.
    
    **Pagination:**
    - limit: Max 100, default 20
    - offset: Skip N readings, default 0
    
    **Returns:** Most recent readings first
    """
    if limit > 100:
        limit = 100
    
    oracle_service = OracleService(db)
    
    readings, total = await oracle_service.get_user_readings(
        user_id=user.id,
        limit=limit,
        offset=offset
    )
    
    return OracleReadingListResponse(
        readings=readings,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(readings)) < total
    )
```

3. **GET /api/oracle/readings/{id}**
```python
from uuid import UUID

@router.get("/readings/{reading_id}", response_model=OracleReadingResponse)
async def get_reading(
    reading_id: UUID,
    user = Depends(get_current_user),
    db = Depends(get_db)
) -> OracleReadingResponse:
    """
    Get specific reading by ID.
    
    **Security:** Only returns reading if owned by current user
    """
    oracle_service = OracleService(db)
    
    reading = await oracle_service.get_reading_by_id(
        reading_id=reading_id,
        user_id=user.id
    )
    
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    
    return reading
```

**Create Service Layer** `/api/app/services/oracle_service.py`:

```python
from typing import List, Tuple, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.models import OracleReading
from app.models.oracle import OracleReadingResponse
from backend.oracle_service.app.engines.fc60 import FC60Engine
from security.encryption import encrypt_text, decrypt_text
from app.websockets.manager import ConnectionManager
import logging

logger = logging.getLogger(__name__)

class OracleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.fc60 = FC60Engine()
    
    async def create_reading(
        self,
        user_id: str,
        question: str,
        timestamp: datetime,
        ws_manager: Optional[ConnectionManager] = None
    ) -> OracleReadingResponse:
        """
        Create new Oracle reading with FC60 analysis.
        
        **Steps:**
        1. Send WebSocket progress: "Calculating numerology..."
        2. Call FC60 engine
        3. Send WebSocket progress: "Analyzing cosmic alignment..."
        4. Interpret results
        5. Encrypt question
        6. Store in database
        7. Send WebSocket complete message
        """
        reading_id = uuid4()
        
        try:
            # Progress update 1
            if ws_manager:
                await ws_manager.broadcast({
                    "type": "progress",
                    "message": "Calculating numerology patterns...",
                    "step": 1,
                    "total_steps": 5
                })
            
            # Calculate numerology score
            numerology_score = self.fc60.calculate_numerology(question, timestamp)
            
            # Progress update 2
            if ws_manager:
                await ws_manager.broadcast({
                    "type": "progress",
                    "message": "Analyzing cosmic alignment...",
                    "step": 2,
                    "total_steps": 5
                })
            
            # Calculate cosmic alignment
            cosmic_alignment = self.fc60.calculate_alignment(timestamp)
            
            # Progress update 3
            if ws_manager:
                await ws_manager.broadcast({
                    "type": "progress",
                    "message": "Determining FC60 signature...",
                    "step": 3,
                    "total_steps": 5
                })
            
            # Get FC60 signature
            fc60_signature = self.fc60.get_signature(timestamp)
            
            # Progress update 4
            if ws_manager:
                await ws_manager.broadcast({
                    "type": "progress",
                    "message": "Generating interpretation...",
                    "step": 4,
                    "total_steps": 5
                })
            
            # Generate interpretation
            interpretation = self.fc60.interpret(
                signature=fc60_signature,
                numerology_score=numerology_score,
                cosmic_alignment=cosmic_alignment,
                question=question
            )
            
            # Get timing guidance
            timing = self.fc60.get_timing_guidance(timestamp)
            
            # Progress update 5
            if ws_manager:
                await ws_manager.broadcast({
                    "type": "progress",
                    "message": "Storing reading...",
                    "step": 5,
                    "total_steps": 5
                })
            
            # Encrypt question before storage
            encrypted_question = encrypt_text(question, os.environ["NPS_MASTER_PASSWORD"])
            
            # Create database record
            db_reading = OracleReading(
                id=reading_id,
                user_id=user_id,
                question_encrypted=encrypted_question,
                fc60_signature=fc60_signature,
                numerology_score=numerology_score,
                cosmic_alignment=cosmic_alignment,
                interpretation=interpretation,
                timing=timing,
                created_at=timestamp
            )
            
            self.db.add(db_reading)
            await self.db.commit()
            await self.db.refresh(db_reading)
            
            # Create response
            response = OracleReadingResponse(
                id=reading_id,
                user_id=user_id,
                question=question,  # Decrypted for response
                fc60_signature=fc60_signature,
                numerology_score=numerology_score,
                cosmic_alignment=cosmic_alignment,
                interpretation=interpretation,
                timing=timing,
                created_at=timestamp
            )
            
            # Send completion message via WebSocket
            if ws_manager:
                await ws_manager.broadcast({
                    "type": "complete",
                    "reading": response.dict()
                })
            
            logger.info("Reading created", extra={"reading_id": str(reading_id)})
            
            return response
            
        except Exception as e:
            logger.error("Reading creation failed", extra={"error": str(e)}, exc_info=True)
            
            # Send error via WebSocket
            if ws_manager:
                await ws_manager.broadcast({
                    "type": "error",
                    "error": "Reading creation failed"
                })
            
            raise
    
    async def get_user_readings(
        self,
        user_id: str,
        limit: int,
        offset: int
    ) -> Tuple[List[OracleReadingResponse], int]:
        """Get user's reading history with pagination."""
        
        # Get total count
        count_query = select(func.count()).select_from(OracleReading).where(
            OracleReading.user_id == user_id
        )
        total = await self.db.scalar(count_query)
        
        # Get readings
        query = select(OracleReading).where(
            OracleReading.user_id == user_id
        ).order_by(
            OracleReading.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        db_readings = result.scalars().all()
        
        # Decrypt and convert to response models
        readings = []
        for db_reading in db_readings:
            decrypted_question = decrypt_text(
                db_reading.question_encrypted,
                os.environ["NPS_MASTER_PASSWORD"]
            )
            
            readings.append(OracleReadingResponse(
                id=db_reading.id,
                user_id=db_reading.user_id,
                question=decrypted_question,
                fc60_signature=db_reading.fc60_signature,
                numerology_score=db_reading.numerology_score,
                cosmic_alignment=db_reading.cosmic_alignment,
                interpretation=db_reading.interpretation,
                timing=db_reading.timing,
                created_at=db_reading.created_at
            ))
        
        return readings, total
    
    async def get_reading_by_id(
        self,
        reading_id: UUID,
        user_id: str
    ) -> Optional[OracleReadingResponse]:
        """Get specific reading by ID (only if owned by user)."""
        
        query = select(OracleReading).where(
            OracleReading.id == reading_id,
            OracleReading.user_id == user_id
        )
        
        result = await self.db.execute(query)
        db_reading = result.scalar_one_or_none()
        
        if not db_reading:
            return None
        
        # Decrypt question
        decrypted_question = decrypt_text(
            db_reading.question_encrypted,
            os.environ["NPS_MASTER_PASSWORD"]
        )
        
        return OracleReadingResponse(
            id=db_reading.id,
            user_id=db_reading.user_id,
            question=decrypted_question,
            fc60_signature=db_reading.fc60_signature,
            numerology_score=db_reading.numerology_score,
            cosmic_alignment=db_reading.cosmic_alignment,
            interpretation=db_reading.interpretation,
            timing=db_reading.timing,
            created_at=db_reading.created_at
        )
```

**Verification:**
```bash
cd api
# Start API
uvicorn app.main:app --reload &

# Test create reading
curl -X POST http://localhost:8000/api/oracle/reading \
  -H "Authorization: Bearer test_key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What should I focus on today?"}'
# Expected: 200 OK, reading object with FC60 analysis

# Test get readings
curl http://localhost:8000/api/oracle/readings?limit=10 \
  -H "Authorization: Bearer test_key"
# Expected: 200 OK, array of readings

# Test get specific reading
curl http://localhost:8000/api/oracle/readings/{id} \
  -H "Authorization: Bearer test_key"
# Expected: 200 OK, reading object
```

**Checkpoint:**
- [ ] All endpoints return 200 for valid requests
- [ ] Pydantic validation works (test with invalid data)
- [ ] Database storage verified (check `oracle_readings` table)
- [ ] Questions are encrypted in database
- [ ] Error handling works (test 401, 404, 500 cases)

**STOP if checkpoint fails** - Fix endpoints before proceeding

---

### Phase 3: WebSocket Implementation (Duration: 60 min)

**Subagent 3 Task:**

Create `/api/app/websockets/manager.py`:

```python
from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections for real-time Oracle updates.
    
    **Usage:**
    - Client connects to ws://localhost:8000/ws/oracle
    - Server broadcasts progress during reading creation
    - Client receives updates and final result
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket client connected", extra={"total_connections": len(self.active_connections)})
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info("WebSocket client disconnected", extra={"total_connections": len(self.active_connections)})
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client."""
        await websocket.send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error("WebSocket send failed", extra={"error": str(e)})
                disconnected.add(connection)
        
        # Remove failed connections
        for connection in disconnected:
            self.disconnect(connection)
```

**Add WebSocket Endpoint** in `/api/app/routers/oracle.py`:

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/oracle")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Oracle reading updates.
    
    **Message Types:**
    - progress: {"type": "progress", "message": "Calculating...", "step": 1, "total_steps": 5}
    - complete: {"type": "complete", "reading": {...}}
    - error: {"type": "error", "error": "Error message"}
    
    **Client Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/oracle/ws/oracle');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'progress') {
            console.log(`Progress: ${data.message} (${data.step}/${data.total_steps})`);
        } else if (data.type === 'complete') {
            console.log('Reading complete:', data.reading);
        } else if (data.type === 'error') {
            console.error('Error:', data.error);
        }
    };
    ```
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive, listen for ping/pong
            data = await websocket.receive_text()
            
            # Echo back to confirm connection
            if data == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**Verification:**
```bash
# Terminal 1: Start API
cd api
uvicorn app.main:app --reload

# Terminal 2: Test WebSocket with wscat
npm install -g wscat
wscat -c ws://localhost:8000/api/oracle/ws/oracle

# Send ping
> ping
# Expected: {"type": "pong"}

# Terminal 3: Create reading (should see WebSocket messages in Terminal 2)
curl -X POST http://localhost:8000/api/oracle/reading \
  -H "Authorization: Bearer test_key" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question"}'

# Terminal 2 should show:
# {"type": "progress", "message": "Calculating numerology patterns...", "step": 1, "total_steps": 5}
# {"type": "progress", "message": "Analyzing cosmic alignment...", "step": 2, "total_steps": 5}
# ...
# {"type": "complete", "reading": {...}}
```

**Checkpoint:**
- [ ] WebSocket connects successfully
- [ ] Progress messages stream during reading creation
- [ ] Final result pushed when complete
- [ ] Error messages sent on failure
- [ ] Disconnect handling works

**STOP if checkpoint fails** - Fix WebSocket before proceeding

---

### Phase 4: Integration Tests (Duration: 60 min)

**Subagent 3 Task (continued):**

Create `/api/tests/test_oracle.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.database.models import OracleReading
from uuid import uuid4
import json

@pytest.mark.asyncio
async def test_create_reading_success():
    """Test successful reading creation."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/oracle/reading",
            headers={"Authorization": "Bearer test_key"},
            json={"question": "What should I focus on today?"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "id" in data
    assert "question" in data
    assert "fc60_signature" in data
    assert "numerology_score" in data
    assert "cosmic_alignment" in data
    assert "interpretation" in data
    assert "timing" in data
    
    # Verify data types
    assert isinstance(data["numerology_score"], int)
    assert 0 <= data["numerology_score"] <= 100
    assert isinstance(data["cosmic_alignment"], float)
    assert 0.0 <= data["cosmic_alignment"] <= 100.0

@pytest.mark.asyncio
async def test_create_reading_invalid_question():
    """Test reading creation with invalid question."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Empty question
        response = await ac.post(
            "/api/oracle/reading",
            headers={"Authorization": "Bearer test_key"},
            json={"question": ""}
        )
    
    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_reading_too_long():
    """Test reading creation with question exceeding max length."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/oracle/reading",
            headers={"Authorization": "Bearer test_key"},
            json={"question": "a" * 501}  # Max is 500
        )
    
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_create_reading_no_auth():
    """Test reading creation without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/oracle/reading",
            json={"question": "Test"}
        )
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_readings_pagination():
    """Test reading history with pagination."""
    # Create 25 readings first
    async with AsyncClient(app=app, base_url="http://test") as ac:
        for i in range(25):
            await ac.post(
                "/api/oracle/reading",
                headers={"Authorization": "Bearer test_key"},
                json={"question": f"Question {i}"}
            )
        
        # Get first page
        response = await ac.get(
            "/api/oracle/readings?limit=10&offset=0",
            headers={"Authorization": "Bearer test_key"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["readings"]) == 10
    assert data["total"] == 25
    assert data["has_more"] is True
    
    # Get second page
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/api/oracle/readings?limit=10&offset=10",
            headers={"Authorization: Bearer test_key"}
        )
    
    data = response.json()
    assert len(data["readings"]) == 10
    assert data["has_more"] is True

@pytest.mark.asyncio
async def test_get_reading_by_id_success():
    """Test getting specific reading by ID."""
    # Create reading
    async with AsyncClient(app=app, base_url="http://test") as ac:
        create_response = await ac.post(
            "/api/oracle/reading",
            headers={"Authorization": "Bearer test_key"},
            json={"question": "Test question"}
        )
        reading_id = create_response.json()["id"]
        
        # Get by ID
        response = await ac.get(
            f"/api/oracle/readings/{reading_id}",
            headers={"Authorization": "Bearer test_key"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == reading_id
    assert data["question"] == "Test question"

@pytest.mark.asyncio
async def test_get_reading_by_id_not_found():
    """Test getting non-existent reading."""
    fake_id = str(uuid4())
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            f"/api/oracle/readings/{fake_id}",
            headers={"Authorization": "Bearer test_key"}
        )
    
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_reading_by_id_wrong_user():
    """Test getting reading owned by different user."""
    # Create reading with user1
    async with AsyncClient(app=app, base_url="http://test") as ac:
        create_response = await ac.post(
            "/api/oracle/reading",
            headers={"Authorization": "Bearer user1_key"},
            json={"question": "User1 question"}
        )
        reading_id = create_response.json()["id"]
        
        # Try to get with user2
        response = await ac.get(
            f"/api/oracle/readings/{reading_id}",
            headers={"Authorization": "Bearer user2_key"}
        )
    
    assert response.status_code == 404  # Security: don't reveal existence

@pytest.mark.asyncio
async def test_reading_encryption():
    """Test that questions are encrypted in database."""
    from app.database import get_db
    
    # Create reading
    async with AsyncClient(app=app, base_url="http://test") as ac:
        create_response = await ac.post(
            "/api/oracle/reading",
            headers={"Authorization": "Bearer test_key"},
            json={"question": "Sensitive question"}
        )
        reading_id = create_response.json()["id"]
    
    # Check database directly
    db = next(get_db())
    db_reading = db.query(OracleReading).filter(
        OracleReading.id == reading_id
    ).first()
    
    # Verify question is encrypted (not plaintext)
    assert db_reading.question_encrypted != "Sensitive question"
    assert len(db_reading.question_encrypted) > len("Sensitive question")
    
    # Verify we can decrypt it
    from security.encryption import decrypt_text
    decrypted = decrypt_text(
        db_reading.question_encrypted,
        os.environ["NPS_MASTER_PASSWORD"]
    )
    assert decrypted == "Sensitive question"

@pytest.mark.asyncio
async def test_fc60_integration():
    """Test FC60 engine integration."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/oracle/reading",
            headers={"Authorization": "Bearer test_key"},
            json={
                "question": "What is my destiny?",
                "timestamp": "2026-02-08T10:30:00Z"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify FC60 signature is valid format
    assert isinstance(data["fc60_signature"], str)
    assert len(data["fc60_signature"]) > 0
    
    # Verify interpretation is meaningful (not empty)
    assert len(data["interpretation"]) > 50  # At least 50 chars
    
    # Verify timing guidance exists
    assert len(data["timing"]) > 0

@pytest.mark.asyncio
async def test_performance_create_reading():
    """Test reading creation performance."""
    import time
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        start = time.time()
        
        response = await ac.post(
            "/api/oracle/reading",
            headers={"Authorization": "Bearer test_key"},
            json={"question": "Performance test"}
        )
        
        end = time.time()
        duration = (end - start) * 1000  # Convert to ms
    
    assert response.status_code == 200
    
    # FC60 calculation should complete in <5s
    # API overhead should be <50ms (excluding FC60)
    # Total should be <5.05s
    assert duration < 5050  # 5.05 seconds in ms

@pytest.mark.asyncio
async def test_websocket_messages():
    """Test WebSocket progress messages during reading creation."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    with TestClient(app) as client:
        # Connect to WebSocket
        with client.websocket_connect("/api/oracle/ws/oracle") as websocket:
            # Send ping to verify connection
            websocket.send_text("ping")
            data = websocket.receive_json()
            assert data["type"] == "pong"
            
            # Create reading in background (this should trigger WebSocket messages)
            # Note: In real test, use background task or separate thread
            
            # Receive progress messages
            messages = []
            for i in range(6):  # 5 progress + 1 complete
                data = websocket.receive_json()
                messages.append(data)
            
            # Verify message sequence
            assert messages[0]["type"] == "progress"
            assert "Calculating numerology" in messages[0]["message"]
            
            assert messages[-1]["type"] == "complete"
            assert "reading" in messages[-1]
```

**Run Tests:**
```bash
cd api
pytest tests/test_oracle.py -v --cov=app/routers/oracle --cov=app/services/oracle_service

# Expected output:
# test_create_reading_success PASSED
# test_create_reading_invalid_question PASSED
# test_create_reading_too_long PASSED
# test_create_reading_no_auth PASSED
# test_get_readings_pagination PASSED
# test_get_reading_by_id_success PASSED
# test_get_reading_by_id_not_found PASSED
# test_get_reading_by_id_wrong_user PASSED
# test_reading_encryption PASSED
# test_fc60_integration PASSED
# test_performance_create_reading PASSED
# test_websocket_messages PASSED
#
# Coverage: 95%+
```

**Checkpoint:**
- [ ] All tests pass (12/12)
- [ ] Coverage ≥95%
- [ ] Performance test passes (<5.05s)
- [ ] Encryption test verifies database storage
- [ ] WebSocket test verifies message flow

**STOP if checkpoint fails** - Fix failing tests before proceeding

---

## VERIFICATION CHECKLIST

### Code Quality
- [ ] Pydantic models have type hints
- [ ] Docstrings on all endpoints (OpenAPI descriptions)
- [ ] Async/await used correctly
- [ ] Error handling with HTTPException
- [ ] Logging present (JSON format)
- [ ] No hardcoded values (uses env vars)

### Authentication
- [ ] API key required on all endpoints
- [ ] Correct scope checked (`oracle_read`)
- [ ] 401 returned for invalid/missing key
- [ ] 403 returned for insufficient permissions

### Error Handling
- [ ] 400 for invalid input (with validation message)
- [ ] 401 for missing/invalid auth
- [ ] 404 for not found
- [ ] 500 for unexpected errors (with logging)
- [ ] No sensitive data in error responses

### Business Logic
- [ ] Input validation complete (Pydantic)
- [ ] Database queries parameterized
- [ ] Questions encrypted before storage
- [ ] Reading IDs are UUIDs (non-guessable)
- [ ] Pagination works correctly
- [ ] User isolation enforced (can't access other users' readings)

### Performance
- [ ] API response time <50ms p95 (excluding FC60)
- [ ] FC60 calculation <5s
- [ ] WebSocket latency <100ms
- [ ] Database queries use indexes
- [ ] No N+1 query problems

### Documentation
- [ ] OpenAPI schema accurate
- [ ] Example requests provided
- [ ] Example responses provided
- [ ] Error codes documented
- [ ] WebSocket protocol documented

### Testing
- [ ] Integration tests pass (12/12)
- [ ] Coverage ≥95%
- [ ] Happy path tested
- [ ] Error cases tested (400, 401, 404, 500)
- [ ] Edge cases tested (pagination, encryption, performance)
- [ ] WebSocket flow tested

### Verification Commands

**Terminal 1: Run Tests**
```bash
cd api
pytest tests/test_oracle.py -v --cov=app/routers/oracle --cov=app/services/oracle_service
# Expected: 12/12 tests pass, 95%+ coverage
```

**Terminal 2: Start API**
```bash
cd api
uvicorn app.main:app --reload
# Expected: API starts on http://localhost:8000
```

**Terminal 3: Test Endpoints**
```bash
# Create reading
curl -X POST http://localhost:8000/api/oracle/reading \
  -H "Authorization: Bearer test_key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What should I focus on today?"}'
# Expected: 200 OK, reading object

# Get readings
curl http://localhost:8000/api/oracle/readings?limit=10 \
  -H "Authorization: Bearer test_key"
# Expected: 200 OK, array of readings

# Get specific reading
READING_ID="<id from previous response>"
curl http://localhost:8000/api/oracle/readings/$READING_ID \
  -H "Authorization: Bearer test_key"
# Expected: 200 OK, reading object

# Test WebSocket
wscat -c ws://localhost:8000/api/oracle/ws/oracle
> ping
# Expected: {"type": "pong"}
```

**Terminal 4: Verify Database**
```bash
psql -h localhost -U nps_user -d nps_db -c "SELECT id, user_id, fc60_signature, created_at FROM oracle_readings ORDER BY created_at DESC LIMIT 5;"
# Expected: List of readings with encrypted questions
```

**Terminal 5: Check OpenAPI Docs**
```bash
curl http://localhost:8000/docs
# Expected: Swagger UI loads with Oracle endpoints documented
```

**Terminal 6: Performance Test**
```bash
ab -n 100 -c 10 -H "Authorization: Bearer test_key" \
   -p reading_request.json \
   -T application/json \
   http://localhost:8000/api/oracle/reading

# reading_request.json:
# {"question": "Performance test question"}

# Expected: Mean response time <5.05s (including FC60 calculation)
```

**Terminal 7: Security Audit**
```bash
# Check database encryption
psql -c "SELECT question_encrypted FROM oracle_readings LIMIT 1;"
# Expected: Encrypted string (not plaintext)

# Check logs for sensitive data
grep -r "question" api/logs/*.log
# Expected: No plaintext questions in logs
```

---

## SUCCESS CRITERIA

1. **Functionality** ✅
   - Create reading endpoint works: User submits question → receives FC60 analysis
   - History endpoint works: User retrieves past readings with pagination
   - Specific reading endpoint works: User gets reading by ID (if owned)
   - WebSocket works: Real-time progress updates stream during creation

2. **Security** ✅
   - Questions encrypted in database (AES-256)
   - API key authentication enforced (scope: `oracle_read`)
   - User isolation: Can't access other users' readings
   - No sensitive data in logs or error messages

3. **Performance** ✅
   - API response time: <50ms p95 (excluding FC60 calculation)
   - FC60 calculation: <5s for complex readings
   - WebSocket latency: <100ms
   - Database queries: <10ms

4. **Quality** ✅
   - Test coverage: 95%+ (12 tests pass)
   - Type hints: 100% (mypy strict mode)
   - OpenAPI documentation: Complete and accurate
   - Error messages: User-friendly and actionable

5. **Integration** ✅
   - FC60 engine integration works (correct signatures, interpretations)
   - Database integration works (encrypted storage, retrieval)
   - WebSocket integration works (progress messages, completion)
   - Authentication integration works (API key validation)

---

## HANDOFF TO NEXT SESSION

If session ends mid-implementation, use this resume guide:

**Resume from Phase:** [Current phase number]

**Context needed:**
- Which files exist: `ls -la api/app/routers/oracle.py api/app/models/oracle.py api/app/services/oracle_service.py`
- Which tests pass: `pytest tests/test_oracle.py -v`
- Database state: `psql -c "SELECT COUNT(*) FROM oracle_readings;"`

**Verification before continuing:**
- [ ] Previous phase checkpoint passed
- [ ] All previous phase tests pass
- [ ] Database migrations applied
- [ ] Environment variables set

**Files to check:**
- `/api/app/routers/oracle.py` - Endpoint definitions
- `/api/app/models/oracle.py` - Pydantic models
- `/api/app/services/oracle_service.py` - Business logic
- `/api/app/websockets/manager.py` - WebSocket handling
- `/api/tests/test_oracle.py` - Integration tests

---

## NEXT STEPS (After This Spec)

1. **Terminal 1 Session 3: Frontend Oracle Integration**
   - Create `Oracle.tsx` page
   - Implement WebSocket client for progress updates
   - Display readings with FC60 visualization
   - History view with pagination

2. **Terminal 2 Session 3: API Scanner Endpoints**
   - POST /api/scanner/start
   - POST /api/scanner/stop
   - GET /api/scanner/terminals
   - WebSocket for scan progress

3. **Terminal 7 Session 1: Oracle Analytics**
   - Track reading patterns
   - Identify most-asked question types
   - Analyze FC60 signature distributions
   - Generate insights for learning system

---

## DEPENDENCIES

**Must exist before starting:**
- ✅ Terminal 4: `oracle_readings` table
- ✅ Terminal 6: Encryption module
- ✅ Terminal 3 Session 1: FC60 engine
- ✅ Terminal 2 Session 1: Auth middleware

**Will be used by:**
- ⏳ Terminal 1 Session 3: Frontend Oracle page
- ⏳ Terminal 7 Session 1: Analytics system
- ⏳ Terminal 3 Session 2: Oracle → Scanner suggestions

---

## REFERENCES

**Architecture Plan:**
- `/mnt/project/NPS_V4_ARCHITECTURE_PLAN.md` (Layer 2: API, Oracle Endpoints section)

**Verification Checklist:**
- `/mnt/project/VERIFICATION_CHECKLISTS.md` (Layer 2: API Verification)

**Skills:**
- `/mnt/skills/public/product-self-knowledge/SKILL.md` (FastAPI best practices)

**Error Recovery:**
- `/mnt/project/ERROR_RECOVERY.md` (Layer 2: API Errors)

**Related Specs:**
- `SPEC_T2_S1_API_HEALTH_AUTH.md` (Previous session: Health + Auth)
- `SPEC_T3_S1_BACKEND_FC60_ENGINE.md` (FC60 core implementation)
- `SPEC_T4_S1_DATABASE_ORACLE_SCHEMA.md` (Database schema)

---

*Estimated Total Duration: 3-4 hours*  
*Confidence Level: High (95%) - Well-defined requirements, existing patterns*  
*Version: 1.0*  
*Created: 2026-02-08*
