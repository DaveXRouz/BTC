# NPS — UPDATE V1: Feature Expansion Specification

> **Created:** February 6, 2026
> **Author:** Dave (The Dave) + Claude Opus 4.6
> **Purpose:** Complete specification for transforming NPS from current build → full-featured system.
> Claude Code reads this file, builds everything in order, verifies each phase.

---

## TABLE OF CONTENTS

1. [Current State Summary](#1-current-state-summary)
2. [Target State Summary](#2-target-state-summary)
3. [Architecture Changes](#3-architecture-changes)
4. [Feature 1: Config System](#4-feature-1-config-system)
5. [Feature 2: Telegram Notifier](#5-feature-2-telegram-notifier)
6. [Feature 3: Balance Checker](#6-feature-3-balance-checker)
7. [Feature 4: Seed Phrase Scanner](#7-feature-4-seed-phrase-scanner)
8. [Feature 5: Headless Mode](#8-feature-5-headless-mode)
9. [GUI Changes](#9-gui-changes)
10. [Integration Map](#10-integration-map)
11. [Build Order](#11-build-order)
12. [Testing Plan](#12-testing-plan)
13. [Quality Checklist](#13-quality-checklist)
14. [Constants & Reference Data](#14-constants--reference-data)
15. [Edge Cases & Error Handling](#15-edge-cases--error-handling)
16. **[ADDENDUM A: Multi-Chain Support + Live Feed](#16-addendum-a-multi-chain-support--live-feed)** ← READ THIS — it modifies Sections 6, 7, 8, 9, 11, 12, 13

---

## 1. CURRENT STATE SUMMARY

### What Exists and Works

```
nps/
├── main.py                    ✅ 235 lines  — Tkinter app launcher, 6 tabs
├── engines/
│   ├── __init__.py            ✅
│   ├── fc60.py                ✅ 966 lines  — FC60 base-60 encoding, moon, ganzhi
│   ├── numerology.py          ✅ 294 lines  — Pythagorean numerology
│   ├── crypto.py              ✅ 713 lines  — secp256k1, Bitcoin utils, Kangaroo, BruteForce
│   ├── math_analysis.py       ✅ 160 lines  — Entropy, primes, palindromes
│   ├── scoring.py             ✅ 290 lines  — hybrid_score() with 3-way blending
│   ├── learning.py            ✅ 290 lines  — Pattern memory, weight adjustment
│   └── ai_engine.py           ✅ 255 lines  — Claude CLI integration (bonus)
├── solvers/
│   ├── __init__.py            ✅
│   ├── base_solver.py         ✅ 68 lines   — Abstract base with thread management
│   ├── btc_solver.py          ✅ 388 lines  — 4 strategies: lightning/mystic/hybrid/oracle
│   ├── number_solver.py       ✅ 279 lines  — Sequence pattern detection
│   ├── name_solver.py         ✅ 162 lines  — Full numerology profile
│   └── date_solver.py         ✅ 175 lines  — FC60 date analysis
├── gui/
│   ├── __init__.py            ✅
│   ├── theme.py               ✅ 61 lines   — Dark luxury color palette + fonts
│   ├── widgets.py             ✅ 430 lines  — StyledButton, ScoreBar, LogPanel, AIInsight
│   ├── dashboard_tab.py       ✅ 360 lines  — FC60 moment, stats, learning status
│   ├── btc_tab.py             ✅ 553 lines  — Puzzle solver interface
│   ├── number_tab.py          ✅ 224 lines  — Number Oracle interface
│   ├── name_tab.py            ✅ 227 lines  — Name Cipher interface
│   ├── date_tab.py            ✅ 184 lines  — Date Decoder interface
│   └── validation_tab.py      ✅ 385 lines  — Honest scoring validation
├── tests/                     ✅ 7 files, 58 tests, ALL PASSING
└── data/                      ✅ JSON storage + AI cache
```

**Total existing code:** 7,332 lines
**Test status:** 58/58 passing (0.342s)
**Dependencies:** Zero pip installs (stdlib only)

### What Does NOT Exist Yet

| Feature | Files Needed | Status |
|---------|-------------|--------|
| Config system | `config.json`, `engines/config.py` | ❌ Not started |
| Telegram notifier | `engines/notifier.py` | ❌ Not started |
| Balance checker | `engines/balance.py` | ❌ Not started |
| Seed phrase scanner | `engines/bip39.py`, `solvers/scanner_solver.py` | ❌ Not started |
| Headless mode | Modifications to `main.py` | ❌ Not started |
| Scanner GUI tab | `gui/scanner_tab.py` | ❌ Not started |
| Chat ID retrieval script | `tools/get_chat_id.py` | ❌ Not started |
| New tests | `tests/test_notifier.py`, `tests/test_bip39.py`, etc. | ❌ Not started |

---

## 2. TARGET STATE SUMMARY

After this update, NPS will:

1. **Solve BTC puzzles** with 4 strategies (existing) ✅
2. **Scan random private keys** looking for addresses with balances (new)
3. **Generate and check BIP39 seed phrases** looking for funded wallets (new)
4. **Notify Dave via Telegram** on any discovery, error, or daily status (new)
5. **Auto-check balances** via Blockstream API (new)
6. **Run headless** on a server with `--headless` flag (new)
7. **All features work offline** except balance checking and Telegram (new)

### New File Tree After Update

```
nps/
├── main.py                    MODIFIED — adds --headless flag, scanner tab
├── config.json                NEW — stores bot token, chat ID, settings
├── engines/
│   ├── ... (existing unchanged)
│   ├── config.py              NEW — config loader/saver
│   ├── notifier.py            NEW — Telegram bot notifications
│   ├── balance.py             NEW — Blockstream API balance checker
│   └── bip39.py               NEW — BIP39 seed phrase generation + BIP32 derivation
├── solvers/
│   ├── ... (existing unchanged)
│   └── scanner_solver.py      NEW — parallel key/seed scanner
├── gui/
│   ├── ... (existing unchanged)
│   └── scanner_tab.py         NEW — Scanner tab interface
├── tools/
│   └── get_chat_id.py         NEW — one-time script to retrieve Telegram chat ID
├── tests/
│   ├── ... (existing unchanged)
│   ├── test_config.py         NEW
│   ├── test_notifier.py       NEW
│   ├── test_balance.py        NEW
│   ├── test_bip39.py          NEW
│   └── test_scanner.py        NEW
└── data/
    ├── ... (existing unchanged)
    └── scanner_hits.json      NEW — log of any addresses found with balance
```

**Estimated new code:** ~2,800 lines
**Total after update:** ~10,100 lines

---

## 3. ARCHITECTURE CHANGES

### 3.1 Dependency Rules (UNCHANGED)

- Python 3.8+ stdlib ONLY
- Zero pip installs
- Internet needed ONLY for: Telegram notifications, balance checking
- Everything else works fully offline

### 3.2 New Module Dependency Graph

```
config.py          ← loaded by everything that needs settings
    │
    ├── notifier.py        ← uses config for bot token + chat ID
    │                         uses urllib.request for HTTPS
    │
    ├── balance.py         ← uses config for API settings
    │                         uses urllib.request for Blockstream API
    │                         uses crypto.py for address utilities
    │
    └── bip39.py           ← uses hashlib (pbkdf2_hmac, sha512)
                              uses hmac (BIP32 key derivation)
                              uses crypto.py for secp256k1 + address generation

scanner_solver.py  ← uses bip39.py, crypto.py, balance.py, notifier.py, scoring.py
                     extends base_solver.py

scanner_tab.py     ← uses scanner_solver.py
                     follows same pattern as btc_tab.py
```

### 3.3 Import Rules

- `config.py` imports nothing from NPS (it's the root)
- `notifier.py` imports only `config`
- `balance.py` imports only `config` and `crypto` (for address_to_hash160)
- `bip39.py` imports only `crypto` (for secp256k1 math)
- `scanner_solver.py` imports `bip39`, `crypto`, `balance`, `notifier`, `scoring`, `base_solver`
- NO circular imports — all dependencies flow one direction

---

## 4. FEATURE 1: CONFIG SYSTEM

### 4.1 File: `config.json`

Located at project root (`nps/config.json`). Created automatically with defaults on first run.

```json
{
  "telegram": {
    "bot_token": "",
    "chat_id": "",
    "enabled": false,
    "notify_on_solve": true,
    "notify_on_balance": true,
    "notify_on_error": true,
    "daily_status": true,
    "daily_status_hour": 9
  },
  "balance_check": {
    "enabled": true,
    "api_url": "https://blockstream.info/api",
    "check_interval_seconds": 60,
    "timeout_seconds": 10
  },
  "scanner": {
    "mode": "random_key",
    "threads": 2,
    "batch_size": 1000,
    "check_balance_every_n": 10000,
    "use_scoring": false,
    "rich_list_path": "data/rich_addresses.txt"
  },
  "headless": {
    "auto_start_puzzles": [],
    "auto_start_scanner": true,
    "log_level": "INFO"
  }
}
```

### 4.2 File: `engines/config.py`

```
Purpose: Load, save, and validate config.json
Size: ~120 lines
```

**API:**

```python
def load_config() -> dict:
    """Load config.json, creating with defaults if missing.
    Returns merged dict (user values + defaults for missing keys)."""

def save_config(config: dict) -> None:
    """Write config dict to config.json with pretty formatting."""

def get(key_path: str, default=None):
    """Dot-notation getter. Example: get('telegram.bot_token')"""

def set(key_path: str, value) -> None:
    """Dot-notation setter. Example: set('telegram.chat_id', '123456')
    Auto-saves after each set."""

def validate() -> list[str]:
    """Return list of validation warnings (empty = all good).
    Checks: bot_token format, chat_id is numeric, paths exist, etc."""
```

**Key behaviors:**
- Config file is created at `nps/config.json` on first `load_config()` call
- Never crashes on missing/corrupt file — falls back to defaults
- `get()` uses dot notation: `get('telegram.bot_token')` → walks the dict
- Thread-safe reads (config cached in module-level dict, reloaded on `load_config()`)

---

## 5. FEATURE 2: TELEGRAM NOTIFIER

### 5.1 File: `engines/notifier.py`

```
Purpose: Send messages to Dave's Telegram bot
Size: ~200 lines
Dependencies: config.py, urllib.request (stdlib)
```

**Telegram Bot Details:**
- Bot name: NPS (@xnpsx_bot)
- Bot token: `8229103669:AAHv98IVTbtMXENK48DHwT2DXOQ5p1vXJIE`
- Chat ID: Unknown — see Section 5.3 for retrieval script

**API:**

```python
def is_configured() -> bool:
    """Return True if bot_token AND chat_id are set in config."""

def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a message to the configured chat. Returns True on success.
    Fails silently (returns False) if not configured or network error.
    Max message length: 4096 chars (Telegram limit)."""

def notify_solve(puzzle_id: int, private_key: int, address: str) -> bool:
    """Send formatted solve notification.
    Message:
    🏆 <b>PUZZLE SOLVED!</b>
    Puzzle: #40
    Key: 0xa3f...
    Address: 1EeAx...
    Time: 2026-02-06 14:30 UTC
    """

def notify_balance_found(address: str, balance_btc: float, source: str) -> bool:
    """Send balance discovery notification.
    Message:
    💰 <b>BALANCE FOUND!</b>
    Address: 1ABC...
    Balance: 0.04 BTC
    Source: puzzle_solve | random_scan | seed_scan
    Time: 2026-02-06 14:30 UTC
    """

def notify_error(error_msg: str, context: str = "") -> bool:
    """Send error notification.
    Message:
    ⚠️ <b>NPS Error</b>
    Context: BTC Solver
    Error: Connection timeout
    Time: 2026-02-06 14:30 UTC
    """

def notify_daily_status(stats: dict) -> bool:
    """Send daily status summary.
    Message:
    📊 <b>NPS Daily Status</b>
    Running: 24h 12m
    Puzzles tested: 1,234,567 candidates
    Scanner tested: 5,678,901 keys
    Scanner seeds: 12,345 phrases
    Balances found: 0
    Errors: 2
    """

def notify_scanner_hit(address: str, private_key: str, balance_btc: float, method: str) -> bool:
    """CRITICAL alert — scanner found a funded address.
    Message:
    🚨🚨🚨 <b>SCANNER HIT!</b> 🚨🚨🚨
    Method: random_key | seed_phrase
    Address: 1ABC...
    Private Key: 0xABC... (or WIF)
    Balance: 0.001 BTC
    ⚡ SECURE THIS IMMEDIATELY ⚡
    Time: 2026-02-06 14:30 UTC
    """
```

**Implementation details:**

```python
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

def _send_raw(token: str, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    """Low-level send using urllib.request. No external dependencies."""
    import urllib.request
    import urllib.parse
    import json

    url = TELEGRAM_API.format(token=token)
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False
```

**Rate limiting:**
- Max 1 message per 2 seconds (Telegram limit is 30/sec but we're conservative)
- Daily status sent once per day at configured hour
- Error notifications capped at 10 per hour (avoid spam loops)
- Use threading.Lock for thread safety

**Fail-safe rules:**
- NEVER crash the app if Telegram fails
- NEVER block the solver thread waiting for Telegram
- Send in background thread (fire-and-forget)
- Log failures to `data/nps.log` but don't retry aggressively

### 5.2 File: `tools/get_chat_id.py`

```
Purpose: One-time script to retrieve Dave's Telegram chat ID
Size: ~50 lines
Usage: python tools/get_chat_id.py
```

**How it works:**

```python
"""
Get your Telegram Chat ID for NPS bot notifications.

Steps:
1. Open Telegram
2. Send any message to @xnpsx_bot
3. Run this script: python tools/get_chat_id.py
4. It will print your Chat ID
5. The Chat ID is auto-saved to config.json
"""

import urllib.request
import json
import sys
import os

# Add parent dir to path so we can import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_chat_id():
    from engines.config import load_config, set as config_set

    config = load_config()
    token = config["telegram"]["bot_token"]

    if not token:
        print("ERROR: No bot token in config.json")
        print("Set telegram.bot_token first.")
        return

    url = f"https://api.telegram.org/bot{token}/getUpdates"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"ERROR: Could not reach Telegram API: {e}")
        print("Make sure you have internet and the bot token is correct.")
        return

    if not data.get("ok") or not data.get("result"):
        print("No messages found.")
        print("")
        print("FIX: Open Telegram → send any message to @xnpsx_bot → run this again.")
        return

    # Get the most recent message's chat ID
    chat_id = None
    for update in data["result"]:
        msg = update.get("message", {})
        if msg.get("chat", {}).get("id"):
            chat_id = str(msg["chat"]["id"])
            sender = msg.get("from", {}).get("first_name", "Unknown")
            print(f"Found chat from: {sender}")

    if chat_id:
        print(f"")
        print(f"✅ Your Chat ID: {chat_id}")
        print(f"")
        config_set("telegram.chat_id", chat_id)
        config_set("telegram.enabled", True)
        print(f"Saved to config.json and enabled Telegram notifications.")
    else:
        print("Could not extract Chat ID. Send a message to the bot and try again.")


if __name__ == "__main__":
    get_chat_id()
```

### 5.3 Setup Sequence (for Dave)

```
Step 1: Open Telegram → send "hello" to @xnpsx_bot
Step 2: cd ~/Desktop/BTC/nps
Step 3: python tools/get_chat_id.py
Step 4: You'll see: "✅ Your Chat ID: 123456789"
Step 5: Done — notifications are now active
```

---

## 6. FEATURE 3: BALANCE CHECKER

### 6.1 File: `engines/balance.py`

```
Purpose: Check Bitcoin address balances via Blockstream API
Size: ~180 lines
Dependencies: config.py, urllib.request (stdlib)
API: https://blockstream.info/api (free, no key needed)
```

**API:**

```python
def check_balance(address: str) -> dict:
    """Check balance of a single Bitcoin address.
    Returns:
    {
        "success": True/False,
        "address": "1ABC...",
        "balance_sat": 400000,          # satoshis
        "balance_btc": 0.004,           # BTC (float)
        "tx_count": 12,                 # total transactions
        "funded_sum_sat": 500000,       # total received
        "spent_sum_sat": 100000,        # total spent
        "has_balance": True,            # balance_sat > 0
        "has_history": True,            # tx_count > 0
        "error": None,
    }
    """

def check_balance_batch(addresses: list[str], delay: float = 0.5) -> list[dict]:
    """Check multiple addresses with delay between calls.
    Returns list of result dicts (same format as check_balance).
    Delay prevents API rate limiting (Blockstream allows ~10 req/sec)."""

def has_any_activity(address: str) -> bool:
    """Quick check: has this address ever received any BTC?
    Faster than full balance check — just checks tx_count > 0."""

def get_utxos(address: str) -> list[dict]:
    """Get unspent transaction outputs for an address.
    Returns list of: {"txid": "abc...", "vout": 0, "value": 50000}
    Only needed if we actually find something."""
```

**Implementation details:**

```python
BLOCKSTREAM_API = "https://blockstream.info/api"

def _fetch_json(endpoint: str) -> dict:
    """Fetch JSON from Blockstream API."""
    import urllib.request
    import json

    url = f"{BLOCKSTREAM_API}/{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "NPS/1.0"})

    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

def check_balance(address: str) -> dict:
    try:
        data = _fetch_json(f"address/{address}")
        chain = data.get("chain_stats", {})
        mempool = data.get("mempool_stats", {})

        funded = chain.get("funded_txo_sum", 0) + mempool.get("funded_txo_sum", 0)
        spent = chain.get("spent_txo_sum", 0) + mempool.get("spent_txo_sum", 0)
        balance = funded - spent
        tx_count = chain.get("tx_count", 0) + mempool.get("tx_count", 0)

        return {
            "success": True,
            "address": address,
            "balance_sat": balance,
            "balance_btc": balance / 100_000_000,
            "tx_count": tx_count,
            "funded_sum_sat": funded,
            "spent_sum_sat": spent,
            "has_balance": balance > 0,
            "has_history": tx_count > 0,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "address": address,
            "balance_sat": 0,
            "balance_btc": 0.0,
            "tx_count": 0,
            "funded_sum_sat": 0,
            "spent_sum_sat": 0,
            "has_balance": False,
            "has_history": False,
            "error": str(e),
        }
```

**Rate limiting:**
- 0.5 second delay between API calls (configurable)
- Batch mode respects delay between each address
- Falls back gracefully if offline or API is down
- Never blocks the solver — balance checks run in background thread

### 6.2 Integration: Auto-Check After Puzzle Solve

In `solvers/btc_solver.py`, modify `_record_win()`:

```python
def _record_win(self, candidate):
    """Record successful solve + check balance + notify."""
    from engines.scoring import hybrid_score
    from engines import learning

    address = privkey_to_address(candidate)
    score_result = hybrid_score(candidate)

    learning.record_solve(
        puzzle_type="btc",
        candidate=candidate,
        score_result=score_result,
        was_correct=True,
        metadata={"puzzle_id": self.puzzle_id, "strategy": self.strategy},
    )

    # Auto-check balance (non-blocking)
    import threading
    def _check():
        from engines.balance import check_balance
        from engines.notifier import notify_solve, notify_balance_found
        result = check_balance(address)
        notify_solve(self.puzzle_id, candidate, address)
        if result["has_balance"]:
            notify_balance_found(address, result["balance_btc"], "puzzle_solve")
    threading.Thread(target=_check, daemon=True).start()

    self._emit({...})  # existing emit code
```

---

## 7. FEATURE 4: SEED PHRASE SCANNER

### ⚠️ HONEST MATH DISCLAIMER (must be shown in GUI)

```
The probability of randomly finding a funded Bitcoin address is approximately
1 in 10^41. This is astronomically unlikely — far less probable than winning
every lottery on Earth simultaneously. This scanner is built as requested
but the mathematical reality should be understood.

The puzzle solver (BTC Hunter tab) has realistic odds because puzzles have
known, bounded key ranges. The scanner does not have this advantage.
```

**This disclaimer MUST appear:**
1. In the Scanner tab header (always visible)
2. In the README.md
3. In the `--headless` startup log
4. It does NOT mean we don't build it — Dave wants it built, so we build it well.

### 7.1 File: `engines/bip39.py`

```
Purpose: BIP39 seed phrase generation + BIP32/BIP44 key derivation
Size: ~450 lines
Dependencies: hashlib (pbkdf2_hmac), hmac, crypto.py (secp256k1)
External deps: NONE — all stdlib
```

**Verified:** `hashlib.pbkdf2_hmac('sha512', ...)` and `hmac.new(..., hashlib.sha512)` are both available in Python 3.8+ stdlib.

**API:**

```python
# ── BIP39: Mnemonic Generation ──

WORDLIST: list[str]  # 2048 English words (embedded in file, see Section 14)

def generate_mnemonic(strength: int = 128) -> str:
    """Generate a random BIP39 mnemonic phrase.
    strength=128 → 12 words, strength=256 → 24 words.
    Uses os.urandom() for cryptographic randomness."""

def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """BIP39: mnemonic → 64-byte seed using PBKDF2-HMAC-SHA512.
    Iterations: 2048 (BIP39 standard).
    Salt: "mnemonic" + passphrase."""

def validate_mnemonic(mnemonic: str) -> bool:
    """Check if mnemonic has valid checksum and all words are in wordlist."""

# ── BIP32: HD Key Derivation ──

def seed_to_master_key(seed: bytes) -> tuple[bytes, bytes]:
    """BIP32: seed → (master_private_key, master_chain_code).
    Uses HMAC-SHA512 with key "Bitcoin seed"."""

def derive_child_key(parent_key: bytes, parent_chain: bytes, index: int,
                     hardened: bool = False) -> tuple[bytes, bytes]:
    """BIP32: derive child key at given index.
    Hardened derivation if index >= 0x80000000 or hardened=True."""

# ── BIP44: Standard Derivation Paths ──

def derive_btc_keys(seed: bytes, account: int = 0, count: int = 20) -> list[dict]:
    """Derive Bitcoin keys using BIP44 path: m/44'/0'/account'/0/i
    Returns list of:
    {
        "path": "m/44'/0'/0'/0/0",
        "private_key": int,
        "address": "1ABC...",
        "wif": "5Kb8...",
    }
    Default: first 20 receiving addresses of account 0."""

# ── Random Key Generation (faster alternative) ──

def generate_random_key() -> int:
    """Generate a random 256-bit private key using os.urandom().
    Ensures key is in valid secp256k1 range (1 to N-1)."""

def generate_random_keys_batch(count: int = 1000) -> list[int]:
    """Generate a batch of random private keys. Much faster than seed phrases
    because no PBKDF2 computation needed."""
```

**BIP39 Implementation Details:**

```python
import hashlib
import hmac as hmac_mod
import os
import struct

def generate_mnemonic(strength: int = 128) -> str:
    """Generate BIP39 mnemonic. strength must be 128, 160, 192, 224, or 256."""
    if strength not in (128, 160, 192, 224, 256):
        raise ValueError(f"Invalid strength: {strength}")

    # Generate entropy
    entropy = os.urandom(strength // 8)

    # Calculate checksum (first CS bits of SHA256)
    h = hashlib.sha256(entropy).digest()
    cs_bits = strength // 32

    # Convert entropy + checksum to bit string
    bits = bin(int.from_bytes(entropy, 'big'))[2:].zfill(strength)
    checksum = bin(int.from_bytes(h, 'big'))[2:].zfill(256)[:cs_bits]
    all_bits = bits + checksum

    # Split into 11-bit groups → word indices
    words = []
    for i in range(0, len(all_bits), 11):
        index = int(all_bits[i:i+11], 2)
        words.append(WORDLIST[index])

    return " ".join(words)


def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """BIP39 standard: PBKDF2-HMAC-SHA512, 2048 iterations."""
    password = mnemonic.encode("utf-8")
    salt = ("mnemonic" + passphrase).encode("utf-8")
    return hashlib.pbkdf2_hmac("sha512", password, salt, 2048)


def seed_to_master_key(seed: bytes) -> tuple:
    """BIP32: HMAC-SHA512 with key 'Bitcoin seed'."""
    I = hmac_mod.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    master_key = I[:32]     # left 32 bytes = private key
    chain_code = I[32:]     # right 32 bytes = chain code
    return master_key, chain_code


def derive_child_key(parent_key: bytes, parent_chain: bytes,
                     index: int, hardened: bool = False) -> tuple:
    """BIP32 child key derivation."""
    from engines.crypto import scalar_multiply, N as SECP256K1_N

    if hardened:
        index += 0x80000000

    if index >= 0x80000000:
        # Hardened: HMAC-SHA512(chain, 0x00 + key + index)
        data = b"\x00" + parent_key + struct.pack(">I", index)
    else:
        # Normal: HMAC-SHA512(chain, compressed_pubkey + index)
        from engines.crypto import pubkey_to_compressed
        k_int = int.from_bytes(parent_key, "big")
        pub_point = scalar_multiply(k_int)
        pub_compressed = pubkey_to_compressed(pub_point)
        data = pub_compressed + struct.pack(">I", index)

    I = hmac_mod.new(parent_chain, data, hashlib.sha512).digest()
    child_key_int = (int.from_bytes(I[:32], "big") +
                     int.from_bytes(parent_key, "big")) % SECP256K1_N
    child_key = child_key_int.to_bytes(32, "big")
    child_chain = I[32:]
    return child_key, child_chain


def derive_btc_keys(seed: bytes, account: int = 0, count: int = 20) -> list:
    """BIP44 path: m/44'/0'/account'/0/i"""
    from engines.crypto import privkey_to_address, privkey_to_wif

    master_key, master_chain = seed_to_master_key(seed)

    # m/44'
    key, chain = derive_child_key(master_key, master_chain, 44, hardened=True)
    # m/44'/0'
    key, chain = derive_child_key(key, chain, 0, hardened=True)
    # m/44'/0'/account'
    key, chain = derive_child_key(key, chain, account, hardened=True)
    # m/44'/0'/account'/0  (external chain)
    key, chain = derive_child_key(key, chain, 0, hardened=False)

    results = []
    for i in range(count):
        child_key, _ = derive_child_key(key, chain, i, hardened=False)
        k_int = int.from_bytes(child_key, "big")
        results.append({
            "path": f"m/44'/0'/{account}'/0/{i}",
            "private_key": k_int,
            "address": privkey_to_address(k_int),
            "wif": privkey_to_wif(k_int),
        })

    return results
```

**Performance expectations:**
- Random key generation: ~100,000 keys/second (secp256k1 scalar multiply is the bottleneck)
- BIP39 seed phrase → addresses: ~50 phrases/second (PBKDF2 2048 iterations is slow)
- Both are far too slow to ever realistically find a funded address, but the system runs 24/7

### 7.2 File: `solvers/scanner_solver.py`

```
Purpose: Background scanner that generates keys/seeds and checks for balances
Size: ~350 lines
Extends: base_solver.py
```

**API:**

```python
class ScannerSolver(BaseSolver):
    """Scans random keys and seed phrases looking for funded Bitcoin addresses."""

    MODES = ["random_key", "seed_phrase", "both"]

    def __init__(self, mode: str = "random_key", callback=None,
                 check_balance_online: bool = True,
                 use_scoring: bool = False):
        """
        mode: "random_key" | "seed_phrase" | "both"
        check_balance_online: if True, check Blockstream API periodically
        use_scoring: if True, score candidates with hybrid_score and try
                     "interesting" ones first (NPS theme — numerology-guided)
        """

    def solve(self):
        """Main scanner loop. Runs until stopped."""

    def _scan_random_keys(self):
        """Generate random 256-bit keys → derive address → check."""

    def _scan_seed_phrases(self):
        """Generate random 12-word BIP39 → derive 20 addresses each → check."""

    def _scan_both(self):
        """Alternate between random keys and seed phrases."""

    def _check_address(self, address: str, private_key: int, source: str) -> bool:
        """Check a single address. If it has balance → log + notify. Returns True if hit."""

    def _local_check(self, address: str) -> bool:
        """Check address against local rich-list cache (data/rich_addresses.txt).
        This is instant and doesn't need internet."""

    def _online_check(self, address: str) -> bool:
        """Check address via Blockstream API. Rate-limited."""

    def _record_hit(self, address: str, private_key: int, balance: dict, source: str):
        """Log hit to data/scanner_hits.json + send Telegram alert."""

    def get_name(self) -> str:
        return "Wallet Scanner"

    def get_description(self) -> str:
        return f"Mode: {self.mode} — scanning for funded addresses"
```

**Scanner Loop Design:**

```python
def _scan_random_keys(self):
    """Main random key scanning loop."""
    from engines.bip39 import generate_random_keys_batch
    from engines.crypto import privkey_to_address
    import time

    tested = 0
    hits = 0
    start = time.time()
    online_counter = 0
    check_every_n = self.config.get("scanner.check_balance_every_n", 10000)

    while self.running:
        # Generate batch
        keys = generate_random_keys_batch(self.batch_size)

        for key in keys:
            if not self.running:
                return

            address = privkey_to_address(key)
            tested += 1
            online_counter += 1

            # Local check (always — instant)
            if self._local_check(address):
                self._record_hit(address, key, {}, "random_key_local")
                hits += 1

            # Online check (periodic — rate limited)
            if self.check_balance_online and online_counter >= check_every_n:
                online_counter = 0
                if self._online_check(address):
                    from engines.balance import check_balance
                    balance = check_balance(address)
                    self._record_hit(address, key, balance, "random_key_online")
                    hits += 1

            # Progress update every 10,000 keys
            if tested % 10000 == 0:
                elapsed = time.time() - start
                speed = tested / max(0.001, elapsed)
                self._emit({
                    "status": "running",
                    "message": f"Scanned {tested:,} keys | {hits} hits | {speed:.0f}/s",
                    "progress": -1,  # indeterminate
                    "speed": speed,
                    "operations": tested,
                    "candidates_tested": tested,
                    "candidates_total": -1,
                    "hits": hits,
                    "current_best": None,
                    "solution": None,
                })
```

**Scoring Integration (optional, NPS-themed):**

When `use_scoring=True`, the scanner uses the existing numerology scoring engine to pick "interesting" random keys before checking them. This doesn't improve the mathematical odds but keeps the NPS theme consistent:

```python
def _scan_scored_keys(self):
    """Score random keys and check the highest-scored ones via API."""
    from engines.bip39 import generate_random_keys_batch
    from engines.scoring import score_batch

    keys = generate_random_keys_batch(self.batch_size)
    scored = score_batch(keys)

    # Check top 10% via API
    top_count = max(1, len(scored) // 10)
    for key, score_result in scored[:top_count]:
        if not self.running:
            return
        address = privkey_to_address(key)
        self._check_address(address, key, "scored_key")
```

### 7.3 Rich Address List (Local Cache)

File: `data/rich_addresses.txt`

This is a text file with known Bitcoin addresses that have (or had) large balances. The scanner checks generated addresses against this list FIRST (instant, no internet needed).

**How to populate:**
- Download top 1000 Bitcoin addresses by balance from public blockchain explorers
- One address per line
- Loaded into a Python `set()` at startup for O(1) lookup

**Format:**
```
1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ
...
```

**Initial creation:** Claude Code should generate a starter file with the top ~200 known rich addresses. These are public information (viewable on any blockchain explorer). The scanner checks against this list for free with no API calls.

**Loading:**
```python
_RICH_SET: set = None

def _load_rich_list() -> set:
    global _RICH_SET
    if _RICH_SET is not None:
        return _RICH_SET
    path = Path(__file__).parent.parent / "data" / "rich_addresses.txt"
    if not path.exists():
        _RICH_SET = set()
        return _RICH_SET
    with open(path) as f:
        _RICH_SET = {line.strip() for line in f if line.strip()}
    logger.info(f"Loaded {len(_RICH_SET)} rich addresses for local checking")
    return _RICH_SET
```

---

## 8. FEATURE 5: HEADLESS MODE

### 8.1 Changes to `main.py`

Add `--headless` flag that runs solvers + scanner without Tkinter GUI.

```python
import argparse

def main():
    parser = argparse.ArgumentParser(description="NPS — Numerology Puzzle Solver")
    parser.add_argument("--headless", action="store_true",
                        help="Run without GUI (for server deployment)")
    parser.add_argument("--config", type=str, default="config.json",
                        help="Path to config file")
    args = parser.parse_args()

    setup_logging()

    if args.headless:
        run_headless(args.config)
    else:
        app = NPSApp()
        app.run()
```

### 8.2 Headless Runner

```python
def run_headless(config_path: str):
    """Run NPS in headless mode — no GUI, just solvers + scanner + Telegram."""
    import signal
    import time
    from engines.config import load_config
    from engines.notifier import send_message, is_configured, notify_daily_status
    from solvers.scanner_solver import ScannerSolver

    logger = logging.getLogger("headless")
    config = load_config()

    # Print startup banner
    print("=" * 60)
    print("  NPS — Numerology Puzzle Solver (Headless Mode)")
    print("=" * 60)
    print(f"  Telegram: {'✅ Configured' if is_configured() else '❌ Not configured'}")
    print(f"  Scanner mode: {config['scanner']['mode']}")
    print(f"  Scanner threads: {config['scanner']['threads']}")
    print("")
    print("  ⚠️  MATH NOTE: Random key scanning has ~1 in 10^41 odds.")
    print("      The puzzle solver has realistic odds within bounded ranges.")
    print("=" * 60)

    # Notify Telegram that headless mode started
    if is_configured():
        send_message("🖥️ <b>NPS Headless Started</b>\nScanner is running.")

    # Start scanner
    active_solvers = []

    def scanner_callback(data):
        if data.get("status") == "running" and data.get("operations", 0) % 100000 == 0:
            logger.info(data.get("message", ""))

    scanner = ScannerSolver(
        mode=config["scanner"]["mode"],
        callback=scanner_callback,
        check_balance_online=config["balance_check"]["enabled"],
        use_scoring=config["scanner"]["use_scoring"],
    )
    scanner.start()
    active_solvers.append(scanner)

    # Auto-start puzzle solvers if configured
    auto_puzzles = config["headless"].get("auto_start_puzzles", [])
    for puzzle_id in auto_puzzles:
        from solvers.btc_solver import BTCSolver
        solver = BTCSolver(puzzle_id, strategy="hybrid", callback=scanner_callback)
        solver.start()
        active_solvers.append(solver)
        logger.info(f"Started puzzle #{puzzle_id} solver")

    # Daily status timer
    start_time = time.time()
    last_daily = 0

    # Graceful shutdown
    running = True
    def handle_signal(sig, frame):
        nonlocal running
        running = False
        logger.info("Shutdown signal received")

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Main loop
    try:
        while running:
            time.sleep(10)

            # Daily status
            elapsed_hours = (time.time() - start_time) / 3600
            if elapsed_hours - last_daily >= 24:
                last_daily = elapsed_hours
                stats = {
                    "uptime_hours": elapsed_hours,
                    "scanner_keys": scanner._tested if hasattr(scanner, '_tested') else 0,
                }
                notify_daily_status(stats)

    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Stopping all solvers...")
        for solver in active_solvers:
            solver.stop()
        if is_configured():
            send_message("🛑 <b>NPS Headless Stopped</b>")
        logger.info("NPS headless mode ended.")
```

### 8.3 Deployment Files

**File: `Procfile`** (for Railway)
```
worker: python main.py --headless
```

**File: `railway.toml`**
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python nps/main.py --headless"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10
```

**File: `requirements.txt`** (empty — zero pip deps)
```
# NPS has zero pip dependencies — stdlib only
```

---

## 9. GUI CHANGES

### 9.1 New Tab: Scanner (Tab 7)

File: `gui/scanner_tab.py`

```
Purpose: Interface for the wallet scanner
Size: ~400 lines
Follows same pattern as btc_tab.py
```

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  Wallet Scanner                                            │
│  ⚠️ Note: Random scanning has ~1 in 10^41 odds.           │
│  Puzzle solving (BTC Hunter tab) has realistic odds.       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Mode: (●) Random Keys  ( ) Seed Phrases  ( ) Both        │
│                                                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │  ▶  Start    │ │  ■  Stop     │ │ ⚙  Settings  │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
│                                                            │
│  ┌─ Stats ──────────────────────────────────────────────┐  │
│  │  Keys Tested: 1,234,567    Speed: 45,000/s           │  │
│  │  Seeds Tested: 12,345      Addresses: 246,900        │  │
│  │  Online Checks: 123        Hits: 0                   │  │
│  │  Running: 02:34:15         Estimated: ∞              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─ Telegram ───────────────────────────────────────────┐  │
│  │  Status: ✅ Connected (Chat ID: 123456789)           │  │
│  │  Last notification: 2 min ago                        │  │
│  │  [ Test Notification ]                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─ Activity Log ───────────────────────────────────────┐  │
│  │  14:30:01 | Scanned 100,000 keys (45,123/s)         │  │
│  │  14:30:15 | Online check: 1ABC... → no balance      │  │
│  │  14:30:30 | Seed #12,345: abandon ability able...    │  │
│  │  14:31:01 | Scanned 200,000 keys (44,987/s)         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─ AI Insight ─────────────────────────────────────────┐  │
│  │  (AI analysis of scanning patterns, if available)    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Settings popup (from ⚙ button):**
- Threads: 1-4
- Batch size: 100-10,000
- Online check frequency: every N keys
- Use scoring: Yes/No
- Telegram test button

### 9.2 Modifications to Existing Tabs

**main.py — Add scanner tab:**
```python
# After existing tab creation, add:

# Tab 7: Scanner
scan_frame = tk.Frame(self.notebook, bg=COLORS["bg"])
self.notebook.add(scan_frame, text="  Scanner  ")
self.scanner_tab = ScannerTab(scan_frame, app=self)
```

**gui/dashboard_tab.py — Add scanner stats:**
- Add scanner key count and speed to the stats panel
- Add "Scanner: Running/Stopped" indicator

**gui/btc_tab.py — Add Telegram notify on solve:**
- After solve, call `notifier.notify_solve()` in background thread
- Show Telegram send status in log panel

### 9.3 Telegram Settings in GUI

Add a small "Telegram" section to the Dashboard tab:

```python
# In dashboard_tab.py, add to stats panel:
self.tg_status = tk.Label(
    panel,
    text="Telegram: ❌ Not configured",
    font=FONTS["small"],
    fg=COLORS["text_dim"],
    bg=COLORS["bg_card"],
)

# Update periodically:
def _update_telegram_status(self):
    from engines.notifier import is_configured
    if is_configured():
        self.tg_status.config(
            text="Telegram: ✅ Connected",
            fg=COLORS["success"]
        )
    else:
        self.tg_status.config(
            text="Telegram: ❌ Not configured",
            fg=COLORS["text_dim"]
        )
```

---

## 10. INTEGRATION MAP

### 10.1 How Everything Connects

```
                     ┌──────────────┐
                     │  config.py   │  ← Everything reads from here
                     └──────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼───────┐
    │ notifier.py  │ │ balance.py  │ │   bip39.py   │
    │ (Telegram)   │ │ (Blockstrm) │ │ (Seed/Keys)  │
    └───────┬──────┘ └──────┬──────┘ └──────┬───────┘
            │               │               │
            │         ┌─────▼─────┐         │
            │         │ crypto.py │◄────────┘
            │         │ (existing)│
            │         └─────┬─────┘
            │               │
            └───────┬───────┘
                    │
           ┌────────▼─────────┐
           │ scanner_solver.py │  ← Uses all three new engines
           │   + btc_solver   │  ← Modified to use notifier + balance
           └────────┬─────────┘
                    │
        ┌───────────┼───────────┐
        │                       │
  ┌─────▼──────┐        ┌──────▼──────┐
  │ scanner_tab│        │  headless   │
  │  (GUI)     │        │  runner     │
  └────────────┘        └─────────────┘
```

### 10.2 Event Flow: Scanner Finds a Hit

```
1. scanner_solver generates random key
2. scanner_solver derives address via crypto.py
3. scanner_solver checks address vs local rich list → MATCH!
4. scanner_solver calls balance.check_balance(address) → has balance!
5. scanner_solver calls notifier.notify_scanner_hit(address, key, balance)
6. scanner_solver logs to data/scanner_hits.json
7. scanner_solver emits callback → GUI updates
8. Telegram: 🚨🚨🚨 SCANNER HIT! 🚨🚨🚨 → Dave's phone
```

### 10.3 Event Flow: Puzzle Solved

```
1. btc_solver finds matching key
2. btc_solver._record_win() → learning.record_solve()
3. btc_solver calls balance.check_balance(address) → background thread
4. btc_solver calls notifier.notify_solve(puzzle_id, key, address)
5. If balance found → notifier.notify_balance_found(address, btc, "puzzle_solve")
6. GUI updates with SOLVED status
7. Telegram: 🏆 PUZZLE SOLVED! → Dave's phone
```

### 10.4 Event Flow: Headless Startup

```
1. python main.py --headless
2. Load config.json
3. Check Telegram → send "NPS Headless Started"
4. Start scanner (mode from config)
5. Start auto-puzzles (from config.headless.auto_start_puzzles)
6. Enter main loop (sleep + daily status)
7. On SIGINT/SIGTERM → stop all, send "NPS Headless Stopped"
```

---

## 11. BUILD ORDER

### Phase 1: Foundation (no dependencies on other new features)

| Step | File | Est. Lines | What to Build | Verify |
|------|------|-----------|---------------|--------|
| 1 | `engines/config.py` | 120 | Config loader/saver with dot-notation | `python -c "from engines.config import load_config; print(load_config())"` |
| 2 | `config.json` | 30 | Default config with bot token pre-filled | File exists with valid JSON |
| 3 | `tests/test_config.py` | 60 | Test load, save, get, set, validate | `python -m unittest tests/test_config -v` |

### Phase 2: Network Features (depend on config)

| Step | File | Est. Lines | What to Build | Verify |
|------|------|-----------|---------------|--------|
| 4 | `engines/notifier.py` | 200 | Telegram bot notifications | `python -c "from engines.notifier import is_configured; print(is_configured())"` |
| 5 | `tools/get_chat_id.py` | 50 | Chat ID retrieval script | `python tools/get_chat_id.py` (will fail without chat ID, that's OK) |
| 6 | `engines/balance.py` | 180 | Blockstream API balance checker | `python -c "from engines.balance import check_balance; print(check_balance('1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'))"` |
| 7 | `tests/test_notifier.py` | 50 | Test message formatting, is_configured | `python -m unittest tests/test_notifier -v` |
| 8 | `tests/test_balance.py` | 50 | Test result dict structure, error handling | `python -m unittest tests/test_balance -v` |

### Phase 3: Scanner Engine (depends on config + crypto)

| Step | File | Est. Lines | What to Build | Verify |
|------|------|-----------|---------------|--------|
| 9 | `engines/bip39.py` | 450 | BIP39 mnemonic + BIP32 derivation + random keys | See test step 11 |
| 10 | `data/rich_addresses.txt` | 200 lines | Top ~200 known rich Bitcoin addresses | File exists with valid addresses |
| 11 | `tests/test_bip39.py` | 120 | Test mnemonic gen, seed derivation, key derivation with known vectors | `python -m unittest tests/test_bip39 -v` |

**BIP39 test vectors (MUST pass):**

```python
# Vector 1: Known mnemonic → known seed (from BIP39 spec)
mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
seed = mnemonic_to_seed(mnemonic, "")
assert seed.hex()[:16] == "5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc1"[:16]

# Vector 2: Known seed → known master key (from BIP32 spec)
seed_hex = "000102030405060708090a0b0c0d0e0f"
seed_bytes = bytes.fromhex(seed_hex)
master_key, chain_code = seed_to_master_key(seed_bytes)
assert master_key.hex() == "e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35"

# Vector 3: Random key is in valid range
key = generate_random_key()
assert 1 <= key < 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Vector 4: Mnemonic validation
assert validate_mnemonic("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about") == True
assert validate_mnemonic("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon") == False  # bad checksum
```

### Phase 4: Scanner Solver + GUI (depends on everything above)

| Step | File | Est. Lines | What to Build | Verify |
|------|------|-----------|---------------|--------|
| 12 | `solvers/scanner_solver.py` | 350 | ScannerSolver class with 3 modes | See test step 14 |
| 13 | `gui/scanner_tab.py` | 400 | Scanner tab with stats, log, settings | App launches with 7 tabs |
| 14 | `tests/test_scanner.py` | 80 | Test scanner init, mode validation, stop | `python -m unittest tests/test_scanner -v` |

### Phase 5: Integration + Headless (depends on everything)

| Step | File | Est. Lines | What to Build | Verify |
|------|------|-----------|---------------|--------|
| 15 | `main.py` (modify) | +80 | Add --headless flag, scanner tab, argparse | `python main.py --help` shows options |
| 16 | `solvers/btc_solver.py` (modify) | +20 | Add notifier + balance calls to _record_win | Existing tests still pass |
| 17 | `gui/dashboard_tab.py` (modify) | +30 | Add Telegram status + scanner stats | Dashboard shows new indicators |
| 18 | `Procfile` | 1 | Railway deployment config | File exists |
| 19 | `railway.toml` | 8 | Railway settings | File exists with valid TOML |
| 20 | `requirements.txt` | 1 | Empty (documents zero deps) | File exists |

### Phase 6: Final Verification

| Step | Action | Verify |
|------|--------|--------|
| 21 | Run ALL tests | `python -m unittest discover tests/ -v` → all pass |
| 22 | Launch GUI mode | `python main.py` → 7 tabs visible, no errors |
| 23 | Launch headless mode | `python main.py --headless` → starts scanner, shows banner |
| 24 | Test Telegram (after Dave gets chat ID) | Send test message → appears in Telegram |
| 25 | Run quality checklist | Section 13 below |

---

## 12. TESTING PLAN

### 12.1 New Test Files

**tests/test_config.py (~60 lines):**
```python
class TestConfig(unittest.TestCase):
    def test_load_creates_default(self):
        """First load creates config.json with defaults."""

    def test_get_dot_notation(self):
        """get('telegram.bot_token') returns correct value."""

    def test_set_and_persist(self):
        """set('telegram.chat_id', '123') persists to file."""

    def test_missing_key_returns_default(self):
        """get('nonexistent.key', 'fallback') returns 'fallback'."""

    def test_validate_empty_token(self):
        """validate() warns about empty bot_token."""
```

**tests/test_notifier.py (~50 lines):**
```python
class TestNotifier(unittest.TestCase):
    def test_is_configured_false_by_default(self):
        """is_configured() returns False when token/chat_id empty."""

    def test_message_formatting(self):
        """notify_solve() produces valid HTML message."""

    def test_send_fails_silently_when_unconfigured(self):
        """send_message() returns False when not configured, doesn't crash."""

    def test_rate_limiting(self):
        """Back-to-back sends respect rate limit."""
```

**tests/test_balance.py (~50 lines):**
```python
class TestBalance(unittest.TestCase):
    def test_result_dict_structure(self):
        """check_balance() returns dict with all required keys."""

    def test_invalid_address_returns_error(self):
        """Invalid address returns success=False with error message."""

    def test_offline_returns_error(self):
        """When offline, returns success=False gracefully."""
```

**tests/test_bip39.py (~120 lines):**
```python
class TestMnemonic(unittest.TestCase):
    def test_generates_12_words(self):
        """generate_mnemonic(128) returns 12 space-separated words."""

    def test_all_words_in_wordlist(self):
        """Every generated word is in the BIP39 wordlist."""

    def test_different_each_time(self):
        """Two calls produce different mnemonics."""

    def test_known_vector_seed(self):
        """Known mnemonic produces known seed (BIP39 test vector)."""

class TestBIP32(unittest.TestCase):
    def test_known_master_key(self):
        """Known seed produces known master key (BIP32 test vector)."""

    def test_derive_child_key(self):
        """Child key derivation matches known vector."""

class TestBIP44(unittest.TestCase):
    def test_derives_20_addresses(self):
        """derive_btc_keys() returns 20 valid Bitcoin addresses."""

    def test_addresses_are_different(self):
        """All 20 derived addresses are unique."""

    def test_addresses_start_with_1(self):
        """All P2PKH addresses start with '1'."""

class TestRandomKey(unittest.TestCase):
    def test_in_valid_range(self):
        """Random key is between 1 and N-1."""

    def test_batch_size(self):
        """generate_random_keys_batch(100) returns exactly 100 keys."""
```

**tests/test_scanner.py (~80 lines):**
```python
class TestScannerSolver(unittest.TestCase):
    def test_init_modes(self):
        """ScannerSolver accepts all 3 modes."""

    def test_invalid_mode_raises(self):
        """Invalid mode raises ValueError."""

    def test_start_stop(self):
        """Scanner starts and stops cleanly."""

    def test_callback_receives_data(self):
        """Callback receives status updates with required keys."""

    def test_local_check_with_empty_richlist(self):
        """Local check returns False when rich list is empty."""
```

### 12.2 Existing Tests Must Still Pass

After all changes, the original 58 tests MUST still pass unchanged:
```
python -m unittest discover tests/ -v
# Expected: 58 original + ~25 new = ~83 tests, ALL passing
```

---

## 13. QUALITY CHECKLIST

Run through every item BEFORE declaring the update complete.

### Code Quality

- [ ] Every new function has a docstring
- [ ] Every new module has a module-level docstring
- [ ] No `TODO`, `FIXME`, or stub functions
- [ ] No hardcoded paths (all relative to project root)
- [ ] All imports at module level or documented lazy imports
- [ ] No circular imports (test: `python -c "import engines.config; import engines.notifier; import engines.balance; import engines.bip39; import solvers.scanner_solver"`)
- [ ] Logging uses per-module logger: `logger = logging.getLogger(__name__)`
- [ ] All network calls have timeout parameter
- [ ] All network failures handled gracefully (no crashes)

### Functionality

- [ ] `python main.py` launches with 7 tabs, no errors
- [ ] `python main.py --headless` starts scanner, shows banner
- [ ] `python main.py --help` shows all CLI options
- [ ] Config file auto-created on first run
- [ ] Bot token pre-filled in config.json
- [ ] `python tools/get_chat_id.py` runs without crash (OK if no chat ID yet)
- [ ] Scanner starts in each mode: random_key, seed_phrase, both
- [ ] Scanner stops cleanly when Stop button pressed
- [ ] Scanner stops cleanly on SIGINT in headless mode
- [ ] BIP39 test vectors pass (Section 11, Phase 3)
- [ ] Balance checker returns proper dict for valid address
- [ ] Balance checker returns error dict for invalid address
- [ ] Notifier returns False when not configured (doesn't crash)
- [ ] All 80+ tests pass: `python -m unittest discover tests/ -v`

### Integration

- [ ] BTC solver notifies Telegram on solve (when configured)
- [ ] BTC solver checks balance on solve (when online)
- [ ] Scanner notifies Telegram on hit (when configured)
- [ ] Scanner logs hits to `data/scanner_hits.json`
- [ ] Dashboard shows Telegram status
- [ ] Dashboard shows scanner stats
- [ ] Headless mode sends startup/shutdown Telegram messages
- [ ] Headless mode respects config for auto-start puzzles

### Edge Cases

- [ ] App works fully offline (no crashes when no internet)
- [ ] Telegram failures don't block solver threads
- [ ] Balance check failures don't block solver threads
- [ ] Config corruption → falls back to defaults (no crash)
- [ ] Empty rich_addresses.txt → scanner still runs (just no local checks)
- [ ] Scanner with 0 threads → raises error, not hang
- [ ] BIP39 with invalid strength → raises ValueError
- [ ] Multiple solvers + scanner running simultaneously → no thread conflicts

---

## 14. CONSTANTS & REFERENCE DATA

### 14.1 BIP39 English Wordlist

The complete 2048-word BIP39 English wordlist MUST be embedded directly in `engines/bip39.py` as a Python list. This avoids any external file dependency.

**Source:** https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt

**Format in code:**
```python
WORDLIST = [
    "abandon", "ability", "able", "about", "above", "absent", "absorb",
    "abstract", "absurd", "abuse", "access", "accident", "account",
    "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act",
    # ... all 2048 words ...
    "zoo"
]
assert len(WORDLIST) == 2048, "BIP39 wordlist must have exactly 2048 words"
```

Claude Code MUST embed the full 2048-word list — do NOT use an external file or URL.

### 14.2 Known Rich Addresses (Starter Set)

For `data/rich_addresses.txt`, include at minimum:

```
1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo
bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97
3M219KR5vEneNb47ewrPfWyb5jQ2DjxRP6
1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ
3LYJfcfHPXYJreMsASk2jkn69LWEYKzexb
1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF
3Kzh9qAqVWQhEsfQz7zEQL1EuSx5tyNLNS
1HQ3Go3ggs8pFnXuHVHRytPCq5fGG8Hbhx
bc1qa5wkgaew2dkv56kc6hp24cc2narsv09mg5jkm
```

Claude Code should populate this with at least 200 known high-balance addresses. These are publicly available on any blockchain explorer.

### 14.3 Telegram API Reference

```
Base URL: https://api.telegram.org/bot{TOKEN}/

Endpoints used:
- sendMessage: POST with {chat_id, text, parse_mode}
- getUpdates: GET (used only in tools/get_chat_id.py)

Parse modes: "HTML" (we use this)
HTML tags supported: <b>, <i>, <u>, <s>, <code>, <pre>, <a href="">

Max message length: 4096 characters
Rate limit: 30 messages/second (we use 1 per 2 seconds to be safe)

Bot token format: {numbers}:{alphanumeric-string}
Chat ID format: positive integer (for private chats)
```

### 14.4 Blockstream API Reference

```
Base URL: https://blockstream.info/api

Endpoints used:
- GET /address/{address}           → address stats
- GET /address/{address}/utxo      → unspent outputs

Response format (GET /address/{address}):
{
  "address": "1A1zP1...",
  "chain_stats": {
    "funded_txo_count": 3,
    "funded_txo_sum": 500000,
    "spent_txo_count": 1,
    "spent_txo_sum": 100000,
    "tx_count": 4
  },
  "mempool_stats": {
    "funded_txo_count": 0,
    "funded_txo_sum": 0,
    "spent_txo_count": 0,
    "spent_txo_sum": 0,
    "tx_count": 0
  }
}

Rate limit: ~10 requests/second (we use 2/second to be safe)
No API key needed.
No CORS restrictions (server-to-server).
```

---

## 15. EDGE CASES & ERROR HANDLING

### 15.1 Network Failures

| Scenario | Expected Behavior |
|----------|-------------------|
| No internet at startup | App launches normally, Telegram/balance features disabled |
| Internet drops during scan | Scanner continues offline, online checks return error |
| Telegram API down | send_message returns False, logged to nps.log |
| Blockstream API down | check_balance returns success=False with error |
| Slow network (>10s) | All urllib calls have timeout=10, fail gracefully |
| DNS failure | Caught by urllib, returned as error |

### 15.2 Data Corruption

| Scenario | Expected Behavior |
|----------|-------------------|
| config.json is invalid JSON | Deleted and recreated with defaults |
| config.json is missing | Created with defaults |
| scanner_hits.json is corrupt | Recreated as empty list |
| rich_addresses.txt is missing | Scanner runs without local checking |
| rich_addresses.txt has bad lines | Bad lines silently skipped |
| data/ directory missing | Created automatically |

### 15.3 Thread Safety

| Resource | Protection |
|----------|-----------|
| config.json reads | Module-level cache, reloaded on load_config() |
| config.json writes | threading.Lock in config.py |
| Telegram sends | threading.Lock + rate limiter |
| scanner_hits.json | threading.Lock in scanner_solver |
| Balance API calls | Rate limiter (0.5s between calls) |
| Scanner stop | self.running = False (atomic bool check in loop) |

### 15.4 Resource Limits

| Resource | Limit | Why |
|----------|-------|-----|
| AI cache files | 200 max | Disk space (existing behavior) |
| Solve history | 10,000 records | Memory + disk (existing behavior) |
| Scanner hits log | 10,000 records | Disk space |
| Telegram error notifications | 10 per hour | Prevent spam |
| Rich address set | ~200 initially, expandable | Memory (~50KB for 1000 addresses) |
| Scanner threads | 1-4 (config) | CPU usage |
| BIP39 batch size | 1-10,000 (config) | Memory |

---

## SUMMARY: WHAT GETS BUILT

| # | File | Type | Lines | Phase |
|---|------|------|-------|-------|
| 1 | `engines/config.py` | New | 120 | 1 |
| 2 | `config.json` | New | 30 | 1 |
| 3 | `engines/notifier.py` | New | 200 | 2 |
| 4 | `tools/get_chat_id.py` | New | 50 | 2 |
| 5 | `engines/balance.py` | New | 180 | 2 |
| 6 | `engines/bip39.py` | New | 450 | 3 |
| 7 | `data/rich_addresses.txt` | New | 200 | 3 |
| 8 | `solvers/scanner_solver.py` | New | 350 | 4 |
| 9 | `gui/scanner_tab.py` | New | 400 | 4 |
| 10 | `main.py` | Modified | +80 | 5 |
| 11 | `solvers/btc_solver.py` | Modified | +20 | 5 |
| 12 | `gui/dashboard_tab.py` | Modified | +30 | 5 |
| 13 | `Procfile` | New | 1 | 5 |
| 14 | `railway.toml` | New | 8 | 5 |
| 15 | `requirements.txt` | New | 1 | 5 |
| 16 | `tests/test_config.py` | New | 60 | 1 |
| 17 | `tests/test_notifier.py` | New | 50 | 2 |
| 18 | `tests/test_balance.py` | New | 50 | 2 |
| 19 | `tests/test_bip39.py` | New | 120 | 3 |
| 20 | `tests/test_scanner.py` | New | 80 | 4 |
| | **Total new code** | | **~2,530** | |
| | **Total after update** | | **~9,860** | |

---

## HOW TO USE THIS FILE

### For Claude Code:

```
Read UPDATE_V1.md completely — every section.
Then read BLUEPRINT.md for the existing architecture context.
Then read the existing source files to understand integration points.

Build in EXACT phase order (Phase 1 → 2 → 3 → 4 → 5 → 6).
Run tests after EACH phase before moving to next.
Run the full quality checklist (Section 13) at the end.

Key rules:
- Zero pip dependencies — stdlib only
- All network calls must have timeout and try/except
- All network features fail silently (return False/error dict)
- Never block solver threads for network I/O
- BIP39 wordlist MUST be embedded in bip39.py (all 2048 words)
- Bot token is already known: 8229103669:AAHv98IVTbtMXENK48DHwT2DXOQ5p1vXJIE
- Chat ID is unknown — Dave will run get_chat_id.py to get it
```

### For Dave:

After Claude Code finishes building:
1. Run `python main.py` → verify 7 tabs appear
2. Open Telegram → send "hello" to @xnpsx_bot
3. Run `python tools/get_chat_id.py` → saves Chat ID
4. Run `python main.py` again → Telegram status should show ✅
5. Click "Test Notification" in Scanner tab → check Telegram
6. Start the scanner → watch it run
7. For 24/7 server: push to GitHub → deploy on Railway

---

*End of UPDATE_V1.md — Upload this + BLUEPRINT.md to Claude Code to build everything.*


---

## 16. ADDENDUM A: MULTI-CHAIN SUPPORT + LIVE FEED

> **Added:** February 6, 2026
> **Why:** Original spec only checked Bitcoin. Dave wants to check ALL valuable chains
> (BTC, ETH, USDT, USDC, BNB, etc.) from the same seed phrase, and see
> every check happening live in the GUI.
>
> **This addendum MODIFIES sections 6, 7, 8, 9, 11, 12, 13 of the main spec.**
> Claude Code: read the main spec first, then apply these modifications on top.

---

### A.1 WHAT CHANGES

| Original Spec | After Addendum |
|---------------|----------------|
| Balance checker: Bitcoin only (Blockstream API) | Multi-chain: BTC + ETH + ERC-20 tokens (USDT, USDC, DAI, WBTC) |
| Scanner generates BTC addresses only | Scanner derives BTC + ETH addresses from same key/seed |
| Scanner tab shows stats summary | Scanner tab shows LIVE FEED of every check in scrolling table |
| Dashboard shows scanner count only | Dashboard shows live mini-feed of recent checks |
| No Ethereum support | Full Ethereum address derivation + Keccak-256 implementation |
| No ERC-20 token support | Check top token balances via JSON-RPC |

### A.2 NEW FILE: `engines/keccak.py`

```
Purpose: Pure Python Keccak-256 implementation (Ethereum uses this, NOT SHA3-256)
Size: ~180 lines
Dependencies: NONE (pure math)
Why: Python's hashlib.sha3_256 uses NIST padding which produces DIFFERENT output
     than Ethereum's Keccak-256. We MUST implement the original Keccak.
```

**CRITICAL:** `hashlib.sha3_256` is NOT compatible with Ethereum. The NIST SHA-3 standard
added a padding byte (0x06) that changes the output. Ethereum uses original Keccak with
padding byte 0x01. They produce completely different hashes for the same input.

**Verification test (MUST pass):**
```python
# The empty string hash is the canonical test
from engines.keccak import keccak256
result = keccak256(b"").hex()
assert result == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"

# "hello" hash
result2 = keccak256(b"hello").hex()
assert result2 == "1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8"

# Compare with sha3_256 to prove they're DIFFERENT
import hashlib
sha3 = hashlib.sha3_256(b"").hexdigest()
assert sha3 != result  # MUST be different!
```

**Implementation specification:**

```python
"""
Pure Python Keccak-256 — the hash function used by Ethereum.

NOT the same as SHA3-256 (NIST added different padding).
This implements the original Keccak with rate=1088, capacity=512, output=256.

Reference: https://keccak.team/keccak_specs_summary.html
"""

# Keccak constants
ROUND_CONSTANTS = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

ROTATION_OFFSETS = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]

MASK64 = 0xFFFFFFFFFFFFFFFF


def _rol64(x, n):
    """64-bit rotate left."""
    return ((x << n) | (x >> (64 - n))) & MASK64


def _keccak_f1600(state):
    """Keccak-f[1600] permutation — 24 rounds."""
    lanes = [[0] * 5 for _ in range(5)]
    for x in range(5):
        for y in range(5):
            offset = 8 * (x + 5 * y)
            lanes[x][y] = int.from_bytes(state[offset:offset + 8], 'little')

    for round_idx in range(24):
        # θ (theta)
        C = [lanes[x][0] ^ lanes[x][1] ^ lanes[x][2] ^ lanes[x][3] ^ lanes[x][4]
             for x in range(5)]
        D = [C[(x - 1) % 5] ^ _rol64(C[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                lanes[x][y] ^= D[x]

        # ρ (rho) and π (pi)
        B = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                B[y][(2 * x + 3 * y) % 5] = _rol64(lanes[x][y],
                                                      ROTATION_OFFSETS[x][y])

        # χ (chi)
        for x in range(5):
            for y in range(5):
                lanes[x][y] = B[x][y] ^ ((~B[(x + 1) % 5][y] & MASK64) &
                                           B[(x + 2) % 5][y])

        # ι (iota)
        lanes[0][0] ^= ROUND_CONSTANTS[round_idx]

    result = bytearray(200)
    for x in range(5):
        for y in range(5):
            offset = 8 * (x + 5 * y)
            result[offset:offset + 8] = lanes[x][y].to_bytes(8, 'little')
    return bytes(result)


def keccak256(data: bytes) -> bytes:
    """Keccak-256 hash (Ethereum-compatible, NOT NIST SHA3-256).
    Returns 32 bytes."""
    rate = 136  # (1600 - 512) / 8 = 136 bytes
    state = bytearray(200)

    # Absorb
    offset = 0
    while offset + rate <= len(data):
        for i in range(rate):
            state[i] ^= data[offset + i]
        state = bytearray(_keccak_f1600(state))
        offset += rate

    # Final block + padding
    remaining = data[offset:]
    block = bytearray(rate)
    block[:len(remaining)] = remaining
    block[len(remaining)] ^= 0x01    # Keccak padding (NOT 0x06 like SHA3)
    block[rate - 1] ^= 0x80
    for i in range(rate):
        state[i] ^= block[i]
    state = bytearray(_keccak_f1600(state))

    # Squeeze (only need 32 bytes for 256-bit output)
    return bytes(state[:32])
```

Claude Code MUST implement this exactly. The padding byte `0x01` is what makes this
Keccak-256 instead of SHA3-256 (which uses `0x06`). Getting this wrong = wrong Ethereum addresses.

---

### A.3 MODIFY: `engines/bip39.py` — Add Ethereum Derivation

Add these functions to the existing bip39.py specification:

```python
# ── Ethereum Address Derivation ──

def derive_eth_keys(seed: bytes, account: int = 0, count: int = 20) -> list[dict]:
    """Derive Ethereum keys using BIP44 path: m/44'/60'/account'/0/i
    Returns list of:
    {
        "path": "m/44'/60'/0'/0/0",
        "private_key": int,
        "address": "0xABC...",    # Ethereum address (checksummed)
    }
    """
    from engines.crypto import scalar_multiply, pubkey_to_compressed

    master_key, master_chain = seed_to_master_key(seed)

    # m/44'
    key, chain = derive_child_key(master_key, master_chain, 44, hardened=True)
    # m/44'/60'  (Ethereum coin type = 60)
    key, chain = derive_child_key(key, chain, 60, hardened=True)
    # m/44'/60'/account'
    key, chain = derive_child_key(key, chain, account, hardened=True)
    # m/44'/60'/account'/0  (external chain)
    key, chain = derive_child_key(key, chain, 0, hardened=False)

    results = []
    for i in range(count):
        child_key, _ = derive_child_key(key, chain, i, hardened=False)
        k_int = int.from_bytes(child_key, "big")
        results.append({
            "path": f"m/44'/60'/{account}'/0/{i}",
            "private_key": k_int,
            "address": privkey_to_eth_address(k_int),
        })

    return results


def privkey_to_eth_address(private_key: int) -> str:
    """Private key → Ethereum address (EIP-55 checksummed).

    Process:
    1. private_key → public key (secp256k1, UNCOMPRESSED, drop 0x04 prefix)
    2. Keccak-256 hash of public key bytes
    3. Take last 20 bytes → address
    4. Apply EIP-55 mixed-case checksum
    """
    from engines.crypto import scalar_multiply
    from engines.keccak import keccak256

    # Get uncompressed public key (64 bytes: x + y, no 0x04 prefix)
    pub = scalar_multiply(private_key)
    pub_bytes = pub.x.to_bytes(32, 'big') + pub.y.to_bytes(32, 'big')

    # Keccak-256 hash → take last 20 bytes
    h = keccak256(pub_bytes)
    addr_bytes = h[-20:]
    addr_hex = addr_bytes.hex()

    # EIP-55 checksum (mixed case)
    addr_hash = keccak256(addr_hex.encode('ascii')).hex()
    checksummed = '0x'
    for i, c in enumerate(addr_hex):
        if c in '0123456789':
            checksummed += c
        elif int(addr_hash[i], 16) >= 8:
            checksummed += c.upper()
        else:
            checksummed += c.lower()

    return checksummed


def derive_all_chains(seed: bytes, account: int = 0, count: int = 5) -> dict:
    """Derive keys for ALL supported chains from one seed.
    Returns:
    {
        "btc": [{"path": "m/44'/0'/0'/0/0", "private_key": int, "address": "1ABC..."}],
        "eth": [{"path": "m/44'/60'/0'/0/0", "private_key": int, "address": "0xABC..."}],
    }

    Note: count defaults to 5 (not 20) to reduce derivation time for scanning.
    """
    return {
        "btc": derive_btc_keys(seed, account, count),
        "eth": derive_eth_keys(seed, account, count),
    }


def privkey_to_all_addresses(private_key: int) -> dict:
    """Derive BTC + ETH addresses from a single private key.
    Returns:
    {
        "btc": "1ABC...",
        "eth": "0xABC...",
    }

    Note: Same private key → different addresses on each chain.
    This is how crypto works — the key is the same, the address format differs.
    """
    from engines.crypto import privkey_to_address
    return {
        "btc": privkey_to_address(private_key),
        "eth": privkey_to_eth_address(private_key),
    }
```

---

### A.4 MODIFY: `engines/balance.py` — Multi-Chain Balance Checking

The original spec only checked Bitcoin via Blockstream. This addendum adds Ethereum + ERC-20 tokens.

**Add to balance.py:**

```python
# ════════════════════════════════════════════════════════════
# Ethereum Balance Checking (JSON-RPC, no API key needed)
# ════════════════════════════════════════════════════════════

# Free public Ethereum RPC endpoints (no API key)
ETH_RPC_ENDPOINTS = [
    "https://eth.llamarpc.com",
    "https://rpc.ankr.com/eth",
    "https://ethereum.publicnode.com",
    "https://1rpc.io/eth",
]

# Top ERC-20 token contracts (Ethereum mainnet)
ERC20_TOKENS = {
    "USDT": {
        "contract": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "decimals": 6,
        "name": "Tether USD",
    },
    "USDC": {
        "contract": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "decimals": 6,
        "name": "USD Coin",
    },
    "DAI": {
        "contract": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "decimals": 18,
        "name": "Dai Stablecoin",
    },
    "WBTC": {
        "contract": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "decimals": 8,
        "name": "Wrapped BTC",
    },
    "WETH": {
        "contract": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "decimals": 18,
        "name": "Wrapped Ether",
    },
    "UNI": {
        "contract": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "decimals": 18,
        "name": "Uniswap",
    },
    "LINK": {
        "contract": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
        "decimals": 18,
        "name": "Chainlink",
    },
    "SHIB": {
        "contract": "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",
        "decimals": 18,
        "name": "Shiba Inu",
    },
}

_rpc_index = 0  # Round-robin through endpoints


def _eth_rpc_call(method: str, params: list) -> dict:
    """Make an Ethereum JSON-RPC call. Rotates through endpoints on failure."""
    import urllib.request
    import json
    global _rpc_index

    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }).encode("utf-8")

    # Try each endpoint
    for attempt in range(len(ETH_RPC_ENDPOINTS)):
        endpoint = ETH_RPC_ENDPOINTS[(_rpc_index + attempt) % len(ETH_RPC_ENDPOINTS)]
        try:
            req = urllib.request.Request(
                endpoint,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                _rpc_index = (_rpc_index + attempt) % len(ETH_RPC_ENDPOINTS)
                return result
        except Exception:
            continue

    return {"error": "All RPC endpoints failed"}


def check_eth_balance(address: str) -> dict:
    """Check ETH balance of an Ethereum address.
    Returns:
    {
        "success": True/False,
        "address": "0xABC...",
        "balance_wei": 1000000000000000000,
        "balance_eth": 1.0,
        "has_balance": True,
        "error": None,
    }
    """
    try:
        result = _eth_rpc_call("eth_getBalance", [address, "latest"])
        if "error" in result and isinstance(result["error"], str):
            return {"success": False, "address": address, "balance_wei": 0,
                    "balance_eth": 0.0, "has_balance": False, "error": result["error"]}

        hex_balance = result.get("result", "0x0")
        balance_wei = int(hex_balance, 16)
        balance_eth = balance_wei / 1e18

        return {
            "success": True,
            "address": address,
            "balance_wei": balance_wei,
            "balance_eth": balance_eth,
            "has_balance": balance_wei > 0,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "address": address, "balance_wei": 0,
                "balance_eth": 0.0, "has_balance": False, "error": str(e)}


def check_erc20_balance(address: str, token_symbol: str) -> dict:
    """Check ERC-20 token balance.
    Uses eth_call with balanceOf(address) on the token contract.

    Returns:
    {
        "success": True/False,
        "address": "0xABC...",
        "token": "USDT",
        "balance_raw": 1000000,
        "balance_human": 1.0,        # adjusted for decimals
        "has_balance": True,
        "error": None,
    }
    """
    token = ERC20_TOKENS.get(token_symbol)
    if not token:
        return {"success": False, "address": address, "token": token_symbol,
                "balance_raw": 0, "balance_human": 0.0, "has_balance": False,
                "error": f"Unknown token: {token_symbol}"}

    # balanceOf(address) function selector = 0x70a08231
    # Pad address to 32 bytes
    addr_clean = address.lower().replace("0x", "")
    call_data = "0x70a08231" + addr_clean.zfill(64)

    try:
        result = _eth_rpc_call("eth_call", [
            {"to": token["contract"], "data": call_data},
            "latest"
        ])
        if "error" in result and isinstance(result["error"], str):
            return {"success": False, "address": address, "token": token_symbol,
                    "balance_raw": 0, "balance_human": 0.0, "has_balance": False,
                    "error": result["error"]}

        hex_balance = result.get("result", "0x0")
        balance_raw = int(hex_balance, 16)
        balance_human = balance_raw / (10 ** token["decimals"])

        return {
            "success": True,
            "address": address,
            "token": token_symbol,
            "token_name": token["name"],
            "balance_raw": balance_raw,
            "balance_human": balance_human,
            "has_balance": balance_raw > 0,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "address": address, "token": token_symbol,
                "balance_raw": 0, "balance_human": 0.0, "has_balance": False,
                "error": str(e)}


def check_all_balances(btc_address: str, eth_address: str,
                       tokens: list = None) -> dict:
    """Check balances across ALL chains for a key pair.

    Default tokens checked: USDT, USDC, DAI, WBTC

    Returns:
    {
        "btc": {"address": "1ABC...", "balance_btc": 0.0, "has_balance": False, ...},
        "eth": {"address": "0xABC...", "balance_eth": 0.0, "has_balance": False, ...},
        "tokens": {
            "USDT": {"balance_human": 0.0, "has_balance": False, ...},
            "USDC": {"balance_human": 0.0, "has_balance": False, ...},
            ...
        },
        "total_usd_estimate": 0.0,
        "has_any_balance": False,
    }
    """
    if tokens is None:
        tokens = ["USDT", "USDC", "DAI", "WBTC"]

    btc_result = check_balance(btc_address)      # existing BTC function
    eth_result = check_eth_balance(eth_address)

    token_results = {}
    for token_sym in tokens:
        token_results[token_sym] = check_erc20_balance(eth_address, token_sym)

    has_any = (
        btc_result.get("has_balance", False) or
        eth_result.get("has_balance", False) or
        any(t.get("has_balance", False) for t in token_results.values())
    )

    return {
        "btc": btc_result,
        "eth": eth_result,
        "tokens": token_results,
        "has_any_balance": has_any,
    }
```

**Rate limiting for multi-chain:**
- BTC (Blockstream): 0.5s between calls (existing)
- ETH (JSON-RPC): 0.3s between calls
- ERC-20: each token is a separate call, 0.2s between
- Full check of 1 address across all chains: ~2-3 seconds total
- This means online checking should be RARE — only every N keys (configurable)

---

### A.5 MODIFY: `config.json` — Add Multi-Chain Settings

Add to the config.json specification:

```json
{
  "balance_check": {
    "enabled": true,
    "btc_api_url": "https://blockstream.info/api",
    "eth_rpc_endpoints": [
      "https://eth.llamarpc.com",
      "https://rpc.ankr.com/eth",
      "https://ethereum.publicnode.com"
    ],
    "tokens_to_check": ["USDT", "USDC", "DAI", "WBTC"],
    "check_interval_seconds": 60,
    "timeout_seconds": 10
  },
  "scanner": {
    "mode": "random_key",
    "threads": 2,
    "batch_size": 1000,
    "check_balance_every_n": 10000,
    "use_scoring": false,
    "chains": ["btc", "eth"],
    "addresses_per_seed": 5,
    "rich_list_path": "data/rich_addresses.txt",
    "live_feed_max_rows": 200
  }
}
```

---

### A.6 MODIFY: `solvers/scanner_solver.py` — Multi-Chain + Live Feed Data

The scanner must now:
1. Derive BOTH BTC and ETH addresses from each key/seed
2. Emit detailed per-check data for the live feed
3. Check token balances when doing online checks

**New callback data format (replaces the one in Section 7.2):**

```python
# Every progress update now includes a `live_feed` list of recent checks
self._emit({
    "status": "running",
    "message": f"Scanned {tested:,} keys | {hits} hits | {speed:.0f}/s",
    "progress": -1,
    "speed": speed,
    "operations": tested,
    "candidates_tested": tested,
    "candidates_total": -1,
    "hits": hits,
    "current_best": None,
    "solution": None,

    # NEW: Live feed batch — last N checks for the GUI to display
    "live_feed": [
        {
            "timestamp": "14:30:01.234",
            "type": "key",                    # "key" or "seed"
            "source": "0x3a7f...8b2c",        # truncated private key or seed words
            "addresses": {
                "btc": "1ABC...XYZ",
                "eth": "0xabc...xyz",
            },
            "balances": {
                "btc": 0.0,
                "eth": 0.0,
                "usdt": 0.0,
                "usdc": 0.0,
            },
            "checked_online": False,           # True if API was called
            "has_balance": False,              # True if ANY balance > 0
        },
        # ... more entries
    ],
})
```

**Scanner loop modification for live feed:**

```python
def _scan_random_keys(self):
    from engines.bip39 import generate_random_keys_batch, privkey_to_all_addresses
    from engines.crypto import privkey_to_address
    import time

    tested = 0
    hits = 0
    start = time.time()
    online_counter = 0
    check_every_n = self.check_every_n
    feed_buffer = []          # Collect entries for live feed
    feed_max = 50             # Send last 50 entries per update

    while self.running:
        keys = generate_random_keys_batch(self.batch_size)

        for key in keys:
            if not self.running:
                return

            # Derive addresses for ALL chains
            addresses = privkey_to_all_addresses(key)
            tested += 1
            online_counter += 1

            # Build feed entry
            entry = {
                "timestamp": time.strftime("%H:%M:%S"),
                "type": "key",
                "source": hex(key)[:10] + "..." + hex(key)[-6:],
                "addresses": addresses,
                "balances": {"btc": 0.0, "eth": 0.0},
                "checked_online": False,
                "has_balance": False,
            }

            # Local check (BTC rich list — instant)
            if self._local_check(addresses["btc"]):
                entry["has_balance"] = True
                hits += 1
                self._record_hit(addresses, key, {}, "random_key_local")

            # Online check (periodic)
            if self.check_balance_online and online_counter >= check_every_n:
                online_counter = 0
                entry["checked_online"] = True
                from engines.balance import check_all_balances
                result = check_all_balances(addresses["btc"], addresses["eth"])
                if result["has_any_balance"]:
                    entry["has_balance"] = True
                    entry["balances"] = {
                        "btc": result["btc"].get("balance_btc", 0),
                        "eth": result["eth"].get("balance_eth", 0),
                        "usdt": result["tokens"].get("USDT", {}).get("balance_human", 0),
                        "usdc": result["tokens"].get("USDC", {}).get("balance_human", 0),
                    }
                    hits += 1
                    self._record_hit(addresses, key, result, "random_key_online")

            feed_buffer.append(entry)
            if len(feed_buffer) > feed_max:
                feed_buffer = feed_buffer[-feed_max:]

            # Emit progress every 5,000 keys (with live feed)
            if tested % 5000 == 0:
                elapsed = time.time() - start
                speed = tested / max(0.001, elapsed)
                self._emit({
                    "status": "running",
                    "message": f"Scanned {tested:,} keys | {hits} hits | {speed:.0f}/s",
                    "progress": -1,
                    "speed": speed,
                    "operations": tested,
                    "candidates_tested": tested,
                    "candidates_total": -1,
                    "hits": hits,
                    "current_best": None,
                    "solution": None,
                    "live_feed": list(feed_buffer),
                })
                feed_buffer.clear()
```

**Seed phrase scanning with multi-chain:**

```python
def _scan_seed_phrases(self):
    from engines.bip39 import generate_mnemonic, mnemonic_to_seed, derive_all_chains
    import time

    tested_seeds = 0
    tested_addresses = 0
    hits = 0
    start = time.time()
    feed_buffer = []

    while self.running:
        # Generate random 12-word mnemonic
        mnemonic = generate_mnemonic(128)
        seed = mnemonic_to_seed(mnemonic)

        # Derive addresses for ALL chains (5 per chain by default)
        all_keys = derive_all_chains(seed, account=0, count=self.addresses_per_seed)
        tested_seeds += 1

        words_preview = " ".join(mnemonic.split()[:3]) + "..."

        for chain, key_list in all_keys.items():
            for key_info in key_list:
                if not self.running:
                    return

                tested_addresses += 1
                address = key_info["address"]

                entry = {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "type": "seed",
                    "source": words_preview,
                    "addresses": {chain: address},
                    "balances": {},
                    "checked_online": False,
                    "has_balance": False,
                }

                # Local check (BTC only — we don't have ETH rich list)
                if chain == "btc" and self._local_check(address):
                    entry["has_balance"] = True
                    hits += 1

                feed_buffer.append(entry)

        # Online check after each seed (all derived addresses)
        if self.check_balance_online and tested_seeds % 100 == 0:
            # Check first BTC and ETH address of this seed
            btc_addr = all_keys["btc"][0]["address"]
            eth_addr = all_keys["eth"][0]["address"]
            from engines.balance import check_all_balances
            result = check_all_balances(btc_addr, eth_addr)
            if result["has_any_balance"]:
                hits += 1
                self._record_hit(
                    {"btc": btc_addr, "eth": eth_addr},
                    all_keys["btc"][0]["private_key"],
                    result,
                    "seed_phrase",
                    extra={"mnemonic": mnemonic}
                )

        if len(feed_buffer) > 50:
            feed_buffer = feed_buffer[-50:]

        # Progress update every 10 seeds
        if tested_seeds % 10 == 0:
            elapsed = time.time() - start
            speed = tested_addresses / max(0.001, elapsed)
            self._emit({
                "status": "running",
                "message": (f"Seeds: {tested_seeds:,} | Addresses: {tested_addresses:,} "
                           f"| {hits} hits | {speed:.0f} addr/s"),
                "progress": -1,
                "speed": speed,
                "operations": tested_addresses,
                "candidates_tested": tested_addresses,
                "candidates_total": -1,
                "hits": hits,
                "live_feed": list(feed_buffer),
            })
            feed_buffer.clear()
```

---

### A.7 MODIFY: `gui/scanner_tab.py` — Live Feed Table

Replace the simple log panel from Section 9.1 with a real-time scrolling table.

**New layout (replaces the layout in Section 9.1):**

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Wallet Scanner                                          [⚙ Settings]    │
│  ⚠️ Random scanning odds: ~1 in 10^41. Puzzle solving has real odds.     │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Mode: (●) Random Keys  ( ) Seed Phrases  ( ) Both                      │
│  Chains: [✓] BTC  [✓] ETH  [✓] USDT  [✓] USDC  [ ] DAI  [ ] WBTC      │
│                                                                          │
│  ┌──────────┐ ┌──────────┐                                               │
│  │ ▶  Start │ │ ■  Stop  │                                               │
│  └──────────┘ └──────────┘                                               │
│                                                                          │
│  ┌─ Stats ───────────────────────────────────────────────────────────┐    │
│  │  Keys: 1,234,567  Seeds: 12,345  Addresses: 310,590             │    │
│  │  Speed: 45,000/s  Online checks: 123  Hits: 0                   │    │
│  │  Running: 02:34:15  Telegram: ✅                                 │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─ Live Feed ───────────────────────────────────────────────────────┐    │
│  │ TIME     TYPE  SOURCE          BTC ADDRESS     ETH ADDRESS       │    │
│  │                                BTC    ETH    USDT   USDC   CHK   │    │
│  ├──────────────────────────────────────────────────────────────────  │    │
│  │ 14:30:01 KEY  0x3a7f...8b2c   1Abc...Xyz     0xabc...xyz        │    │
│  │                                0.000  0.000  0.000  0.000  ·     │    │
│  │ 14:30:01 KEY  0x9c12...4d5e   1Def...Uvw     0xdef...uvw        │    │
│  │                                0.000  0.000  0.000  0.000  ·     │    │
│  │ 14:30:02 SEED abandon ab...   1Ghi...Rst     0xghi...rst        │    │
│  │                                0.000  0.000  0.000  0.000  ·     │    │
│  │ 14:30:02 KEY  0x5f88...1a3b   1Jkl...Mno     0xjkl...mno        │    │
│  │                                0.000  0.000  0.000  0.000  API ✓ │    │
│  │                                                                   │    │
│  │ (scrolls automatically, last 200 entries, green row = HIT)        │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─ Activity Log ────────────────────────────────────────────────────┐    │
│  │ 14:30:15 | Online check: 1ABC... → BTC: 0 | ETH: 0 | USDT: 0   │    │
│  │ 14:30:30 | Seed #12,345 checked (5 BTC + 5 ETH addresses)       │    │
│  └───────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────────┘
```

**Live Feed widget implementation:**

```python
class LiveFeedTable(tk.Frame):
    """Scrolling table showing real-time scanner activity."""

    MAX_ROWS = 200  # Keep last 200 entries in memory

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)

        # Header row
        header = tk.Frame(self, bg=COLORS["bg_input"])
        header.pack(fill="x")
        headers = ["Time", "Type", "Source", "BTC Address", "ETH Address",
                    "BTC", "ETH", "USDT", "USDC", "Chk"]
        widths = [8, 4, 14, 14, 14, 7, 7, 7, 7, 4]
        for text, w in zip(headers, widths):
            tk.Label(header, text=text, font=FONTS["mono_sm"],
                     fg=COLORS["text_dim"], bg=COLORS["bg_input"],
                     width=w, anchor="w").pack(side="left", padx=1)

        # Scrollable body
        container = tk.Frame(self, bg=COLORS["bg_card"])
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=COLORS["bg_card"],
                                highlightthickness=0)
        self.scrollbar = tk.Scrollbar(container, orient="vertical",
                                      command=self.canvas.yview)
        self.scrollable = tk.Frame(self.canvas, bg=COLORS["bg_card"])

        self.scrollable.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.rows = []
        self.auto_scroll = True

    def add_entries(self, entries: list):
        """Add batch of feed entries. Each entry is a dict from scanner callback."""
        for entry in entries:
            self._add_row(entry)

        # Trim old rows
        while len(self.rows) > self.MAX_ROWS:
            old = self.rows.pop(0)
            old.destroy()

        # Auto-scroll to bottom
        if self.auto_scroll:
            self.canvas.yview_moveto(1.0)

    def _add_row(self, entry: dict):
        """Add a single row to the table."""
        has_balance = entry.get("has_balance", False)
        bg = COLORS["bg_success"] if has_balance else COLORS["bg_card"]
        fg = COLORS["text_bright"] if has_balance else COLORS["text"]

        row = tk.Frame(self.scrollable, bg=bg)
        row.pack(fill="x", pady=1)

        # Column values
        btc_addr = entry.get("addresses", {}).get("btc", "—")
        eth_addr = entry.get("addresses", {}).get("eth", "—")
        balances = entry.get("balances", {})

        values = [
            entry.get("timestamp", ""),
            entry.get("type", "?").upper()[:4],
            entry.get("source", "")[:14],
            btc_addr[:6] + "..." + btc_addr[-4:] if len(btc_addr) > 12 else btc_addr,
            eth_addr[:6] + "..." + eth_addr[-4:] if len(eth_addr) > 12 else eth_addr,
            f"{balances.get('btc', 0):.3f}",
            f"{balances.get('eth', 0):.3f}",
            f"{balances.get('usdt', 0):.1f}",
            f"{balances.get('usdc', 0):.1f}",
            "API ✓" if entry.get("checked_online") else "·",
        ]
        widths = [8, 4, 14, 14, 14, 7, 7, 7, 7, 4]

        for val, w in zip(values, widths):
            tk.Label(row, text=val, font=FONTS["mono_sm"], fg=fg, bg=bg,
                     width=w, anchor="w").pack(side="left", padx=1)

        self.rows.append(row)

    def clear(self):
        """Clear all rows."""
        for row in self.rows:
            row.destroy()
        self.rows.clear()
```

---

### A.8 MODIFY: `gui/dashboard_tab.py` — Live Mini-Feed

Add a compact live feed to the dashboard showing the last 10 scanner checks.

```python
# In dashboard_tab.py, add after the "Recent Solves" section:

# Scanner Mini-Feed
tk.Label(main, text="Scanner Activity", font=FONTS["subhead"],
         fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(8, 4))

self.mini_feed = tk.Frame(main, bg=COLORS["bg_card"], bd=1, relief="solid")
self.mini_feed.pack(fill="x")

self.mini_feed_labels = []
for i in range(10):
    lbl = tk.Label(self.mini_feed, text="—",
                   font=FONTS["mono_sm"], fg=COLORS["text_dim"],
                   bg=COLORS["bg_card"], anchor="w", padx=8, pady=1)
    lbl.pack(fill="x")
    self.mini_feed_labels.append(lbl)

def update_mini_feed(self, entries: list):
    """Update dashboard mini-feed with last 10 scanner entries."""
    for i, lbl in enumerate(self.mini_feed_labels):
        if i < len(entries):
            e = entries[-(i + 1)]  # Most recent first
            btc = e.get("addresses", {}).get("btc", "—")[:10]
            eth = e.get("addresses", {}).get("eth", "—")[:10]
            has = "💰" if e.get("has_balance") else "  "
            text = f"{e.get('timestamp', '')} {has} BTC:{btc}.. ETH:{eth}.."
            fg = COLORS["success"] if e.get("has_balance") else COLORS["text_dim"]
            lbl.config(text=text, fg=fg)
        else:
            lbl.config(text="—", fg=COLORS["text_dim"])
```

---

### A.9 MODIFY: `engines/notifier.py` — Multi-Chain Notifications

Update `notify_scanner_hit` and `notify_balance_found` to show all chain balances:

```python
def notify_scanner_hit(address_dict: dict, private_key: str,
                       balances: dict, method: str) -> bool:
    """CRITICAL alert with multi-chain balance details.
    Message:
    🚨🚨🚨 SCANNER HIT! 🚨🚨🚨
    Method: random_key
    BTC: 1ABC... → 0.004 BTC
    ETH: 0xabc... → 1.23 ETH
    USDT: 500.00
    USDC: 0.00
    Private Key: 0xABC...
    ⚡ SECURE THIS IMMEDIATELY ⚡
    """
    btc_addr = address_dict.get("btc", "—")
    eth_addr = address_dict.get("eth", "—")

    btc_bal = balances.get("btc", {}).get("balance_btc", 0)
    eth_bal = balances.get("eth", {}).get("balance_eth", 0)
    token_lines = []
    for sym, data in balances.get("tokens", {}).items():
        bal = data.get("balance_human", 0)
        if bal > 0:
            token_lines.append(f"  {sym}: {bal:,.2f}")

    msg = (
        "🚨🚨🚨 <b>SCANNER HIT!</b> 🚨🚨🚨\n\n"
        f"<b>Method:</b> {method}\n"
        f"<b>BTC:</b> <code>{btc_addr}</code> → {btc_bal:.8f} BTC\n"
        f"<b>ETH:</b> <code>{eth_addr}</code> → {eth_bal:.6f} ETH\n"
    )
    if token_lines:
        msg += "<b>Tokens:</b>\n" + "\n".join(token_lines) + "\n"
    msg += (
        f"\n<b>Key:</b> <code>{private_key}</code>\n"
        "⚡ <b>SECURE THIS IMMEDIATELY</b> ⚡"
    )
    return send_message(msg)
```

---

### A.10 MODIFY: Build Order — Additional Steps

Insert these into the build order from Section 11:

**After Phase 2 Step 8, add:**

| Step | File | Est. Lines | What to Build | Verify |
|------|------|-----------|---------------|--------|
| 8b | `engines/keccak.py` | 180 | Pure Python Keccak-256 | Test vectors below |
| 8c | `tests/test_keccak.py` | 40 | Keccak-256 verification | `python -m unittest tests/test_keccak -v` |

**Keccak test vectors (MUST pass):**
```python
class TestKeccak256(unittest.TestCase):
    def test_empty_string(self):
        from engines.keccak import keccak256
        assert keccak256(b"").hex() == \
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"

    def test_hello(self):
        from engines.keccak import keccak256
        assert keccak256(b"hello").hex() == \
            "1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8"

    def test_not_sha3(self):
        """Prove Keccak-256 ≠ SHA3-256."""
        import hashlib
        from engines.keccak import keccak256
        data = b"test"
        assert keccak256(data).hex() != hashlib.sha3_256(data).hexdigest()

    def test_ethereum_address_derivation(self):
        """Known private key → known Ethereum address."""
        from engines.bip39 import privkey_to_eth_address
        # Private key 1 → known address
        addr = privkey_to_eth_address(1)
        assert addr.lower() == "0x7e5f4552091a69125d5dfcb7b8c2659029395bdf"
```

**Phase 3 modifications:**
- Step 9 (`engines/bip39.py`) now includes `derive_eth_keys()`, `privkey_to_eth_address()`, `derive_all_chains()`, and `privkey_to_all_addresses()` — add ~120 lines
- Step 11 (`tests/test_bip39.py`) adds ETH address derivation tests — add ~30 lines

**Phase 4 modifications:**
- Step 12 (`solvers/scanner_solver.py`) now emits `live_feed` data + multi-chain checking — add ~100 lines
- Step 13 (`gui/scanner_tab.py`) now includes `LiveFeedTable` widget + chain checkboxes — add ~200 lines

**Phase 5 modifications:**
- Step 17 (`gui/dashboard_tab.py`) now includes mini-feed of 10 recent checks — add ~40 lines
- `engines/balance.py` (Step 6) now includes ETH + ERC-20 checking — add ~200 lines

---

### A.11 MODIFY: Updated Line Count Estimates

| File | Original Est. | After Addendum | Reason |
|------|-------------|----------------|--------|
| `engines/keccak.py` | — (new) | 180 | Pure Python Keccak-256 |
| `engines/balance.py` | 180 | 380 | + ETH RPC + ERC-20 checking |
| `engines/bip39.py` | 450 | 570 | + ETH derivation + multi-chain |
| `solvers/scanner_solver.py` | 350 | 480 | + multi-chain + live feed data |
| `gui/scanner_tab.py` | 400 | 650 | + LiveFeedTable + chain selectors |
| `gui/dashboard_tab.py` | +30 | +70 | + mini-feed widget |
| `tests/test_keccak.py` | — (new) | 40 | Keccak verification |
| `tests/test_bip39.py` | 120 | 150 | + ETH derivation tests |
| **Total new code** | ~2,530 | **~3,550** | +1,020 lines from addendum |
| **Total after update** | ~9,860 | **~10,880** | |

---

### A.12 SUPPORTED CHAINS & TOKENS SUMMARY

| Chain | Derivation Path | Address Format | Balance API | Status |
|-------|----------------|----------------|-------------|--------|
| **Bitcoin (BTC)** | m/44'/0'/0'/0/i | 1ABC... (P2PKH) | Blockstream | ✅ Included |
| **Ethereum (ETH)** | m/44'/60'/0'/0/i | 0xABC... (EIP-55) | JSON-RPC (free) | ✅ Included |
| **USDT** | (ERC-20 on ETH) | Same as ETH | eth_call balanceOf | ✅ Included |
| **USDC** | (ERC-20 on ETH) | Same as ETH | eth_call balanceOf | ✅ Included |
| **DAI** | (ERC-20 on ETH) | Same as ETH | eth_call balanceOf | ✅ Included |
| **WBTC** | (ERC-20 on ETH) | Same as ETH | eth_call balanceOf | ✅ Included |
| **WETH** | (ERC-20 on ETH) | Same as ETH | eth_call balanceOf | ✅ Included |
| **UNI** | (ERC-20 on ETH) | Same as ETH | eth_call balanceOf | ✅ Included |
| **LINK** | (ERC-20 on ETH) | Same as ETH | eth_call balanceOf | ✅ Included |
| **SHIB** | (ERC-20 on ETH) | Same as ETH | eth_call balanceOf | ✅ Included |

**Why only BTC + ETH/ERC-20:**
- Same secp256k1 curve for both → reuse all existing EC math
- Same BIP39/BIP32 derivation → just change the coin type in BIP44 path
- ETH + ERC-20 covers ~70% of total crypto market value
- Adding BNB/Polygon/Tron would need different RPCs but same derivation — easy to add later

**NOT included (can add later):**
| Chain | Why Not Now | Effort to Add |
|-------|------------|---------------|
| BNB (BSC) | Same derivation as ETH, just different RPC URL | Low (~20 lines) |
| Polygon | Same derivation as ETH, just different RPC URL | Low (~20 lines) |
| Tron (TRX) | Different address format (Base58 + different hash) | Medium (~100 lines) |
| Solana | Completely different curve (Ed25519, not secp256k1) | High (~300 lines) |
| Litecoin | Same as BTC but different version byte | Low (~10 lines) |

---

### A.13 MODIFY: Quality Checklist — Additional Items

Add to Section 13:

**Multi-Chain:**
- [ ] Keccak-256 test vectors pass (empty string + "hello" + not-SHA3 proof)
- [ ] ETH address for private key 1 matches known address
- [ ] EIP-55 checksum produces mixed-case addresses
- [ ] ETH balance check returns valid dict via JSON-RPC
- [ ] ERC-20 balanceOf call works for USDT contract
- [ ] All RPC endpoints are tried on failure (rotation)
- [ ] check_all_balances() returns combined multi-chain result
- [ ] privkey_to_all_addresses() returns both BTC and ETH

**Live Feed:**
- [ ] LiveFeedTable shows scrolling entries in scanner tab
- [ ] Feed auto-scrolls to latest entry
- [ ] Feed shows truncated key/seed, BTC address, ETH address, balances
- [ ] Rows with balance > 0 are highlighted green
- [ ] Feed trims to 200 rows maximum (no memory leak)
- [ ] Dashboard mini-feed shows last 10 scanner entries
- [ ] Feed updates at readable speed (~every 5,000 keys, not every single key)

---

*End of Addendum A. This modifies UPDATE_V1.md — build everything together.*
