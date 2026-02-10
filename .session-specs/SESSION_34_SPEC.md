# SESSION 34 SPEC: Telegram Bot — Reading Commands

**Block:** Features & Integration (Sessions 32-37)
**Estimated Duration:** 4-5 hours
**Complexity:** High
**Dependencies:** Session 33 (Telegram bot core setup)

---

## TL;DR

- Build 5 reading command handlers (`/time`, `/name`, `/question`, `/daily`, `/history`) for the Telegram bot
- Create a Telegram Markdown formatter that renders reading results beautifully with sections, numbers, and patterns
- Implement progressive message editing: show status updates while reading generates ("Calculating..." → "Consulting AI..." → "Ready!")
- Add inline keyboard buttons after each reading: "Full Details" | "Rate" | "Share"
- Build on the Session 33 bot foundation (account linking, `python-telegram-bot` async, Docker service)

---

## OBJECTIVES

1. Implement 5 Telegram command handlers that call the NPS API to generate readings
2. Format reading results into rich Telegram MarkdownV2 messages with sections, emojis, and structure
3. Show real-time progress by editing the bot message during reading generation
4. Display inline keyboard buttons after readings for follow-up actions
5. Handle `/history` with paginated inline buttons showing last 5 readings
6. Support both linked accounts (using profile data) and anonymous usage (manual input)
7. Write 12+ tests covering command handlers, formatting, progress updates, and error cases

---

## PREREQUISITES

- [ ] Session 33 complete: Telegram bot service running in Docker with `/start`, `/link`, `/help`, `/status`, `/profile` commands
- [ ] Bot service directory exists at `services/telegram/`
- [ ] Bot communicates with NPS API via HTTP (not direct database access)
- [ ] API reading endpoints exist: `POST /api/oracle/reading`, `POST /api/oracle/question`, `POST /api/oracle/name`, `GET /api/oracle/daily`, `GET /api/oracle/readings`
- [ ] Account linking stores API key per Telegram chat ID

Verification:

```bash
test -d services/telegram && echo "OK" || echo "MISSING"
test -f services/telegram/bot.py && echo "OK" || echo "MISSING"
test -f services/telegram/handlers/__init__.py && echo "OK" || echo "MISSING"
test -f api/app/routers/oracle.py && echo "OK" || echo "MISSING"
test -f api/app/services/oracle_reading.py && echo "OK" || echo "MISSING"
```

---

## FILES TO CREATE

- `services/telegram/handlers/readings.py` — Reading command handlers (/time, /name, /question, /daily, /history)
- `services/telegram/formatters.py` — Telegram MarkdownV2 formatter for reading results
- `services/telegram/api_client.py` — HTTP client wrapper for calling NPS API from the bot
- `services/telegram/keyboards.py` — Inline keyboard builder for reading follow-up actions
- `services/telegram/tests/__init__.py` — Test package init
- `services/telegram/tests/test_readings.py` — Reading handler tests
- `services/telegram/tests/test_formatters.py` — Formatter tests
- `services/telegram/tests/test_api_client.py` — API client tests

## FILES TO MODIFY

| File                                     | Current Lines        | Action | Notes                                               |
| ---------------------------------------- | -------------------- | ------ | --------------------------------------------------- |
| `services/telegram/bot.py`               | ~varies (Session 33) | MODIFY | Register reading command handlers                   |
| `services/telegram/handlers/__init__.py` | ~varies (Session 33) | MODIFY | Export reading handlers                             |
| `docker-compose.yml`                     | 224                  | VERIFY | Telegram service already added in Session 33        |
| `api/app/routers/oracle.py`              | 627                  | VERIFY | Reading endpoints already exist — no changes needed |
| `api/app/services/oracle_reading.py`     | 579                  | VERIFY | Reading service already exists — no changes needed  |

## FILES TO DELETE

None

---

## PHASE 1: API Client for Bot-to-API Communication (30 min)

### Tasks

1. Create `services/telegram/api_client.py` — a lightweight async HTTP client that the bot uses to call the NPS API
2. The client must handle authentication (pass the user's linked API key in the Authorization header)
3. Include timeout handling, error classification (auth error vs server error vs network error), and retry logic

### Code Pattern

```python
"""HTTP client for bot → NPS API communication."""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

API_BASE_URL = "http://api:8000/api"  # Docker service name
API_TIMEOUT = 30.0  # readings can take time with AI interpretation


@dataclass
class APIResponse:
    success: bool
    data: dict | None = None
    error: str | None = None
    status_code: int = 0


class NPSAPIClient:
    """Async HTTP client for NPS API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=API_TIMEOUT,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def create_reading(self, datetime_str: str | None = None) -> APIResponse:
        """POST /oracle/reading"""
        ...

    async def create_question(self, question: str) -> APIResponse:
        """POST /oracle/question"""
        ...

    async def create_name_reading(self, name: str) -> APIResponse:
        """POST /oracle/name"""
        ...

    async def get_daily(self, date: str | None = None) -> APIResponse:
        """GET /oracle/daily"""
        ...

    async def list_readings(self, limit: int = 5, offset: int = 0) -> APIResponse:
        """GET /oracle/readings"""
        ...

    async def close(self):
        await self._client.aclose()
```

> **Key design decision:** The bot NEVER touches the database directly. All communication goes through the API layer, respecting the architecture rule: Frontend/Telegram → API → Services → Database.

### Checkpoint 1

```bash
cd services/telegram && python -c "from api_client import NPSAPIClient; print('OK')"
```

---

## PHASE 2: Telegram MarkdownV2 Formatter (45 min)

### Tasks

1. Create `services/telegram/formatters.py` with functions that convert API response dicts into beautifully formatted Telegram MarkdownV2 messages
2. Handle MarkdownV2 escaping (Telegram requires escaping of special chars: `_`, `*`, `[`, `]`, `(`, `)`, `~`, `` ` ``, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`)
3. Create formatters for each reading type: time reading, question reading, name reading, daily insight, and history list
4. Support Persian text rendering (RTL is handled by Telegram natively)
5. Keep messages under Telegram's 4096 character limit — truncate with "See full reading on web" link if needed

### Code Pattern

```python
"""Telegram MarkdownV2 formatters for reading results."""

import re

_ESCAPE_CHARS = r"_*[]()~`>#+-=|{}.!"


def _escape(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    return re.sub(r"([" + re.escape(_ESCAPE_CHARS) + r"])", r"\\\1", str(text))


def format_time_reading(data: dict) -> str:
    """Format a full oracle time reading for Telegram.

    Sections: FC60 stamp, Numerology, Moon, Zodiac, Patterns, AI Interpretation.
    """
    ...


def format_question_reading(data: dict) -> str:
    """Format a question/answer reading.

    Shows: question, answer (yes/no/maybe), sign number, confidence, interpretation.
    """
    ...


def format_name_reading(data: dict) -> str:
    """Format a name cipher reading.

    Shows: destiny number, soul urge, personality, letter breakdown.
    """
    ...


def format_daily_insight(data: dict) -> str:
    """Format the daily insight message.

    Shows: date, insight text, lucky numbers, optimal activity.
    """
    ...


def format_history_item(reading: dict, index: int) -> str:
    """Format a single history entry for the history list."""
    ...


def format_history_list(readings: list[dict], total: int) -> str:
    """Format the reading history list.

    Shows: numbered list of recent readings with type, date, excerpt.
    """
    ...


def format_progress(step: int, total: int, message: str) -> str:
    """Format a progress update message.

    Uses emojis for visual progress: ⏳ → 🔮 → ✨ → ✅
    """
    STEPS = ["⏳", "🔮", "✨", "✅"]
    icon = STEPS[min(step, len(STEPS) - 1)]
    bar = "▓" * step + "░" * (total - step)
    return f"{icon} {_escape(message)}\n`{bar}` {step}/{total}"
```

### Formatting Guidelines

- **Time reading:** Header with FC60 stamp, then sections for Numerology (life path, personal year), Moon phase with emoji, Zodiac sign, Chinese animal, Synchronicities, and AI interpretation (truncated if long)
- **Question reading:** Bold question, large answer emoji (✅/❌/🤔), sign number, confidence bar, interpretation
- **Name reading:** Name in bold, destiny/soul/personality numbers in a table-like format, letter breakdown
- **Daily insight:** Date header, insight text, lucky numbers as inline code, optimal activity
- **History list:** Numbered list with type emoji (🕐/❓/📛/🌟), date, and first 40 chars of content

### Checkpoint 2

```bash
cd services/telegram && python -c "
from formatters import format_daily_insight, _escape
result = format_daily_insight({'date': '2026-02-10', 'insight': 'Trust the process', 'lucky_numbers': ['3', '7'], 'optimal_activity': 'meditation'})
assert len(result) > 0
print('OK:', len(result), 'chars')
"
```

---

## PHASE 3: Inline Keyboard Builder (20 min)

### Tasks

1. Create `services/telegram/keyboards.py` with functions that generate `InlineKeyboardMarkup` objects for reading follow-up actions
2. After each reading: show "📊 Full Details" | "⭐ Rate" | "📤 Share" buttons
3. For history: show per-reading "View" buttons and a "Load More" button
4. Callback data format: `reading:{action}:{reading_id}` (e.g., `reading:details:42`)

### Code Pattern

```python
"""Inline keyboard builders for Telegram bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def reading_actions_keyboard(reading_id: int | None = None) -> InlineKeyboardMarkup:
    """Post-reading action buttons."""
    buttons = []
    if reading_id:
        buttons.append([
            InlineKeyboardButton("📊 Full Details", callback_data=f"reading:details:{reading_id}"),
            InlineKeyboardButton("⭐ Rate", callback_data=f"reading:rate:{reading_id}"),
        ])
        buttons.append([
            InlineKeyboardButton("📤 Share", callback_data=f"reading:share:{reading_id}"),
        ])
    buttons.append([
        InlineKeyboardButton("🔮 New Reading", callback_data="reading:new"),
    ])
    return InlineKeyboardMarkup(buttons)


def history_keyboard(readings: list[dict], has_more: bool) -> InlineKeyboardMarkup:
    """History navigation keyboard with per-reading view buttons."""
    ...


def reading_type_keyboard() -> InlineKeyboardMarkup:
    """Choose reading type when user sends /reading without args."""
    ...
```

### Checkpoint 3

```bash
cd services/telegram && python -c "
from keyboards import reading_actions_keyboard
kb = reading_actions_keyboard(42)
print('OK:', len(kb.inline_keyboard), 'rows')
"
```

---

## PHASE 4: Reading Command Handlers (90 min)

### Tasks

1. Create `services/telegram/handlers/readings.py` with async handler functions for each reading command
2. Each handler follows this pattern:
   - Parse command arguments
   - Send initial "calculating" message
   - Call API via `NPSAPIClient`
   - Edit message with progress updates
   - Format the result using `formatters`
   - Edit message with final formatted reading + inline keyboard
3. Handle errors gracefully: show user-friendly error messages, log technical details

### 4.1 `/time HH:MM` — Time Reading

```python
async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a time-based oracle reading.

    Usage: /time HH:MM [YYYY-MM-DD]
    If no date given, uses today.
    If no time given, uses current time.
    """
    # 1. Parse args
    args = context.args or []
    time_str = args[0] if args else None
    date_str = args[1] if len(args) > 1 else None

    # 2. Validate time format (HH:MM)
    if time_str and not re.match(r"^\d{2}:\d{2}$", time_str):
        await update.message.reply_text("Usage: /time HH:MM [YYYY-MM-DD]")
        return

    # 3. Get user's API key from linked account
    api_key = get_user_api_key(update.effective_chat.id)
    if not api_key:
        await update.message.reply_text("Link your account first: /link <api_key>")
        return

    # 4. Send progress message
    msg = await update.message.reply_text("⏳ Calculating FC60 stamp...")

    # 5. Call API
    client = NPSAPIClient(api_key)
    try:
        iso_datetime = build_iso_datetime(time_str, date_str)
        result = await client.create_reading(iso_datetime)
    finally:
        await client.close()

    # 6. Handle error
    if not result.success:
        await msg.edit_text(f"❌ Error: {result.error}")
        return

    # 7. Progress update
    await msg.edit_text("🔮 Formatting reading...")

    # 8. Format and send
    text = format_time_reading(result.data)
    keyboard = reading_actions_keyboard(result.data.get("reading_id"))
    await msg.edit_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
```

### 4.2 `/name [name]` — Name Reading

- If `[name]` is provided, use it directly
- If no name and user has a linked profile, use the profile name
- Call `POST /api/oracle/name` with the name
- Format with `format_name_reading()`

### 4.3 `/question [text]` — Question Reading

- Require question text (show usage if empty)
- Call `POST /api/oracle/question` with the question
- Format with `format_question_reading()`
- Show answer prominently with emoji (✅ Yes / ❌ No / 🤔 Maybe)

### 4.4 `/daily` — Daily Reading

- No arguments needed
- Call `GET /api/oracle/daily` (optionally with today's date)
- Format with `format_daily_insight()`
- Lighter format than full reading — meant as a quick daily check-in

### 4.5 `/history` — Reading History

- Call `GET /api/oracle/readings?limit=5`
- Format with `format_history_list()`
- Show inline buttons for each reading ("View #1", "View #2", etc.)
- Show "Load More" button if `total > 5`
- Callback handler: when user clicks "View #N", fetch that reading and display full details

### 4.6 Callback Query Handler

Register a callback query handler for `reading:*` patterns:

- `reading:details:{id}` — Fetch full reading and display formatted
- `reading:rate:{id}` — Show rating buttons (1-5 stars) [stub for now, log selection]
- `reading:share:{id}` — Generate a share-friendly text version
- `reading:new` — Show reading type selector keyboard
- `history:view:{id}` — Fetch and display a specific history reading
- `history:more:{offset}` — Load next page of history

### Checkpoint 4

```bash
cd services/telegram && python -c "
from handlers.readings import time_command, name_command, question_command, daily_command, history_command
print('All handlers imported OK')
"
```

---

## PHASE 5: User Account Helpers (30 min)

### Tasks

1. Create helper functions that retrieve the linked API key for a given Telegram chat ID
2. Create helper to get the user's Oracle profile (name, birthday) for commands that need it
3. These helpers interact with the bot's local storage (set up in Session 33) — NOT directly with the database

### Code Pattern

```python
# In services/telegram/handlers/readings.py or a shared utils module

def get_user_api_key(chat_id: int) -> str | None:
    """Retrieve the linked API key for a Telegram chat ID.

    Returns None if the user hasn't linked their account.
    Uses the storage mechanism established in Session 33.
    """
    ...


async def get_user_profile(api_key: str) -> dict | None:
    """Fetch the user's Oracle profile via API.

    Returns {name, birthday, ...} or None if no profile exists.
    """
    ...


def build_iso_datetime(time_str: str | None, date_str: str | None) -> str | None:
    """Build ISO 8601 datetime string from time and optional date.

    If time_str is None, returns None (API defaults to now).
    If date_str is None, uses today's date.
    """
    ...
```

### Checkpoint 5

```bash
cd services/telegram && python -c "
from handlers.readings import build_iso_datetime
result = build_iso_datetime('14:30', '2026-02-10')
assert result == '2026-02-10T14:30:00'
print('OK:', result)
"
```

---

## PHASE 6: Register Handlers in Bot (20 min)

### Tasks

1. Modify `services/telegram/bot.py` to register the 5 new command handlers
2. Register the callback query handler for `reading:*` patterns
3. Set bot commands list via `set_my_commands()` so Telegram shows command suggestions

### Code Pattern

```python
# In services/telegram/bot.py — additions to existing setup

from handlers.readings import (
    time_command,
    name_command,
    question_command,
    daily_command,
    history_command,
    reading_callback_handler,
)

# Inside the application setup function:
app.add_handler(CommandHandler("time", time_command))
app.add_handler(CommandHandler("name", name_command))
app.add_handler(CommandHandler("question", question_command))
app.add_handler(CommandHandler("daily", daily_command))
app.add_handler(CommandHandler("history", history_command))
app.add_handler(CallbackQueryHandler(reading_callback_handler, pattern=r"^(reading|history):"))
```

### Checkpoint 6

```bash
cd services/telegram && python -c "
import bot
print('Bot module loads without errors')
"
```

---

## PHASE 7: Progress Message Editing (30 min)

### Tasks

1. Create a progress helper that encapsulates the pattern of editing a Telegram message through multiple steps
2. Handle Telegram API rate limits (max ~30 edits/second) — add small delays between edits
3. Handle the case where the user deletes the message before editing completes (catch `BadRequest` exceptions)

### Code Pattern

```python
"""Progressive message editing for reading generation."""

import asyncio
import logging

from telegram import Message
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

PROGRESS_STEPS = [
    (1, 4, "⏳ Calculating numerological stamp..."),
    (2, 4, "🔮 Consulting the Oracle..."),
    (3, 4, "✨ Generating interpretation..."),
    (4, 4, "✅ Reading complete!"),
]


async def update_progress(msg: Message, step: int, total: int, text: str) -> bool:
    """Edit a message with progress text. Returns False if message was deleted."""
    try:
        from formatters import format_progress
        await msg.edit_text(format_progress(step, total, text), parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)  # Rate limit protection
        return True
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            return True  # Same text, not an error
        if "message to edit not found" in str(e).lower():
            return False  # User deleted the message
        logger.warning("Progress update failed: %s", e)
        return True  # Unknown error, continue anyway
```

### Checkpoint 7

```bash
cd services/telegram && python -c "
from formatters import format_progress
text = format_progress(2, 4, 'Consulting the Oracle...')
assert '🔮' in text
assert '▓▓░░' in text
print('OK:', repr(text))
"
```

---

## PHASE 8: Error Handling & Edge Cases (30 min)

### Tasks

1. Handle all error scenarios gracefully with user-friendly messages
2. Implement per-user rate limiting (max 10 readings/hour per chat ID)
3. Handle Telegram message length limit (4096 chars) — truncate with "See more" link
4. Handle API timeout (30s) with a specific timeout message

### Error Scenarios

| Scenario                           | User Sees                                             | Technical Action              |
| ---------------------------------- | ----------------------------------------------------- | ----------------------------- |
| Account not linked                 | "Link your account first: /link <api_key>"            | Return early, don't call API  |
| API key expired/invalid            | "Your API key is no longer valid. Re-link with /link" | Log warning, suggest re-link  |
| API timeout                        | "Reading took too long. Try again in a moment."       | Log timeout, no retry         |
| API server error (500)             | "Server error. Our team has been notified."           | Log full error details        |
| API rate limited (429)             | "Too many requests. Wait a minute and try again."     | Respect Retry-After header    |
| Empty question for /question       | "Usage: /question What does today hold?"              | Show usage, return early      |
| Invalid time format                | "Invalid time format. Use HH:MM (e.g., /time 14:30)"  | Parse error, show usage       |
| Reading too long for Telegram      | Truncated message + "Full reading: [web link]"        | Truncate at ~3800 chars       |
| User rate limited (10/hour)        | "You've reached the hourly limit. Try again later."   | In-memory counter per chat_id |
| Bot not linked but has profile cmd | "Link account first"                                  | Check before every API call   |

### Code Pattern

```python
# Rate limiter (in-memory, resets hourly)
import time
from collections import defaultdict

_user_readings: dict[int, list[float]] = defaultdict(list)
_RATE_LIMIT = 10  # readings per hour
_RATE_WINDOW = 3600  # 1 hour in seconds


def check_rate_limit(chat_id: int) -> bool:
    """Returns True if the user is within rate limits."""
    now = time.time()
    timestamps = _user_readings[chat_id]
    # Remove expired entries
    _user_readings[chat_id] = [t for t in timestamps if now - t < _RATE_WINDOW]
    if len(_user_readings[chat_id]) >= _RATE_LIMIT:
        return False
    _user_readings[chat_id].append(now)
    return True
```

### Checkpoint 8

```bash
cd services/telegram && python -c "
from handlers.readings import check_rate_limit
# First 10 should pass
for i in range(10):
    assert check_rate_limit(123) == True
# 11th should fail
assert check_rate_limit(123) == False
print('Rate limiter OK')
"
```

---

## PHASE 9: Tests (60 min)

### 9.1 Reading Handler Tests

**File:** `services/telegram/tests/test_readings.py`

| #   | Test Name                          | What It Verifies                                                             |
| --- | ---------------------------------- | ---------------------------------------------------------------------------- |
| 1   | `test_time_command_basic`          | `/time 14:30` calls API with correct ISO datetime, returns formatted reading |
| 2   | `test_time_command_with_date`      | `/time 14:30 2026-02-10` passes both time and date to API                    |
| 3   | `test_time_command_no_args`        | `/time` with no args uses current time (API default)                         |
| 4   | `test_time_command_invalid_format` | `/time abc` returns usage message, does not call API                         |
| 5   | `test_name_command_with_arg`       | `/name Alice` calls name reading API                                         |
| 6   | `test_name_command_uses_profile`   | `/name` without arg fetches profile name from API                            |
| 7   | `test_question_command`            | `/question What does today hold?` calls question API                         |
| 8   | `test_question_command_no_text`    | `/question` with no text shows usage                                         |
| 9   | `test_daily_command`               | `/daily` calls daily insight API                                             |
| 10  | `test_history_command`             | `/history` fetches last 5 readings, formats list                             |
| 11  | `test_unlinked_user_gets_error`    | Any reading command without linked account shows "link first"                |
| 12  | `test_rate_limit_enforced`         | 11th reading in an hour gets rate limit message                              |

### 9.2 Formatter Tests

**File:** `services/telegram/tests/test_formatters.py`

| #   | Test Name                                   | What It Verifies                                                        |
| --- | ------------------------------------------- | ----------------------------------------------------------------------- |
| 1   | `test_escape_special_chars`                 | `_escape()` properly escapes all MarkdownV2 special characters          |
| 2   | `test_format_time_reading_all_sections`     | Time reading formatter includes FC60, numerology, moon, zodiac sections |
| 3   | `test_format_time_reading_missing_sections` | Gracefully handles None sections (moon=None, angel=None, etc.)          |
| 4   | `test_format_question_reading_yes`          | Question with "yes" answer shows ✅ emoji                               |
| 5   | `test_format_question_reading_no`           | Question with "no" answer shows ❌ emoji                                |
| 6   | `test_format_name_reading`                  | Name reading shows destiny, soul urge, personality numbers              |
| 7   | `test_format_daily_insight`                 | Daily insight shows date, insight text, lucky numbers                   |
| 8   | `test_format_history_list`                  | History list shows numbered entries with type emoji                     |
| 9   | `test_format_progress`                      | Progress formatter shows correct emoji and progress bar                 |
| 10  | `test_truncation_under_limit`               | Messages under 4096 chars are not truncated                             |
| 11  | `test_truncation_over_limit`                | Messages over 4096 chars are truncated with "See more" link             |
| 12  | `test_persian_text_preserved`               | Persian text passes through formatter without corruption                |

### 9.3 API Client Tests

**File:** `services/telegram/tests/test_api_client.py`

| #   | Test Name                        | What It Verifies                                                  |
| --- | -------------------------------- | ----------------------------------------------------------------- |
| 1   | `test_create_reading_success`    | Successful API call returns APIResponse with success=True         |
| 2   | `test_create_reading_auth_error` | 401 response returns success=False with auth error message        |
| 3   | `test_create_reading_timeout`    | httpx.TimeoutException returns success=False with timeout message |
| 4   | `test_question_request_body`     | Question API call sends correct JSON body                         |
| 5   | `test_list_readings_pagination`  | History API call sends correct limit/offset query params          |

### Checkpoint 9

```bash
cd services/telegram && python -m pytest tests/ -v --tb=short
# Verify: All 29 tests pass
# Verify: Zero import errors
```

---

## PHASE 10: Final Verification (20 min)

### Tasks

1. Run the full test suite
2. Verify all handlers are registered in the bot
3. Verify Docker build succeeds
4. Test message formatting with sample data

### Integration Verification

```bash
# Run all tests
cd services/telegram && python -m pytest tests/ -v

# Verify imports
python -c "
from handlers.readings import time_command, name_command, question_command, daily_command, history_command, reading_callback_handler
from formatters import format_time_reading, format_question_reading, format_name_reading, format_daily_insight, format_history_list, format_progress
from api_client import NPSAPIClient, APIResponse
from keyboards import reading_actions_keyboard, history_keyboard
print('All imports OK')
"

# Verify Docker build (dry run)
cd services/telegram && docker build --check . 2>/dev/null || docker build -t nps-telegram-test .

# Format check
cd services/telegram && python -m ruff check . --fix && python -m ruff format .
```

### Manual Verification Checklist

- [ ] `/time 14:30` produces a multi-section formatted reading with FC60, numerology, moon, zodiac
- [ ] `/question What does today hold?` shows yes/no/maybe with emoji and interpretation
- [ ] `/name Alice` shows destiny number, soul urge, personality with letter breakdown
- [ ] `/daily` shows today's insight with lucky numbers
- [ ] `/history` shows last 5 readings as a numbered list with View buttons
- [ ] Inline keyboard buttons appear after each reading
- [ ] Progress messages edit correctly (⏳ → 🔮 → ✅)
- [ ] Unlinked user gets "link first" message on every reading command
- [ ] Rate limit kicks in after 10 readings/hour
- [ ] Messages longer than 4096 chars are truncated cleanly

### Checkpoint 10 (FINAL)

```bash
cd services/telegram && python -m pytest tests/ -v
# Verify: ALL 29 tests pass
# Verify: Zero linting errors
# Verify: Docker build succeeds
```

---

## TESTS TO WRITE

Full test listing with exact paths and function names:

```
services/telegram/tests/test_readings.py::test_time_command_basic
services/telegram/tests/test_readings.py::test_time_command_with_date
services/telegram/tests/test_readings.py::test_time_command_no_args
services/telegram/tests/test_readings.py::test_time_command_invalid_format
services/telegram/tests/test_readings.py::test_name_command_with_arg
services/telegram/tests/test_readings.py::test_name_command_uses_profile
services/telegram/tests/test_readings.py::test_question_command
services/telegram/tests/test_readings.py::test_question_command_no_text
services/telegram/tests/test_readings.py::test_daily_command
services/telegram/tests/test_readings.py::test_history_command
services/telegram/tests/test_readings.py::test_unlinked_user_gets_error
services/telegram/tests/test_readings.py::test_rate_limit_enforced
services/telegram/tests/test_formatters.py::test_escape_special_chars
services/telegram/tests/test_formatters.py::test_format_time_reading_all_sections
services/telegram/tests/test_formatters.py::test_format_time_reading_missing_sections
services/telegram/tests/test_formatters.py::test_format_question_reading_yes
services/telegram/tests/test_formatters.py::test_format_question_reading_no
services/telegram/tests/test_formatters.py::test_format_name_reading
services/telegram/tests/test_formatters.py::test_format_daily_insight
services/telegram/tests/test_formatters.py::test_format_history_list
services/telegram/tests/test_formatters.py::test_format_progress
services/telegram/tests/test_formatters.py::test_truncation_under_limit
services/telegram/tests/test_formatters.py::test_truncation_over_limit
services/telegram/tests/test_formatters.py::test_persian_text_preserved
services/telegram/tests/test_api_client.py::test_create_reading_success
services/telegram/tests/test_api_client.py::test_create_reading_auth_error
services/telegram/tests/test_api_client.py::test_create_reading_timeout
services/telegram/tests/test_api_client.py::test_question_request_body
services/telegram/tests/test_api_client.py::test_list_readings_pagination
```

**Total: 29 tests**

---

## ACCEPTANCE CRITERIA

- [ ] All 5 reading commands generate readings via API and display formatted results
- [ ] Progress updates show during reading generation (message editing)
- [ ] Inline keyboard buttons appear after each reading
- [ ] History command shows last 5 readings with View buttons
- [ ] Unlinked users get a clear "link first" message
- [ ] Rate limiting enforced at 10 readings/hour per user
- [ ] Messages over 4096 chars are truncated cleanly
- [ ] Persian text renders correctly in all formatters
- [ ] All 29 tests pass
- [ ] Zero linting errors (ruff)
- [ ] Docker build succeeds

---

## ERROR SCENARIOS

### Problem 1: API returns 401 after account was linked

**Cause:** API key was revoked or expired after the user linked their Telegram account.

**Fix:**

1. Bot catches 401 from `NPSAPIClient`
2. Shows message: "Your API key is no longer valid. Please re-link with /link <new_key>"
3. Optionally clears the stored (invalid) API key from local storage

### Problem 2: Reading message exceeds Telegram's 4096 character limit

**Cause:** AI interpretation is very long, or multiple rich sections push the message over the limit.

**Fix:**

1. `formatters.py` checks `len(message)` before returning
2. If over 3800 chars (leaving buffer for Markdown overhead), truncate the AI interpretation section
3. Append "... [See full reading on web](http://localhost:5173/oracle)" with a link to the web UI
4. If still over after truncation, progressively remove sections (patterns, synchronicities, extended FC60) until under limit

### Problem 3: Telegram API rate limit on message editing

**Cause:** Editing messages too fast (>30/second across all chats, or >1/second per chat).

**Fix:**

1. `update_progress()` includes `asyncio.sleep(0.3)` between edits
2. If `BadRequest: Too Many Requests` is caught, read `retry_after` from the exception and sleep for that duration
3. Progress updates are optional — if they fail, the final message still sends correctly

---

## DEPENDENCY GRAPH

```
Phase 1 (API Client)
  ├── Phase 2 (Formatters) ── independent
  ├── Phase 3 (Keyboards)  ── independent
  └──→ Phase 4 (Command Handlers) ── requires 1, 2, 3
          ├── Phase 5 (Account Helpers) ── parallel with 4
          └──→ Phase 6 (Register in Bot) ── requires 4
                  └──→ Phase 7 (Progress Editing) ── requires 4, 6
                          └──→ Phase 8 (Error Handling) ── requires 7
                                  └──→ Phase 9 (Tests) ── requires all
                                          └──→ Phase 10 (Verification)
```

Phases 1, 2, 3 can be done in parallel.
Phases 4-5 can be done in parallel after Phase 1.
Phases 6-10 are sequential.

---

## HANDOFF

### Created

- `services/telegram/handlers/readings.py` — 5 command handlers + callback handler
- `services/telegram/formatters.py` — MarkdownV2 formatters for all reading types + progress
- `services/telegram/api_client.py` — Async HTTP client for API communication
- `services/telegram/keyboards.py` — Inline keyboard builders
- `services/telegram/tests/test_readings.py` — 12 handler tests
- `services/telegram/tests/test_formatters.py` — 12 formatter tests
- `services/telegram/tests/test_api_client.py` — 5 API client tests

### Modified

- `services/telegram/bot.py` — Registered 5 command handlers + 1 callback handler
- `services/telegram/handlers/__init__.py` — Exported reading handlers

### Deleted

None

### What Next Session (35) Receives

Session 35 (Telegram Bot: Daily Auto-Insight) builds on this session. It receives:

- A working Telegram bot with 5 reading commands that call the NPS API
- A tested formatter module that can render any reading type as Telegram MarkdownV2
- An API client module for communicating with the NPS API from the bot
- An inline keyboard system for post-reading actions
- A rate limiter for per-user throttling

Session 35 will add:

- Scheduled daily reading delivery at user-preferred time
- `/daily_on`, `/daily_off`, `/daily_time HH:MM` commands
- Background scheduler that checks for pending deliveries every minute
- The `format_daily_insight()` formatter from this session will be reused for scheduled messages

---

## NOTES FOR EXECUTOR

1. **`python-telegram-bot` version:** Session 33 installs this library (async version, v20+). Use `from telegram import Update` and `from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler` patterns.

2. **API base URL in Docker:** The bot container communicates with the API container using Docker service names. The URL is `http://api:8000/api` (not localhost). Make this configurable via environment variable `NPS_API_URL`.

3. **httpx vs requests:** Use `httpx` (async) for the API client since `python-telegram-bot` v20 is fully async. Do NOT use synchronous `requests`.

4. **MarkdownV2 escaping is critical:** Telegram's MarkdownV2 parsing is very strict. ALL special characters must be escaped except inside code blocks. The `_escape()` function in formatters.py is the single source of truth for escaping. Test it thoroughly.

5. **Existing notifier.py is legacy:** The file `services/oracle/oracle_service/engines/notifier.py` (1578 lines) is the OLD Telegram notification system from the legacy version. It uses raw `urllib` and synchronous threading. Do NOT import from it. Session 33's bot is a separate, modern async service.

6. **Reading IDs for callbacks:** The API returns reading IDs in stored reading responses. For inline keyboard callbacks that reference specific readings, you need the reading ID. The time/question/name endpoints store the reading and can return the ID — check if `reading_id` is in the response or if you need to extract it from a separate call.

7. **Persian text in Telegram:** Telegram handles RTL text natively. You do NOT need to add `dir="rtl"` or any special markers. Just send the Persian text and Telegram renders it correctly.

8. **Test mocking strategy:** Use `unittest.mock.AsyncMock` for mocking `telegram.Update`, `telegram.Message`, and the API client. Mock the `NPSAPIClient` methods to return canned `APIResponse` objects.
