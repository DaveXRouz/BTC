# SESSION 36 SPEC — Telegram Bot: Admin Commands & Notifications

**Block:** Features & Integration (Sessions 32-37)
**Estimated Duration:** 4-5 hours
**Complexity:** Medium
**Dependencies:** Session 35 (daily bot), Session 33 (bot core), Session 2 (auth)

---

## TL;DR

- Build admin-only Telegram commands: `/admin_stats`, `/admin_users`, `/admin_broadcast`
- Create a system notification service that pushes alerts to an admin-only Telegram channel
- Bridge the existing `notifier.py` (1578-line legacy module) with the new `python-telegram-bot` infrastructure from Session 33
- Wire API error tracking, new user registration, and startup/shutdown events into admin notifications
- Role-gate every admin command through the bot's account-linking auth (Session 33) and the API's `admin` scope

---

## OBJECTIVES

1. **Admin commands** — Three Telegram commands restricted to admin-linked accounts: system stats, user listing, message broadcast
2. **System notifications** — Automated alerts pushed to an admin-only chat on: API errors, high error rate (>5%), new user registration, service startup/shutdown
3. **Notifier bridge** — Refactor `notifier.py` to emit events through the new bot's `Application` instance instead of raw `urllib` calls, while preserving existing notification templates
4. **Admin channel config** — Support a separate `NPS_ADMIN_CHAT_ID` env var for admin-only alerts (falls back to `NPS_CHAT_ID`)
5. **Broadcast with confirmation** — `/admin_broadcast` shows a confirmation prompt (inline keyboard "Send" / "Cancel") before delivering to all linked users
6. **Audit logging** — All admin commands logged to `oracle_audit_log` table

---

## PREREQUISITES

- [ ] Bot core running in Docker (`services/telegram/bot.py` from Session 33)
- [ ] Account linking operational (users link Telegram to API key, Session 33)
- [ ] Reading commands functional (`services/telegram/handlers/readings.py` from Session 34)
- [ ] Daily scheduler running (`services/telegram/scheduler.py` from Session 35)
- [ ] Telegram settings API exists (`api/app/routers/telegram.py` from Session 35)
- [ ] Auth middleware with `admin` scope (`api/app/middleware/auth.py`)

Verification:

```bash
ls services/telegram/bot.py
ls services/telegram/handlers/readings.py
ls services/telegram/handlers/daily.py
ls services/telegram/scheduler.py
ls api/app/routers/telegram.py
grep "require_scope" api/app/middleware/auth.py
grep "NPS_BOT_TOKEN" .env.example
```

---

## FILES TO CREATE

| File                                            | Purpose                                                               |
| ----------------------------------------------- | --------------------------------------------------------------------- |
| `services/telegram/handlers/admin.py`           | Admin command handlers (/admin_stats, /admin_users, /admin_broadcast) |
| `services/telegram/notifications.py`            | System notification service — dispatches alerts to admin channel      |
| `services/telegram/tests/test_admin.py`         | Unit tests for admin commands                                         |
| `services/telegram/tests/test_notifications.py` | Unit tests for notification service                                   |

## FILES TO MODIFY

| File                                                 | Change                                                                                                |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `services/oracle/oracle_service/engines/notifier.py` | Add `emit_event()` bridge that forwards to new notification service; deprecate raw `urllib` send path |
| `services/telegram/bot.py`                           | Register admin handlers; initialize notification service on startup                                   |
| `services/telegram/handlers/__init__.py`             | Export admin handlers                                                                                 |
| `api/app/routers/telegram.py`                        | Add `/admin/stats` and `/admin/users` API endpoints for bot to call                                   |
| `api/app/config.py`                                  | Add `nps_admin_chat_id` setting                                                                       |
| `.env.example`                                       | Add `NPS_ADMIN_CHAT_ID` variable                                                                      |
| `docker-compose.yml`                                 | Pass `NPS_ADMIN_CHAT_ID` to telegram service                                                          |

## FILES TO DELETE

None.

---

## IMPLEMENTATION PHASES

### Phase 1 — Admin Channel Configuration

**Goal:** Support a dedicated admin chat ID separate from the user-facing bot chat.

**Work:**

1. Add `NPS_ADMIN_CHAT_ID` to `api/app/config.py`:
   ```python
   nps_admin_chat_id: str = ""  # Falls back to nps_chat_id if empty
   ```
2. Add `NPS_ADMIN_CHAT_ID` to `.env.example` with comment
3. Add env var passthrough in `docker-compose.yml` for the telegram service
4. Create a helper in `services/telegram/notifications.py`:
   ```python
   def get_admin_chat_id() -> str:
       """Return admin chat ID, falling back to main chat ID."""
   ```

**Checkpoint:**

```bash
grep "NPS_ADMIN_CHAT_ID" .env.example
grep "nps_admin_chat_id" api/app/config.py
grep "NPS_ADMIN_CHAT_ID" docker-compose.yml
```

---

### Phase 2 — Admin Stats API Endpoint

**Goal:** Expose system stats via API so the bot can query them.

**Work:**

1. Add `GET /api/telegram/admin/stats` to `api/app/routers/telegram.py`:
   - Requires `admin` scope via `require_scope("admin")`
   - Returns JSON:
     ```json
     {
       "total_users": 42,
       "readings_today": 15,
       "readings_total": 1284,
       "error_count_24h": 3,
       "active_sessions": 2,
       "uptime_seconds": 86400,
       "db_size_mb": 128.5,
       "last_reading_at": "2026-02-10T14:30:00Z"
     }
     ```
   - Query `oracle_users` for user count
   - Query `oracle_readings` for reading counts (today filter: `created_at >= today`)
   - Query `oracle_audit_log` for error count (action = 'error', last 24h)
   - Get uptime from application start time (stored in `app.state`)

2. Add `GET /api/telegram/admin/users` to `api/app/routers/telegram.py`:
   - Requires `admin` scope
   - Query params: `limit` (default 10), `offset` (default 0), `sort` (default `created_at desc`)
   - Returns paginated list of `oracle_users` with ID, name, birthday, created_at
   - Does NOT return sensitive fields (mother_name, coordinates)

**Checkpoint:**

```bash
grep "admin/stats" api/app/routers/telegram.py
grep "admin/users" api/app/routers/telegram.py
grep "require_scope" api/app/routers/telegram.py
```

---

### Phase 3 — Admin Command Handlers

**Goal:** Build the three admin Telegram commands.

**Work:**

1. Create `services/telegram/handlers/admin.py` with:

   **`/admin_stats` handler:**
   - Check caller is admin (via account-linking lookup → API role check)
   - Call `GET /api/telegram/admin/stats` using bot's HTTP client
   - Format response as Telegram Markdown:

     ```
     📊 *System Stats*

     👥 Users: 42
     📖 Readings today: 15 (total: 1,284)
     ⚠️ Errors (24h): 3
     🖥 Active sessions: 2
     ⏱ Uptime: 1d 0h 0m
     💾 DB size: 128.5 MB
     📅 Last reading: 2 min ago
     ```

   **`/admin_users` handler:**
   - Check caller is admin
   - Call `GET /api/telegram/admin/users?limit=10`
   - Format as numbered list with inline pagination buttons ("◀ Prev" / "Next ▶")
   - Each user shows: `#ID — Name — Joined: YYYY-MM-DD`
   - Callback data format: `admin_users:page:{n}`

   **`/admin_broadcast` handler:**
   - Check caller is admin
   - Parse message from command args: `/admin_broadcast Hello everyone!`
   - If no message provided, reply with usage hint
   - Show confirmation prompt via inline keyboard:

     ```
     📢 *Broadcast Preview*

     > Hello everyone!

     This will be sent to X linked users.

     [✅ Send] [❌ Cancel]
     ```

   - On "Send" callback: iterate all linked Telegram chat IDs, send message to each with rate limiting (max 30 messages/second per Telegram API limits)
   - On "Cancel" callback: edit message to "Broadcast cancelled."
   - Log broadcast to `oracle_audit_log`

2. Admin role verification helper:

   ```python
   async def is_admin(chat_id: int, http_client: httpx.AsyncClient) -> bool:
       """Check if the Telegram chat_id is linked to an admin-role API account."""
   ```

   - Calls the bot's internal user-lookup (from Session 33's account linking)
   - Checks the linked API key's role

3. Register all handlers in `services/telegram/bot.py`:
   ```python
   from services.telegram.handlers.admin import register_admin_handlers
   register_admin_handlers(application)
   ```

**Checkpoint:**

```bash
python3 -c "from services.telegram.handlers.admin import register_admin_handlers; print('OK')"
grep "admin_stats" services/telegram/handlers/admin.py
grep "admin_users" services/telegram/handlers/admin.py
grep "admin_broadcast" services/telegram/handlers/admin.py
```

---

### Phase 4 — System Notification Service

**Goal:** Build the notification dispatch service that pushes system events to the admin channel.

**Work:**

1. Create `services/telegram/notifications.py`:

   ```python
   class SystemNotifier:
       """Sends system notifications to the admin Telegram channel."""

       def __init__(self, bot: Bot, admin_chat_id: str):
           self._bot = bot
           self._admin_chat_id = admin_chat_id
           self._cooldowns: dict[str, float] = {}

       async def notify_api_error(self, endpoint: str, status: int, detail: str) -> None:
           """Alert on API error (429, 500, 503)."""

       async def notify_high_error_rate(self, rate: float, window_minutes: int) -> None:
           """Alert when error rate exceeds threshold."""

       async def notify_new_user(self, user_name: str, user_id: int) -> None:
           """Alert on new Oracle user registration."""

       async def notify_startup(self, service: str, version: str) -> None:
           """Alert on service startup."""

       async def notify_shutdown(self, service: str, reason: str) -> None:
           """Alert on service shutdown."""

       async def notify_reading_milestone(self, total: int) -> None:
           """Alert on reading count milestones (100, 500, 1000, ...)."""
   ```

2. **Notification templates** — Each method formats a Telegram message:

   API Error:

   ```
   🚨 *API Error*
   Endpoint: `POST /api/oracle/reading`
   Status: 500
   Detail: Internal Server Error
   Time: 2026-02-10 14:30:00 UTC
   ```

   High Error Rate:

   ```
   ⚠️ *High Error Rate Alert*
   Rate: 7.2% (threshold: 5%)
   Window: last 15 minutes
   Action: Check API logs
   ```

   New User:

   ```
   👤 *New User Registered*
   Name: John Doe
   ID: #42
   Time: 2026-02-10 14:30:00 UTC
   ```

   Startup:

   ```
   🟢 *Service Started*
   Service: API Gateway
   Version: 1.0.0
   Time: 2026-02-10 14:30:00 UTC
   ```

   Shutdown:

   ```
   🔴 *Service Stopped*
   Service: API Gateway
   Reason: SIGTERM
   Time: 2026-02-10 14:30:00 UTC
   ```

3. **Cooldown system** — Prevent alert spam:
   - API errors: 1 notification per endpoint per 5 minutes
   - High error rate: 1 notification per 15 minutes
   - New user: no cooldown
   - Startup/shutdown: no cooldown
   - Milestone: no cooldown (inherently rare)

4. **Graceful degradation** — If admin chat ID is not configured or bot token is missing, log warning and skip notification (never crash).

**Checkpoint:**

```bash
python3 -c "from services.telegram.notifications import SystemNotifier; print('OK')"
grep "notify_api_error" services/telegram/notifications.py
grep "notify_new_user" services/telegram/notifications.py
grep "cooldown" services/telegram/notifications.py
```

---

### Phase 5 — Notifier Bridge (Legacy Integration)

**Goal:** Connect the existing `notifier.py` to the new notification service without breaking existing functionality.

**Work:**

1. Add an event emission layer to `services/oracle/oracle_service/engines/notifier.py`:
   - Add `_event_callback: Optional[Callable]` class/module-level variable
   - Add `register_event_callback(callback: Callable)` function
   - Modify existing notification functions (`notify_error`, `notify_solve`, `notify_balance_found`, `notify_daily_status`) to also call `_event_callback` if registered
   - The callback signature: `async def callback(event_type: str, data: dict) -> None`

2. In `services/telegram/bot.py` startup:
   - Import `register_event_callback` from `notifier.py`
   - Register the `SystemNotifier` as the callback:

     ```python
     from services.oracle.oracle_service.engines.notifier import register_event_callback

     async def handle_notifier_event(event_type: str, data: dict) -> None:
         if event_type == "error":
             await system_notifier.notify_api_error(...)
         elif event_type == "balance_found":
             # Forward to admin channel
             ...
     register_event_callback(handle_notifier_event)
     ```

3. **Deprecation path** — Add comments marking the raw `urllib`-based `send_message()` in `notifier.py` as deprecated in favor of the new bot's `Bot.send_message()`. Do NOT remove it yet (Session 37 polish will handle migration).

4. Wire `devops/alerts/oracle_alerts.py` events through the same callback:
   - When `OracleAlerter` detects CRITICAL/WARNING, it can optionally also call `register_event_callback` to forward structured alerts

**Checkpoint:**

```bash
grep "register_event_callback" services/oracle/oracle_service/engines/notifier.py
grep "event_callback" services/oracle/oracle_service/engines/notifier.py
grep "handle_notifier_event" services/telegram/bot.py
```

---

### Phase 6 — API Event Hooks

**Goal:** Wire API-side events into the notification service.

**Work:**

1. Create a lightweight event emitter in the API layer:
   - Add to `api/app/services/notifications.py` (or extend if exists):

     ```python
     import httpx

     async def emit_telegram_notification(event_type: str, data: dict) -> None:
         """Send notification event to the Telegram service."""
     ```

   - Uses an internal HTTP call to the telegram service (or shared message queue if available)
   - Falls back silently if telegram service is unreachable

2. Wire into API lifecycle:
   - **Startup:** In `api/app/main.py` `@app.on_event("startup")`, call `emit_telegram_notification("startup", {"service": "api", "version": ...})`
   - **Shutdown:** In `@app.on_event("shutdown")`, call `emit_telegram_notification("shutdown", {"service": "api", "reason": "shutdown"})`
   - **New user registration:** In the `POST /api/oracle/users` endpoint handler (or ORM post-create hook), call `emit_telegram_notification("new_user", {"name": ..., "id": ...})`
   - **API errors:** In the global exception handler middleware, track errors and call `emit_telegram_notification("api_error", {...})` for 500-level responses

3. Add `POST /api/telegram/internal/notify` endpoint:
   - Internal-only endpoint (not exposed via nginx, only reachable within Docker network)
   - Accepts `{"event_type": str, "data": dict}`
   - Forwards to `SystemNotifier`
   - Secured with internal service token (simple shared secret between API and telegram containers)

**Checkpoint:**

```bash
grep "emit_telegram_notification" api/app/services/notifications.py
grep "startup" api/app/main.py | head -5
grep "new_user" api/app/routers/oracle_users.py || grep "new_user" api/app/routers/oracle.py
```

---

### Phase 7 — Error Rate Monitoring

**Goal:** Track API error rates and trigger high-error-rate notifications.

**Work:**

1. Add a sliding-window error counter in the API:
   - Use an in-memory deque of timestamps (last 15 minutes)
   - On each 500-level response, append timestamp
   - Periodically (every 60 seconds via background task), compute error rate:
     ```
     error_rate = errors_in_window / total_requests_in_window * 100
     ```
   - If `error_rate > 5.0`, emit `high_error_rate` notification

2. Integration point — hook into the existing exception handler middleware in `api/app/middleware/`:
   - Increment error counter on 500-level responses
   - Increment total counter on all responses

3. Store error rate in `app.state` for the `/admin/stats` endpoint to read.

**Checkpoint:**

```bash
grep "error_rate" api/app/middleware/*.py || echo "Check middleware"
grep "error_rate" api/app/routers/telegram.py
```

---

### Phase 8 — Audit Logging for Admin Actions

**Goal:** Log all admin Telegram commands to `oracle_audit_log`.

**Work:**

1. In each admin command handler, after execution, call the API to log the action:

   ```python
   await http_client.post("/api/audit/log", json={
       "user_id": linked_user_id,
       "action": "telegram_admin_stats",
       "resource_type": "system",
       "success": True,
       "details": {"chat_id": chat_id, "command": "/admin_stats"}
   })
   ```

2. If no audit API endpoint exists yet, add `POST /api/admin/audit` in `api/app/routers/telegram.py`:
   - Requires `admin` scope
   - Inserts into `oracle_audit_log` table
   - Fields: `user_id`, `action`, `resource_type`, `success`, `ip_address` (set to "telegram"), `details` (JSONB)

3. Log these specific actions:
   - `telegram_admin_stats` — when `/admin_stats` is called
   - `telegram_admin_users` — when `/admin_users` is called
   - `telegram_admin_broadcast` — when broadcast is confirmed and sent (include recipient count)
   - `telegram_admin_broadcast_cancelled` — when broadcast is cancelled

**Checkpoint:**

```bash
grep "oracle_audit_log" api/app/routers/telegram.py
grep "telegram_admin" services/telegram/handlers/admin.py
```

---

### Phase 9 — Bot Registration & Wiring

**Goal:** Wire everything together in the bot application.

**Work:**

1. Update `services/telegram/bot.py`:
   - Import and register admin handlers:
     ```python
     from handlers.admin import register_admin_handlers
     register_admin_handlers(app)
     ```
   - Initialize `SystemNotifier` on startup:
     ```python
     system_notifier = SystemNotifier(
         bot=app.bot,
         admin_chat_id=get_admin_chat_id()
     )
     ```
   - Send startup notification:
     ```python
     await system_notifier.notify_startup("telegram-bot", version="1.0.0")
     ```
   - Register shutdown hook:
     ```python
     async def on_shutdown(app):
         await system_notifier.notify_shutdown("telegram-bot", "graceful shutdown")
     ```

2. Update `services/telegram/handlers/__init__.py` to export admin handlers.

3. Update `docker-compose.yml`:
   - Add `NPS_ADMIN_CHAT_ID` environment variable to telegram service
   - Ensure telegram service has network access to API service (should already exist from Session 33)

**Checkpoint:**

```bash
grep "register_admin_handlers" services/telegram/bot.py
grep "SystemNotifier" services/telegram/bot.py
grep "NPS_ADMIN_CHAT_ID" docker-compose.yml
```

---

### Phase 10 — Tests

**Goal:** Comprehensive test coverage for all new functionality.

**Work:**

1. Create `services/telegram/tests/test_admin.py`:

   ```
   test_admin_stats_returns_formatted_message
   test_admin_stats_rejects_non_admin
   test_admin_users_returns_paginated_list
   test_admin_users_pagination_buttons
   test_admin_users_rejects_non_admin
   test_admin_broadcast_shows_confirmation
   test_admin_broadcast_send_callback
   test_admin_broadcast_cancel_callback
   test_admin_broadcast_no_message_shows_usage
   test_admin_broadcast_rejects_non_admin
   test_admin_broadcast_rate_limiting
   test_is_admin_with_admin_account
   test_is_admin_with_regular_account
   ```

2. Create `services/telegram/tests/test_notifications.py`:

   ```
   test_notify_api_error_sends_message
   test_notify_api_error_cooldown
   test_notify_high_error_rate_sends_alert
   test_notify_high_error_rate_cooldown
   test_notify_new_user_sends_message
   test_notify_startup_sends_message
   test_notify_shutdown_sends_message
   test_notify_reading_milestone_sends_message
   test_graceful_degradation_no_chat_id
   test_graceful_degradation_bot_error
   test_cooldown_expires_after_window
   ```

3. API endpoint tests (extend `api/tests/test_telegram.py` or create):

   ```
   test_admin_stats_endpoint_returns_data
   test_admin_stats_requires_admin_scope
   test_admin_users_endpoint_returns_paginated
   test_admin_users_requires_admin_scope
   test_internal_notify_endpoint_accepts_event
   test_internal_notify_rejects_without_token
   ```

4. Integration tests (extend `integration/tests/`):

   ```
   test_admin_command_flow_end_to_end
   test_notification_on_new_user_registration
   test_notification_on_api_startup
   ```

Run all:

```bash
cd services/telegram && python3 -m pytest tests/test_admin.py -v
cd services/telegram && python3 -m pytest tests/test_notifications.py -v
cd api && python3 -m pytest tests/test_telegram.py -v
python3 -m pytest integration/tests/ -v -k "admin or notification"
```

---

## TESTS SUMMARY

| #   | Test                                          | File                    | What It Verifies                                         |
| --- | --------------------------------------------- | ----------------------- | -------------------------------------------------------- |
| 1   | `test_admin_stats_returns_formatted_message`  | `test_admin.py`         | /admin_stats formats system stats as Telegram Markdown   |
| 2   | `test_admin_stats_rejects_non_admin`          | `test_admin.py`         | Non-admin users get "Access denied"                      |
| 3   | `test_admin_users_returns_paginated_list`     | `test_admin.py`         | /admin_users shows numbered user list                    |
| 4   | `test_admin_users_pagination_buttons`         | `test_admin.py`         | Inline keyboard nav works for user pages                 |
| 5   | `test_admin_broadcast_shows_confirmation`     | `test_admin.py`         | Broadcast shows preview with Send/Cancel buttons         |
| 6   | `test_admin_broadcast_send_callback`          | `test_admin.py`         | Confirming broadcast sends to all linked users           |
| 7   | `test_admin_broadcast_cancel_callback`        | `test_admin.py`         | Cancelling broadcast edits message                       |
| 8   | `test_admin_broadcast_rejects_non_admin`      | `test_admin.py`         | Non-admin users cannot broadcast                         |
| 9   | `test_notify_api_error_sends_message`         | `test_notifications.py` | API error alert is sent to admin channel                 |
| 10  | `test_notify_api_error_cooldown`              | `test_notifications.py` | Duplicate alerts suppressed within 5-min window          |
| 11  | `test_notify_high_error_rate_sends_alert`     | `test_notifications.py` | High error rate triggers admin alert                     |
| 12  | `test_notify_new_user_sends_message`          | `test_notifications.py` | New user registration sends notification                 |
| 13  | `test_notify_startup_sends_message`           | `test_notifications.py` | Service startup sends notification                       |
| 14  | `test_notify_shutdown_sends_message`          | `test_notifications.py` | Service shutdown sends notification                      |
| 15  | `test_graceful_degradation_no_chat_id`        | `test_notifications.py` | Missing chat ID logs warning, no crash                   |
| 16  | `test_cooldown_expires_after_window`          | `test_notifications.py` | Alerts resume after cooldown window passes               |
| 17  | `test_admin_stats_endpoint_returns_data`      | `test_telegram.py`      | API stats endpoint returns correct JSON shape            |
| 18  | `test_admin_stats_requires_admin_scope`       | `test_telegram.py`      | Non-admin tokens get 403                                 |
| 19  | `test_admin_users_endpoint_returns_paginated` | `test_telegram.py`      | API users endpoint paginates correctly                   |
| 20  | `test_internal_notify_endpoint_accepts_event` | `test_telegram.py`      | Internal notify endpoint processes events                |
| 21  | `test_admin_command_flow_end_to_end`          | integration             | Full flow: Telegram command → API → response → audit log |
| 22  | `test_notification_on_new_user_registration`  | integration             | Creating user triggers admin notification                |

---

## ACCEPTANCE CRITERIA

- [ ] `/admin_stats` returns formatted system stats to admin-linked Telegram accounts
- [ ] `/admin_stats` rejects non-admin users with "Access denied" message
- [ ] `/admin_users` lists recent users with inline pagination (10 per page)
- [ ] `/admin_broadcast [message]` shows confirmation, sends on confirm, cancels on cancel
- [ ] Broadcast respects Telegram's 30 msg/sec rate limit
- [ ] System notifications arrive in admin channel for: API errors, high error rate, new user, startup, shutdown
- [ ] Cooldown system prevents alert spam (5 min for errors, 15 min for error rate)
- [ ] Missing `NPS_ADMIN_CHAT_ID` falls back to `NPS_CHAT_ID`
- [ ] Missing bot token or chat ID logs warning and skips notification (no crash)
- [ ] All admin commands are logged to `oracle_audit_log`
- [ ] `notifier.py` event callback bridge is functional
- [ ] All 22 tests pass
- [ ] No `any` types in TypeScript, no bare `except:` in Python
- [ ] `ruff check` and `black --check` pass on all modified Python files

---

## ERROR SCENARIOS

| Scenario                                     | Expected Behavior                                                    |
| -------------------------------------------- | -------------------------------------------------------------------- |
| Non-admin calls `/admin_stats`               | Bot replies: "⛔ Access denied. Admin role required."                |
| Non-admin calls `/admin_broadcast`           | Bot replies: "⛔ Access denied. Admin role required."                |
| `/admin_broadcast` with no message           | Bot replies: "Usage: `/admin_broadcast [message]`"                   |
| API unreachable during `/admin_stats`        | Bot replies: "⚠️ Could not fetch stats. API may be down."            |
| No linked users for broadcast                | Bot replies: "No linked users to broadcast to."                      |
| Telegram API rate limit hit during broadcast | Queue remaining messages, retry after delay, report partial delivery |
| `NPS_ADMIN_CHAT_ID` not set                  | Fall back to `NPS_CHAT_ID`; if also unset, log warning and skip      |
| Bot token invalid                            | Log error on startup, disable notifications, bot still starts        |
| Database unreachable during stats query      | API returns 503, bot shows "Service temporarily unavailable"         |
| Notification send failure                    | Log error, increment failure counter, continue (never crash)         |

---

## ARCHITECTURE NOTES

### Admin Command Flow

```
Admin types /admin_stats in Telegram
    ↓
python-telegram-bot dispatches to admin_stats_handler
    ↓
Handler checks is_admin(chat_id) via account-linking lookup
    ↓ (admin confirmed)
Handler calls GET /api/telegram/admin/stats with linked API key
    ↓
API queries PostgreSQL (oracle_users, oracle_readings, oracle_audit_log)
    ↓
Handler formats response as Telegram Markdown
    ↓
Bot sends formatted message to chat
    ↓
Handler logs action to oracle_audit_log via API
```

### Notification Flow

```
API event occurs (new user, error, startup)
    ↓
API calls POST /api/telegram/internal/notify
    ↓
Telegram service receives event
    ↓
SystemNotifier checks cooldown for event type
    ↓ (not in cooldown)
SystemNotifier formats message from template
    ↓
Bot.send_message() to admin_chat_id
```

### Notifier Bridge Flow

```
Legacy notifier.py notify_error() called
    ↓
Existing logic runs (preserving legacy behavior)
    ↓
_event_callback invoked if registered
    ↓
Event forwarded to SystemNotifier
    ↓
Admin channel receives structured alert
```

### Broadcast Flow

```
Admin types /admin_broadcast Hello everyone!
    ↓
Bot shows confirmation with inline keyboard [Send] [Cancel]
    ↓ (Admin clicks Send)
Bot queries all linked Telegram chat IDs from API
    ↓
Bot sends message to each chat ID (rate-limited: 30/sec)
    ↓
Bot reports delivery summary: "Sent to X/Y users"
    ↓
Action logged to oracle_audit_log with recipient count
```

---

## DEPENDENCIES GRAPH

```
Session 33 (Bot Core)
    ├── Account linking (admin verification depends on this)
    ├── Bot Application lifecycle (handler registration)
    └── Docker networking (API ↔ Telegram communication)

Session 35 (Daily Bot)
    ├── Scheduler infrastructure (shared scheduling patterns)
    └── api/app/routers/telegram.py (we extend this)

Session 2 (Auth)
    ├── JWT + API key auth (admin scope verification)
    └── Role hierarchy (admin > user > readonly)

This Session (36)
    ├── Admin commands → Session 37 depends on this
    ├── Notification service → Session 37 polishes this
    └── Notifier bridge → Session 37 completes migration
```

---

## HANDOFF TO SESSION 37

After Session 36, the following is ready for Session 37 (Multi-User & Polish):

- Admin commands operational and tested
- System notification service running
- Notifier bridge established (legacy → new)
- Admin channel configured

Session 37 will:

- Add `/compare` multi-user command using the notification/admin infrastructure
- Polish all handlers with comprehensive error messages
- Add rate limiting per user (10 readings/hour)
- Add bilingual support (EN/FA) for bot responses
- Complete notifier.py migration from raw urllib to python-telegram-bot
- Add help text with examples for every command
