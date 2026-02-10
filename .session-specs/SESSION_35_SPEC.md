# SESSION 35 SPEC — Telegram Bot: Daily Auto-Insight

**Block:** Features & Integration (Sessions 32-37)
**Estimated Duration:** 5 hours
**Complexity:** Medium-High
**Dependencies:** Session 34 (reading commands), Session 33 (bot core)

---

## TL;DR

- Build a scheduled daily reading system that delivers a brief Oracle insight to each opted-in Telegram user at their preferred time
- Create `/daily_on`, `/daily_off`, and `/daily_time HH:MM` commands so users control their subscription preferences
- Implement a background scheduler (`services/telegram/scheduler.py`) that runs every 60 seconds, checking which users are due for delivery based on their configured timezone
- Add a new `telegram_daily_preferences` database table storing per-user opt-in status, preferred delivery time, and timezone offset
- Create `api/app/routers/telegram.py` exposing a REST API for managing Telegram settings (used by the frontend Settings page and the bot itself)

---

## OBJECTIVES

1. **Opt-in/out commands** — `/daily_on` enables daily delivery; `/daily_off` disables it. Both confirm the action with a Telegram reply message
2. **Time preference** — `/daily_time HH:MM` sets the user's preferred delivery time (24h format). Default is `08:00`
3. **Scheduler** — Background asyncio task that runs every 60 seconds, queries users whose delivery minute has arrived (accounting for timezone), generates a brief daily reading, and sends it
4. **Daily content** — A shortened daily reading: FC60 stamp of the day, numerology personal-day number, moon phase, and a 2-3 sentence summary — plus an inline "See full reading" button linking to the web app
5. **Settings API** — `api/app/routers/telegram.py` with endpoints to get/update daily preferences (used by the bot handlers and optionally by the frontend Settings page)
6. **Idempotent delivery** — Track the last delivery date per user so a reading is never sent twice for the same calendar day, even if the scheduler restarts

---

## PREREQUISITES

- [ ] Session 33 complete — `services/telegram/` directory exists with `bot.py`, `handlers/`, `Dockerfile`
- [ ] Session 34 complete — `services/telegram/handlers/readings.py` and `services/telegram/formatters.py` exist
- [ ] Telegram bot is running as a Docker service and responding to `/start`, `/help`, `/link`
- [ ] Oracle reading generation is functional (numerology framework importable)
- [ ] Database is accessible from both the API and the Telegram bot service

**Verification:**

```bash
# Telegram service directory exists with bot core
test -f services/telegram/bot.py && echo "OK: bot.py exists"
test -f services/telegram/handlers/readings.py && echo "OK: readings handler exists"
test -f services/telegram/formatters.py && echo "OK: formatter exists"

# Docker service runs
docker-compose ps | grep nps-telegram

# Oracle framework importable
python3 -c "from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator; print('OK')"

# Database accessible
docker-compose exec postgres psql -U nps -d nps -c "SELECT 1;"
```

---

## FILES TO CREATE

### 1. `database/schemas/telegram_daily_preferences.sql`

New table for daily delivery preferences:

```sql
CREATE TABLE IF NOT EXISTS telegram_daily_preferences (
    id SERIAL PRIMARY KEY,

    -- Link to Telegram user (chat_id is the unique Telegram identifier)
    chat_id BIGINT NOT NULL UNIQUE,

    -- Link to NPS oracle_users profile (nullable if user hasn't linked yet)
    user_id INTEGER REFERENCES oracle_users(id) ON DELETE SET NULL,

    -- Daily delivery settings
    daily_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    delivery_time TIME NOT NULL DEFAULT '08:00:00',
    timezone_offset_minutes INTEGER NOT NULL DEFAULT 0,

    -- Delivery tracking
    last_delivered_date DATE,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_telegram_daily_enabled ON telegram_daily_preferences(daily_enabled)
    WHERE daily_enabled = TRUE;
CREATE INDEX idx_telegram_daily_chat_id ON telegram_daily_preferences(chat_id);
```

**Fields explained:**

- `chat_id` — Telegram chat ID (BIGINT, unique per user). Comes from Session 33's account linking
- `user_id` — FK to `oracle_users.id`. Nullable because a Telegram user might opt in before linking their NPS profile
- `daily_enabled` — Whether the user wants daily readings
- `delivery_time` — The time of day (in the user's local timezone) to deliver. Default 08:00
- `timezone_offset_minutes` — UTC offset in minutes (e.g., +3:30 Tehran = +210). Integer to handle half-hour offsets
- `last_delivered_date` — The calendar date (in user's timezone) of the last successful delivery. Prevents duplicate sends

### 2. `database/migrations/013_telegram_daily_preferences.sql`

Migration applying the above schema.

### 3. `database/migrations/013_telegram_daily_preferences_rollback.sql`

Rollback: `DROP TABLE IF EXISTS telegram_daily_preferences CASCADE;`

### 4. `services/telegram/handlers/daily.py`

Command handlers for daily preferences:

```
/daily_on   — Enable daily delivery. Creates or updates preference row. Confirms with message.
/daily_off  — Disable daily delivery. Updates preference row. Confirms with message.
/daily_time — Set delivery time. Validates HH:MM format. Confirms with message showing new time.
/daily_status — Show current daily settings (enabled/disabled, time, timezone).
```

**Implementation details:**

- Each handler receives the `Update` object from `python-telegram-bot`
- Extract `chat_id` from `update.effective_chat.id`
- Use async HTTP calls to the API (`POST /api/telegram/daily/preferences`) to persist changes
- Or use direct database access via SQLAlchemy async session (depends on Session 33's architecture — check `services/telegram/bot.py` for the pattern used)
- Reply messages should be bilingual if the user's locale is known (check Session 33/34 for locale handling pattern)

**Handler signatures:**

```python
async def daily_on_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: ...
async def daily_off_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: ...
async def daily_time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: ...
async def daily_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: ...
```

### 5. `services/telegram/scheduler.py`

Background scheduler that delivers daily readings.

**Architecture:**

```
┌──────────────────────────────────────────────┐
│  Scheduler Loop (runs every 60 seconds)      │
│                                              │
│  1. Get current UTC time                     │
│  2. Query telegram_daily_preferences WHERE   │
│     daily_enabled = TRUE                     │
│     AND last_delivered_date < today_in_tz    │
│     AND delivery_time_in_utc is NOW (±1 min) │
│  3. For each due user:                       │
│     a. Generate brief daily reading          │
│     b. Format as Telegram message            │
│     c. Send via bot.send_message()           │
│     d. Update last_delivered_date            │
│  4. Sleep 60 seconds                         │
│  5. Repeat                                   │
└──────────────────────────────────────────────┘
```

**Delivery time matching algorithm:**

```python
# For each user with daily_enabled=TRUE and last_delivered_date != today:
#   user_local_now = utc_now + timedelta(minutes=user.timezone_offset_minutes)
#   user_local_time = user_local_now.time()
#   if user.delivery_time <= user_local_time < user.delivery_time + 1 minute:
#       → deliver
```

**Key design decisions:**

- The scheduler runs as an asyncio task inside the Telegram bot process (not a separate container)
- It starts when the bot starts (`bot.py` calls `scheduler.start()` during initialization)
- Uses `asyncio.sleep(60)` between iterations (not `apscheduler` — keep dependencies minimal)
- Generates readings via HTTP call to the API (`POST /api/oracle/daily`) or direct framework import
- Rate-limits Telegram sends to 1 per second (Telegram API limit: 30 msgs/sec, but be conservative)
- If a send fails (network error, user blocked bot), log the error and skip — do NOT retry in the same cycle
- If the bot restarts mid-day, the `last_delivered_date` check prevents re-delivery

**Class structure:**

```python
class DailyScheduler:
    def __init__(self, bot: Bot, db_session_factory, api_base_url: str): ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def _run_loop(self) -> None: ...
    async def _check_and_deliver(self) -> None: ...
    async def _generate_daily_insight(self, user_id: int | None, chat_id: int) -> str: ...
    async def _send_daily_message(self, chat_id: int, message: str, reading_date: str) -> bool: ...
    async def _mark_delivered(self, chat_id: int, date: date) -> None: ...
```

### 6. `api/app/routers/telegram.py`

REST API for Telegram settings. Registered at `/api/telegram`.

**Endpoints:**

| Method | Path                                    | Auth          | Description                                        |
| ------ | --------------------------------------- | ------------- | -------------------------------------------------- |
| `GET`  | `/telegram/daily/preferences`           | JWT           | Get current user's daily preferences               |
| `PUT`  | `/telegram/daily/preferences`           | JWT           | Update daily preferences (enabled, time, timezone) |
| `GET`  | `/telegram/daily/preferences/{chat_id}` | API Key (bot) | Get preferences by chat_id (bot internal use)      |
| `PUT`  | `/telegram/daily/preferences/{chat_id}` | API Key (bot) | Update preferences by chat_id (bot internal use)   |
| `GET`  | `/telegram/daily/pending`               | API Key (bot) | List users due for delivery right now              |
| `POST` | `/telegram/daily/delivered`             | API Key (bot) | Mark a user as delivered for today                 |

**Pydantic models (in `api/app/models/telegram.py` — NEW):**

```python
class DailyPreferencesResponse(BaseModel):
    chat_id: int
    user_id: int | None
    daily_enabled: bool
    delivery_time: str  # "HH:MM"
    timezone_offset_minutes: int
    last_delivered_date: str | None  # "YYYY-MM-DD"

class DailyPreferencesUpdate(BaseModel):
    daily_enabled: bool | None = None
    delivery_time: str | None = None  # "HH:MM" validated
    timezone_offset_minutes: int | None = None

class PendingDelivery(BaseModel):
    chat_id: int
    user_id: int | None
    delivery_time: str
    timezone_offset_minutes: int

class DeliveryConfirmation(BaseModel):
    chat_id: int
    delivered_date: str  # "YYYY-MM-DD"
```

### 7. `api/app/models/telegram.py`

Pydantic models as listed above.

### 8. `api/app/orm/telegram_preferences.py`

SQLAlchemy ORM model for `telegram_daily_preferences`:

```python
class TelegramDailyPreference(Base):
    __tablename__ = "telegram_daily_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("oracle_users.id", ondelete="SET NULL"))
    daily_enabled: Mapped[bool] = mapped_column(default=False)
    delivery_time: Mapped[time] = mapped_column(Time, default=time(8, 0))
    timezone_offset_minutes: Mapped[int] = mapped_column(default=0)
    last_delivered_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

### 9. `services/telegram/handlers/__tests__/test_daily.py`

Unit tests for daily command handlers.

### 10. `services/telegram/__tests__/test_scheduler.py`

Unit tests for the scheduler.

### 11. `api/app/routers/__tests__/test_telegram.py`

API endpoint tests.

---

## FILES TO MODIFY

### 1. `services/telegram/bot.py` — MODIFY

Add registration of the new daily command handlers and scheduler startup:

```python
# In the handler registration section (after Session 34's readings handlers):
from services.telegram.handlers.daily import (
    daily_on_handler,
    daily_off_handler,
    daily_time_handler,
    daily_status_handler,
)

app.add_handler(CommandHandler("daily_on", daily_on_handler))
app.add_handler(CommandHandler("daily_off", daily_off_handler))
app.add_handler(CommandHandler("daily_time", daily_time_handler))
app.add_handler(CommandHandler("daily_status", daily_status_handler))

# In the startup section (after bot initialization):
from services.telegram.scheduler import DailyScheduler

scheduler = DailyScheduler(bot=app.bot, db_session_factory=..., api_base_url=...)
# Start scheduler as background task
asyncio.create_task(scheduler.start())
```

### 2. `docker-compose.yml` — VERIFY

Ensure the Telegram bot service (added in Session 33) has:

- `env_file: .env` (for `NPS_BOT_TOKEN`, database creds)
- Network access to `postgres` and `api` services
- Restart policy for scheduler reliability

No changes expected — Session 33 should have configured this correctly. Verify only.

### 3. `api/app/main.py` — MODIFY

Register the new telegram router:

```python
from api.app.routers import telegram

app.include_router(telegram.router, prefix="/api/telegram", tags=["telegram"])
```

Add this BEFORE the static file mount (line 128), consistent with the existing router registration pattern at lines 116-123.

### 4. `.env.example` — MODIFY

Add new environment variables if needed:

```
# Telegram Daily Settings (optional)
TELEGRAM_DAILY_DEFAULT_TIME=08:00
TELEGRAM_FRONTEND_URL=http://localhost:5173
```

The `TELEGRAM_FRONTEND_URL` is used to generate "See full reading" links in daily messages.

### 5. `services/telegram/formatters.py` — MODIFY

Add a daily insight formatter function:

```python
def format_daily_insight(
    reading_date: str,
    fc60_stamp: str,
    personal_day: int,
    moon_phase: str,
    moon_emoji: str,
    summary: str,
    full_reading_url: str,
) -> str:
    """Format a brief daily insight for Telegram delivery."""
    ...
```

This produces a compact Telegram-friendly message (MarkdownV2 or HTML) with:

- Date header
- FC60 stamp of the day
- Personal day number + meaning
- Moon phase + emoji
- 2-3 sentence summary
- Inline keyboard button: "See Full Reading" → links to web app

---

## FILES TO DELETE

None.

---

## IMPLEMENTATION PHASES

### Phase 1: Database Schema (~30 min)

**Create the `telegram_daily_preferences` table.**

1. Write `database/schemas/telegram_daily_preferences.sql` with the schema defined above
2. Write `database/migrations/013_telegram_daily_preferences.sql` applying the schema
3. Write `database/migrations/013_telegram_daily_preferences_rollback.sql`
4. Write `api/app/orm/telegram_preferences.py` — SQLAlchemy ORM model
5. Apply migration:
   ```bash
   docker-compose exec postgres psql -U nps -d nps -f /path/to/013_telegram_daily_preferences.sql
   ```
6. Verify table exists:
   ```bash
   docker-compose exec postgres psql -U nps -d nps -c "\d telegram_daily_preferences"
   ```

**STOP checkpoint:** Table exists with correct columns, indexes, and constraints. ORM model imports without error.

---

### Phase 2: Pydantic Models + API Router (~45 min)

**Build the Telegram settings API.**

1. Create `api/app/models/telegram.py` with the Pydantic models:
   - `DailyPreferencesResponse`
   - `DailyPreferencesUpdate`
   - `PendingDelivery`
   - `DeliveryConfirmation`

2. Create `api/app/routers/telegram.py` with 6 endpoints:
   - `GET /telegram/daily/preferences` — Get preferences for authenticated user (JWT). Look up by user's linked chat_id
   - `PUT /telegram/daily/preferences` — Update preferences for authenticated user (JWT)
   - `GET /telegram/daily/preferences/{chat_id}` — Get preferences by chat_id (API key auth — bot internal)
   - `PUT /telegram/daily/preferences/{chat_id}` — Update preferences by chat_id (API key auth — bot internal)
   - `GET /telegram/daily/pending` — Query users due for delivery NOW (API key auth — scheduler calls this)
   - `POST /telegram/daily/delivered` — Mark delivery complete (API key auth — scheduler calls this)

3. Register router in `api/app/main.py`:

   ```python
   from api.app.routers import telegram
   app.include_router(telegram.router, prefix="/api/telegram", tags=["telegram"])
   ```

4. Validate HH:MM format in `DailyPreferencesUpdate`:

   ```python
   @field_validator("delivery_time")
   @classmethod
   def validate_time_format(cls, v: str | None) -> str | None:
       if v is None:
           return v
       try:
           datetime.strptime(v, "%H:%M")
       except ValueError:
           raise ValueError("delivery_time must be HH:MM format (24h)")
       return v
   ```

5. The `/telegram/daily/pending` endpoint implements the delivery-time matching:
   ```python
   # Pseudocode for pending query:
   utc_now = datetime.utcnow()
   for pref in all_enabled_preferences:
       user_local_now = utc_now + timedelta(minutes=pref.timezone_offset_minutes)
       user_local_time = user_local_now.time()
       today_in_user_tz = user_local_now.date()
       if (pref.last_delivered_date is None or pref.last_delivered_date < today_in_user_tz):
           if pref.delivery_time <= user_local_time:
               yield pref  # due for delivery
   ```

**STOP checkpoint:** All 6 endpoints return correct responses. Swagger docs at `/docs` show the telegram tag. `PUT` updates persist to database. `GET /pending` returns correct users based on time logic.

---

### Phase 3: Daily Command Handlers (~45 min)

**Create the Telegram bot command handlers for daily preferences.**

1. Create `services/telegram/handlers/daily.py` with 4 handlers:

   **`/daily_on` handler:**
   - Get `chat_id` from `update.effective_chat.id`
   - Call API: `PUT /api/telegram/daily/preferences/{chat_id}` with `{"daily_enabled": true}`
   - If no preference row exists, create one with defaults (enabled=true, time=08:00, tz=0)
   - Reply: "Daily insights enabled! You'll receive a reading every day at HH:MM (UTC+X)."
   - Include tip: "Use /daily_time HH:MM to change the delivery time."

   **`/daily_off` handler:**
   - Call API: `PUT /api/telegram/daily/preferences/{chat_id}` with `{"daily_enabled": false}`
   - Reply: "Daily insights disabled. Use /daily_on to re-enable anytime."

   **`/daily_time HH:MM` handler:**
   - Parse time from `context.args[0]` (e.g., "14:30")
   - Validate HH:MM format (00:00 - 23:59)
   - If invalid, reply with usage hint: "Usage: /daily_time HH:MM (24-hour format). Example: /daily_time 08:30"
   - Call API: `PUT /api/telegram/daily/preferences/{chat_id}` with `{"delivery_time": "HH:MM"}`
   - Reply: "Delivery time updated to HH:MM."

   **`/daily_status` handler:**
   - Call API: `GET /api/telegram/daily/preferences/{chat_id}`
   - If no preferences exist, reply: "You haven't set up daily insights yet. Use /daily_on to start."
   - Otherwise, format and reply:
     ```
     Daily Insight Settings:
     Status: Enabled/Disabled
     Time: HH:MM
     Timezone: UTC+X:XX
     Last delivered: YYYY-MM-DD (or "Never")
     ```

2. Register handlers in `services/telegram/bot.py`:

   ```python
   from services.telegram.handlers.daily import (
       daily_on_handler, daily_off_handler,
       daily_time_handler, daily_status_handler,
   )
   app.add_handler(CommandHandler("daily_on", daily_on_handler))
   app.add_handler(CommandHandler("daily_off", daily_off_handler))
   app.add_handler(CommandHandler("daily_time", daily_time_handler))
   app.add_handler(CommandHandler("daily_status", daily_status_handler))
   ```

3. Update the `/help` command output (in Session 33's help handler) to include the new daily commands.

**STOP checkpoint:** All 4 commands respond correctly in Telegram. `/daily_on` creates a preference row. `/daily_off` disables. `/daily_time 14:30` updates time. `/daily_status` shows current settings.

---

### Phase 4: Daily Insight Formatter (~30 min)

**Add a formatter for the daily insight message.**

1. Add `format_daily_insight()` to `services/telegram/formatters.py`:
   - Input: reading date, FC60 stamp, personal day number, moon phase, summary text, web URL
   - Output: Telegram MarkdownV2 (or HTML) formatted message

2. Message structure:

   ```
   🌅 Daily Insight — Feb 10, 2026

   🔢 FC60: [stamp]
   🔮 Personal Day: [number] — [meaning]
   🌙 Moon: [phase] [emoji]

   [2-3 sentence summary]

   [Inline button: "See Full Reading →"]
   ```

3. The inline button uses `InlineKeyboardMarkup` with a URL button:

   ```python
   keyboard = InlineKeyboardMarkup([
       [InlineKeyboardButton("See Full Reading →", url=full_reading_url)]
   ])
   ```

4. Handle Persian locale: if user's locale is FA (check Session 33/34 for locale storage pattern), format the message in Persian with RTL-friendly layout.

**STOP checkpoint:** `format_daily_insight()` produces valid Telegram markup. Test with sample data — verify no MarkdownV2 escaping issues.

---

### Phase 5: Scheduler Implementation (~60 min)

**Build the background scheduler that delivers daily readings.**

1. Create `services/telegram/scheduler.py` with `DailyScheduler` class:

   **`__init__`:**
   - Store bot instance, database session factory, API base URL
   - Initialize `_running = False` flag and `_task: asyncio.Task | None = None`

   **`start()`:**
   - Set `_running = True`
   - Create asyncio task: `self._task = asyncio.create_task(self._run_loop())`
   - Log: "Daily scheduler started"

   **`stop()`:**
   - Set `_running = False`
   - Cancel task if running, await cancellation
   - Log: "Daily scheduler stopped"

   **`_run_loop()`:**

   ```python
   while self._running:
       try:
           await self._check_and_deliver()
       except Exception as exc:
           logger.error("Scheduler cycle error", exc_info=exc)
       await asyncio.sleep(60)
   ```

   **`_check_and_deliver()`:**
   - Call API: `GET /api/telegram/daily/pending` → list of `PendingDelivery`
   - For each pending user:
     a. Generate daily insight (call `_generate_daily_insight`)
     b. Format message (call `format_daily_insight`)
     c. Send via `_send_daily_message`
     d. If send succeeded, call `_mark_delivered`
     e. Sleep 1 second between sends (rate limiting)

   **`_generate_daily_insight(user_id, chat_id)`:**
   - Option A (preferred): Call API `POST /api/oracle/daily` → returns daily reading data
   - Option B (fallback): Import `MasterOrchestrator` directly and generate a lightweight reading
   - Extract: FC60 stamp, personal day number, moon phase, short summary
   - If user has a linked `user_id`, personalize with their birth data
   - If no linked profile, generate a generic daily reading (no personalization)

   **`_send_daily_message(chat_id, message, reading_date)`:**
   - Use `self.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML", reply_markup=keyboard)`
   - Wrap in try/except: catch `telegram.error.Forbidden` (user blocked bot) → disable their daily preference
   - Catch `telegram.error.TelegramError` → log and return False
   - Return True on success

   **`_mark_delivered(chat_id, date)`:**
   - Call API: `POST /api/telegram/daily/delivered` with `{"chat_id": chat_id, "delivered_date": "YYYY-MM-DD"}`

2. Integrate scheduler into `services/telegram/bot.py`:

   ```python
   # In bot startup:
   scheduler = DailyScheduler(
       bot=application.bot,
       db_session_factory=get_db_session,
       api_base_url=os.getenv("API_BASE_URL", "http://api:8000/api"),
   )

   # Start scheduler after bot is initialized:
   async def post_init(application: Application) -> None:
       await scheduler.start()

   async def post_shutdown(application: Application) -> None:
       await scheduler.stop()

   application.post_init = post_init
   application.post_shutdown = post_shutdown
   ```

3. Handle edge cases:
   - **Bot restart:** `last_delivered_date` prevents re-delivery
   - **User blocked bot:** `Forbidden` exception → auto-disable daily preference
   - **API down:** Log error, skip cycle, retry next minute
   - **Timezone changes (DST):** Users set offset manually; no automatic DST handling (documented limitation)
   - **Many users:** Process sequentially with 1-second delays. For 1000 users, one cycle takes ~17 minutes — well within the 60-second check window since each cycle processes ALL pending users, not just those due in the current minute

**STOP checkpoint:** Scheduler starts with the bot. Create a test user with `daily_enabled=true` and `delivery_time` set to 1 minute from now. Verify the reading is delivered. Verify `last_delivered_date` is updated. Restart bot — verify no duplicate delivery.

---

### Phase 6: Write Tests (~60 min)

**Write comprehensive tests for all new components.**

#### Test File: `services/telegram/handlers/__tests__/test_daily.py`

| #   | Test Name                          | What It Tests                                                                   |
| --- | ---------------------------------- | ------------------------------------------------------------------------------- |
| 1   | `test_daily_on_creates_preference` | `/daily_on` creates a new preference row with `daily_enabled=True`              |
| 2   | `test_daily_on_enables_existing`   | `/daily_on` when preference exists but disabled → sets `daily_enabled=True`     |
| 3   | `test_daily_off_disables`          | `/daily_off` sets `daily_enabled=False`                                         |
| 4   | `test_daily_off_when_not_exists`   | `/daily_off` when no preference exists → creates disabled row, friendly message |
| 5   | `test_daily_time_valid`            | `/daily_time 14:30` updates `delivery_time` to 14:30                            |
| 6   | `test_daily_time_invalid_format`   | `/daily_time abc` returns error message with usage hint                         |
| 7   | `test_daily_time_out_of_range`     | `/daily_time 25:00` returns error message                                       |
| 8   | `test_daily_time_no_args`          | `/daily_time` with no argument returns usage hint                               |
| 9   | `test_daily_status_enabled`        | `/daily_status` shows enabled state with correct time and timezone              |
| 10  | `test_daily_status_not_configured` | `/daily_status` when no preference exists shows setup hint                      |

#### Test File: `services/telegram/__tests__/test_scheduler.py`

| #   | Test Name                                | What It Tests                                                   |
| --- | ---------------------------------------- | --------------------------------------------------------------- |
| 11  | `test_scheduler_starts_and_stops`        | Scheduler starts asyncio task, stops cleanly                    |
| 12  | `test_scheduler_delivers_to_due_user`    | User with matching delivery time gets a message                 |
| 13  | `test_scheduler_skips_already_delivered` | User with `last_delivered_date = today` is skipped              |
| 14  | `test_scheduler_handles_blocked_user`    | `Forbidden` error → user's daily preference is disabled         |
| 15  | `test_scheduler_handles_api_error`       | API failure → logs error, continues to next user                |
| 16  | `test_scheduler_respects_timezone`       | User in UTC+3:30 at 08:00 local time gets delivery at 04:30 UTC |
| 17  | `test_scheduler_rate_limits`             | Multiple users → 1-second delay between sends                   |
| 18  | `test_scheduler_no_duplicate_on_restart` | Restart scheduler mid-day → no re-delivery                      |

#### Test File: `api/app/routers/__tests__/test_telegram.py`

| #   | Test Name                                 | What It Tests                                                    |
| --- | ----------------------------------------- | ---------------------------------------------------------------- |
| 19  | `test_get_preferences_by_chat_id`         | `GET /telegram/daily/preferences/{chat_id}` returns correct data |
| 20  | `test_update_preferences`                 | `PUT /telegram/daily/preferences/{chat_id}` updates fields       |
| 21  | `test_update_preferences_invalid_time`    | Invalid time format returns 422                                  |
| 22  | `test_get_pending_deliveries`             | `GET /telegram/daily/pending` returns only due users             |
| 23  | `test_mark_delivered`                     | `POST /telegram/daily/delivered` updates `last_delivered_date`   |
| 24  | `test_pending_excludes_already_delivered` | Users delivered today not in pending list                        |
| 25  | `test_pending_respects_timezone_offset`   | Timezone math is correct in pending query                        |

**Test patterns:**

- Use `pytest-asyncio` for async handler tests
- Mock `telegram.Bot.send_message` to avoid real Telegram API calls
- Mock HTTP calls to API endpoints using `httpx` or `aioresponses`
- Use a test database (or SQLite in-memory) for preference storage tests
- Use `freezegun` or `time-machine` to freeze time for scheduler tests

**STOP checkpoint:** All 25 tests pass. `pytest services/telegram/ -v` and `pytest api/app/routers/__tests__/test_telegram.py -v` both green.

---

### Phase 7: Final Verification (~15 min)

**End-to-end verification of the complete daily auto-insight system.**

1. Start all services:

   ```bash
   docker-compose up -d
   ```

2. Create a test user preference via API:

   ```bash
   curl -X PUT http://localhost:8000/api/telegram/daily/preferences/123456789 \
     -H "Authorization: Bearer <api_key>" \
     -H "Content-Type: application/json" \
     -d '{"daily_enabled": true, "delivery_time": "HH:MM", "timezone_offset_minutes": 0}'
   ```

   (Set `delivery_time` to 1 minute from now)

3. Wait for scheduler cycle (max 60 seconds) and verify:
   - Message received in Telegram chat
   - Message contains FC60 stamp, personal day, moon phase
   - "See Full Reading" button present and links to web app
   - `last_delivered_date` updated in database

4. Run all commands:

   ```
   /daily_on → "Daily insights enabled!"
   /daily_off → "Daily insights disabled."
   /daily_time 09:30 → "Delivery time updated to 09:30."
   /daily_status → Shows settings
   ```

5. Run full test suite:

   ```bash
   pytest services/telegram/ -v
   pytest api/app/routers/__tests__/test_telegram.py -v
   ```

6. Verify no regressions:
   ```bash
   pytest api/ -v
   pytest integration/ -v -s
   ```

**STOP checkpoint:** Daily reading delivered on schedule. All commands work. All 25 tests pass. No regressions.

---

## ACCEPTANCE CRITERIA

- [ ] `telegram_daily_preferences` table exists with correct schema, indexes, and constraints
- [ ] `/daily_on` command creates/enables daily delivery preference
- [ ] `/daily_off` command disables daily delivery preference
- [ ] `/daily_time HH:MM` command updates delivery time with validation
- [ ] `/daily_status` command shows current settings
- [ ] Scheduler runs every 60 seconds and delivers to due users
- [ ] Daily insight message contains: FC60 stamp, personal day, moon phase, summary, "See Full Reading" button
- [ ] `last_delivered_date` prevents duplicate delivery on the same calendar day
- [ ] Timezone offset is respected in delivery time calculation
- [ ] Blocked-bot detection auto-disables daily preference
- [ ] API endpoints at `/api/telegram/daily/*` work correctly with proper auth
- [ ] All 25 tests pass
- [ ] No regressions in existing tests

**Verification commands:**

```bash
# Database table exists
docker-compose exec postgres psql -U nps -d nps -c "\d telegram_daily_preferences"

# API endpoints respond
curl http://localhost:8000/api/telegram/daily/preferences/123 -H "Authorization: Bearer <key>"

# Tests pass
pytest services/telegram/ -v
pytest api/app/routers/__tests__/test_telegram.py -v

# No regressions
pytest api/ -v
pytest integration/ -v -s
```

---

## ERROR SCENARIOS

### Scenario 1: Telegram API rate limit exceeded

**Trigger:** Too many messages sent too quickly (Telegram limit: 30 msgs/sec global, 1 msg/sec per chat)

**Recovery:**

1. Scheduler catches `RetryAfter` exception from `python-telegram-bot`
2. Extracts `retry_after` seconds from the exception
3. Sleeps for that duration before continuing
4. Logs warning: "Rate limited by Telegram, sleeping {N} seconds"
5. Resumes delivery queue from where it left off

### Scenario 2: User blocks the bot after opting in

**Trigger:** User sends /daily_on, then blocks the bot in Telegram

**Recovery:**

1. Scheduler catches `telegram.error.Forbidden` when sending message
2. Automatically sets `daily_enabled = false` for that chat_id
3. Logs info: "User {chat_id} blocked bot, disabling daily delivery"
4. Continues to next user in queue
5. If user later unblocks and sends /daily_on again, preference is re-enabled

### Scenario 3: Database connection lost during scheduler cycle

**Trigger:** PostgreSQL goes down or connection pool exhausted

**Recovery:**

1. `_check_and_deliver()` wrapped in try/except
2. Catches `OperationalError` / `ConnectionError`
3. Logs error: "Database unavailable, skipping delivery cycle"
4. Sleeps 60 seconds and retries on next cycle
5. No users miss deliveries permanently — they'll be caught on the next successful cycle since `last_delivered_date` hasn't been updated

### Scenario 4: API service unavailable during scheduler query

**Trigger:** API gateway is restarting or unhealthy

**Recovery:**

1. HTTP call to `/api/telegram/daily/pending` fails with connection error or 5xx
2. Scheduler logs warning: "API unavailable, skipping cycle"
3. Retries on next 60-second cycle
4. After 5 consecutive failures, logs error at higher level
5. No data loss — pending deliveries accumulate and are processed when API recovers

---

## HANDOFF

### What Session 36 Receives

Session 36 ("Telegram Bot: Admin Commands & Notifications") builds on this session's foundation:

1. **Working scheduler infrastructure** — Session 36 can reuse the `DailyScheduler` pattern for system notification scheduling
2. **`telegram_daily_preferences` table** — Admin broadcast in Session 36 can query this table to find all linked Telegram users
3. **`api/app/routers/telegram.py`** — Session 36 adds admin endpoints to this router (e.g., `/telegram/admin/broadcast`, `/telegram/admin/stats`)
4. **Handler registration pattern** — Session 36 follows the same pattern to register `/admin_stats`, `/admin_users`, `/admin_broadcast` handlers in `bot.py`
5. **Formatter pattern** — Session 36 adds admin-specific formatters to `services/telegram/formatters.py`

### Files Session 36 Will Use

| File                                                 | How Session 36 Uses It                 |
| ---------------------------------------------------- | -------------------------------------- |
| `services/telegram/bot.py`                           | Add admin command handlers             |
| `services/telegram/scheduler.py`                     | Reference for background task pattern  |
| `services/telegram/formatters.py`                    | Add admin notification formatters      |
| `api/app/routers/telegram.py`                        | Add admin endpoints                    |
| `telegram_daily_preferences` table                   | Query for broadcast recipient list     |
| `services/oracle/oracle_service/engines/notifier.py` | Integrate legacy notifier with new bot |

### State After Session 35

```
services/telegram/
├── bot.py                          # Main bot (Session 33) + daily handlers registered
├── scheduler.py                    # NEW — Background daily delivery scheduler
├── formatters.py                   # Session 34 + daily insight formatter added
├── handlers/
│   ├── __init__.py                 # Session 33
│   ├── core.py                     # Session 33 (/start, /help, /link, /status)
│   ├── readings.py                 # Session 34 (/time, /name, /question, /daily, /history)
│   └── daily.py                    # NEW — /daily_on, /daily_off, /daily_time, /daily_status
├── Dockerfile                      # Session 33
└── __tests__/
    ├── test_scheduler.py           # NEW — 8 scheduler tests
    └── handlers/__tests__/
        └── test_daily.py           # NEW — 10 handler tests

api/app/
├── routers/
│   └── telegram.py                 # NEW — 6 endpoints for daily preferences
├── models/
│   └── telegram.py                 # NEW — Pydantic models
├── orm/
│   └── telegram_preferences.py     # NEW — SQLAlchemy ORM model
└── routers/__tests__/
    └── test_telegram.py            # NEW — 7 API tests

database/
├── schemas/
│   └── telegram_daily_preferences.sql  # NEW
└── migrations/
    ├── 013_telegram_daily_preferences.sql          # NEW
    └── 013_telegram_daily_preferences_rollback.sql # NEW
```
