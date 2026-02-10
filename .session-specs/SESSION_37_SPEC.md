# SESSION 37 SPEC — Telegram Bot: Multi-User & Polish

**Block:** Features & Integration (Sessions 32-37)
**Estimated Duration:** 5-6 hours
**Complexity:** Medium-High
**Dependencies:** Sessions 33-36 (all Telegram bot features)

---

## TL;DR

- Build `/compare` command for multi-user compatibility readings via Telegram — resolve 2-5 profile names to IDs, call `POST /api/oracle/readings` with `reading_type: "multi"`, format individual summaries + compatibility meter + group analysis
- Add per-user reading rate limiting (10 readings/hour per chat ID) with friendly cooldown messages
- Create `services/telegram/i18n/` with `en.json` and `fa.json` — every bot string becomes locale-aware based on the linked account's language preference; Persian locale auto-converts Western digits to Persian numerals (۰-۹)
- Rewrite `/help` to support per-command help (`/help time`, `/help compare`) with examples and grouped categories
- Complete the legacy `notifier.py` migration: remove deprecated `urllib`-based send path, replace with `SystemNotifier` from Session 36
- Polish all formatters from Session 34 for consistent emoji usage, truncation safety (4000 char cap), and Persian text rendering
- Final session in the Telegram bot block — after this, the bot is feature-complete

---

## OBJECTIVES

1. **Multi-user reading command** — `/compare profile1 profile2 [profile3...]` resolves 2-5 profile names via the API search endpoint, generates a multi-user compatibility reading via `POST /api/oracle/readings` with `reading_type: "multi"`, and returns formatted individual summaries + pairwise compatibility + group analysis
2. **Reading rate limiter** — Track readings per chat ID with a sliding 1-hour window; reject with a friendly "slow down" message and remaining cooldown when the user exceeds 10 readings/hour
3. **Bilingual bot (i18n)** — All bot messages rendered in the user's linked locale (EN or FA); Persian locale shows Persian numerals (۰-۹) and RTL-friendly formatting
4. **Comprehensive help** — `/help` grouped by category with emoji headers; `/help <command>` shows detailed usage + examples for any specific command
5. **Error handling polish** — Consistent error taxonomy across all handlers: auth errors, API errors, validation errors, network errors, rate limit errors — each with emoji, recovery suggestion, and locale-aware text
6. **Formatting polish** — Audit and refine all Session 34 formatters; add section headers with emoji legends, consistent truncation at 4000 chars (under Telegram's 4096 limit), and `format_multi_user_reading()` for the new compare command
7. **Legacy notifier migration** — Remove deprecated `urllib`/threading code from `notifier.py`; all notification paths now use `SystemNotifier` from Session 36
8. **Tests** — 28+ tests covering multi-user handler, rate limiter, i18n, help, error handling, and legacy migration

---

## PREREQUISITES

- [ ] Session 33 complete — `services/telegram/bot.py`, `handlers/core.py`, `client.py`, `rate_limiter.py`, `Dockerfile` exist
- [ ] Session 34 complete — `handlers/readings.py`, `formatters.py`, `keyboards.py`, `api_client.py` exist
- [ ] Session 35 complete — `handlers/daily.py`, `scheduler.py` exist; daily preferences API at `/api/telegram/daily/*`
- [ ] Session 36 complete — `handlers/admin.py`, `notifications.py` exist; `SystemNotifier` operational; `notifier.py` has event callback bridge with `register_event_callback()`
- [ ] Multi-user reading API exists — `POST /api/oracle/readings` accepts `reading_type: "multi"` with `user_ids[]` and `primary_user_index` (Session 16)
- [ ] Profile search API exists — `GET /api/oracle/profiles?search=name` (Session 3)
- [ ] Account linking stores user locale in linked account data (Session 33)

Verification:

```bash
# Bot service exists with all prior session outputs
test -f services/telegram/bot.py && echo "OK: bot.py"
test -f services/telegram/handlers/readings.py && echo "OK: readings handlers"
test -f services/telegram/handlers/daily.py && echo "OK: daily handlers"
test -f services/telegram/handlers/admin.py && echo "OK: admin handlers"
test -f services/telegram/notifications.py && echo "OK: notifications"
test -f services/telegram/formatters.py && echo "OK: formatters"

# Multi-user reading endpoint (Session 16's unified endpoint)
grep "multi" api/app/routers/oracle.py
# Expected: reading_type: "multi" handling

# Legacy notifier has event callback bridge from Session 36
grep "register_event_callback" services/oracle/oracle_service/engines/notifier.py
# Expected: function definition found
```

---

## FILES TO CREATE

| File                                                   | Purpose                                                                                         |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| `services/telegram/handlers/multi_user.py`             | `/compare` command handler — profile resolution, multi-user reading, formatted results          |
| `services/telegram/i18n/__init__.py`                   | i18n package init with `t()` translation function, Persian numeral conversion, locale detection |
| `services/telegram/i18n/en.json`                       | English translations for all bot messages (~120 keys)                                           |
| `services/telegram/i18n/fa.json`                       | Persian translations for all bot messages (~120 keys)                                           |
| `services/telegram/reading_rate_limiter.py`            | Per-user reading rate limiter: 10 readings/hour sliding window                                  |
| `services/telegram/tests/test_multi_user.py`           | Tests for `/compare` handler (8 tests)                                                          |
| `services/telegram/tests/test_reading_rate_limiter.py` | Tests for reading rate limiter (5 tests)                                                        |
| `services/telegram/tests/test_i18n.py`                 | Tests for i18n system (6 tests)                                                                 |
| `services/telegram/tests/test_help.py`                 | Tests for enhanced help command (4 tests)                                                       |
| `services/telegram/tests/test_error_handling.py`       | Tests for error taxonomy and formatting (5 tests)                                               |

## FILES TO MODIFY

| File                                                 | Change                                                                                                                                                                                                                                             |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `services/telegram/bot.py`                           | Register `/compare` handler, inject reading rate limiter into `bot_data`, initialize i18n with `load_translations()`, update bot command list                                                                                                      |
| `services/telegram/handlers/__init__.py`             | Export multi-user handlers                                                                                                                                                                                                                         |
| `services/telegram/handlers/core.py`                 | Rewrite `/help` handler with categories + per-command help (`/help time`); make all messages locale-aware via `t()`                                                                                                                                |
| `services/telegram/handlers/readings.py`             | Add `reading_rate_limiter.check()` before each reading generation; make all messages locale-aware; replace inline error handling with `handle_api_error()`                                                                                         |
| `services/telegram/handlers/daily.py`                | Make messages locale-aware via `t()`                                                                                                                                                                                                               |
| `services/telegram/handlers/admin.py`                | Make error messages locale-aware (admin content stays EN by default)                                                                                                                                                                               |
| `services/telegram/formatters.py`                    | Add `format_multi_user_reading()`, `_format_meter_bar()`, `_number_emoji()`, `_truncate()`; polish existing formatters; add truncation safety to all formatters                                                                                    |
| `services/telegram/keyboards.py`                     | Add `compare_actions_keyboard()` with group-specific actions                                                                                                                                                                                       |
| `services/telegram/api_client.py`                    | Add `search_profiles()`, `create_multi_user_reading()`, `classify_error()` methods                                                                                                                                                                 |
| `services/oracle/oracle_service/engines/notifier.py` | Remove deprecated `urllib`-based `_send_message()`, `_enqueue_message()`, `_process_queue()`, threading globals; rewrite notification functions to route through `_event_callback`; keep `register_event_callback()`, `COMMANDS`, `CURRENCY_ICONS` |
| `services/telegram/rate_limiter.py`                  | Add docstring clarifying this is the _message_ rate limiter (20/min) vs the new _reading_ rate limiter (10/hr)                                                                                                                                     |

## FILES TO DELETE

None.

---

## IMPLEMENTATION PHASES

### Phase 1 — Reading Rate Limiter (30 min)

**Goal:** Enforce a per-user limit of 10 readings per hour to prevent API abuse.

**Context:** Session 33 created `rate_limiter.py` for general message rate limiting (20 messages/minute). This is a _separate_ rate limiter specifically for reading generation, which is expensive (calls AI, generates framework output). The distinction: message rate limiter prevents spam; reading rate limiter prevents API cost overruns.

**Work:**

1. Create `services/telegram/reading_rate_limiter.py`:

```python
"""Per-user reading rate limiter.

Tracks reading generation requests per chat ID using a sliding 1-hour window.
Maximum 10 readings per hour per user. This is separate from the message
rate limiter (Session 33) which limits general bot interaction at 20/min.
"""

import time
from collections import defaultdict, deque

MAX_READINGS_PER_HOUR = 10
WINDOW_SECONDS = 3600  # 1 hour


class ReadingRateLimiter:
    """Sliding-window rate limiter for reading generation."""

    def __init__(
        self,
        max_readings: int = MAX_READINGS_PER_HOUR,
        window_seconds: int = WINDOW_SECONDS,
    ):
        self._max = max_readings
        self._window = window_seconds
        self._timestamps: dict[int, deque[float]] = defaultdict(deque)

    def check(self, chat_id: int) -> tuple[bool, int]:
        """Check if a reading is allowed for this chat ID.

        Returns:
            (allowed, remaining_seconds) — if not allowed, remaining_seconds
            is the time until the oldest reading expires from the window.
        """
        now = time.monotonic()
        timestamps = self._timestamps[chat_id]

        # Evict expired entries
        while timestamps and timestamps[0] <= now - self._window:
            timestamps.popleft()

        if len(timestamps) >= self._max:
            oldest = timestamps[0]
            wait_seconds = int(self._window - (now - oldest)) + 1
            return False, wait_seconds

        return True, 0

    def record(self, chat_id: int) -> None:
        """Record a reading generation for this chat ID."""
        self._timestamps[chat_id].append(time.monotonic())

    def remaining(self, chat_id: int) -> int:
        """Return how many readings the user has left in the current window."""
        now = time.monotonic()
        timestamps = self._timestamps[chat_id]

        while timestamps and timestamps[0] <= now - self._window:
            timestamps.popleft()

        return max(0, self._max - len(timestamps))
```

2. Integration pattern — every reading handler calls the rate limiter before proceeding:

```python
# In handlers/readings.py — at the top of each reading handler:
allowed, wait_seconds = reading_rate_limiter.check(chat_id)
if not allowed:
    minutes = wait_seconds // 60
    await update.message.reply_text(
        t("rate_limit_reading", locale, minutes=minutes)
    )
    return

# After successful reading generation:
reading_rate_limiter.record(chat_id)
```

3. Store the rate limiter instance in `bot_data` for handler access:

```python
# In bot.py during setup:
app.bot_data["reading_rate_limiter"] = ReadingRateLimiter()
```

**STOP — Checkpoint 1:**

```bash
cd services/telegram && python3 -c "
from reading_rate_limiter import ReadingRateLimiter
rl = ReadingRateLimiter(max_readings=2, window_seconds=10)
ok, _ = rl.check(123)
assert ok
rl.record(123)
rl.record(123)
ok, wait = rl.check(123)
assert not ok
assert wait > 0
print('OK: rate limiter works, wait =', wait, 'seconds')
"
```

---

### Phase 2 — i18n System (45 min)

**Goal:** Every bot message becomes locale-aware. Persian users see Persian text with Persian numerals.

**Work:**

1. Create `services/telegram/i18n/__init__.py`:

```python
"""Bot internationalization.

Loads translation files and provides a t() function for rendering
locale-aware messages. Supports variable interpolation and Persian
numeral conversion.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_translations: dict[str, dict[str, str]] = {}
_LOCALE_DIR = Path(__file__).parent
_DEFAULT_LOCALE = "en"

# Persian numeral mapping
_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def load_translations() -> None:
    """Load all translation JSON files from the i18n directory."""
    for json_file in _LOCALE_DIR.glob("*.json"):
        locale = json_file.stem  # "en" from "en.json"
        with open(json_file, encoding="utf-8") as f:
            _translations[locale] = json.load(f)
        logger.info("Loaded %d keys for locale '%s'", len(_translations[locale]), locale)


def t(key: str, locale: str = "en", **kwargs: str | int) -> str:
    """Translate a key to the given locale with variable interpolation.

    Usage: t("welcome", "fa", name="Ali")
    Looks up key in locale file, falls back to EN, falls back to key itself.
    For Persian locale, converts Western numerals to Persian numerals.
    """
    messages = _translations.get(locale, _translations.get(_DEFAULT_LOCALE, {}))
    text = messages.get(key, _translations.get(_DEFAULT_LOCALE, {}).get(key, key))

    # Interpolate variables: {name} → value
    for var_name, value in kwargs.items():
        text = text.replace(f"{{{var_name}}}", str(value))

    # Convert numerals for Persian locale
    if locale == "fa":
        text = to_persian_numerals(text)

    return text


def to_persian_numerals(text: str) -> str:
    """Convert Western digits 0-9 to Persian ۰-۹."""
    return text.translate(_PERSIAN_DIGITS)


def get_user_locale(chat_id: int, linked_accounts: dict) -> str:
    """Determine user's locale from their linked account settings.

    Priority:
    1. Stored locale preference in linked account
    2. Default to 'en'
    """
    account = linked_accounts.get(chat_id)
    if account and account.get("locale"):
        return account["locale"]
    return _DEFAULT_LOCALE
```

2. Create `services/telegram/i18n/en.json` with all bot messages (~60 keys organized by category). Include keys for:
   - Account management: `welcome`, `welcome_linked`, `link_success`, `link_failed`, `link_required`, `link_usage`, `link_deleted_warning`, `unlink_success`
   - Help system: `help_title`, `help_getting_started`, `help_readings`, `help_daily`, `help_admin`, `help_cmd_*` (one per command), `help_detail_*` (detailed help per reading command), `help_no_detail`
   - Progress: `progress_calculating`, `progress_ai`, `progress_formatting`, `progress_done`, `reading_complete`
   - Compare: `compare_resolving`, `compare_generating`, `compare_profile_not_found`, `compare_need_profiles`, `compare_too_many`, `compare_duplicate`, `compare_self_only`
   - Rate limiting: `rate_limit_reading`, `rate_limit_remaining`, `rate_limited`
   - Errors: `error_generic`, `error_network`, `error_auth`, `error_auth_expired`, `error_not_found`, `error_server`, `error_validation`, `error_rate_limit_api`
   - Status/Profile: `status_linked`, `status_unlinked`, `profile_header`, `profile_birthday`, `profile_gender`, `profile_no_profile`, `profile_empty`
   - Daily: `daily_not_available`, `daily_on_success`, `daily_off_success`, `daily_time_success`, `daily_time_usage`, `daily_time_invalid`
   - Admin: `admin_access_denied`
   - History: `history_empty`, `history_header`

3. Create `services/telegram/i18n/fa.json` with matching Persian translations for all keys. Key requirements:
   - All user-facing text in natural Persian
   - Technical terms (API, NPS, FC60) stay in English
   - Telegram command names stay as-is (e.g., `/help`, `/time`)
   - Persian numerals auto-applied by `t()` — no need to pre-convert in JSON

4. Call `load_translations()` in `services/telegram/bot.py` during startup.

**STOP — Checkpoint 2:**

```bash
cd services/telegram && python3 -c "
from i18n import load_translations, t, to_persian_numerals
load_translations()
assert t('welcome', 'en') != t('welcome', 'fa')
assert 'Oracle' in t('help_title', 'en')
assert 'اوراکل' in t('help_title', 'fa')
assert to_persian_numerals('123') == '۱۲۳'
# Variable interpolation
assert 'Ali' in t('link_success', 'en', name='Ali')
# Persian numerals in FA locale
fa_rate = t('rate_limit_reading', 'fa', minutes=5)
assert '۵' in fa_rate
print('OK: i18n system works in both locales with Persian numerals')
"
```

---

### Phase 3 — API Client Extensions (20 min)

**Goal:** Add methods to `api_client.py` for profile search, multi-user reading generation, and error classification.

**Work:**

1. Add `search_profiles()` to `NPSAPIClient`:

```python
async def search_profiles(self, name: str) -> APIResponse:
    """GET /oracle/profiles?search={name}

    Returns list of profiles matching the name.
    Used by /compare to resolve profile names to user IDs.
    """
    return await self._get("/oracle/profiles", params={"search": name})
```

2. Add `create_multi_user_reading()` — uses Session 16's unified endpoint:

```python
async def create_multi_user_reading(
    self,
    user_ids: list[int],
    primary_user_index: int = 0,
) -> APIResponse:
    """POST /oracle/readings with reading_type: 'multi'.

    Uses Session 16's unified reading endpoint — NOT the old
    /oracle/reading/multi-user path.
    """
    return await self._post("/oracle/readings", json={
        "reading_type": "multi",
        "user_ids": user_ids,
        "primary_user_index": primary_user_index,
    })
```

3. Add error classifier:

```python
def classify_error(self, response: APIResponse) -> str:
    """Classify an API error into an i18n key for user-friendly messaging."""
    if response.status_code == 401:
        return "error_auth"
    elif response.status_code == 403:
        return "error_auth"
    elif response.status_code == 404:
        return "error_not_found"
    elif response.status_code == 422:
        return "error_validation"
    elif response.status_code == 429:
        return "error_rate_limit_api"
    elif response.status_code >= 500:
        return "error_server"
    else:
        return "error_generic"
```

**STOP — Checkpoint 3:**

```bash
cd services/telegram && python3 -c "
from api_client import NPSAPIClient
print('OK: API client methods exist')
"
```

---

### Phase 4 — Multi-User Compare Handler (60 min)

**Goal:** Build the `/compare` command for 2-5 profile compatibility readings.

**Work:**

1. Create `services/telegram/handlers/multi_user.py` with `compare_command()`:

**Key design decisions:**

- Supports 3 name parsing styles: simple (`/compare Ali Sara`), quoted (`/compare "Ali Rezaei" "Sara"`), comma-separated (`/compare Ali Rezaei, Sara Ahmadi`)
- Validates 2-5 profiles, rejects duplicates (case-insensitive)
- Checks reading rate limit before API call
- Resolves names via `GET /api/oracle/profiles?search=name` — uses first match
- Calls `POST /api/oracle/readings` with `reading_type: "multi"` and `user_ids[]`
- Shows progress updates: "Looking up profiles..." → "Generating compatibility..."
- Uses `classify_error()` for consistent error handling
- Catches `httpx.ConnectError`/`httpx.TimeoutException` for network errors

2. Helper function `_parse_profile_names(args)`:
   - Checks for quoted names first (highest priority)
   - Then checks for commas
   - Falls back to treating each arg as a separate name

3. Register in `bot.py`:

```python
from handlers.multi_user import compare_command
app.add_handler(CommandHandler("compare", compare_command))
```

**STOP — Checkpoint 4:**

```bash
cd services/telegram && python3 -c "
from handlers.multi_user import _parse_profile_names
assert _parse_profile_names(['Ali', 'Sara', 'Bob']) == ['Ali', 'Sara', 'Bob']
assert len(_parse_profile_names(['\"A B\"', '\"C D\"'])) == 2
print('OK: name parser works')
"
```

---

### Phase 5 — Multi-User Formatters & Keyboards (45 min)

**Goal:** Create Telegram-formatted output for multi-user readings.

**Work:**

1. Add `format_multi_user_reading(data, profile_names, locale)` to `formatters.py`:
   - Header with all participant names
   - Individual highlights: circled number + name + life path + personal year
   - Pairwise compatibility with visual meter bars (🟢/🟡/🔴 + `▓▓▓▓░░░░` + percentage)
   - Group dynamics: energy type + harmony score
   - AI interpretation excerpt (capped at 400 chars)
   - Truncated to 4000 chars total

2. Helper functions:
   - `_format_meter_bar(score, width=10)` — visual bar with color indicator emoji
   - `_number_emoji(n)` — 1→①, 2→②, etc.
   - `_truncate(text, max_chars=4000)` — safe truncation with "see web" note

3. Add `_truncate()` to ALL existing formatters from Session 34.

4. Add `compare_actions_keyboard()` to `keyboards.py` with "Full Details" | "Share" | "New Compare" buttons.

5. Apply consistent emoji header scheme across all reading types (see table in objectives).

**STOP — Checkpoint 5:**

```bash
cd services/telegram && python3 -c "
from formatters import _format_meter_bar, _number_emoji, _truncate
assert '🟢' in _format_meter_bar(80)
assert '🔴' in _format_meter_bar(20)
assert _number_emoji(1) == '①'
assert len(_truncate('x' * 5000, 4000)) <= 4000
print('OK: formatters work')
"
```

---

### Phase 6 — Enhanced Help Command (30 min)

**Goal:** Rewrite `/help` with grouped categories and per-command detailed help.

**Work:**

1. Rewrite help handler in `handlers/core.py`:
   - `/help` → All commands grouped under emoji headers: 🚀 Getting Started, 🔮 Readings, 🌅 Daily, ⚙️ Admin (admin only)
   - `/help <command>` → Detailed usage with examples (looks up `help_detail_{cmd}` i18n key)
   - `/help nonexistent` → Fallback message via `help_no_detail` i18n key

2. Apply i18n `t()` to ALL existing handlers — replace every hardcoded English string:
   - `handlers/core.py` — `/start`, `/link`, `/status`, `/profile`
   - `handlers/readings.py` — `/time`, `/name`, `/question`, `/daily`, `/history`
   - `handlers/daily.py` — `/daily_on`, `/daily_off`, `/daily_time`, `/daily_status`
   - `handlers/admin.py` — Error messages only

**Pattern:**

```python
# Before: await update.message.reply_text("Link your account first")
# After:  await update.message.reply_text(t("link_required", locale))
```

**STOP — Checkpoint 6:**

```bash
grep "from.*i18n import" services/telegram/handlers/core.py
grep -c 'reply_text("' services/telegram/handlers/core.py
# Expected: 0 (all should use t())
```

---

### Phase 7 — Error Handling Polish (30 min)

**Goal:** Consistent, locale-aware error messages across all handlers.

**Work:**

1. Error taxonomy — map HTTP status to i18n key + emoji:

| Status  | Key                    | Emoji | Recovery       |
| ------- | ---------------------- | ----- | -------------- |
| 401     | `error_auth`           | ❌    | Re-link        |
| 403     | `error_auth`           | ❌    | Re-link        |
| 404     | `error_not_found`      | 🔍    | Check input    |
| 422     | `error_validation`     | ⚠️    | Fix format     |
| 429     | `error_rate_limit_api` | ⏳    | Wait           |
| 500+    | `error_server`         | 🛑    | Admin notified |
| Network | `error_network`        | 📡    | Check service  |
| Other   | `error_generic`        | ❓    | Try later      |

2. Create shared `handle_api_error(msg, result, locale, client)` utility.

3. Add network error catching (`httpx.ConnectError`, `httpx.TimeoutException`) to all handlers.

4. Apply `handle_api_error()` to all reading handlers, replacing inline error strings.

**STOP — Checkpoint 7:**

```bash
grep "handle_api_error\|classify_error" services/telegram/handlers/readings.py
grep "httpx.ConnectError" services/telegram/handlers/readings.py
```

---

### Phase 8 — Legacy Notifier Migration (30 min)

**Goal:** Remove deprecated `urllib`-based code from `notifier.py`.

**Context:** `notifier.py` is ~1578 lines using `urllib.request` and `threading`. Session 36 added `register_event_callback()`. Now the old code is dead weight.

**Work:**

1. **Remove:**
   - `_send_message()` (raw `urllib.request.urlopen`)
   - `_enqueue_message()`, `_process_queue()` (threading daemon)
   - `_message_queue`, `_queue_lock`, `_queue_thread`, `_queue_running` globals
   - `_lock`, `_last_send_time` globals
   - `_ssl_ctx` creation
   - `import ssl`, `import urllib.request`, `import urllib.error`, `import threading`

2. **Keep:**
   - `register_event_callback()` and `_event_callback`
   - `COMMANDS`, `CURRENCY_ICONS`, `CONTROL_BUTTONS`
   - `is_bot_healthy()`, `_record_success()`, `_record_failure()` (update to track callback health)
   - All `notify_*` functions — rewrite bodies to call `_event_callback` instead of `_enqueue_message`

3. **Rewrite notification functions** to use `_event_callback`:

```python
def notify_error(error_msg, details=None):
    if _event_callback is None:
        logger.warning("No callback registered; dropped: %s", error_msg)
        return
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_event_callback("error", {"message": error_msg, "details": details}))
        else:
            loop.run_until_complete(_event_callback("error", {"message": error_msg, "details": details}))
    except RuntimeError:
        logger.warning("No event loop for notification: %s", error_msg)
```

4. **Result:** ~1578 lines → ~400-500 lines.

**STOP — Checkpoint 8:**

```bash
grep -c "urllib" services/oracle/oracle_service/engines/notifier.py
# Expected: 0

grep -c "threading" services/oracle/oracle_service/engines/notifier.py
# Expected: 0

grep "register_event_callback" services/oracle/oracle_service/engines/notifier.py
# Expected: found

wc -l services/oracle/oracle_service/engines/notifier.py
# Expected: ~400-500
```

---

### Phase 9 — Formatting Polish (20 min)

**Goal:** Final formatting consistency pass.

**Work:**

1. Add `_truncate()` to all existing formatter functions.

2. Add locale-aware progress formatter:

```python
PROGRESS_EMOJIS = {0: "⏳", 1: "🔮", 2: "✨", 3: "✅"}

def format_progress(step: int, total: int, locale: str = "en") -> str:
    step_keys = ["progress_calculating", "progress_ai", "progress_formatting", "progress_done"]
    key = step_keys[min(step, len(step_keys) - 1)]
    message = t(key, locale)
    icon = PROGRESS_EMOJIS.get(step, "⏳")
    bar = "▓" * (step + 1) + "░" * (total - step - 1)
    return f"{icon} {_escape(message)}\n`{bar}` {step + 1}/{total}"
```

3. Verify consistent emoji headers across all reading types.

**STOP — Checkpoint 9:**

```bash
cd services/telegram && python3 -c "
from formatters import format_progress
r = format_progress(0, 4, 'en')
assert '⏳' in r and '▓' in r
print('OK')
"
```

---

### Phase 10 — Tests (60 min)

**Goal:** 28 tests across 5 test files.

#### `test_multi_user.py` (8 tests):

1. `test_parse_simple_names` — simple space-separated
2. `test_parse_comma_separated` — comma-delimited
3. `test_parse_quoted_names` — quoted names
4. `test_rejects_single_profile` — min 2 enforced
5. `test_rejects_more_than_five` — max 5 enforced
6. `test_rejects_duplicate_profiles` — duplicate detection
7. `test_handles_profile_not_found` — missing profile
8. `test_success_formats_reading` — mock API → formatted output

#### `test_reading_rate_limiter.py` (5 tests):

9. `test_allows_under_limit` — 10 pass
10. `test_blocks_after_limit` — 11th blocked
11. `test_window_expires` — reset after window
12. `test_remaining_count` — correct count
13. `test_independent_per_user` — per-user isolation

#### `test_i18n.py` (6 tests):

14. `test_loads_en_translations` — EN loads
15. `test_loads_fa_translations` — FA loads
16. `test_variable_interpolation` — {name} replaced
17. `test_persian_numerals` — 0-9 → ۰-۹
18. `test_fa_locale_auto_converts_numerals` — auto conversion
19. `test_fallback_to_english` — missing FA → EN

#### `test_help.py` (4 tests):

20. `test_help_shows_all_categories` — all sections
21. `test_help_specific_command` — /help time detail
22. `test_help_unknown_command` — fallback message
23. `test_help_admin_section_for_admins` — admin gating

#### `test_error_handling.py` (5 tests):

24. `test_classify_error_401` — auth classification
25. `test_classify_error_500` — server classification
26. `test_handle_api_error_formats_message` — locale-aware
27. `test_validation_error_includes_detail` — 422 detail
28. `test_network_error_caught` — network → friendly msg

**STOP — Checkpoint 10:**

```bash
cd services/telegram && python3 -m pytest tests/ -v --tb=short
# Expected: 28+ tests, 0 failures
```

---

### Phase 11 — Integration Verification (15 min)

**Goal:** End-to-end verification.

```bash
docker-compose up -d
docker-compose logs nps-telegram | tail -20

# Manual Telegram tests:
# /help → grouped with emojis
# /help compare → detailed usage
# /compare Ali Sara → compatibility result
# /time 14:30 (x11) → 11th rate-limited

# Persian locale test (change locale to fa, then):
# /help → Persian text

# Notifier verification:
wc -l services/oracle/oracle_service/engines/notifier.py
# Expected: ~400-500

# Full test suite:
cd services/telegram && python3 -m pytest tests/ -v
cd api && python3 -m pytest tests/ -v -k "telegram"
cd services/telegram && python3 -m ruff check . && python3 -m black --check .
```

---

## TESTS SUMMARY

| #   | Test                                    | File                           | Verifies                |
| --- | --------------------------------------- | ------------------------------ | ----------------------- |
| 1   | `test_parse_simple_names`               | `test_multi_user.py`           | Space-separated parsing |
| 2   | `test_parse_comma_separated`            | `test_multi_user.py`           | Comma parsing           |
| 3   | `test_parse_quoted_names`               | `test_multi_user.py`           | Quoted parsing          |
| 4   | `test_rejects_single_profile`           | `test_multi_user.py`           | Min 2 enforced          |
| 5   | `test_rejects_more_than_five`           | `test_multi_user.py`           | Max 5 enforced          |
| 6   | `test_rejects_duplicate_profiles`       | `test_multi_user.py`           | Duplicate detection     |
| 7   | `test_handles_profile_not_found`        | `test_multi_user.py`           | Missing profile         |
| 8   | `test_success_formats_reading`          | `test_multi_user.py`           | Mock → formatted        |
| 9   | `test_allows_under_limit`               | `test_reading_rate_limiter.py` | 10 pass                 |
| 10  | `test_blocks_after_limit`               | `test_reading_rate_limiter.py` | 11th blocked            |
| 11  | `test_window_expires`                   | `test_reading_rate_limiter.py` | Reset works             |
| 12  | `test_remaining_count`                  | `test_reading_rate_limiter.py` | Count correct           |
| 13  | `test_independent_per_user`             | `test_reading_rate_limiter.py` | Per-user isolation      |
| 14  | `test_loads_en_translations`            | `test_i18n.py`                 | EN loads                |
| 15  | `test_loads_fa_translations`            | `test_i18n.py`                 | FA loads                |
| 16  | `test_variable_interpolation`           | `test_i18n.py`                 | Vars replaced           |
| 17  | `test_persian_numerals`                 | `test_i18n.py`                 | ۰-۹ conversion          |
| 18  | `test_fa_locale_auto_converts_numerals` | `test_i18n.py`                 | Auto convert            |
| 19  | `test_fallback_to_english`              | `test_i18n.py`                 | FA→EN fallback          |
| 20  | `test_help_shows_all_categories`        | `test_help.py`                 | All sections            |
| 21  | `test_help_specific_command`            | `test_help.py`                 | /help time              |
| 22  | `test_help_unknown_command`             | `test_help.py`                 | Fallback msg            |
| 23  | `test_help_admin_section_for_admins`    | `test_help.py`                 | Admin gating            |
| 24  | `test_classify_error_401`               | `test_error_handling.py`       | Auth classify           |
| 25  | `test_classify_error_500`               | `test_error_handling.py`       | Server classify         |
| 26  | `test_handle_api_error_formats_message` | `test_error_handling.py`       | Locale-aware            |
| 27  | `test_validation_error_includes_detail` | `test_error_handling.py`       | 422 detail              |
| 28  | `test_network_error_caught`             | `test_error_handling.py`       | Network msg             |

---

## ACCEPTANCE CRITERIA

- [ ] `/compare name1 name2` generates multi-user compatibility reading with formatted output
- [ ] `/compare` supports 2-5 profiles via simple, quoted, or comma-separated name styles
- [ ] `/compare` rejects duplicates, handles missing profiles, respects rate limit
- [ ] Profile names resolved via `GET /api/oracle/profiles?search=name`
- [ ] Multi-user reading called via `POST /api/oracle/readings` with `reading_type: "multi"` (Session 16 unified endpoint)
- [ ] Reading rate limiter enforces 10 readings/hour per user with cooldown message
- [ ] All bot messages rendered in user's linked locale (EN or FA)
- [ ] Persian locale auto-converts Western numerals to Persian (۰-۹)
- [ ] `/help` shows grouped commands with emoji category headers
- [ ] `/help <command>` shows detailed usage with examples
- [ ] Admin section in `/help` only visible to admin-linked users
- [ ] All error paths: consistent emoji + locale-aware text + recovery suggestion
- [ ] Error classification via `classify_error()` maps HTTP status → i18n key
- [ ] Network errors caught and produce friendly messages
- [ ] Legacy `urllib`/threading code removed from `notifier.py`
- [ ] `notifier.py` functions route through `_event_callback`
- [ ] `notifier.py` reduced from ~1578 to ~400-500 lines
- [ ] All formatters truncate to 4000 chars
- [ ] Consistent emoji scheme across all reading types
- [ ] All 28 tests pass
- [ ] No bare `except:` in Python
- [ ] `ruff check` and `black --check` pass

---

## ERROR SCENARIOS

| Scenario                              | Expected Behavior                               |
| ------------------------------------- | ----------------------------------------------- |
| `/compare Ali` (1 name)               | "Provide 2-5 profile names" with usage examples |
| `/compare A B C D E F` (6 names)      | "Maximum 5 profiles. You provided 6."           |
| `/compare Ali Ali` (duplicate)        | "Duplicate profile: Ali"                        |
| `/compare UnknownPerson Ali`          | "Profile not found: UnknownPerson"              |
| 11th reading in 1 hour                | Rate limit message with minutes until reset     |
| API returns 500                       | "🛑 Server error, admin notified"               |
| API unreachable                       | "📡 Couldn't reach NPS server"                  |
| API returns 401                       | "❌ Authentication failed. Try /link"           |
| API returns 422                       | "⚠️ Invalid input: {detail}"                    |
| User not linked                       | "Link your account first: /link <api_key>"      |
| `/help nonexistent`                   | "No detailed help for /nonexistent"             |
| Persian user sends /help              | All text in Persian with Persian numerals       |
| `/compare "Ali Rezaei" "Sara Ahmadi"` | Quoted names parsed correctly                   |
| `/compare Ali Rezaei, Sara Ahmadi`    | Comma names parsed correctly                    |

---

## HANDOFF

**What this session completes:**

- The entire Telegram bot block (Sessions 33-37) is feature-complete
- Bot capabilities: core commands, 5 reading types + multi-user compare, daily scheduler, admin commands, notifications, bilingual i18n (EN/FA with Persian numerals), reading rate limiting, comprehensive per-command help
- Legacy `notifier.py` modernized — no more `urllib`/threading code

**What the next block (Sessions 38-40) needs:**

- Session 38 (Admin Panel) can reference Telegram-linked users via `telegram_links` table
- Session 39 (System Monitoring) can read bot health from notification service
- Session 40 (Backup) includes `telegram_links` and `telegram_daily_preferences` tables

**Dependencies resolved:**

- `services/telegram/` fully operational with all handlers, i18n, rate limiting
- `notifier.py` modernized — notifications flow through `SystemNotifier`
- Bot supports bilingual EN/FA matching the frontend's i18n system
