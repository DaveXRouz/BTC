# SESSION 33 SPEC — Telegram Bot: Core Setup

**Block:** Features & Integration (Sessions 32-37)
**Estimated Duration:** 5-6 hours
**Complexity:** High
**Dependencies:** Sessions 2-3 (auth + user API), Session 14-16 (reading flows), Session 32 (share/export)

---

## TL;DR

- Create `services/telegram/` as a standalone async Python service using `python-telegram-bot` v20+ (async)
- Build account linking: user sends `/link <api_key>` to the bot, bot validates key against the NPS API, and stores the Telegram↔NPS user association in a new `telegram_links` table
- Implement 5 core commands: `/start` (welcome + instructions), `/link` (account linking), `/help` (all commands), `/status` (account info), `/profile` (Oracle profile summary)
- Bot runs as its own Docker container, communicating with the NPS API exclusively over HTTP — never touches the database directly
- Add rate limiting (20 messages/minute per chat ID) and structured JSON logging

---

## OBJECTIVES

1. **Bot service** — Standalone Python service using `python-telegram-bot` v20+ async handlers, running in its own Docker container
2. **Account linking** — Users link their Telegram account to NPS by sending an API key; bot validates the key via `GET /api/auth/me` and stores the association
3. **Core commands** — `/start`, `/link <api_key>`, `/help`, `/status`, `/profile` all functional
4. **API client** — HTTP client module that wraps all calls to the NPS API with auth headers, timeout, and error handling
5. **Rate limiting** — Per-chat-ID rate limiting (20 messages/minute) to prevent abuse
6. **Docker integration** — Dockerfile + docker-compose.yml entry, bot starts automatically with the stack
7. **Database table** — `telegram_links` table linking `telegram_chat_id` → `user_id` with activation status

---

## PREREQUISITES

- [ ] Auth system functional — `POST /api/auth/login` returns JWT, `POST /api/auth/api-keys` creates API keys
- [ ] User model exists — `api/app/orm/user.py` with `id`, `username`, `role`
- [ ] API key validation works — `api/app/middleware/auth.py` validates API keys via SHA-256 hash lookup
- [ ] Oracle profile endpoints — `GET /api/oracle/profiles` returns user profiles
- [ ] Docker Compose runs — `docker-compose up` starts all current services

**Verification:**

```bash
# Auth router exists
grep "api/auth" api/app/main.py
# Expected: include_router line for auth

# User ORM model
wc -l api/app/orm/user.py
# Expected: >= 10 lines

# API key model
wc -l api/app/orm/api_key.py
# Expected: >= 20 lines

# Docker Compose has services
grep -c "service" docker-compose.yml
# Expected: >= 7
```

---

## FILES TO CREATE

| File                                                  | Purpose                                                                    |
| ----------------------------------------------------- | -------------------------------------------------------------------------- |
| `services/telegram/bot.py`                            | Main entry point — creates Application, registers handlers, starts polling |
| `services/telegram/config.py`                         | Bot configuration from environment variables                               |
| `services/telegram/client.py`                         | Async HTTP client for NPS API calls (httpx-based)                          |
| `services/telegram/rate_limiter.py`                   | Per-chat-ID rate limiting with sliding window                              |
| `services/telegram/handlers/__init__.py`              | Handler registration helper                                                |
| `services/telegram/handlers/core.py`                  | Core command handlers: /start, /link, /help, /status, /profile             |
| `services/telegram/Dockerfile`                        | Multi-stage Docker image for the bot service                               |
| `services/telegram/requirements.txt`                  | Python dependencies: python-telegram-bot, httpx                            |
| `services/telegram/tests/__init__.py`                 | Test package init                                                          |
| `services/telegram/tests/test_core_handlers.py`       | Tests for core command handlers                                            |
| `services/telegram/tests/test_rate_limiter.py`        | Tests for rate limiter                                                     |
| `services/telegram/tests/test_client.py`              | Tests for API client                                                       |
| `api/app/routers/telegram.py`                         | API-side endpoints for Telegram link management                            |
| `api/app/orm/telegram_link.py`                        | ORM model for `telegram_links` table                                       |
| `api/app/models/telegram.py`                          | Pydantic models for Telegram link requests/responses                       |
| `database/migrations/013_telegram_links.sql`          | Migration: `telegram_links` table                                          |
| `database/migrations/013_telegram_links_rollback.sql` | Rollback migration                                                         |
| `api/tests/test_telegram_link.py`                     | Backend tests for Telegram link endpoints                                  |

---

## FILES TO MODIFY

| File                 | What Changes                                                 |
| -------------------- | ------------------------------------------------------------ |
| `docker-compose.yml` | Add `telegram-bot` service definition                        |
| `api/app/main.py`    | Register `telegram.router` with prefix `/api/telegram`       |
| `.env.example`       | Add `TELEGRAM_BOT_API_URL` env var for bot→API communication |

---

## FILES TO DELETE

None.

---

## IMPLEMENTATION PHASES

### Phase 1: Database — Telegram Links Table (30 min)

**Tasks:**

1. Create migration `database/migrations/013_telegram_links.sql`:

   ```sql
   CREATE TABLE IF NOT EXISTS telegram_links (
       id SERIAL PRIMARY KEY,
       telegram_chat_id BIGINT UNIQUE NOT NULL,
       telegram_username VARCHAR(100),
       user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
       linked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       last_active TIMESTAMPTZ,
       is_active BOOLEAN NOT NULL DEFAULT TRUE,
       CONSTRAINT telegram_links_chat_id_unique UNIQUE (telegram_chat_id)
   );
   CREATE INDEX idx_telegram_links_user_id ON telegram_links(user_id);
   CREATE INDEX idx_telegram_links_chat_id ON telegram_links(telegram_chat_id);
   ```

2. Create rollback migration `database/migrations/013_telegram_links_rollback.sql`:

   ```sql
   DROP TABLE IF EXISTS telegram_links;
   ```

3. Create ORM model `api/app/orm/telegram_link.py`:

   ```python
   from datetime import datetime
   from sqlalchemy import BigInteger, Boolean, ForeignKey, String, func
   from sqlalchemy.orm import Mapped, mapped_column
   from app.database import Base

   class TelegramLink(Base):
       __tablename__ = "telegram_links"

       id: Mapped[int] = mapped_column(primary_key=True)
       telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
       telegram_username: Mapped[str | None] = mapped_column(String(100))
       user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
       linked_at: Mapped[datetime] = mapped_column(server_default=func.now())
       last_active: Mapped[datetime | None] = mapped_column()
       is_active: Mapped[bool] = mapped_column(Boolean, default=True)
   ```

4. Create Pydantic models `api/app/models/telegram.py`:

   ```python
   from pydantic import BaseModel

   class TelegramLinkRequest(BaseModel):
       telegram_chat_id: int
       telegram_username: str | None = None
       api_key: str  # raw API key for validation

   class TelegramLinkResponse(BaseModel):
       telegram_chat_id: int
       telegram_username: str | None
       user_id: str
       username: str
       role: str
       linked_at: str
       is_active: bool

   class TelegramUserStatus(BaseModel):
       linked: bool
       username: str | None = None
       role: str | None = None
       oracle_profile_count: int = 0
       reading_count: int = 0
   ```

**Checkpoint:**

- [ ] Migration file exists at `database/migrations/013_telegram_links.sql`
- [ ] ORM model imports without error
- [ ] Pydantic models validate correctly

```bash
ls -la database/migrations/013_telegram_links.sql
# Expected: file exists

python3 -c "from app.orm.telegram_link import TelegramLink; print('OK')" 2>/dev/null || echo "Run from api/ dir"

python3 -c "from app.models.telegram import TelegramLinkRequest, TelegramLinkResponse; print('OK')" 2>/dev/null || echo "Run from api/ dir"
```

🚨 STOP if checkpoint fails

---

### Phase 2: API — Telegram Link Endpoints (45 min)

**Tasks:**

1. Create `api/app/routers/telegram.py` with these endpoints:

   **`POST /api/telegram/link`** — Link a Telegram chat to an NPS user account.
   - Input: `TelegramLinkRequest` (telegram_chat_id, telegram_username, api_key)
   - Validates the API key by looking up its SHA-256 hash in the `api_keys` table
   - Verifies the associated user exists and is active
   - Creates or updates a `telegram_links` row (upsert: if chat_id already linked, update the user_id)
   - Returns `TelegramLinkResponse` with user info
   - **No auth header required** — the API key is in the request body (since the bot calls this on behalf of a user)

   **`GET /api/telegram/status/{chat_id}`** — Get link status for a Telegram chat.
   - Returns `TelegramUserStatus` with linked status, username, role, oracle profile count, reading count
   - **Auth required** — bot authenticates with a service API key
   - If chat_id not linked, returns `{"linked": false}`

   **`DELETE /api/telegram/link/{chat_id}`** — Unlink a Telegram account.
   - Sets `is_active = False` on the telegram_link row
   - **Auth required** — bot service key or the linked user's own JWT

   **`GET /api/telegram/profile/{chat_id}`** — Get Oracle profile for a linked Telegram user.
   - Looks up user_id from telegram_links, then queries oracle_users for the user's profiles
   - Returns list of oracle profiles or empty list
   - **Auth required** — bot service key

2. Register router in `api/app/main.py`:

   ```python
   from app.routers import telegram
   app.include_router(telegram.router, prefix="/api/telegram", tags=["telegram"])
   ```

3. Import ORM model in `api/app/main.py`:

   ```python
   import app.orm.telegram_link  # noqa: F401
   ```

**Code Pattern — Link Endpoint:**

```python
import hashlib
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.orm.api_key import APIKey
from app.orm.user import User
from app.orm.telegram_link import TelegramLink
from app.models.telegram import TelegramLinkRequest, TelegramLinkResponse

router = APIRouter()

@router.post("/link", response_model=TelegramLinkResponse)
def link_telegram(body: TelegramLinkRequest, db: Session = Depends(get_db)):
    # Validate the API key
    key_hash = hashlib.sha256(body.api_key.encode()).hexdigest()
    api_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True,
    ).first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    # Look up the user
    user = db.query(User).filter(User.id == api_key.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or inactive")

    # Upsert telegram link
    existing = db.query(TelegramLink).filter(
        TelegramLink.telegram_chat_id == body.telegram_chat_id
    ).first()
    if existing:
        existing.user_id = user.id
        existing.telegram_username = body.telegram_username
        existing.is_active = True
    else:
        existing = TelegramLink(
            telegram_chat_id=body.telegram_chat_id,
            telegram_username=body.telegram_username,
            user_id=user.id,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)

    return TelegramLinkResponse(
        telegram_chat_id=existing.telegram_chat_id,
        telegram_username=existing.telegram_username,
        user_id=user.id,
        username=user.username,
        role=user.role,
        linked_at=existing.linked_at.isoformat(),
        is_active=existing.is_active,
    )
```

**Checkpoint:**

- [ ] `POST /api/telegram/link` registered in main.py
- [ ] Link endpoint validates API key and creates telegram_links row
- [ ] Status endpoint returns user info or `{"linked": false}`
- [ ] Profile endpoint returns oracle profiles

```bash
grep "telegram" api/app/main.py
# Expected: include_router line for telegram

cd api && python3 -c "from app.routers.telegram import router; print(f'{len(router.routes)} routes')"
# Expected: 4 routes
```

🚨 STOP if checkpoint fails

---

### Phase 3: Bot Core — Application Skeleton (60 min)

**Tasks:**

1. Create `services/telegram/requirements.txt`:

   ```
   python-telegram-bot[ext]==20.7
   httpx>=0.25.0,<1.0
   ```

   Note: `python-telegram-bot[ext]` includes `httpx` and other optional dependencies. We list `httpx` explicitly for the API client.

2. Create `services/telegram/config.py`:

   ```python
   """Bot configuration from environment variables."""
   import os

   BOT_TOKEN: str = os.environ.get("NPS_BOT_TOKEN", "")
   API_BASE_URL: str = os.environ.get("TELEGRAM_BOT_API_URL", "http://api:8000/api")
   BOT_SERVICE_KEY: str = os.environ.get("TELEGRAM_BOT_SERVICE_KEY", "")
   RATE_LIMIT_PER_MINUTE: int = int(os.environ.get("TELEGRAM_RATE_LIMIT", "20"))
   LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
   ```

   - `BOT_TOKEN`: The Telegram Bot API token (from BotFather)
   - `API_BASE_URL`: The NPS API URL reachable from inside Docker network
   - `BOT_SERVICE_KEY`: An API key with `oracle:read` scope, used for bot→API calls that require auth (status, profile lookups)
   - `RATE_LIMIT_PER_MINUTE`: Max messages per chat per minute

3. Create `services/telegram/client.py` — Async HTTP client for NPS API:

   ```python
   """Async HTTP client for NPS API communication."""
   import logging
   import httpx
   from . import config

   logger = logging.getLogger(__name__)

   _client: httpx.AsyncClient | None = None

   async def get_client() -> httpx.AsyncClient:
       global _client
       if _client is None or _client.is_closed:
           _client = httpx.AsyncClient(
               base_url=config.API_BASE_URL,
               timeout=httpx.Timeout(10.0, connect=5.0),
               headers={"Authorization": f"Bearer {config.BOT_SERVICE_KEY}"},
           )
       return _client

   async def close_client():
       global _client
       if _client and not _client.is_closed:
           await _client.aclose()
           _client = None

   async def link_account(chat_id: int, username: str | None, api_key: str) -> dict | None:
       """Call POST /api/telegram/link to associate a Telegram chat with an NPS user."""
       client = await get_client()
       try:
           resp = await client.post("/telegram/link", json={
               "telegram_chat_id": chat_id,
               "telegram_username": username,
               "api_key": api_key,
           })
           if resp.status_code == 200:
               return resp.json()
           logger.warning("Link failed: %d %s", resp.status_code, resp.text)
           return None
       except httpx.HTTPError as exc:
           logger.error("API link_account error: %s", exc)
           return None

   async def get_status(chat_id: int) -> dict | None:
       """Call GET /api/telegram/status/{chat_id} to get link info."""
       client = await get_client()
       try:
           resp = await client.get(f"/telegram/status/{chat_id}")
           if resp.status_code == 200:
               return resp.json()
           return None
       except httpx.HTTPError as exc:
           logger.error("API get_status error: %s", exc)
           return None

   async def get_profile(chat_id: int) -> list[dict]:
       """Call GET /api/telegram/profile/{chat_id} to get Oracle profiles."""
       client = await get_client()
       try:
           resp = await client.get(f"/telegram/profile/{chat_id}")
           if resp.status_code == 200:
               return resp.json()
           return []
       except httpx.HTTPError as exc:
           logger.error("API get_profile error: %s", exc)
           return []
   ```

4. Create `services/telegram/rate_limiter.py`:

   ```python
   """Per-chat-ID sliding window rate limiter."""
   import time
   from collections import defaultdict
   from . import config

   class RateLimiter:
       def __init__(self, max_per_minute: int | None = None):
           self.max_per_minute = max_per_minute or config.RATE_LIMIT_PER_MINUTE
           self._timestamps: dict[int, list[float]] = defaultdict(list)

       def is_allowed(self, chat_id: int) -> bool:
           now = time.monotonic()
           window_start = now - 60.0
           # Prune old timestamps
           self._timestamps[chat_id] = [
               t for t in self._timestamps[chat_id] if t > window_start
           ]
           if len(self._timestamps[chat_id]) >= self.max_per_minute:
               return False
           self._timestamps[chat_id].append(now)
           return True

   rate_limiter = RateLimiter()
   ```

5. Create `services/telegram/bot.py` — Main entry point:

   ```python
   """NPS Telegram Bot — main entry point."""
   import logging
   import sys

   from telegram.ext import Application, CommandHandler

   from . import config
   from .client import close_client
   from .handlers.core import start_handler, help_handler, link_handler, status_handler, profile_handler

   logging.basicConfig(
       level=getattr(logging, config.LOG_LEVEL, logging.INFO),
       format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
   )
   logger = logging.getLogger(__name__)

   def main():
       if not config.BOT_TOKEN:
           logger.error("NPS_BOT_TOKEN not set — cannot start bot")
           sys.exit(1)

       logger.info("Starting NPS Telegram Bot")

       app = Application.builder().token(config.BOT_TOKEN).build()

       # Register command handlers
       app.add_handler(CommandHandler("start", start_handler))
       app.add_handler(CommandHandler("help", help_handler))
       app.add_handler(CommandHandler("link", link_handler))
       app.add_handler(CommandHandler("status", status_handler))
       app.add_handler(CommandHandler("profile", profile_handler))

       # Graceful shutdown
       import signal
       async def shutdown(app):
           await close_client()

       app.post_shutdown = shutdown

       logger.info("Bot handlers registered, starting polling")
       app.run_polling(
           drop_pending_updates=True,
           allowed_updates=["message", "callback_query"],
       )

   if __name__ == "__main__":
       main()
   ```

**Checkpoint:**

- [ ] `services/telegram/bot.py` exists with `main()` function
- [ ] `services/telegram/config.py` reads env vars
- [ ] `services/telegram/client.py` has async HTTP methods
- [ ] `services/telegram/rate_limiter.py` implements sliding window

```bash
wc -l services/telegram/bot.py services/telegram/config.py services/telegram/client.py services/telegram/rate_limiter.py
# Expected: all files exist with reasonable line counts

python3 -c "import ast; ast.parse(open('services/telegram/bot.py').read()); print('Syntax OK')"
# Expected: Syntax OK
```

🚨 STOP if checkpoint fails

---

### Phase 4: Command Handlers (60 min)

**Tasks:**

1. Create `services/telegram/handlers/__init__.py` (empty or minimal).

2. Create `services/telegram/handlers/core.py` with 5 command handlers:

**`/start` handler:**

- Sends welcome message with NPS branding
- Explains how to link account
- Shows available commands
- Message uses Telegram MarkdownV2 formatting

**`/link <api_key>` handler:**

- Parses API key from command arguments
- If no key provided: replies with usage instructions
- Calls `client.link_account(chat_id, username, api_key)`
- On success: "Account linked! Welcome, {username}. Use /help to see available commands."
- On failure: "Invalid API key. Generate one at Settings → API Keys in the NPS web app."
- **Security**: Immediately deletes the user's message containing the API key (via `context.bot.delete_message`) to prevent key exposure in chat history

**`/help` handler:**

- Lists all available commands with descriptions
- Groups by category: Account, Oracle, Info
- Shows Session 34+ commands as "Coming soon" placeholders

**`/status` handler:**

- Calls `client.get_status(chat_id)`
- If linked: shows username, role, profile count, reading count
- If not linked: "Not linked. Use /link <api_key> to connect your NPS account."

**`/profile` handler:**

- Calls `client.get_profile(chat_id)`
- If profiles exist: shows each profile (name, birthday, created date)
- If no profiles: "No Oracle profiles found. Create one in the NPS web app."
- If not linked: "Not linked. Use /link <api_key> first."

**Code Pattern — Core Handlers:**

```python
"""Core command handlers for the NPS Telegram bot."""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from ..rate_limiter import rate_limiter
from .. import client

logger = logging.getLogger(__name__)

async def _check_rate_limit(update: Update) -> bool:
    """Check rate limit. Returns True if allowed, False if rate-limited."""
    chat_id = update.effective_chat.id
    if not rate_limiter.is_allowed(chat_id):
        await update.message.reply_text("Slow down! Please wait a moment before sending more commands.")
        return False
    return True

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command — welcome message."""
    if not await _check_rate_limit(update):
        return

    text = (
        "Welcome to *NPS Oracle Bot*\\!\n\n"
        "Link your NPS account to get Oracle readings, "
        "daily insights, and notifications right here in Telegram\\.\n\n"
        "*Quick Start:*\n"
        "1\\. Go to NPS web app → Settings → API Keys\n"
        "2\\. Create an API key\n"
        "3\\. Send: `/link YOUR_API_KEY`\n\n"
        "Use /help for all available commands\\."
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2")

async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /link <api_key> — account linking."""
    if not await _check_rate_limit(update):
        return

    chat_id = update.effective_chat.id
    username = update.effective_user.username

    # Delete the message containing the API key for security
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception:
        pass  # May fail if bot lacks delete permission

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /link <api_key>\n\nGet your API key from NPS web app → Settings → API Keys.",
        )
        return

    api_key = context.args[0]
    result = await client.link_account(chat_id, username, api_key)

    if result:
        nps_username = result.get("username", "user")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Account linked! Welcome, {nps_username}.\nUse /help to see available commands.",
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Invalid or expired API key. Generate a new one at NPS → Settings → API Keys.",
        )

# ... similar patterns for help_handler, status_handler, profile_handler
```

**Checkpoint:**

- [ ] All 5 handlers exist in `services/telegram/handlers/core.py`
- [ ] `/link` handler deletes the user message containing API key
- [ ] `/start` handler sends formatted welcome message
- [ ] Rate limiting applied to all handlers

```bash
grep -c "async def.*_handler" services/telegram/handlers/core.py
# Expected: 5

grep "delete_message" services/telegram/handlers/core.py
# Expected: found (API key deletion for /link)
```

🚨 STOP if checkpoint fails

---

### Phase 5: Docker Integration (45 min)

**Tasks:**

1. Create `services/telegram/Dockerfile`:

   ```dockerfile
   FROM python:3.11-slim-bookworm

   WORKDIR /app

   # Install dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy bot source
   COPY . .

   # Create non-root user
   RUN groupadd -r botuser && useradd -r -g botuser -u 1001 botuser && \
       chown -R botuser:botuser /app
   USER botuser

   CMD ["python", "-m", "services.telegram.bot"]
   ```

   Note: The CMD uses module path. Alternatively, the entry point can be:

   ```dockerfile
   CMD ["python", "-c", "from services.telegram.bot import main; main()"]
   ```

   The exact CMD depends on how the Python package is structured. If `services/telegram/` is at the repo root with no `__init__.py` chain, use:

   ```dockerfile
   ENV PYTHONPATH=/app
   CMD ["python", "-m", "bot"]
   ```

   with the COPY adjusting accordingly. The simplest approach:

   ```dockerfile
   FROM python:3.11-slim-bookworm
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . /app/services/telegram/
   RUN groupadd -r botuser && useradd -r -g botuser -u 1001 botuser && \
       chown -R botuser:botuser /app
   USER botuser
   ENV PYTHONPATH=/app/services/telegram
   CMD ["python", "-c", "from bot import main; main()"]
   ```

   **Preferred approach** — keep it self-contained:

   ```dockerfile
   FROM python:3.11-slim-bookworm
   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   RUN groupadd -r botuser && useradd -r -g botuser -u 1001 botuser && \
       chown -R botuser:botuser /app
   USER botuser

   # Run as a module: python -m bot (bot.py at /app/bot.py)
   # But since we use relative imports, we need package structure:
   ENTRYPOINT ["python", "-c", "import sys; sys.path.insert(0, '/app'); exec(open('/app/run.py').read())"]
   ```

   **Simplest reliable approach**: Add a `run.py` at the root of `services/telegram/`:

   ```python
   """Entry point for Docker — avoids relative import issues."""
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent))

   # Re-export config module name so relative imports work
   import importlib
   # Use absolute imports by setting up the package
   from bot import main
   main()
   ```

   **Final Dockerfile:**

   ```dockerfile
   FROM python:3.11-slim-bookworm
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   RUN groupadd -r botuser && useradd -r -g botuser -u 1001 botuser && \
       chown -R botuser:botuser /app
   USER botuser
   CMD ["python", "run.py"]
   ```

2. Add `telegram-bot` service to `docker-compose.yml`:

   ```yaml
   # ─── Telegram Bot ───
   telegram-bot:
     build:
       context: ./services/telegram
       dockerfile: Dockerfile
     container_name: nps-telegram-bot
     env_file: .env
     environment:
       TELEGRAM_BOT_API_URL: http://api:8000/api
     depends_on:
       api:
         condition: service_healthy
     restart: unless-stopped
     deploy:
       resources:
         limits:
           cpus: "0.25"
           memory: 128M
   ```

   Important details:
   - `depends_on: api` — Bot only starts after API is healthy
   - `TELEGRAM_BOT_API_URL` — Points to the API container via Docker network
   - Low resource limits — bot is lightweight (polling, not webhook)
   - No ports exposed — bot communicates outward to Telegram API and inward to NPS API
   - No healthcheck — Telegram bot doesn't serve HTTP; health is implied by the process running

3. Update `.env.example` — add under the Telegram section:

   ```
   # Telegram Bot service-to-API communication
   TELEGRAM_BOT_API_URL=http://api:8000/api
   TELEGRAM_BOT_SERVICE_KEY=
   TELEGRAM_RATE_LIMIT=20
   ```

**Checkpoint:**

- [ ] `services/telegram/Dockerfile` builds successfully
- [ ] `telegram-bot` service defined in `docker-compose.yml`
- [ ] `.env.example` has new Telegram env vars
- [ ] Bot depends on API service health

```bash
grep "telegram-bot" docker-compose.yml
# Expected: service definition found

grep "TELEGRAM_BOT_API_URL" .env.example
# Expected: found

grep "TELEGRAM_BOT_SERVICE_KEY" .env.example
# Expected: found
```

🚨 STOP if checkpoint fails

---

### Phase 6: Security & Hardening (30 min)

**Tasks:**

1. **API key deletion in /link** — The handler MUST delete the user's message containing the API key immediately after reading it. This prevents the key from being visible in chat history. The bot needs "Delete messages" permission in the chat (for group chats) or can always delete in private chats.

2. **Rate limiter integration** — Every handler checks `rate_limiter.is_allowed(chat_id)` before processing. If rate-limited, reply with a brief "slow down" message and return.

3. **Input validation in /link** — Validate the API key format before sending to API:
   - Must be non-empty
   - Must be URL-safe base64 (alphanumeric + `-_`)
   - Length between 20 and 100 characters
   - Reject obviously invalid keys early to avoid unnecessary API calls

4. **Bot service key** — The bot uses `TELEGRAM_BOT_SERVICE_KEY` (an API key with `oracle:read` scope) to authenticate with protected endpoints (`/status/{chat_id}`, `/profile/{chat_id}`). This key is created during initial setup (documented in the spec handoff).

5. **Error handling** — All handlers wrapped in try/except. On unhandled errors:
   - Log the full traceback
   - Reply to user with generic "Something went wrong. Please try again."
   - Never expose internal error details to users

6. **Structured logging** — JSON-formatted logs matching the NPS logging standard:

   ```python
   logging.basicConfig(
       level=config.LOG_LEVEL,
       format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
   )
   ```

7. **Graceful shutdown** — On SIGTERM/SIGINT:
   - Close the httpx client
   - Let python-telegram-bot handle its own cleanup
   - Log shutdown event

**Checkpoint:**

- [ ] `/link` deletes user message containing API key
- [ ] Rate limiter rejects >20 messages/minute per chat
- [ ] API key format validated before API call
- [ ] All handlers have error handling
- [ ] Logs are JSON formatted

```bash
grep "delete_message" services/telegram/handlers/core.py
# Expected: found

grep "is_allowed" services/telegram/handlers/core.py
# Expected: found (rate limit check)

grep "logger" services/telegram/handlers/core.py | head -5
# Expected: logger usage in handlers
```

🚨 STOP if checkpoint fails

---

### Phase 7: Tests (60 min)

**Tasks:**

**Backend tests** — Create `api/tests/test_telegram_link.py`:

1. `test_link_telegram_success` — POST `/api/telegram/link` with valid API key → 200, returns link info
2. `test_link_telegram_invalid_key` — POST with invalid API key → 401
3. `test_link_telegram_inactive_user` — POST with key belonging to inactive user → 404
4. `test_link_telegram_upsert` — POST same chat_id twice → updates existing link, not duplicate
5. `test_status_linked_user` — GET `/api/telegram/status/{chat_id}` for linked user → returns info
6. `test_status_unlinked_user` — GET for unlinked chat_id → `{"linked": false}`
7. `test_unlink_telegram` — DELETE `/api/telegram/link/{chat_id}` → sets is_active = False
8. `test_profile_linked_user` — GET `/api/telegram/profile/{chat_id}` → returns oracle profiles

**Bot tests** — Create `services/telegram/tests/test_core_handlers.py`:

9. `test_start_handler_sends_welcome` — /start sends welcome message with MarkdownV2
10. `test_link_handler_no_args` — /link without API key sends usage message
11. `test_link_handler_success` — /link with valid key sends success message, deletes original message
12. `test_link_handler_invalid_key` — /link with bad key sends error message
13. `test_help_handler_lists_commands` — /help lists all available commands
14. `test_status_handler_linked` — /status for linked user shows account info
15. `test_status_handler_unlinked` — /status for unlinked user sends link instructions
16. `test_profile_handler_with_profiles` — /profile shows oracle profiles
17. `test_rate_limit_blocks_spam` — 21st message within 60s is rejected

**Rate limiter tests** — Create `services/telegram/tests/test_rate_limiter.py`:

18. `test_allows_under_limit` — Messages under limit are allowed
19. `test_blocks_over_limit` — Messages over limit are blocked
20. `test_window_expires` — Messages allowed again after window expires
21. `test_separate_chat_ids` — Different chat IDs have independent limits

**API client tests** — Create `services/telegram/tests/test_client.py`:

22. `test_link_account_success` — Mock httpx, verify correct request
23. `test_link_account_failure` — Mock httpx 401, returns None
24. `test_get_status_success` — Mock httpx, verify response parsing

**Testing approach for bot handlers:** Use `python-telegram-bot`'s testing utilities or mock `Update` and `ContextTypes.DEFAULT_TYPE` objects. The handlers are async functions that take `(update, context)`, so they can be tested by creating mock objects:

```python
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

@pytest.mark.asyncio
async def test_start_handler_sends_welcome():
    update = MagicMock()
    update.effective_chat.id = 12345
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("services.telegram.rate_limiter.rate_limiter.is_allowed", return_value=True):
        await start_handler(update, context)

    update.message.reply_text.assert_called_once()
    call_text = update.message.reply_text.call_args[0][0]
    assert "NPS Oracle Bot" in call_text
```

#### STOP Checkpoint 7 (FINAL)

- [ ] All backend tests pass
- [ ] All bot handler tests pass
- [ ] All rate limiter tests pass
- [ ] No lint errors

```bash
# Backend tests
cd api && python3 -m pytest tests/test_telegram_link.py -v
# Expected: 8 tests pass

# Bot tests (from repo root)
cd services/telegram && python3 -m pytest tests/ -v
# Expected: 15 tests pass

# Lint
cd services/telegram && python3 -m ruff check .
# Expected: no errors
```

---

## TESTS TO WRITE

### Backend (`api/tests/test_telegram_link.py`)

| #   | Test                               | Verifies                             |
| --- | ---------------------------------- | ------------------------------------ |
| 1   | `test_link_telegram_success`       | POST creates link with valid API key |
| 2   | `test_link_telegram_invalid_key`   | 401 for bad API key                  |
| 3   | `test_link_telegram_inactive_user` | 404 for inactive user                |
| 4   | `test_link_telegram_upsert`        | Same chat_id updates existing link   |
| 5   | `test_status_linked_user`          | Returns user info for linked chat    |
| 6   | `test_status_unlinked_user`        | Returns `{"linked": false}`          |
| 7   | `test_unlink_telegram`             | DELETE sets is_active = False        |
| 8   | `test_profile_linked_user`         | Returns oracle profiles              |

### Bot Handlers (`services/telegram/tests/test_core_handlers.py`)

| #   | Test                                 | Verifies                              |
| --- | ------------------------------------ | ------------------------------------- |
| 9   | `test_start_handler_sends_welcome`   | Welcome message sent                  |
| 10  | `test_link_handler_no_args`          | Usage message when no key             |
| 11  | `test_link_handler_success`          | Success message + key message deleted |
| 12  | `test_link_handler_invalid_key`      | Error message for bad key             |
| 13  | `test_help_handler_lists_commands`   | All commands listed                   |
| 14  | `test_status_handler_linked`         | Account info shown                    |
| 15  | `test_status_handler_unlinked`       | Link instructions shown               |
| 16  | `test_profile_handler_with_profiles` | Profiles displayed                    |
| 17  | `test_rate_limit_blocks_spam`        | 21st message blocked                  |

### Rate Limiter (`services/telegram/tests/test_rate_limiter.py`)

| #   | Test                      | Verifies                    |
| --- | ------------------------- | --------------------------- |
| 18  | `test_allows_under_limit` | Under-limit messages pass   |
| 19  | `test_blocks_over_limit`  | Over-limit messages blocked |
| 20  | `test_window_expires`     | Window reset works          |
| 21  | `test_separate_chat_ids`  | Independent per-chat limits |

### API Client (`services/telegram/tests/test_client.py`)

| #   | Test                        | Verifies                  |
| --- | --------------------------- | ------------------------- |
| 22  | `test_link_account_success` | Correct API request sent  |
| 23  | `test_link_account_failure` | Returns None on 401       |
| 24  | `test_get_status_success`   | Response parsed correctly |

---

## ACCEPTANCE CRITERIA

| #   | Criterion                   | Verify                                                                  |
| --- | --------------------------- | ----------------------------------------------------------------------- |
| 1   | Bot starts without errors   | `python services/telegram/run.py` (with valid BOT_TOKEN) starts polling |
| 2   | `/start` sends welcome      | Send /start to bot → receives welcome message                           |
| 3   | `/link` validates API key   | Send `/link invalid_key` → "Invalid" error message                      |
| 4   | `/link` creates association | Send `/link valid_key` → "Welcome, username" + message deleted          |
| 5   | `/status` shows info        | After linking → /status shows username, role, counts                    |
| 6   | `/profile` shows profiles   | After linking → /profile shows Oracle profiles                          |
| 7   | `/help` lists commands      | Send /help → all 5 commands listed                                      |
| 8   | Rate limiting works         | Send 21 messages in <60s → 21st is rejected                             |
| 9   | API key message deleted     | After /link, the message containing the key is removed from chat        |
| 10  | Docker container runs       | `docker-compose up telegram-bot` → container starts and connects        |
| 11  | Bot depends on API          | Bot container waits for API health before starting                      |
| 12  | telegram_links table exists | Migration creates the table with correct schema                         |
| 13  | All 24 tests pass           | Backend: 8 pass, Bot: 9 pass, Rate limiter: 4 pass, Client: 3 pass      |
| 14  | No lint errors              | `ruff check` clean on all Python files                                  |

**Verify all at once:**

```bash
# Backend
cd api && python3 -m pytest tests/test_telegram_link.py -v && \
# Bot
cd ../services/telegram && python3 -m pytest tests/ -v
```

---

## ERROR SCENARIOS

### Scenario 1: Bot token not configured

**Problem:** `NPS_BOT_TOKEN` env var empty or missing.
**Fix:**

1. `bot.py` checks for empty token at startup
2. Logs clear error: "NPS_BOT_TOKEN not set — cannot start bot"
3. Exits with code 1 (Docker will show container as failed)
4. Does NOT retry — requires manual fix

### Scenario 2: NPS API unreachable

**Problem:** API container not ready or network issue between containers.
**Fix:**

1. `docker-compose.yml` has `depends_on: api: condition: service_healthy`
2. `client.py` catches `httpx.ConnectError` specifically
3. Returns `None` from API calls (handlers show user-friendly error)
4. Logs connection error for debugging
5. Bot continues running — API calls fail gracefully, bot remains responsive with error messages

### Scenario 3: User sends API key in group chat

**Problem:** API key visible to all group members before bot deletes the message.
**Fix:**

1. `/link` handler immediately attempts `delete_message` before any processing
2. If deletion fails (bot lacks permission), warn user: "Could not delete your message. Please revoke this API key and create a new one in a private chat."
3. Still process the link request (key is already exposed)
4. Consider: Only allow `/link` in private chats (check `update.effective_chat.type == "private"`)

### Scenario 4: Rate limiter memory leak

**Problem:** `_timestamps` dict grows unbounded as new chat IDs send messages.
**Fix:**

1. Periodic cleanup: every 100 `is_allowed()` calls, remove entries where all timestamps are older than 60s
2. Maximum tracked chat IDs: 10,000 (evict oldest on overflow)
3. In practice, memory usage is negligible — each entry is ~200 bytes

### Scenario 5: API key already linked to different Telegram account

**Problem:** User A links their API key. User B (different Telegram account) tries to link the same API key.
**Fix:**

1. The `telegram_links` table has UNIQUE on `telegram_chat_id`, not on `user_id`
2. Multiple Telegram accounts CAN link to the same NPS user (allowed)
3. The same Telegram account linking to a different user updates the existing link (upsert behavior)
4. This is intentional — a user might want to relink to a different NPS account

### Scenario 6: python-telegram-bot polling failure

**Problem:** Telegram Bot API returns errors (429 rate limit, 502 gateway, network timeout).
**Fix:**

1. `python-telegram-bot` has built-in retry logic with exponential backoff
2. Default behavior handles Telegram API rate limits automatically
3. On persistent failure (>10 consecutive errors), log warning but keep retrying
4. Docker `restart: unless-stopped` ensures container restarts on crash

---

## HANDOFF

**Created:**

- `services/telegram/bot.py` — Main bot entry point with polling
- `services/telegram/config.py` — Configuration from env vars
- `services/telegram/client.py` — Async HTTP client for NPS API
- `services/telegram/rate_limiter.py` — Per-chat rate limiting
- `services/telegram/handlers/__init__.py` — Handler package
- `services/telegram/handlers/core.py` — 5 core command handlers
- `services/telegram/run.py` — Docker entry point
- `services/telegram/Dockerfile` — Container image
- `services/telegram/requirements.txt` — Python dependencies
- `services/telegram/tests/` — 16 bot tests
- `api/app/routers/telegram.py` — Telegram link API endpoints
- `api/app/orm/telegram_link.py` — TelegramLink ORM model
- `api/app/models/telegram.py` — Telegram Pydantic models
- `database/migrations/013_telegram_links.sql` — Migration
- `database/migrations/013_telegram_links_rollback.sql` — Rollback
- `api/tests/test_telegram_link.py` — 8 backend tests

**Modified:**

- `docker-compose.yml` — Added `telegram-bot` service
- `api/app/main.py` — Registered telegram router + ORM import
- `.env.example` — Added `TELEGRAM_BOT_API_URL`, `TELEGRAM_BOT_SERVICE_KEY`, `TELEGRAM_RATE_LIMIT`

**Deleted:** None

**Next session (Session 34) needs:**

- Bot service running and responding to `/start`, `/help`
- Account linking functional (`/link` → telegram_links table populated)
- `services/telegram/client.py` as base for adding reading API calls
- `services/telegram/handlers/` package structure for adding `readings.py`
- `services/telegram/rate_limiter.py` for rate limiting reading commands
- `telegram_links` table in database for looking up linked users
- `TELEGRAM_BOT_SERVICE_KEY` env var configured (an API key with `oracle:read` scope)
- Existing legacy `notifier.py` (in Oracle service) remains unchanged — Session 36 will integrate it with the new bot

**Relationship to existing `notifier.py`:**

The existing `services/oracle/oracle_service/engines/notifier.py` is a legacy notification system that uses raw urllib to send one-way Telegram messages (alerts, scanner hits, daily status). It is NOT a Telegram bot — it doesn't receive or process commands from users.

Session 33's Telegram bot is a completely separate service that:

- Receives user commands via Telegram Bot API polling
- Processes commands and calls the NPS API
- Sends responses back to users

The two systems coexist:

- `notifier.py` → Oracle service sends alerts to admin chat (one-way)
- `telegram-bot` → Users interact with NPS via commands (two-way)

Session 36 will unify them by having `notifier.py` route alerts through the bot service.
