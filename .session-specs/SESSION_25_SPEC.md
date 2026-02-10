# SESSION 25 SPEC: WebSocket & Real-Time Updates

**Block:** Frontend Core (Sessions 19-25)
**Estimated Duration:** 4-5 hours
**Complexity:** Medium-High
**Dependencies:** Session 20 (Oracle page), Session 13 (AI engine)

---

## TL;DR

- Wire JWT authentication into the WebSocket connection (query param token)
- Add oracle-specific event types: `reading_started`, `reading_progress`, `reading_complete`, `reading_error`, `daily_reading`
- Integrate `OracleProgressManager.send_progress()` into the reading service so clients see live progress
- Add heartbeat ping/pong to detect stale connections
- Fix the frontend WebSocket client to pass auth token, handle oracle events, and expose typed hooks

---

## OBJECTIVES

1. Authenticate WebSocket connections using JWT token passed as query parameter
2. Define and emit oracle reading progress events through the existing `OracleProgressManager`
3. Implement heartbeat ping/pong with 30-second interval to detect stale connections
4. Update the frontend `WebSocketClient` to pass JWT, handle reconnect with backoff, and type oracle events
5. Create a `useReadingProgress` hook for the Oracle page to show live reading status
6. Add `daily_reading` push event so connected clients receive daily insights automatically
7. Write 12+ tests covering auth, events, heartbeat, reconnect, and hook behavior

---

## PREREQUISITES

- [ ] Oracle reading endpoint works (`POST /api/oracle/reading`)
- [ ] JWT auth system exists (`api/app/middleware/auth.py`)
- [ ] WebSocket manager exists (`api/app/services/websocket_manager.py`)
- [ ] Frontend WebSocket hooks exist (`frontend/src/hooks/useWebSocket.ts`)

Verification:

```bash
test -f api/app/services/websocket_manager.py && echo "OK" || echo "MISSING"
test -f api/app/middleware/auth.py && echo "OK" || echo "MISSING"
test -f frontend/src/hooks/useWebSocket.ts && echo "OK" || echo "MISSING"
test -f frontend/src/services/websocket.ts && echo "OK" || echo "MISSING"
test -f api/app/services/oracle_reading.py && echo "OK" || echo "MISSING"
```

---

## FILES TO CREATE

- `api/tests/test_websocket.py` — WebSocket endpoint tests (auth, events, heartbeat)
- `frontend/src/hooks/useReadingProgress.ts` — Typed hook for reading progress events
- `frontend/src/hooks/__tests__/useReadingProgress.test.ts` — Hook tests
- `frontend/src/services/__tests__/websocket.test.ts` — WebSocket client tests

## FILES TO MODIFY

| File                                    | Current Lines | Action  | Notes                                                     |
| --------------------------------------- | ------------- | ------- | --------------------------------------------------------- |
| `api/app/services/websocket_manager.py` | 63            | REWRITE | Add JWT auth, heartbeat, typed events, room-based routing |
| `api/app/models/events.py`              | 31            | MODIFY  | Add oracle reading event types                            |
| `api/app/services/oracle_reading.py`    | 579           | MODIFY  | Wire progress events into reading methods                 |
| `api/app/routers/oracle.py`             | 627           | MODIFY  | Update oracle WS endpoint to use authenticated manager    |
| `api/app/main.py`                       | 134           | MODIFY  | Update global WS route registration                       |
| `frontend/src/services/websocket.ts`    | 78            | REWRITE | Add JWT auth, heartbeat, typed events                     |
| `frontend/src/hooks/useWebSocket.ts`    | 33            | MODIFY  | Add `useWebSocketConnection` auth param, export status    |
| `frontend/src/types/index.ts`           | 411           | MODIFY  | Add oracle WS event types                                 |
| `frontend/src/locales/en.json`          | 190           | MODIFY  | Add reading progress translation keys                     |
| `frontend/src/locales/fa.json`          | 190           | MODIFY  | Add reading progress translation keys (Persian)           |

## FILES TO DELETE

None.

---

## IMPLEMENTATION PHASES

### Phase 1: Oracle Event Types (15 min)

**Goal:** Define the oracle-specific WebSocket event vocabulary.

**Tasks:**

1. Add oracle reading events to `api/app/models/events.py`
2. Add corresponding TypeScript types to `frontend/src/types/index.ts`

**Code Pattern — `api/app/models/events.py`:**

Add these event type entries to the existing `EVENT_TYPES` dict:

```python
# Oracle reading progress events
"READING_STARTED": "reading_started",
"READING_PROGRESS": "reading_progress",
"READING_COMPLETE": "reading_complete",
"READING_ERROR": "reading_error",
"DAILY_READING": "daily_reading",
```

Add Pydantic models for typed event payloads:

```python
class ReadingProgressEvent(BaseModel):
    """Progress update during reading generation."""
    reading_id: int | None = None
    step: str          # "calculating", "ai_generating", "combining", "complete"
    progress: int      # 0-100 percentage
    message: str       # Human-readable status
    user_id: int | None = None

class ReadingCompleteEvent(BaseModel):
    """Sent when a reading finishes successfully."""
    reading_id: int
    sign_type: str
    summary: str       # Brief preview
    user_id: int | None = None

class ReadingErrorEvent(BaseModel):
    """Sent when a reading fails."""
    error: str
    sign_type: str | None = None
    user_id: int | None = None

class DailyReadingEvent(BaseModel):
    """Pushed when daily reading is generated."""
    date: str
    insight: str
    lucky_numbers: list[str]
```

**Code Pattern — `frontend/src/types/index.ts`:**

Add to the `EventType` union:

```typescript
export type EventType =
  | "finding"
  | "health"
  // ... existing types ...
  | "reading_started"
  | "reading_progress"
  | "reading_complete"
  | "reading_error"
  | "daily_reading";

export interface ReadingProgressData {
  reading_id: number | null;
  step: "calculating" | "ai_generating" | "combining" | "complete";
  progress: number;
  message: string;
  user_id: number | null;
}

export interface ReadingCompleteData {
  reading_id: number;
  sign_type: string;
  summary: string;
  user_id: number | null;
}

export interface ReadingErrorData {
  error: string;
  sign_type: string | null;
  user_id: number | null;
}

export interface DailyReadingData {
  date: string;
  insight: string;
  lucky_numbers: string[];
}
```

**STOP CHECKPOINT 1:**

- [ ] `api/app/models/events.py` has 5 new oracle event types in `EVENT_TYPES`
- [ ] 4 new Pydantic models exist for event payloads
- [ ] `frontend/src/types/index.ts` has new `EventType` entries and data interfaces
- [ ] No import errors: `cd api && python3 -c "from app.models.events import ReadingProgressEvent; print('OK')"`

---

### Phase 2: WebSocket Manager Rewrite — Auth & Heartbeat (45 min)

**Goal:** Replace the basic ConnectionManager with an authenticated, heartbeat-enabled manager.

**Tasks:**

1. Rewrite `api/app/services/websocket_manager.py` to add JWT auth, heartbeat, and room routing
2. Consolidate the two WS managers (global `ConnectionManager` + oracle `OracleProgressManager`)

**Code Pattern — `api/app/services/websocket_manager.py`:**

```python
class AuthenticatedConnection:
    """Wraps a WebSocket with user context."""
    def __init__(self, websocket: WebSocket, user_ctx: dict):
        self.websocket = websocket
        self.user_id: str | None = user_ctx.get("user_id")
        self.role: str = user_ctx.get("role", "user")
        self.scopes: list[str] = user_ctx.get("scopes", [])
        self.connected_at: float = time.time()
        self.last_pong: float = time.time()

class WebSocketManager:
    """Authenticated WebSocket manager with heartbeat and room routing."""

    def __init__(self):
        self.connections: list[AuthenticatedConnection] = []
        self._heartbeat_task: asyncio.Task | None = None
        self._heartbeat_interval: int = 30  # seconds
        self._pong_timeout: int = 10  # seconds

    async def authenticate(self, websocket: WebSocket) -> dict | None:
        """Extract JWT from query params and verify."""
        # Token from ?token=xxx query param
        token = websocket.query_params.get("token")
        if not token:
            return None
        # Reuse existing JWT decode from auth middleware
        from app.middleware.auth import _try_jwt_auth
        return _try_jwt_auth(token)

    async def connect(self, websocket: WebSocket) -> AuthenticatedConnection | None:
        """Authenticate and accept a WebSocket connection."""
        user_ctx = await self.authenticate(websocket)
        if not user_ctx:
            await websocket.close(code=4001, reason="Authentication required")
            return None
        await websocket.accept()
        conn = AuthenticatedConnection(websocket, user_ctx)
        self.connections.append(conn)
        return conn

    def disconnect(self, conn: AuthenticatedConnection): ...
    async def broadcast(self, event: str, data: dict): ...
    async def send_to_user(self, user_id: str, event: str, data: dict): ...
    async def _heartbeat_loop(self): ...
    async def start_heartbeat(self): ...
    async def stop_heartbeat(self): ...
```

**Key Design Decisions:**

1. **Auth via query param:** `ws://host/ws/oracle?token=<jwt>` — WebSocket doesn't support custom headers in browsers, so JWT goes in the URL query.
2. **Single manager:** Remove `OracleProgressManager` from `oracle_reading.py`. The `WebSocketManager` singleton handles all WS connections. Oracle progress is just a specific event type broadcast through it.
3. **Heartbeat:** Server sends ping every 30s, expects pong within 10s. Stale connections are closed and removed.
4. **Room routing:** `send_to_user(user_id, event, data)` sends only to connections authenticated as that user. `broadcast(event, data)` sends to all.

**Update `api/app/main.py`:**

Change the WS route from the basic `websocket_endpoint` to the new manager's handler:

```python
from app.services.websocket_manager import ws_manager

@app.websocket("/ws/oracle")
async def oracle_websocket(websocket: WebSocket):
    conn = await ws_manager.connect(websocket)
    if not conn:
        return
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client pong responses
            if data == "pong":
                conn.last_pong = time.time()
    except WebSocketDisconnect:
        ws_manager.disconnect(conn)
```

Remove the old `/ws` route. The new canonical endpoint is `/ws/oracle`.

**Update `api/app/routers/oracle.py`:**

Remove the `oracle_ws` endpoint (lines 356-364). The WS is now mounted in `main.py` at `/ws/oracle`.

**STOP CHECKPOINT 2:**

- [ ] `api/app/services/websocket_manager.py` has `WebSocketManager` with `authenticate`, `connect`, `broadcast`, `send_to_user`, heartbeat
- [ ] JWT auth rejects connections without valid token (close code 4001)
- [ ] `api/app/main.py` mounts WS at `/ws/oracle` using new manager
- [ ] Oracle router's standalone WS endpoint removed
- [ ] `OracleProgressManager` removed from `oracle_reading.py`
- [ ] Verify: `cd api && python3 -c "from app.services.websocket_manager import ws_manager; print('OK')"`

---

### Phase 3: Wire Progress Events into Reading Service (30 min)

**Goal:** Make reading endpoints emit progress events as they compute.

**Tasks:**

1. Import `ws_manager` into `oracle_reading.py`
2. Add `async` progress emission at key computation steps
3. Emit events: `reading_started` → `reading_progress` (calculating, ai_generating, combining) → `reading_complete` or `reading_error`

**Code Pattern — Reading progress integration:**

The reading service methods (`get_reading`, `get_question_sign`, `get_name_reading`) are synchronous. Progress events need to be emitted from within them. Since FastAPI runs sync endpoints in a threadpool, use `asyncio.run_coroutine_threadsafe` to send WS messages from sync context:

```python
import asyncio

def _emit_progress(event: str, data: dict):
    """Emit a WebSocket event from synchronous context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast(event, data), loop
            )
    except RuntimeError:
        pass  # No event loop — skip silently (e.g., in tests)
```

Add progress calls in `get_reading()`:

```python
def get_reading(self, datetime_str, extended=False):
    _emit_progress("reading_started", {"step": "started", "progress": 0, "message": "Reading started"})

    # FC60 encoding
    _emit_progress("reading_progress", {"step": "calculating", "progress": 25, "message": "Computing FC60 encoding"})
    fc60_result = encode_fc60(...)

    # Numerology
    _emit_progress("reading_progress", {"step": "calculating", "progress": 50, "message": "Calculating numerology"})
    ...

    # AI interpretation
    _emit_progress("reading_progress", {"step": "ai_generating", "progress": 75, "message": "Generating AI interpretation"})
    try:
        interp_result = interpret_reading(...)
    except Exception:
        _emit_progress("reading_error", {"error": "AI interpretation unavailable"})

    _emit_progress("reading_complete", {"step": "complete", "progress": 100, "message": "Reading complete"})
    return result
```

Also wire into `get_daily_insight()` to broadcast a `daily_reading` event when a daily insight is generated.

**STOP CHECKPOINT 3:**

- [ ] `get_reading()` emits `reading_started`, `reading_progress` (x3), and `reading_complete`
- [ ] `get_question_sign()` emits `reading_started` and `reading_complete`
- [ ] `get_name_reading()` emits `reading_started` and `reading_complete`
- [ ] `get_daily_insight()` broadcasts `daily_reading` event
- [ ] Errors emit `reading_error` instead of `reading_complete`
- [ ] Progress calls are non-blocking and failure-safe (no crash if WS unavailable)

---

### Phase 4: Frontend WebSocket Client Rewrite (40 min)

**Goal:** Update the frontend WS client to authenticate, handle heartbeat, and type oracle events.

**Tasks:**

1. Rewrite `frontend/src/services/websocket.ts` — add JWT, heartbeat, typed events
2. Update `frontend/src/hooks/useWebSocket.ts` — expose connection status

**Code Pattern — `frontend/src/services/websocket.ts`:**

```typescript
type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";
type StatusHandler = (status: ConnectionStatus) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Map<EventType, Set<EventHandler>> = new Map();
  private statusHandlers: Set<StatusHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private status: ConnectionStatus = "disconnected";

  connect(url?: string) {
    // Get JWT from localStorage
    const token = localStorage.getItem("nps_token");
    if (!token) {
      this.setStatus("error");
      return;
    }

    const wsUrl = url || `ws://${window.location.host}/ws/oracle?token=${token}`;
    this.setStatus("connecting");
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.setStatus("connected");
      this.reconnectDelay = 1000;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      // Handle server ping
      if (event.data === "ping") {
        this.ws?.send("pong");
        return;
      }
      // Parse and dispatch event
      try {
        const msg: WSEvent = JSON.parse(event.data);
        const handlers = this.handlers.get(msg.event as EventType);
        handlers?.forEach(h => h(msg.data));
      } catch {
        // ignore parse errors
      }
    };

    this.ws.onclose = (event) => {
      this.stopHeartbeat();
      if (event.code === 4001) {
        this.setStatus("error"); // Auth failure — don't reconnect
        return;
      }
      this.setStatus("disconnected");
      this.scheduleReconnect();
    };

    this.ws.onerror = () => { this.ws?.close(); };
  }

  private startHeartbeat() { ... }  // setInterval client-side ping every 25s
  private stopHeartbeat() { ... }
  private setStatus(s: ConnectionStatus) { ... }

  onStatus(handler: StatusHandler): () => void { ... }
  on(event: EventType, handler: EventHandler): () => void { ... }  // existing
  off(event: EventType, handler: EventHandler): void { ... }       // existing
  disconnect(): void { ... }                                        // existing
}
```

**Key changes from current:**

1. JWT token appended to WS URL as query param
2. Heartbeat: client responds with `"pong"` when server sends `"ping"`
3. Auth failure (close code 4001) does NOT trigger reconnect
4. `ConnectionStatus` exposed via `onStatus` callback
5. Exponential backoff capped at 30 seconds

**Code Pattern — `frontend/src/hooks/useWebSocket.ts`:**

Update `useWebSocketConnection` to expose status:

```typescript
export function useWebSocketConnection(): ConnectionStatus {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");

  useEffect(() => {
    wsClient.connect();
    const unsub = wsClient.onStatus(setStatus);
    return () => {
      unsub();
      wsClient.disconnect();
    };
  }, []);

  return status;
}
```

**STOP CHECKPOINT 4:**

- [ ] `frontend/src/services/websocket.ts` passes JWT in WS URL query param
- [ ] Client responds to server `"ping"` with `"pong"`
- [ ] Close code 4001 does not trigger reconnect
- [ ] `ConnectionStatus` type exported and tracked
- [ ] `useWebSocketConnection` returns connection status
- [ ] No TypeScript errors: `cd frontend && npx tsc --noEmit`

---

### Phase 5: useReadingProgress Hook (25 min)

**Goal:** Create a typed hook for Oracle page components to consume reading progress.

**Tasks:**

1. Create `frontend/src/hooks/useReadingProgress.ts`
2. Add translation keys for progress messages

**Code Pattern — `frontend/src/hooks/useReadingProgress.ts`:**

```typescript
import { useState, useCallback } from "react";
import { useWebSocket } from "./useWebSocket";
import type {
  ReadingProgressData,
  ReadingCompleteData,
  ReadingErrorData,
} from "@/types";

interface ReadingProgress {
  isActive: boolean;
  step: string;
  progress: number; // 0-100
  message: string;
  error: string | null;
  lastReading: ReadingCompleteData | null;
}

export function useReadingProgress(): ReadingProgress {
  const [state, setState] = useState<ReadingProgress>({
    isActive: false,
    step: "",
    progress: 0,
    message: "",
    error: null,
    lastReading: null,
  });

  useWebSocket(
    "reading_started",
    useCallback((data) => {
      setState({
        isActive: true,
        step: "started",
        progress: 0,
        message: (data as ReadingProgressData).message || "Starting...",
        error: null,
        lastReading: null,
      });
    }, []),
  );

  useWebSocket(
    "reading_progress",
    useCallback((data) => {
      const d = data as ReadingProgressData;
      setState((prev) => ({
        ...prev,
        step: d.step,
        progress: d.progress,
        message: d.message,
      }));
    }, []),
  );

  useWebSocket(
    "reading_complete",
    useCallback((data) => {
      const d = data as ReadingCompleteData;
      setState({
        isActive: false,
        step: "complete",
        progress: 100,
        message: "Reading complete",
        error: null,
        lastReading: d,
      });
    }, []),
  );

  useWebSocket(
    "reading_error",
    useCallback((data) => {
      const d = data as ReadingErrorData;
      setState((prev) => ({
        ...prev,
        isActive: false,
        step: "error",
        error: d.error,
      }));
    }, []),
  );

  return state;
}
```

**Translation keys to add:**

`en.json`:

```json
{
  "oracle": {
    "progress_started": "Starting reading...",
    "progress_calculating": "Computing numerology...",
    "progress_ai": "Generating AI interpretation...",
    "progress_combining": "Combining results...",
    "progress_complete": "Reading complete",
    "progress_error": "Reading failed",
    "ws_connected": "Connected",
    "ws_disconnected": "Disconnected",
    "ws_reconnecting": "Reconnecting..."
  }
}
```

`fa.json`:

```json
{
  "oracle": {
    "progress_started": "شروع خوانش...",
    "progress_calculating": "محاسبه عددشناسی...",
    "progress_ai": "تولید تفسیر هوش مصنوعی...",
    "progress_combining": "ترکیب نتایج...",
    "progress_complete": "خوانش کامل شد",
    "progress_error": "خطا در خوانش",
    "ws_connected": "متصل",
    "ws_disconnected": "قطع شده",
    "ws_reconnecting": "در حال اتصال مجدد..."
  }
}
```

**STOP CHECKPOINT 5:**

- [ ] `frontend/src/hooks/useReadingProgress.ts` exports `useReadingProgress`
- [ ] Hook returns `isActive`, `step`, `progress`, `message`, `error`, `lastReading`
- [ ] Listens to 4 event types: `reading_started`, `reading_progress`, `reading_complete`, `reading_error`
- [ ] Translation keys added to both `en.json` and `fa.json`
- [ ] No TypeScript errors: `cd frontend && npx tsc --noEmit`

---

### Phase 6: Backend Tests (40 min)

**Goal:** Test WebSocket auth, event emission, heartbeat, and progress integration.

**Tasks:**

1. Create `api/tests/test_websocket.py` with comprehensive tests

**Test File: `api/tests/test_websocket.py`**

Uses `httpx` WebSocket test client and the existing `conftest.py` fixtures.

```
test_ws_connect_with_valid_jwt
  — Connect with valid JWT token in query param → connection accepted

test_ws_reject_without_token
  — Connect without token → close code 4001

test_ws_reject_invalid_token
  — Connect with invalid JWT → close code 4001

test_ws_receive_ping
  — After connection, server sends "ping" → client receives it

test_ws_pong_updates_last_seen
  — Client sends "pong" → connection's last_pong timestamp updates

test_ws_broadcast_event
  — Two clients connected → broadcast reaches both

test_ws_send_to_user
  — Two clients with different user_ids → send_to_user delivers only to target

test_ws_reading_started_event
  — Trigger a reading via API → connected WS client receives "reading_started"

test_ws_reading_progress_event
  — During reading computation → WS client receives "reading_progress" with step/progress

test_ws_reading_complete_event
  — After reading finishes → WS client receives "reading_complete" with reading_id

test_ws_reading_error_event
  — When AI interpretation fails → WS client receives "reading_error"

test_ws_daily_reading_broadcast
  — GET /oracle/daily → all connected clients receive "daily_reading" event
```

**STOP CHECKPOINT 6:**

- [ ] `api/tests/test_websocket.py` has 12 test functions
- [ ] All tests pass: `cd api && python3 -m pytest tests/test_websocket.py -v`
- [ ] Existing API tests still pass: `cd api && python3 -m pytest tests/ -v`

---

### Phase 7: Frontend Tests (35 min)

**Goal:** Test the frontend WebSocket client and hooks.

**Tasks:**

1. Create `frontend/src/services/__tests__/websocket.test.ts`
2. Create `frontend/src/hooks/__tests__/useReadingProgress.test.ts`

**Test File: `frontend/src/services/__tests__/websocket.test.ts`**

```
test_connect_appends_jwt_to_url
  — localStorage has nps_token → WebSocket constructor called with ?token=xxx

test_connect_fails_without_token
  — No nps_token in localStorage → status becomes "error", no WS created

test_reconnect_on_normal_close
  — WS closes normally (code 1000) → scheduleReconnect called

test_no_reconnect_on_auth_failure
  — WS closes with code 4001 → no reconnect attempted

test_pong_response_to_ping
  — Server sends "ping" → client sends "pong"

test_event_dispatch
  — Server sends JSON event → registered handler called with data

test_exponential_backoff
  — After multiple disconnects → delay doubles up to 30s max
```

**Test File: `frontend/src/hooks/__tests__/useReadingProgress.test.ts`**

```
test_initial_state
  — Hook returns isActive=false, progress=0, error=null

test_reading_started
  — "reading_started" event → isActive=true, progress=0

test_reading_progress_updates
  — "reading_progress" event → step and progress update

test_reading_complete
  — "reading_complete" event → isActive=false, progress=100, lastReading set

test_reading_error
  — "reading_error" event → isActive=false, error set
```

**STOP CHECKPOINT 7:**

- [ ] `frontend/src/services/__tests__/websocket.test.ts` has 7 tests
- [ ] `frontend/src/hooks/__tests__/useReadingProgress.test.ts` has 5 tests
- [ ] All pass: `cd frontend && npx vitest run`

---

### Phase 8: Integration & Vite Proxy Update (15 min)

**Goal:** Ensure the WS proxy in Vite dev config points to the new endpoint and everything works end-to-end.

**Tasks:**

1. Update `frontend/vite.config.ts` WS proxy from `/ws` to `/ws/oracle`
2. Verify the Layout component calls `useWebSocketConnection()` (Session 19 should have wired this)
3. If not yet wired, add `useWebSocketConnection()` call in the Layout component

**Code Pattern — `frontend/vite.config.ts`:**

The current proxy config:

```typescript
"/ws": {
  target: "ws://localhost:8000",
  ws: true,
},
```

Update to:

```typescript
"/ws/oracle": {
  target: "ws://localhost:8000",
  ws: true,
},
```

**STOP CHECKPOINT 8:**

- [ ] `frontend/vite.config.ts` proxies `/ws/oracle` to backend
- [ ] Layout (or App) calls `useWebSocketConnection()`
- [ ] No TypeScript errors: `cd frontend && npx tsc --noEmit`
- [ ] All frontend tests pass: `cd frontend && npx vitest run`
- [ ] All API tests pass: `cd api && python3 -m pytest tests/ -v`

---

### Phase 9: Final Verification (15 min)

**Goal:** End-to-end verification that all pieces work together.

**Tasks:**

1. Run full API test suite
2. Run full frontend test suite
3. Verify no import errors
4. Check that old WS endpoint `/ws` no longer exists (replaced by `/ws/oracle`)

**Verification commands:**

```bash
# API tests
cd api && python3 -m pytest tests/ -v

# Frontend tests
cd frontend && npx vitest run

# TypeScript check
cd frontend && npx tsc --noEmit

# Import verification
cd api && python3 -c "
from app.services.websocket_manager import ws_manager
from app.models.events import ReadingProgressEvent, ReadingCompleteEvent
print('Backend imports OK')
"

# Verify old /ws route removed
cd api && python3 -c "
from app.main import app
routes = [r.path for r in app.routes]
assert '/ws' not in routes, 'Old /ws route still exists'
assert any('/ws/oracle' in str(r) for r in app.routes), '/ws/oracle not found'
print('Route check OK')
"
```

**STOP CHECKPOINT 9:**

- [ ] All API tests pass (12+ WS tests + existing suite)
- [ ] All frontend tests pass (12+ new + existing suite)
- [ ] No TypeScript errors
- [ ] `/ws` route removed, `/ws/oracle` exists
- [ ] Import checks pass

---

## TESTS TO WRITE

### Backend Tests — `api/tests/test_websocket.py`

| #   | Function                          | Description                           |
| --- | --------------------------------- | ------------------------------------- |
| 1   | `test_ws_connect_with_valid_jwt`  | Valid JWT in query param → accepted   |
| 2   | `test_ws_reject_without_token`    | No token → close 4001                 |
| 3   | `test_ws_reject_invalid_token`    | Bad JWT → close 4001                  |
| 4   | `test_ws_receive_ping`            | Server sends ping to connected client |
| 5   | `test_ws_pong_updates_last_seen`  | Pong updates last_pong timestamp      |
| 6   | `test_ws_broadcast_event`         | Broadcast reaches all clients         |
| 7   | `test_ws_send_to_user`            | Send to specific user only            |
| 8   | `test_ws_reading_started_event`   | Reading API triggers WS started event |
| 9   | `test_ws_reading_progress_event`  | Progress events during computation    |
| 10  | `test_ws_reading_complete_event`  | Complete event with reading_id        |
| 11  | `test_ws_reading_error_event`     | Error event on AI failure             |
| 12  | `test_ws_daily_reading_broadcast` | Daily insight broadcasts to all       |

### Frontend Tests — `frontend/src/services/__tests__/websocket.test.ts`

| #   | Function                            | Description                     |
| --- | ----------------------------------- | ------------------------------- |
| 13  | `test_connect_appends_jwt_to_url`   | JWT added to WS URL             |
| 14  | `test_connect_fails_without_token`  | No token → error status         |
| 15  | `test_reconnect_on_normal_close`    | Reconnect on normal close       |
| 16  | `test_no_reconnect_on_auth_failure` | No reconnect on 4001            |
| 17  | `test_pong_response_to_ping`        | Client sends pong for ping      |
| 18  | `test_event_dispatch`               | Event handlers called correctly |
| 19  | `test_exponential_backoff`          | Backoff caps at 30s             |

### Frontend Tests — `frontend/src/hooks/__tests__/useReadingProgress.test.ts`

| #   | Function                        | Description                      |
| --- | ------------------------------- | -------------------------------- |
| 20  | `test_initial_state`            | Default state values             |
| 21  | `test_reading_started`          | Started event → isActive         |
| 22  | `test_reading_progress_updates` | Progress event → step updates    |
| 23  | `test_reading_complete`         | Complete event → lastReading set |
| 24  | `test_reading_error`            | Error event → error set          |

**Total: 24 tests**

---

## ACCEPTANCE CRITERIA

- [ ] WebSocket connects with JWT auth (token in query param)
- [ ] Unauthenticated WS connections are rejected with code 4001
- [ ] Progress events received during reading generation (started → progress → complete/error)
- [ ] Auto-reconnect on disconnection with exponential backoff (max 30s)
- [ ] No reconnect on auth failure (code 4001)
- [ ] Heartbeat ping/pong every 30 seconds
- [ ] `useReadingProgress` hook returns typed progress state
- [ ] Daily reading broadcasts to all connected clients
- [ ] Vite proxy correctly routes `/ws/oracle` to backend
- [ ] All 24+ tests pass
- [ ] No TypeScript errors
- [ ] Existing test suites unbroken

Verification:

```bash
cd api && python3 -m pytest tests/ -v --tb=short
cd frontend && npx vitest run
cd frontend && npx tsc --noEmit
```

---

## ERROR SCENARIOS

### Problem: WebSocket fails to connect in development

**Cause:** Vite proxy not forwarding `/ws/oracle` correctly.

**Fix:**

1. Check `frontend/vite.config.ts` has the proxy entry for `/ws/oracle`
2. Verify API is running on port 8000: `curl http://localhost:8000/api/health`
3. Check browser devtools Network tab for WS connection attempt
4. Ensure JWT token exists in `localStorage.getItem('nps_token')`

### Problem: Reading progress events not arriving

**Cause:** `_emit_progress()` fails silently because no event loop is available in the sync reading methods.

**Fix:**

1. The reading endpoints run in FastAPI's threadpool. `asyncio.get_event_loop()` may raise `RuntimeError`.
2. Use `asyncio.get_running_loop()` wrapped in try/except, or use `anyio.from_thread.run` to bridge sync → async.
3. Alternative: Use a thread-safe queue. The WS manager's heartbeat loop drains the queue and broadcasts.

### Problem: Existing tests break after removing OracleProgressManager

**Cause:** `oracle_reading.py` used to export `oracle_progress` which is imported in `oracle.py` (router).

**Fix:**

1. Remove the `oracle_ws` endpoint from `oracle.py` that imports `oracle_progress`
2. Remove the `OracleProgressManager` class and `oracle_progress` singleton from `oracle_reading.py`
3. Update any test that imports `oracle_progress` directly
4. Search with: `grep -r "oracle_progress" api/`

---

## HANDOFF

### Created Files

- `api/tests/test_websocket.py` — 12 backend WS tests
- `frontend/src/hooks/useReadingProgress.ts` — Reading progress hook
- `frontend/src/hooks/__tests__/useReadingProgress.test.ts` — 5 hook tests
- `frontend/src/services/__tests__/websocket.test.ts` — 7 client tests

### Modified Files

- `api/app/services/websocket_manager.py` — Authenticated WS manager with heartbeat
- `api/app/models/events.py` — 5 oracle event types + 4 Pydantic models
- `api/app/services/oracle_reading.py` — Progress emission in reading methods, OracleProgressManager removed
- `api/app/routers/oracle.py` — Oracle WS endpoint removed (moved to main.py)
- `api/app/main.py` — New `/ws/oracle` route with auth
- `frontend/src/services/websocket.ts` — JWT auth, heartbeat, typed events
- `frontend/src/hooks/useWebSocket.ts` — Connection status exposed
- `frontend/src/types/index.ts` — Oracle WS event types
- `frontend/vite.config.ts` — WS proxy updated
- `frontend/src/locales/en.json` — Progress translation keys
- `frontend/src/locales/fa.json` — Progress translation keys (Persian)

### Deleted Files

None.

### What the Next Session Receives

Session 25 is the final session in the Frontend Core block (19-25). The next session (Session 26 — RTL Layout System) receives:

- A fully functional real-time WebSocket layer with authenticated connections
- Reading progress events flowing from backend to frontend during computation
- The `useReadingProgress` hook ready for use in Oracle page components
- All oracle event types defined and typed on both backend and frontend
- A stable WebSocket infrastructure that subsequent sessions (26-31 Frontend Advanced) can build on for real-time features like live RTL preview, responsive breakpoint indicators, etc.
