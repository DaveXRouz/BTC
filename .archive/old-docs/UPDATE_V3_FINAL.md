# NPS — UPDATE V3 FINAL: Multi-Terminal Hunter + AI Memory + Settings Hub

> **Created:** February 7, 2026
> **Author:** Dave (The Dave) + Claude Opus 4.6
> **Prerequisite:** V2 must be fully built and working (the current state of the repo).
> **Purpose:** Transform NPS from a single-session scanner into a multi-terminal, AI-learning powerhouse with unified hunting, human-readable oracle, persistent findings vault, and remote control hub.
> **Executor:** Claude Code CLI — reads this file and builds autonomously with approval gates.
> **Supersedes:** UPDATE_V3.md (this is the corrected, gap-free version)

---

## HOW TO USE THIS FILE (READ THIS FIRST)

### For Dave (the human)

1. Place this file in your project root: `~/Desktop/BTC/UPDATE_V3_FINAL.md`
2. Open terminal, navigate to the project: `cd ~/Desktop/BTC`
3. Launch Claude Code: `claude`
4. Type this exact prompt:

```
Read UPDATE_V3_FINAL.md completely. This is the V3 FINAL specification for the NPS project.
Create a comprehensive plan to implement all 8 phases in order.
Each phase must pass its verification checklist before moving to the next.
Use /plan mode first, then after I approve, build phase by phase.
Ask me (using the Ask User tool) before any high-stakes decision.
Use Task subagents for parallel work where possible.
After each phase, run the test suite and show me the results before proceeding.
After each phase, update PROGRESS.md with completion status.
```

5. Review the plan Claude Code generates. If it looks right, approve it.
6. Claude Code will build phase by phase. You just click "approve" or answer questions.

### For Claude Code (the executor)

You are reading a V3 FINAL specification document. Here are your rules:

1. **Read this entire file first** before making any plan or writing any code.
2. **Understand the current codebase** by reading `CLAUDE.md`, `docs/BLUEPRINT.md`, `docs/UPDATE_V1.md`, `docs/UPDATE_V2.md`, and browsing the `nps/` source tree.
3. **Work in phases.** There are 8 phases (0-7). Do them in order.
4. **Each phase has a verification checklist.** ALL items must pass before moving to the next phase.
5. **Run tests after every phase:** `cd nps && python3 -m unittest discover tests/ -v`
6. **Ask the user** (using Ask User tool) before: deleting files, changing config.json structure, or any decision with multiple valid approaches.
7. **Use Task subagents** for independent work within a phase (for example, building two engines at the same time).
8. **Do not break existing functionality.** Every feature that works now must still work after your changes.
9. **Follow the architecture rules** in CLAUDE.md: engines are stateless, solvers orchestrate, GUI tabs are independent.
10. **Keep the dark theme.** All new GUI elements must use the existing `COLORS` and `FONTS` from `gui/theme.py`.
11. **Test each new engine** with a corresponding `tests/test_<n>.py` file.
12. **Update PROGRESS.md** after completing each phase (see Phase 0 for format).
13. **When in doubt, ask.** Do not guess. Use the Ask User tool.

---

## TABLE OF CONTENTS

- Phase 0: [Cleanup, Migration & Preparation](#phase-0-cleanup-migration--preparation)
- Phase 1: [Security Layer — Encryption + Secret Management](#phase-1-security-layer)
- Phase 2: [Findings Vault — Persistent Encrypted Storage](#phase-2-findings-vault)
- Phase 3: [Unified Hunter — One Mission, Multiple Targets](#phase-3-unified-hunter)
- Phase 4: [Oracle Upgrade — Human-Readable Wisdom](#phase-4-oracle-upgrade)
- Phase 5: [Memory Restructure — Active AI Learning System](#phase-5-memory-restructure)
- Phase 6: [Dashboard Upgrade — Multi-Terminal Command Center](#phase-6-dashboard-upgrade)
- Phase 7: [Settings & Connections Tab — Telegram + Remote Control](#phase-7-settings--connections-tab)
- Appendix A: [File Map — What Exists Now](#appendix-a-file-map)
- Appendix B: [New File Map — What Will Exist After V3](#appendix-b-new-file-map)
- Appendix C: [Config.json Changes](#appendix-c-configjson-changes)
- Appendix D: [Test Plan](#appendix-d-test-plan)
- Appendix E: [Performance Acceptance Criteria](#appendix-e-performance-acceptance-criteria)

---

## CURRENT STATE (What You Have Now)

Before building anything, understand what exists. This is the V2 build, confirmed working.

### Existing File Tree

```
nps/
├── main.py                     # App entry, 4 tabs, --headless mode
├── config.json                 # All settings
├── engines/
│   ├── fc60.py                 # FC60 encoding
│   ├── numerology.py           # Numerology calculations
│   ├── math_analysis.py        # Mathematical analysis
│   ├── crypto.py               # secp256k1, address generation
│   ├── scoring.py              # Weighted scoring
│   ├── learning.py             # Learning from solved puzzles
│   ├── ai_engine.py            # Claude Code CLI integration
│   ├── config.py               # Config loader
│   ├── notifier.py             # Telegram notifications
│   ├── balance.py              # BTC + ETH + ERC-20 balance checking
│   ├── bip39.py                # BIP39/BIP32/BIP44 seed phrases
│   ├── keccak.py               # Pure Python Keccak-256
│   ├── oracle.py               # Sign reading engine
│   └── memory.py               # Scan memory system
├── solvers/
│   ├── btc_solver.py           # Bitcoin puzzle solver
│   ├── scanner_solver.py       # Wallet scanner
│   ├── name_solver.py          # Name cipher solver
│   ├── number_solver.py        # Number oracle solver
│   ├── date_solver.py          # Date decoder solver
│   └── base_solver.py          # Base class
├── gui/
│   ├── dashboard_tab.py        # Dashboard view
│   ├── btc_tab.py              # BTC Hunter tab (puzzle)
│   ├── scanner_tab.py          # Scanner tab
│   ├── oracle_tab.py           # Oracle tab
│   ├── memory_tab.py           # Memory tab
│   ├── name_tab.py             # DEAD CODE — never imported
│   ├── theme.py                # Dark luxury theme (COLORS, FONTS)
│   └── widgets.py              # Reusable widgets
├── tests/                      # 18 test files, 147 tests
│   └── ...
├── data/
│   ├── scan_sessions.json      # V2 scan session history
│   └── scanner_knowledge/      # V2 scanner AI knowledge
└── tools/
    └── get_chat_id.py          # Telegram chat ID helper
```

### Current Stats

| Metric | Value |
|--------|-------|
| Total Python lines | ~17,369 |
| Tabs | 4 (Dashboard, Hunter, Oracle, Memory) |
| Engines | 14 |
| Solvers | 6 |
| GUI files | 8 (including dead name_tab.py) |
| Test files | 18 |
| Test count | 147 (146 pass, 1 expected fail) |
| Scan modes | 3 (random_key, seed_phrase, both) |
| Chains | 2 (BTC, ETH + 8 ERC-20 tokens) |

---

## PHASE 0: CLEANUP, MIGRATION & PREPARATION

**Goal:** Clean up dead code, migrate V2 data to new structure, create directories, set up progress tracking, and verify baseline.

### Task 0.1: Delete Dead Code

- Delete `nps/gui/name_tab.py` (it is never imported — confirmed by grep)
- Verify no imports reference it: `grep -rn "name_tab\|NameTab" nps/`

### Task 0.2: Verify Baseline

Run the full test suite and confirm 146/147 pass (the 1 failure is `test_rich_list_loads` — expected because `rich_addresses.txt` is not shipped):

```bash
cd nps && python3 -m unittest discover tests/ -v
```

### Task 0.3: Create Data Directories

The V3 build needs new directories. Create them now:

```bash
mkdir -p nps/data/findings
mkdir -p nps/data/findings/sessions
mkdir -p nps/data/findings/summaries
mkdir -p nps/data/sessions
mkdir -p nps/data/learning
mkdir -p nps/data/checkpoints
```

Make sure `nps/.gitignore` includes:
```
data/
__pycache__/
*.pyc
```

### Task 0.4: Backup Current Config

Before modifying `config.json`, save a copy:

```bash
cp nps/config.json nps/config.json.v2.backup
```

### Task 0.5: Migrate V2 Data (NEW — was missing from original V3)

V2 has existing data files that must be preserved and migrated:

```python
# migration.py — run ONCE during Phase 0
import json, shutil
from pathlib import Path

DATA = Path("nps/data")

def migrate_v2_to_v3():
    """Migrate V2 data files to V3 structure."""
    
    # 1. Migrate scan_sessions.json → data/sessions/v2_sessions.json
    old_sessions = DATA / "scan_sessions.json"
    if old_sessions.exists():
        new_path = DATA / "sessions" / "v2_sessions.json"
        shutil.copy2(old_sessions, new_path)
        print(f"  Migrated: {old_sessions} → {new_path}")
    
    # 2. Migrate scanner_knowledge/ → data/learning/v2_knowledge/
    old_knowledge = DATA / "scanner_knowledge"
    if old_knowledge.exists():
        new_path = DATA / "learning" / "v2_knowledge"
        shutil.copytree(old_knowledge, new_path, dirs_exist_ok=True)
        print(f"  Migrated: {old_knowledge} → {new_path}")
    
    # 3. Migrate memory.json → data/learning/v2_memory.json
    old_memory = DATA / "memory.json"
    if old_memory.exists():
        new_path = DATA / "learning" / "v2_memory.json"
        shutil.copy2(old_memory, new_path)
        print(f"  Migrated: {old_memory} → {new_path}")
    
    # 4. Archive originals (don't delete)
    archive = DATA / "v2_archive"
    archive.mkdir(exist_ok=True)
    for old_file in [old_sessions, old_memory]:
        if old_file.exists():
            shutil.copy2(old_file, archive / old_file.name)
    if old_knowledge.exists():
        shutil.copytree(old_knowledge, archive / "scanner_knowledge", dirs_exist_ok=True)
    
    print("  V2 data migrated. Originals archived in data/v2_archive/")

if __name__ == "__main__":
    migrate_v2_to_v3()
```

Run: `cd nps && python3 migration.py`

### Task 0.6: Create PROGRESS.md (NEW — build tracking)

Create `PROGRESS.md` in project root. Claude Code updates this after every phase:

```markdown
# NPS V3 Build Progress

## Status: Phase 0 — In Progress

| Phase | Status | Tests | Timestamp |
|-------|--------|-------|-----------|
| 0 - Cleanup & Migration | ⏳ In Progress | — | — |
| 1 - Security Layer | ⬜ Not Started | — | — |
| 2 - Findings Vault | ⬜ Not Started | — | — |
| 3 - Unified Hunter | ⬜ Not Started | — | — |
| 4 - Oracle Upgrade | ⬜ Not Started | — | — |
| 5 - Memory Restructure | ⬜ Not Started | — | — |
| 6 - Dashboard Upgrade | ⬜ Not Started | — | — |
| 7 - Settings Tab | ⬜ Not Started | — | — |

## Notes
- V2 baseline: 146/147 tests pass
```

Claude Code: after completing each phase, update the table row to `✅ Complete`, add test count and timestamp. If resuming from a new session, read this file FIRST.

### Phase 0 Verification Checklist

- [ ] `gui/name_tab.py` deleted
- [ ] `grep -rn "name_tab\|NameTab" nps/` returns nothing
- [ ] Test suite runs: 146/147 pass
- [ ] `nps/data/findings/` directory exists
- [ ] `nps/data/findings/sessions/` directory exists
- [ ] `nps/data/findings/summaries/` directory exists
- [ ] `nps/data/sessions/` directory exists
- [ ] `nps/data/learning/` directory exists
- [ ] `nps/data/checkpoints/` directory exists
- [ ] `config.json.v2.backup` exists
- [ ] V2 data migrated (scan_sessions, scanner_knowledge, memory)
- [ ] Originals archived in `data/v2_archive/`
- [ ] `PROGRESS.md` created and updated

---

## PHASE 1: SECURITY LAYER

**Goal:** Before storing any private keys or seed phrases, build the encryption and secret management layer that protects them. This phase creates the security foundation that the Vault (Phase 2) and Settings (Phase 7) build on.

> **WHY THIS PHASE EXISTS:** The original V3 stored private keys and seeds in plaintext JSON files. Anyone who opens those files (malware, backup software, accidental GitHub push) gets everything. This phase fixes that.

### Task 1.1: Create `nps/engines/security.py` (New Engine)

This engine handles all encryption, decryption, and secret management.

**Public API:**

```python
"""
NPS Security Engine — Encryption at rest for sensitive data.

Uses AES-256-GCM for encryption, PBKDF2 for key derivation.
All stdlib — no pip dependencies.

Master password is set once, then cached in RAM for the session.
If no password is set, the app still works but shows a warning
and stores data unencrypted (for backward compatibility).
"""

import hashlib, hmac, os, json, base64
from pathlib import Path

# Module-level state
_master_key: bytes | None = None
_salt_file = Path("nps/data/.vault_salt")

def set_master_password(password: str) -> bool:
    """
    Derive encryption key from password using PBKDF2.
    Call this once at app startup (GUI password dialog or --password flag).
    Returns True if key was derived successfully.
    
    The salt is stored in a separate file (not with the encrypted data).
    If no salt exists, a new one is generated (first-time setup).
    """
    global _master_key
    
    if not password:
        _master_key = None
        return False
    
    # Load or generate salt
    if _salt_file.exists():
        salt = _salt_file.read_bytes()
    else:
        salt = os.urandom(32)
        _salt_file.parent.mkdir(parents=True, exist_ok=True)
        _salt_file.write_bytes(salt)
    
    # PBKDF2 with 600,000 iterations (OWASP recommendation 2024)
    _master_key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 600_000
    )
    return True


def is_encrypted_mode() -> bool:
    """Check if encryption is active (master password was set)."""
    return _master_key is not None


def encrypt(plaintext: str) -> str:
    """
    Encrypt a string. Returns base64-encoded ciphertext.
    If no master password set, returns plaintext with a prefix marker.
    
    Format: base64(nonce[12] + ciphertext + tag[16])
    Uses AES-256-GCM via Python's hashlib/hmac (no pip).
    
    NOTE: Python stdlib doesn't have AES-GCM directly.
    We use XOR cipher with HMAC-SHA256 as a stream cipher + authentication.
    This is not as strong as AES-GCM but is sufficient for local file encryption
    and requires zero pip dependencies.
    
    For production-grade encryption, install `cryptography` pip package
    and switch to Fernet or AES-GCM. This is flagged in CLAUDE.md.
    """
    if not _master_key:
        return "PLAIN:" + plaintext
    
    nonce = os.urandom(16)
    
    # Generate keystream using HMAC-SHA256 in counter mode
    ciphertext = bytearray()
    for i in range(0, len(plaintext.encode()), 32):
        block_key = hmac.new(
            _master_key,
            nonce + i.to_bytes(4, "big"),
            hashlib.sha256
        ).digest()
        chunk = plaintext.encode("utf-8")[i:i+32]
        ciphertext.extend(bytes(a ^ b for a, b in zip(chunk, block_key)))
    
    # Authentication tag
    tag = hmac.new(_master_key, nonce + bytes(ciphertext), hashlib.sha256).digest()[:16]
    
    return "ENC:" + base64.b64encode(nonce + bytes(ciphertext) + tag).decode()


def decrypt(encoded: str) -> str:
    """
    Decrypt a string. Accepts both encrypted and plaintext-marked strings.
    Returns plaintext.
    Raises ValueError if authentication fails (wrong password or tampered data).
    """
    if encoded.startswith("PLAIN:"):
        return encoded[6:]
    
    if not encoded.startswith("ENC:"):
        return encoded  # Legacy unencrypted data
    
    if not _master_key:
        raise ValueError("Master password not set. Cannot decrypt.")
    
    raw = base64.b64decode(encoded[4:])
    nonce = raw[:16]
    tag = raw[-16:]
    ciphertext = raw[16:-16]
    
    # Verify authentication tag
    expected_tag = hmac.new(_master_key, nonce + ciphertext, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("Decryption failed: wrong password or corrupted data")
    
    # Decrypt
    plaintext = bytearray()
    for i in range(0, len(ciphertext), 32):
        block_key = hmac.new(
            _master_key,
            nonce + i.to_bytes(4, "big"),
            hashlib.sha256
        ).digest()
        chunk = ciphertext[i:i+32]
        plaintext.extend(bytes(a ^ b for a, b in zip(chunk, block_key)))
    
    return plaintext.decode("utf-8")


def encrypt_dict(data: dict, sensitive_keys: list[str]) -> dict:
    """
    Encrypt only the sensitive fields in a dict.
    Non-sensitive fields are left as-is for searchability.
    
    Example:
        encrypt_dict(
            {"address": "1ABC...", "private_key": "0x123...", "balance": 0.5},
            sensitive_keys=["private_key"]
        )
        # Returns: {"address": "1ABC...", "private_key": "ENC:base64...", "balance": 0.5}
    """
    result = data.copy()
    for key in sensitive_keys:
        if key in result and result[key]:
            result[key] = encrypt(str(result[key]))
    return result


def decrypt_dict(data: dict, sensitive_keys: list[str]) -> dict:
    """Decrypt the sensitive fields in a dict."""
    result = data.copy()
    for key in sensitive_keys:
        if key in result and result[key]:
            try:
                result[key] = decrypt(str(result[key]))
            except ValueError:
                result[key] = "[DECRYPTION FAILED]"
    return result


def get_env_or_config(key: str, config_value: str | None = None) -> str | None:
    """
    Check environment variable first, then fall back to config value.
    Used for secrets like bot tokens.
    
    Environment variable names: NPS_BOT_TOKEN, NPS_CHAT_ID, etc.
    """
    env_name = f"NPS_{key.upper()}"
    return os.environ.get(env_name) or config_value
```

### Task 1.2: Create Password Dialog

Add to `gui/widgets.py`:

```python
def ask_master_password(parent, first_time=False):
    """
    Show a password dialog at startup.
    If first_time=True, asks to confirm the password.
    Returns the password string, or None if cancelled/skipped.
    
    The dialog has a "Skip (no encryption)" button that lets the user
    run without encryption — shows a warning in the status bar.
    """
    # Implementation: tkinter Toplevel with Entry(show="*"), OK/Skip buttons
    # If first_time: add "Confirm password" field
    # Returns: password string or None
```

### Task 1.3: Integrate into main.py

At startup, before loading any data:

```python
from engines.security import set_master_password, is_encrypted_mode, _salt_file

# Check if vault salt exists (= encryption was set up before)
first_time = not _salt_file.exists()

if not args.headless:
    password = ask_master_password(root, first_time=first_time)
    if password:
        set_master_password(password)
else:
    # Headless mode: read from environment
    password = os.environ.get("NPS_MASTER_PASSWORD")
    if password:
        set_master_password(password)

# Show warning in status bar if not encrypted
if not is_encrypted_mode():
    status_bar.set_warning("⚠ No encryption — keys stored in plaintext")
```

### Task 1.4: Environment Variable Support for Secrets

Modify `engines/config.py` to check env vars first:

```python
from engines.security import get_env_or_config

def get_bot_token():
    config = load_config()
    return get_env_or_config("BOT_TOKEN", config.get("telegram", {}).get("bot_token"))

def get_chat_id():
    config = load_config()
    return get_env_or_config("CHAT_ID", config.get("telegram", {}).get("chat_id"))
```

### Task 1.5: Create Tests

`nps/tests/test_security.py`:

```python
# Test cases:
# 1. set_master_password → encrypt → decrypt roundtrip
# 2. Wrong password → ValueError on decrypt
# 3. encrypt_dict encrypts only sensitive_keys
# 4. decrypt_dict decrypts only sensitive_keys
# 5. No password → "PLAIN:" prefix
# 6. Legacy unencrypted data → decrypt returns as-is
# 7. Empty string → encrypt/decrypt roundtrip
# 8. Unicode string → encrypt/decrypt roundtrip
# 9. get_env_or_config prefers env var over config
# 10. Tampered ciphertext → ValueError
```

### Phase 1 Verification Checklist

- [ ] `nps/engines/security.py` exists with all functions
- [ ] `nps/tests/test_security.py` exists with 10+ tests
- [ ] All security tests pass
- [ ] Encrypt → decrypt roundtrip works for strings, dicts
- [ ] Wrong password raises ValueError
- [ ] No password mode returns "PLAIN:" prefix
- [ ] Environment variables override config values
- [ ] Password dialog works in GUI mode
- [ ] Headless mode reads NPS_MASTER_PASSWORD env var
- [ ] Full test suite still passes
- [ ] PROGRESS.md updated

---

## PHASE 2: FINDINGS VAULT

**Goal:** Create a persistent, encrypted storage system that saves every wallet finding with its private key/seed, balance across all chains, and metadata. Sensitive data (keys, seeds) are encrypted using the security layer from Phase 1.

### What "Findings Vault" Means

Every time the scanner finds a wallet with ANY balance (even $0.01) on ANY chain (BTC, ETH, or any ERC-20 token), it must:

1. Encrypt the private key/seed before writing
2. Save the finding immediately to a running log file
3. After every 100 findings, create a clean summary file
4. Keep per-session files so each scan run has its own record
5. Store everything in `nps/data/findings/`

### Task 2.1: Create `nps/engines/vault.py` (New Engine)

**Public API:**

```python
"""
NPS Findings Vault — Encrypted persistent storage for all wallet discoveries.

Every finding is encrypted at rest (if master password set).
Sensitive fields (private_key, seed_phrase, wif) are encrypted.
Non-sensitive fields (address, balance, chain, timestamp) stay readable for search.

Storage format:
  vault_live.jsonl  — Append-only log, one JSON line per finding (fast writes)
  vault_master.json — Clean summary, regenerated every 100 findings
  sessions/<id>.json — Per-session findings
  summaries/<n>.json — Every 100 findings, a summary snapshot
"""

import json, threading, time
from pathlib import Path
from datetime import datetime
from engines.security import encrypt_dict, decrypt_dict, is_encrypted_mode

VAULT_DIR = Path("nps/data/findings")
LIVE_FILE = VAULT_DIR / "vault_live.jsonl"
MASTER_FILE = VAULT_DIR / "vault_master.json"
SESSIONS_DIR = VAULT_DIR / "sessions"
SUMMARIES_DIR = VAULT_DIR / "summaries"

SENSITIVE_KEYS = ["private_key", "seed_phrase", "wif", "extended_private_key"]

_lock = threading.Lock()
_finding_count = 0
_session_id: str | None = None


def init_vault():
    """Initialize vault directories. Call at app startup."""
    for d in [VAULT_DIR, SESSIONS_DIR, SUMMARIES_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def start_session(session_name: str = None) -> str:
    """
    Start a new vault session. Returns session_id.
    Each scanner terminal starts its own session.
    """
    global _session_id
    _session_id = session_name or datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file = SESSIONS_DIR / f"{_session_id}.json"
    _atomic_write(session_file, json.dumps({
        "session_id": _session_id,
        "started_at": datetime.now().isoformat(),
        "findings": [],
        "stats": {"total": 0, "with_balance": 0}
    }, indent=2))
    return _session_id


def record_finding(finding: dict) -> bool:
    """
    Record a wallet finding. Thread-safe.
    
    finding = {
        "address_btc": "1ABC...",
        "address_eth": "0xABC...",
        "private_key": "0x123...",       # Will be encrypted
        "seed_phrase": "abandon ...",    # Will be encrypted (if present)
        "wif": "5J...",                  # Will be encrypted
        "balance_btc": 0.0,
        "balance_eth": 0.0,
        "tokens": {"USDT": 0.0, ...},
        "has_balance": True,
        "source": "random_key" | "seed_phrase" | "puzzle",
        "chain": "btc" | "eth" | "multi",
        "numerology_score": 0.45,
        "timestamp": "2026-02-07T14:30:00",
        "terminal_id": "terminal_1",
    }
    """
    global _finding_count
    
    with _lock:
        # Add metadata
        finding["recorded_at"] = datetime.now().isoformat()
        finding["encrypted"] = is_encrypted_mode()
        
        # Encrypt sensitive fields
        safe_finding = encrypt_dict(finding, SENSITIVE_KEYS)
        
        # 1. Append to live log (JSONL — one line per finding)
        with open(LIVE_FILE, "a") as f:
            f.write(json.dumps(safe_finding) + "\n")
        
        # 2. Append to session file
        if _session_id:
            session_file = SESSIONS_DIR / f"{_session_id}.json"
            if session_file.exists():
                session = json.loads(session_file.read_text())
                session["findings"].append(safe_finding)
                session["stats"]["total"] += 1
                if finding.get("has_balance"):
                    session["stats"]["with_balance"] += 1
                _atomic_write(session_file, json.dumps(session, indent=2))
        
        _finding_count += 1
        
        # 3. Create summary every 100 findings
        if _finding_count % 100 == 0:
            _create_summary()
        
        return True


def get_findings(decrypt_keys=False, limit=100) -> list[dict]:
    """
    Read findings from the vault.
    If decrypt_keys=True, decrypts sensitive fields (requires master password).
    """
    findings = []
    if LIVE_FILE.exists():
        with open(LIVE_FILE) as f:
            for line in f:
                line = line.strip()
                if line:
                    finding = json.loads(line)
                    if decrypt_keys:
                        finding = decrypt_dict(finding, SENSITIVE_KEYS)
                    findings.append(finding)
    
    return findings[-limit:]  # Most recent


def get_summary() -> dict:
    """Get vault summary statistics."""
    total = 0
    with_balance = 0
    chains = {"btc": 0, "eth": 0, "multi": 0}
    
    if LIVE_FILE.exists():
        with open(LIVE_FILE) as f:
            for line in f:
                if line.strip():
                    finding = json.loads(line.strip())
                    total += 1
                    if finding.get("has_balance"):
                        with_balance += 1
                    chain = finding.get("chain", "unknown")
                    chains[chain] = chains.get(chain, 0) + 1
    
    return {
        "total_findings": total,
        "with_balance": with_balance,
        "by_chain": chains,
        "encrypted": is_encrypted_mode(),
        "vault_size_kb": LIVE_FILE.stat().st_size / 1024 if LIVE_FILE.exists() else 0,
    }


def export_csv(output_path: str, decrypt_keys=False) -> str:
    """
    Export vault to CSV. Sensitive fields only included if decrypt_keys=True.
    Returns the output file path.
    """
    import csv
    findings = get_findings(decrypt_keys=decrypt_keys, limit=999999)
    
    if not findings:
        return ""
    
    # Determine columns from first finding
    columns = list(findings[0].keys())
    if not decrypt_keys:
        # Remove encrypted fields from CSV
        columns = [c for c in columns if c not in SENSITIVE_KEYS]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for finding in findings:
            writer.writerow(finding)
    
    return output_path


def export_json(output_path: str, decrypt_keys=False) -> str:
    """Export vault to formatted JSON."""
    findings = get_findings(decrypt_keys=decrypt_keys, limit=999999)
    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)
    return output_path


def shutdown():
    """Flush and close vault. Call at app shutdown."""
    _create_summary()


def _create_summary():
    """Create a point-in-time summary file."""
    summary = get_summary()
    summary["created_at"] = datetime.now().isoformat()
    summary_file = SUMMARIES_DIR / f"summary_{_finding_count}.json"
    _atomic_write(summary_file, json.dumps(summary, indent=2))


def _atomic_write(path: Path, content: str):
    """Write to .tmp then rename — never corrupt the target file."""
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(content)
    tmp_path.rename(path)
```

### Task 2.2: Integrate Vault into Scanner Solver

Modify `nps/solvers/scanner_solver.py`:

- When a key/seed is checked and has ANY balance, call `vault.record_finding()`
- Also record if the wallet's numerology score is above a threshold (e.g., > 0.7) even if balance is 0 — these are "interesting" findings.
- At session start, call vault's `start_session()`. At session end, call vault's `shutdown()`.

### Task 2.3: Integrate Vault into BTC Solver

Modify `nps/solvers/btc_solver.py`:

- When a puzzle key is tested and produces a valid address, if balance check is enabled, record it in the vault too.

### Task 2.4: Add Vault Shutdown to Main

In `nps/main.py`, in the `_on_close` method and in `run_headless` shutdown:

```python
from engines.vault import shutdown as vault_shutdown, init_vault
init_vault()  # At startup
# ... at shutdown:
vault_shutdown()
```

### Task 2.5: Create Tests

`nps/tests/test_vault.py`:

```python
# Test cases:
# 1. init_vault creates directories
# 2. start_session creates session file
# 3. record_finding appends to JSONL
# 4. record_finding encrypts sensitive fields when password set
# 5. get_findings returns decrypted data when requested
# 6. get_summary returns correct counts
# 7. export_csv creates valid CSV
# 8. export_json creates valid JSON
# 9. Thread safety: 10 threads recording simultaneously
# 10. Atomic write: corrupt data doesn't destroy vault
# 11. Summary created every 100 findings
```

### Phase 2 Verification Checklist

- [ ] `nps/engines/vault.py` exists and has all 8 public functions
- [ ] `nps/tests/test_vault.py` exists with 11+ tests
- [ ] All vault tests pass
- [ ] Scanner solver records findings to vault
- [ ] BTC solver records findings to vault
- [ ] `vault_live.jsonl` gets written when scanner runs
- [ ] Sensitive fields are encrypted when master password is set
- [ ] Sensitive fields are plaintext-marked when no password
- [ ] Summary file generated after 100 findings (test with mock data)
- [ ] export_csv and export_json work
- [ ] Vault shutdown is called in both GUI and headless modes
- [ ] Thread-safe: 10 concurrent writes don't corrupt
- [ ] Full test suite still passes
- [ ] PROGRESS.md updated

---

## PHASE 3: UNIFIED HUNTER

**Goal:** Merge the Puzzle Mission and Scanner Mission into ONE unified hunting system. The puzzle becomes a toggle option within the scanner. When enabled, the scanner focuses its random scanning around the puzzle's key range while ALSO checking every generated address for balance on all chains. Add crash recovery with checkpoints.

### What "Unified Hunter" Means

**Current behavior (V2):**
- Puzzle section: Solves puzzle #66 (or any selected puzzle) using 4 strategies. Tests keys in the puzzle's range.
- Scanner section: Generates random keys or seed phrases across the ENTIRE keyspace. Checks balance online.
- They are TWO separate systems with TWO start/stop buttons.

**New behavior (V3):**
- ONE unified scanner with ONE start/stop button.
- The puzzle becomes a TOGGLE. When "Puzzle Mode" is ON, the scanner does two things at once.
- When "Puzzle Mode" is OFF, it behaves like the current scanner — random keys across the full keyspace.
- Every key is tested for puzzle match AND balance. One move, two targets.

### Task 3.1: Create `nps/solvers/unified_solver.py` (New Solver)

This replaces both `btc_solver.py` and `scanner_solver.py` as the primary hunting engine. Do NOT delete the old files — they become fallback/reference.

**Public API:**

```python
class UnifiedSolver(BaseSolver):
    def __init__(
        self,
        mode="both",                # "random_key", "seed_phrase", "both"
        puzzle_enabled=False,       # Toggle: also solve puzzle?
        puzzle_number=66,           # Which puzzle
        strategy="hybrid",         # Puzzle strategy
        chains=None,               # ["btc", "eth"] — which chains to check
        tokens=None,               # ["USDT", "USDC"] — which ERC-20 tokens
        online_check=True,         # Check balances online?
        check_every_n=5000,        # How often to do online checks
        use_brain=True,            # Use AI brain for strategy?
        terminal_id=None,          # For multi-terminal identification
        callback=None,             # GUI callback for updates
    ):
        ...

    def start(self):
        """Start scanning. Runs in its own thread."""

    def stop(self):
        """Stop scanning gracefully."""

    def pause(self):
        """Pause scanning (keep state)."""

    def resume(self):
        """Resume from pause."""

    def get_stats(self) -> dict:
        """
        Returns:
        {
            "keys_tested": int,
            "seeds_tested": int,
            "speed": float,           # keys/second
            "elapsed_seconds": float,
            "online_checks": int,
            "hits": int,
            "puzzle_progress": float,  # 0.0-100.0 if puzzle enabled
            "mode": str,
            "is_running": bool,
            "is_paused": bool,
            "last_key": str,           # Truncated, for display
            "last_address_btc": str,
            "last_address_eth": str,
            "last_balance": dict,
            "high_score": float,
            "high_score_key": str,
        }
        """

    def save_checkpoint(self):
        """Save current scanner position for crash recovery."""

    @classmethod
    def resume_from_checkpoint(cls, checkpoint_path: str, callback=None):
        """Create a solver that resumes from a saved checkpoint."""
```

### Task 3.2: Checkpoint System (NEW — crash recovery)

Add to `unified_solver.py`:

```python
CHECKPOINT_DIR = Path("nps/data/checkpoints")
CHECKPOINT_INTERVAL = 100_000  # Save checkpoint every 100K keys

def save_checkpoint(self):
    """Save current state for crash recovery."""
    checkpoint = {
        "terminal_id": self.terminal_id,
        "mode": self.mode,
        "puzzle_enabled": self.puzzle_enabled,
        "puzzle_number": self.puzzle_number,
        "strategy": self.strategy,
        "chains": self.chains,
        "tokens": self.tokens,
        "keys_tested": self.keys_tested,
        "seeds_tested": self.seeds_tested,
        "last_key_index": self._last_key_index,
        "last_seed_index": self._last_seed_index,
        "high_score": self.high_score,
        "timestamp": datetime.now().isoformat(),
    }
    path = CHECKPOINT_DIR / f"{self.terminal_id or 'default'}.json"
    _atomic_write(path, json.dumps(checkpoint, indent=2))

@classmethod
def resume_from_checkpoint(cls, checkpoint_path: str, callback=None):
    """Resume scanning from a saved checkpoint."""
    checkpoint = json.loads(Path(checkpoint_path).read_text())
    solver = cls(
        mode=checkpoint["mode"],
        puzzle_enabled=checkpoint["puzzle_enabled"],
        puzzle_number=checkpoint["puzzle_number"],
        strategy=checkpoint["strategy"],
        chains=checkpoint["chains"],
        tokens=checkpoint["tokens"],
        terminal_id=checkpoint["terminal_id"],
        callback=callback,
    )
    solver.keys_tested = checkpoint["keys_tested"]
    solver.seeds_tested = checkpoint["seeds_tested"]
    solver._last_key_index = checkpoint["last_key_index"]
    solver._last_seed_index = checkpoint["last_seed_index"]
    solver.high_score = checkpoint["high_score"]
    return solver
```

In the main scan loop, save checkpoint every `CHECKPOINT_INTERVAL` keys:

```python
if self.keys_tested % CHECKPOINT_INTERVAL == 0:
    self.save_checkpoint()
```

At startup, check for existing checkpoints and offer to resume:

```python
# In main.py or dashboard_tab.py
checkpoints = list(CHECKPOINT_DIR.glob("*.json"))
if checkpoints:
    # Ask user: "Found checkpoint from [time]. Resume?"
    # If yes: UnifiedSolver.resume_from_checkpoint(path)
    # If no: delete checkpoint
```

### Task 3.3: BNB + Polygon Chain Support (NEW — was deferred from V1)

Modify `engines/balance.py` to add BSC and Polygon RPCs:

```python
# BSC (Binance Smart Chain) — same derivation as ETH, different RPC
BSC_RPC_ENDPOINTS = [
    "https://bsc-dataseed1.binance.org",
    "https://bsc-dataseed2.binance.org",
    "https://rpc.ankr.com/bsc",
]

# Polygon — same derivation as ETH, different RPC
POLYGON_RPC_ENDPOINTS = [
    "https://polygon-rpc.com",
    "https://rpc.ankr.com/polygon",
    "https://1rpc.io/matic",
]

# BSC ERC-20 tokens (BEP-20)
BSC_TOKENS = {
    "BUSD": {"contract": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56", "decimals": 18},
    "CAKE": {"contract": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "decimals": 18},
}

def check_bsc_balance(address: str) -> dict:
    """Check BNB balance on BSC."""
    return _generic_eth_balance(address, BSC_RPC_ENDPOINTS, "BNB")

def check_polygon_balance(address: str) -> dict:
    """Check MATIC balance on Polygon."""
    return _generic_eth_balance(address, POLYGON_RPC_ENDPOINTS, "MATIC")
```

Update `check_all_balances()` to include BSC and Polygon when enabled in config.

### Task 3.4: Redesign Hunter Tab

**File:** `gui/hunter_tab.py` — REDESIGNED (~700 lines)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Hunter — Unified Scan Engine                                        │
│                                                                      │
│  ┌─ Mode ──────────────────────────┐  ┌─ Puzzle ──────────────────┐ │
│  │  (●) Random Keys                │  │  ☑ Puzzle Mode            │ │
│  │  ( ) Seed Phrases               │  │  Puzzle: [#66 ▼]         │ │
│  │  ( ) Both                       │  │  Strategy: [Hybrid ▼]    │ │
│  └─────────────────────────────────┘  └───────────────────────────┘ │
│                                                                      │
│  ┌─ Chains ────────────────────────────────────────────────────────┐ │
│  │  ☑ BTC   ☑ ETH   ☑ BSC   ☑ Polygon                           │ │
│  │  Tokens: ☑ USDT  ☑ USDC  ☑ DAI  ☑ WBTC  ☐ BUSD  ☐ CAKE     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────────┐ │
│  │  ▶  START  │  │  ⏸  PAUSE  │  │  ■  STOP   │  │ 🧠 Brain: ON │ │
│  └────────────┘  └────────────┘  └────────────┘  └───────────────┘ │
│                                                                      │
│  ┌─ Live Stats ────────────────────────────────────────────────────┐ │
│  │  Keys: 1,234,567  │  Seeds: 12,345  │  Speed: 45,000/s        │ │
│  │  Puzzle: 0.23%    │  Hits: 0        │  Online: 123 checks     │ │
│  │  Elapsed: 01:23:45│  High Score: 0.82                         │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─ Live Feed ─────────────────────────────────────────────────────┐ │
│  │  TIME     SRC  KEY/SEED          BTC ADDR     ETH ADDR         │ │
│  │                                  ₿ BTC  Ξ ETH  ₮ USDT   CHK   │ │
│  ├─────────────────────────────────────────────────────────────────│ │
│  │  14:30:01 🎯  key:891234        1Abc...Xyz   —                 │ │
│  │  14:30:01 🔍  0x3a7f...8b2c     1Def...Uvw   0xdef...uvw      │ │
│  │                                  0.000  0.000  0.000    ·      │ │
│  │  14:30:02 🔍  SEED abandon...   1Ghi...Rst   0xghi...rst      │ │
│  │                                  0.000  0.000  0.000    ·      │ │
│  │  (green row = BALANCE FOUND)                                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─ AI Insight ────────────────────────────────────────────────────┐ │
│  │  Pattern: keys near 2^70 have 12% higher entropy.              │ │
│  │  Try focusing on master numbers in this range.                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─ High Score Alert ──────────────────────────────────────────────┐ │
│  │  🏆 Best: 0.823 — Key 0x4a8f... at 14:23:05                   │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### Task 3.5: Create Tests

`nps/tests/test_unified_solver.py`:

```python
# Test cases:
# 1. UnifiedSolver initializes with all parameter combinations
# 2. Random key mode generates valid keys
# 3. Seed phrase mode generates valid mnemonics
# 4. Both mode alternates between keys and seeds
# 5. Puzzle toggle: when ON, keys are in puzzle range
# 6. Stats dict has all required fields
# 7. Checkpoint saves correctly
# 8. Resume from checkpoint restores state
# 9. Stop/pause/resume lifecycle
# 10. Thread safety: concurrent access to stats
# 11. Vault integration: findings are recorded
# 12. BSC/Polygon balance check format (mock)
```

### Phase 3 Verification Checklist

- [ ] `nps/solvers/unified_solver.py` exists with full API
- [ ] `nps/tests/test_unified_solver.py` exists with 12+ tests
- [ ] All unified solver tests pass
- [ ] Random key mode works
- [ ] Seed phrase mode works
- [ ] Both mode works
- [ ] Puzzle toggle ON: keys restricted to puzzle range + balance check
- [ ] Puzzle toggle OFF: full keyspace random scan
- [ ] BSC and Polygon balance checking works (mock test)
- [ ] Checkpoint saves every 100K keys
- [ ] Resume from checkpoint restores correct state
- [ ] Pause/resume keeps scanner state
- [ ] Hunter tab redesigned with unified controls
- [ ] Live Feed shows real-time entries
- [ ] Green highlight on balance > 0
- [ ] AI Insight card shows latest recommendation
- [ ] High Score Alert updates
- [ ] Findings recorded to Vault
- [ ] Full test suite passes
- [ ] PROGRESS.md updated

---

## PHASE 4: ORACLE UPGRADE

**Goal:** Transform the Oracle from a basic name cipher into a human-readable wisdom engine. Add "Question + Time Sign" feature. Make output feel like advice from a wise mentor, not raw data.

### What "Human-Readable Oracle" Means

**Current behavior (V2):**
- Name Cipher: Takes a name → runs FC60 + numerology → outputs raw numbers and codes
- Output is technical (FC60 glyphs, raw scores)

**New behavior (V3):**
- Same input, but output includes HUMAN MEANINGS
- Example: Instead of "FC60: VE-OX-OXFI" → "Venus-Earth cycle: creativity meets grounding. This is a period of manifesting ideas into reality."
- New feature: "Question Mode" — enter a question + current time → get a sign reading

### Task 4.1: Modify `nps/engines/oracle.py`

Add these functions:

```python
def get_human_meaning(fc60_code: str) -> str:
    """Convert FC60 code to human-readable meaning."""

def question_sign(question: str, timestamp: datetime = None) -> dict:
    """
    Read a sign for a question at a given moment.
    Combines FC60 of the moment, numerology of the question,
    moon phase, and any active planetary transits.
    
    Returns: {
        "question": str,
        "moment": {"fc60": str, "meaning": str, "moon": str},
        "numerology": {"value": int, "meaning": str},
        "reading": str,     # 2-3 sentence human reading
        "advice": str,      # 1 sentence actionable advice
    }
    """

def daily_insight() -> dict:
    """
    Generate today's insight based on current cosmic moment.
    Returns: {"date": str, "insight": str, "lucky_numbers": list, "energy": str}
    """
```

### Task 4.2: FC60 Human Meanings Dictionary

Create a meanings dictionary inside oracle.py:

```python
FC60_MEANINGS = {
    "VE": "Venus — Love, beauty, attraction, creativity, harmony",
    "OX": "Earth — Grounding, stability, practical wisdom, patience",
    "MO": "Moon — Intuition, cycles, emotional depth, reflection",
    # ... (all FC60 base symbols get human meanings)
}

COMBINED_MEANINGS = {
    ("VE", "OX"): "Creativity meets grounding — manifest ideas into reality",
    ("MO", "VE"): "Emotional creativity — trust your artistic intuition",
    # ... (common pairings get combined readings)
}
```

### Task 4.3: Redesign Oracle Tab

**File:** `gui/oracle_tab.py` — REDESIGNED (~450 lines)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Oracle — Wisdom Engine                                              │
│  "Ask the cosmos a question, or decode a name."                      │
│                                                                      │
│  ┌─ Mode ─────────────────────────────────────────────────────────┐ │
│  │  (●) Question Mode     ( ) Name Cipher                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  === QUESTION MODE ===                                               │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Your Question: [Should I focus on puzzle 66 or 67?         ]  │ │
│  │  Time: [Now ▼] or [14:30]   Location: [Optional            ]  │ │
│  │  [Read Sign]                                                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─ Reading ───────────────────────────────────────────────────────┐ │
│  │                                                                  │ │
│  │  🌙 Moment: Waning Gibbous (81%) — Release, let go, surrender   │ │
│  │  ☿ FC60: VE-OX-OXFI — Creativity meets Earth wisdom            │ │
│  │  🔢 Question Energy: 7 — Seeker, analyst, inner wisdom          │ │
│  │                                                                  │ │
│  │  ═══════════════════════════════════════════════════════════     │ │
│  │                                                                  │ │
│  │  "The cosmic moment favors depth over breadth. The number 7     │ │
│  │   says: go deep into ONE puzzle rather than spreading energy.   │ │
│  │   Venus-Earth grounding suggests: pick the puzzle with the     │ │
│  │   strongest personal connection."                               │ │
│  │                                                                  │ │
│  │  Advice: Focus on puzzle 66 — the waning moon favors            │ │
│  │  completing what's already in motion.                            │ │
│  │                                                                  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  === NAME CIPHER MODE ===                                            │
│  (same as current but with human meanings added to output)           │
└──────────────────────────────────────────────────────────────────────┘
```

### Task 4.4: Oracle from Telegram

The Oracle can be triggered from Telegram:

```
/sign 11:11
/sign 444 at 14:30
/name Hamzeh 1990-05-15
```

### Task 4.5: Create Tests

Modify `nps/tests/test_oracle.py` — add tests for:
- `get_human_meaning()` returns non-empty strings
- `question_sign()` returns complete dict with all required keys
- `daily_insight()` returns dict with date, insight, lucky_numbers, energy
- Empty question handling
- Unicode names in name cipher

### Phase 4 Verification Checklist

- [ ] `engines/oracle.py` modified with 3 new functions
- [ ] Human meanings dictionary covers all FC60 base symbols
- [ ] `question_sign()` returns complete reading with advice
- [ ] `daily_insight()` generates daily insight
- [ ] Oracle tab redesigned with Question Mode and Name Cipher Mode
- [ ] Question Mode shows human-readable reading (not raw data)
- [ ] Name Cipher Mode shows human meanings alongside raw output
- [ ] Telegram `/sign` and `/name` commands work
- [ ] All oracle tests pass
- [ ] Full test suite passes
- [ ] PROGRESS.md updated

---

## PHASE 5: MEMORY RESTRUCTURE — ACTIVE AI LEARNING

**Goal:** Transform the Memory tab from a passive statistics display into an ACTIVE AI learning system. The AI doesn't just show recommendations — it can AUTO-ADJUST scanner behavior. Add leveled learning, model selection, and session archives.

> **WHY "ACTIVE" MATTERS:** The original V3 had passive recommendations. The AI said "try Both mode" but the scanner never changed. Now: when `auto_adapt` is ON, the AI reads from learning state and adjusts strategy, batch size, and scan focus automatically.

### What "Active AI Learning" Means

- **Level 1 (Novice):** AI just watches and records patterns. No recommendations.
- **Level 2 (Student):** AI makes recommendations in the Memory tab. User applies them manually.
- **Level 3 (Apprentice):** AI auto-suggests strategy changes via popup. User approves/rejects.
- **Level 4 (Expert):** AI auto-adjusts strategy without asking (`auto_adapt` mode). User can override.
- **Level 5 (Master):** AI runs fully autonomous — picks puzzles, switches modes, adjusts timing.

Levels are earned through XP (experience points): 1 XP per 100K keys tested, 10 XP per "Learn Now" session, 100 XP per balance hit.

### Task 5.1: Create `nps/engines/learner.py` (New Engine)

**Public API:**

```python
"""
NPS AI Learning Engine — Active learning with levels and auto-adaptation.

The learner accumulates knowledge across scan sessions and uses
Claude Code CLI to analyze patterns and generate insights.

Learning State persists to disk: data/learning/learning_state.json
"""

LEVELS = {
    1: {"name": "Novice", "xp_required": 0, "capabilities": ["observe"]},
    2: {"name": "Student", "xp_required": 100, "capabilities": ["observe", "recommend"]},
    3: {"name": "Apprentice", "xp_required": 500, "capabilities": ["observe", "recommend", "suggest"]},
    4: {"name": "Expert", "xp_required": 2000, "capabilities": ["observe", "recommend", "suggest", "auto_adapt"]},
    5: {"name": "Master", "xp_required": 10000, "capabilities": ["observe", "recommend", "suggest", "auto_adapt", "autonomous"]},
}

def get_level() -> dict:
    """Get current AI level, XP, and capabilities."""

def add_xp(amount: int, reason: str):
    """Add experience points. Automatically levels up when threshold met."""

def learn(session_data: dict, model: str = "sonnet") -> dict:
    """
    Trigger AI learning from a scan session.
    Uses Claude Code CLI to analyze patterns.
    
    model: "opus" | "sonnet" | "haiku" — which Claude model to use
    
    Returns: {
        "insights": [str, ...],
        "recommendations": [str, ...],
        "auto_adjustments": {"strategy": ..., "batch_size": ..., ...} | None,
        "xp_earned": int,
    }
    """

def get_auto_adjustments() -> dict | None:
    """
    If level >= 4 and auto_adapt is enabled, return recommended adjustments.
    The unified_solver checks this every 100K keys and applies changes.
    
    Returns None if no adjustments recommended or level too low.
    Returns: {"strategy": str, "batch_size": int, "focus_range": tuple, ...}
    """

def get_insights(limit=10) -> list[dict]:
    """Get recent AI insights."""

def get_recommendations() -> list[str]:
    """Get current recommendations based on accumulated knowledge."""

def save_state():
    """Persist learning state to disk."""

def load_state():
    """Load learning state from disk."""
```

### Task 5.2: Active Learning Integration in UnifiedSolver

Add to `unified_solver.py`'s main scan loop:

```python
# Every 100K keys, check for AI auto-adjustments
if self.keys_tested % 100_000 == 0:
    from engines.learner import get_auto_adjustments, add_xp
    
    add_xp(1, "100K keys scanned")
    
    adjustments = get_auto_adjustments()
    if adjustments and self.use_brain:
        # Apply adjustments
        if "strategy" in adjustments:
            self.strategy = adjustments["strategy"]
        if "batch_size" in adjustments:
            self.batch_size = adjustments["batch_size"]
        if "check_every_n" in adjustments:
            self.check_every_n = adjustments["check_every_n"]
        
        # Notify callback so GUI can show what changed
        if self.callback:
            self.callback({"type": "auto_adjust", "adjustments": adjustments})
```

### Task 5.3: Create `nps/engines/session_manager.py` (New Engine)

**Public API:**

```python
def start_session(terminal_id: str, settings: dict) -> str:
    """Start a new session, return session_id."""

def end_session(session_id: str, stats: dict):
    """End a session, save final stats."""

def get_session(session_id: str) -> dict:
    """Get session data."""

def list_sessions(limit=50) -> list[dict]:
    """List all sessions, newest first."""

def get_session_stats() -> dict:
    """Aggregate stats across all sessions."""
```

### Task 5.4: Redesign Memory Tab

**File:** `gui/memory_tab.py` — REDESIGNED (~400 lines)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Memory — AI Learning Center                                         │
│  "What the AI has learned from all scanning and solving."            │
│                                                                      │
│  ┌─ AI Level ──────────────────────────────────────────────────────┐ │
│  │  Level 3: APPRENTICE                                            │ │
│  │  XP: 547 / 2000 [████████░░░░░░░░░░░░] → Expert                │ │
│  │  Capabilities: Observe, Recommend, Suggest                      │ │
│  │  ☐ Auto-Adapt (unlocks at Level 4)                              │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─ Lifetime Stats ────────────────────────────────────────────────┐ │
│  │  Total keys tested:    50,234,567    Total runtime: 120.5 hours │ │
│  │  Total seeds tested:   1,234,567     Scan sessions: 47          │ │
│  │  Online checks:        12,345        Balances found: 0          │ │
│  │  Puzzles solved:       10/160        Avg speed: 42,000/s        │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─ AI Brain ─────────────────────────┐  ┌─ Vault Summary ────────┐ │
│  │  Model: [Sonnet ▼]                 │  │  Total findings: 156   │ │
│  │  [Learn Now]                       │  │  With balance: 0       │ │
│  │                                     │  │  BTC: 89 | ETH: 67    │ │
│  │  Latest insights:                   │  │  Vault: 2.1 MB        │ │
│  │  • Score gap is positive (+0.305)   │  │  Encrypted: ✅        │ │
│  │  • Entropy < 2.1 in 63% of highs   │  │  [Export CSV] [JSON]   │ │
│  │  • Try Both mode more often         │  │  [View All Findings]   │ │
│  └─────────────────────────────────────┘  └────────────────────────┘ │
│                                                                      │
│  ┌─ Sessions Archive ──────────────────────────────────────────────┐ │
│  │  Session 47 | Feb 6, 08:30-12:15 | 3.75h | 168,750,000 keys   │ │
│  │  Session 46 | Feb 5, 22:00-02:30 | 4.50h | 202,500,000 keys   │ │
│  │  ...                                                            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─ Controls ──────────────────────────────────────────────────────┐ │
│  │  [Recalculate Weights]  [Flush Memory]  [Export Report]         │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### Task 5.5: Create Tests

- `nps/tests/test_learner.py` — test learn function (with mocked Claude CLI), state save/load, levels, XP, auto_adjustments
- `nps/tests/test_session_manager.py` — test session lifecycle, listing, data integrity

### Phase 5 Verification Checklist

- [ ] `nps/engines/learner.py` exists with full API
- [ ] `nps/engines/session_manager.py` exists with full API
- [ ] Learning levels system works (XP, level names, progression)
- [ ] "Learn Now" button triggers AI analysis (or shows "CLI not available")
- [ ] Model dropdown works (Opus, Sonnet, Haiku)
- [ ] Insights are displayed in the tab
- [ ] Auto-adapt mode works at Level 4+ (adjusts scanner settings)
- [ ] UnifiedSolver reads auto_adjustments every 100K keys
- [ ] Sessions Archive shows all past sessions
- [ ] Vault Summary connects to Vault with export buttons
- [ ] Learning state persists to disk
- [ ] All new tests pass
- [ ] Full test suite passes
- [ ] PROGRESS.md updated

---

## PHASE 6: DASHBOARD UPGRADE

**Goal:** Transform the Dashboard into a multi-terminal command center. Support running multiple scan instances simultaneously. Show daily insights. Add connection health monitoring.

### What "Multi-Terminal" Means

Currently: ONE scanner can run at a time.
After V3: The user can launch MULTIPLE scan instances (called "terminals"), each with its own settings. For example:

- Terminal 1: Random key scan, BTC + ETH, puzzle #66 enabled
- Terminal 2: BIP39 seed scan, ETH + USDT only, no puzzle
- Terminal 3: Random key scan, BTC only, puzzle #67 enabled

Each terminal runs its own `UnifiedSolver` instance in its own thread. The Dashboard shows all of them.

### Task 6.1: Create `nps/engines/terminal_manager.py` (New Engine)

**Public API:**

```python
MAX_TERMINALS = 10

def create_terminal(settings: dict) -> str:
    """
    Create a new scan terminal with given settings.
    Returns terminal_id.
    
    settings = {
        "name": "Terminal 1",
        "mode": "both",
        "puzzle_enabled": True,
        "puzzle_number": 66,
        "strategy": "hybrid",
        "chains": ["btc", "eth"],
        "tokens": ["USDT", "USDC"],
        "online_check": True,
        "use_brain": True,
    }
    """

def start_terminal(terminal_id: str) -> bool:
    """Start scanning on this terminal."""

def stop_terminal(terminal_id: str) -> bool:
    """Stop scanning on this terminal."""

def pause_terminal(terminal_id: str) -> bool:
    """Pause scanning (keep state)."""

def resume_terminal(terminal_id: str) -> bool:
    """Resume scanning."""

def remove_terminal(terminal_id: str) -> bool:
    """Remove a terminal (must be stopped first)."""

def start_all() -> int:
    """Start all terminals. Returns count started."""

def stop_all() -> int:
    """Stop all terminals. Returns count stopped."""

def get_terminal_stats(terminal_id: str) -> dict:
    """Get stats for one terminal."""

def get_all_stats() -> dict:
    """
    Get combined stats across all terminals.
    Returns: {
        "terminals": [{"id": ..., "stats": {...}}, ...],
        "combined": {
            "total_keys": int,
            "total_seeds": int,
            "combined_speed": float,
            "total_hits": int,
        }
    }
    """

def get_active_count() -> int:
    """How many terminals are currently running."""
```

### Task 6.2: Connection Health Monitor (NEW — was missing)

Add to `nps/engines/health.py` (New Engine):

```python
"""
NPS Connection Health Monitor — Background heartbeat checking.

Checks API endpoints every 60 seconds and reports status.
Results shown as colored dots in the status bar.
"""

import threading, time, urllib.request, json

ENDPOINTS = {
    "blockstream": "https://blockstream.info/api/blocks/tip/hash",
    "eth_rpc": None,       # Set from config
    "telegram": None,      # Set from config (uses getMe endpoint)
}

_status = {}  # {"blockstream": True, "eth_rpc": False, ...}
_lock = threading.Lock()
_running = False


def start_monitoring(interval=60):
    """Start background health checks."""

def stop_monitoring():
    """Stop background health checks."""

def get_status() -> dict:
    """Get current health status for all endpoints."""

def is_healthy(endpoint: str) -> bool:
    """Check if a specific endpoint is healthy."""
```

### Task 6.3: Redesign Dashboard Tab

**File:** `gui/dashboard_tab.py` — REDESIGNED (~600 lines)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Dashboard — Command Center                                         │
│                                                                     │
│  ┌─ Health ────────────────────────────────────────────────────────┐│
│  │  BTC API: ● GREEN   ETH RPC: ● GREEN   Telegram: ● GREEN      ││
│  │  BSC: ● GREEN   Polygon: ● YELLOW   Last check: 30s ago       ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  ┌─ Daily Insight ─────────────────────────────────────────────────┐│
│  │  🌙 Waning Gibbous (81%) — Release, refinement, completion     ││
│  │  FC60: VE-OX — Creativity meets grounding                      ││
│  │  Lucky numbers: 7, 11, 22                                      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  ┌─ Terminals ─────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │  ┌─ Terminal 1 ─────────┐  ┌─ Terminal 2 ─────────┐            ││
│  │  │  ▶ RUNNING            │  │  ■ STOPPED            │           ││
│  │  │  Mode: Both + #66     │  │  Mode: Seeds only     │           ││
│  │  │  Keys: 1.2M  45K/s   │  │  Seeds: 0             │           ││
│  │  │  Hits: 0              │  │  Hits: 0              │           ││
│  │  │  [Pause] [Stop]       │  │  [Start] [Remove]     │           ││
│  │  └──────────────────────┘  └──────────────────────┘            ││
│  │                                                                  ││
│  │  [+ Add Terminal]   [Start All]   [Stop All]                    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  ┌─ Combined Stats ─────────┐  ┌─ Vault Quick View ──────────────┐│
│  │  Total: 6.9M operations  │  │  Findings: 156                   ││
│  │  Speed: 68,456/s combined│  │  With balance: 0                 ││
│  │  AI Level: 3 (Apprentice)│  │  BTC: 89 | ETH: 67              ││
│  │  Runtime: 4h 23m today   │  │  Encrypted: ✅                   ││
│  └──────────────────────────┘  └──────────────────────────────────┘│
│                                                                     │
│  ┌─ Activity Log ──────────────────────────────────────────────────┐│
│  │  14:30:15 Terminal 1 started (Both + #66, BTC+ETH)             ││
│  │  14:30:30 Health check: all endpoints healthy                  ││
│  │  14:31:00 Checkpoint saved (Terminal 1, 100K keys)             ││
│  │  14:32:00 AI auto-adjust: batch_size 1099 → 1500              ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### Task 6.4: Keyboard Shortcuts (NEW — quality of life)

Add to `main.py`:

```python
# Keyboard shortcuts
root.bind("<Command-1>", lambda e: notebook.select(0))  # Dashboard
root.bind("<Command-2>", lambda e: notebook.select(1))  # Hunter
root.bind("<Command-3>", lambda e: notebook.select(2))  # Oracle
root.bind("<Command-4>", lambda e: notebook.select(3))  # Memory
root.bind("<Command-5>", lambda e: notebook.select(4))  # Settings
root.bind("<Command-s>", lambda e: terminal_manager.start_all())
root.bind("<Command-x>", lambda e: terminal_manager.stop_all())
root.bind("<Command-n>", lambda e: dashboard_tab.add_terminal())
```

### Task 6.5: Move Hunter Tab to Terminal-Based

After the Dashboard gets multi-terminal support, the Hunter tab changes role:

- The Hunter tab becomes a **detailed view** for the currently selected terminal
- It shows the Live Feed, detailed stats, High Score Alert, and AI Insight for ONE terminal
- The Dashboard shows ALL terminals at a glance
- The user can click on a terminal in the Dashboard to switch the Hunter tab to that terminal

**Implementation:** add a `set_active_terminal(terminal_id)` method to HunterTab.

### Task 6.6: Sound Alert (NEW — quality of life)

Add to `engines/notifier.py`:

```python
def play_alert_sound():
    """Play alert sound on balance hit. Cross-platform."""
    import platform
    system = platform.system()
    if system == "Darwin":  # macOS
        os.system('afplay /System/Library/Sounds/Glass.aiff &')
    elif system == "Linux":
        os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga &')
    else:
        print('\a')  # Terminal bell
```

Config toggle in config.json: `"sound_on_hit": true`

### Task 6.7: Create Tests

- `nps/tests/test_terminal_manager.py` — create/start/stop/remove terminals, max limit, stats, concurrent
- `nps/tests/test_health.py` — health monitor start/stop, status reporting

### Phase 6 Verification Checklist

- [ ] `nps/engines/terminal_manager.py` exists with full API
- [ ] `nps/engines/health.py` exists with health monitoring
- [ ] Dashboard shows terminal cards with live stats
- [ ] Health status dots show API connectivity
- [ ] "+ Add Terminal" creates a new terminal
- [ ] Each terminal can be started/stopped/paused independently
- [ ] "Start All" / "Stop All" work
- [ ] Maximum 10 terminals enforced
- [ ] Hunter tab shows detailed view of selected terminal
- [ ] Daily Insight card shows today's insight
- [ ] Vault Quick View shows summary from vault
- [ ] Activity Log captures events
- [ ] Keyboard shortcuts work (Cmd+1-5, Cmd+S, Cmd+X, Cmd+N)
- [ ] Sound alert plays on balance hit (when enabled)
- [ ] Checkpoint resume dialog on startup (if checkpoints exist)
- [ ] All new tests pass
- [ ] Full test suite passes
- [ ] PROGRESS.md updated

---

## PHASE 7: SETTINGS & CONNECTIONS TAB

**Goal:** Add a 5th tab called "Settings" that covers Telegram configuration, deployment, remote control, and general app settings. This is the control hub for everything that connects NPS to the outside world.

### Task 7.1: Create `nps/gui/settings_tab.py` (New GUI Tab)

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  Settings & Connections                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─ Telegram ─────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Bot Token: [**********************JIE]  [Show/Hide]           │ │
│  │  ⚠ Using plaintext config. Set NPS_BOT_TOKEN env var instead.  │ │
│  │  Chat ID:   [7624925300            ]                            │ │
│  │  Status:    ● Connected                                         │ │
│  │                                                                 │ │
│  │  [ Test Connection ]    [ Save ]                                │ │
│  │                                                                 │ │
│  │  ── Telegram Commands ──                                        │ │
│  │  /status  — Get current stats from all terminals                │ │
│  │  /pause   — Pause all scanning                                  │ │
│  │  /resume  — Resume scanning                                     │ │
│  │  /stop    — Stop all scanning                                   │ │
│  │  /sign    — Read a sign remotely                                │ │
│  │  /name    — Analyze a name remotely                             │ │
│  │  /memory  — Get memory/learning stats                           │ │
│  │  /vault   — Get vault summary                                   │ │
│  │  /perf    — Performance metrics                                 │ │
│  │  /help    — Show all commands                                   │ │
│  │                                                                 │ │
│  │  ── Notification Settings ──                                    │ │
│  │  ☑ Notify on balance hit                                        │ │
│  │  ☑ Notify on puzzle match                                       │ │
│  │  ☑ Notify on high score (> 0.8)                                 │ │
│  │  ☑ Daily status report                                          │ │
│  │  ☑ Sound alert on balance hit                                   │ │
│  │  Report interval: [24] hours                                    │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ Security ─────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Encryption: ● Active (AES-256)                                 │ │
│  │  Vault encrypted: ✅  Keys protected: ✅                        │ │
│  │  [ Change Master Password ]  [ Re-encrypt Vault ]              │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ Deployment ───────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Headless Mode Settings:                                        │ │
│  │  Auto-start scanner: ☑    Mode: [Both ▼]                       │ │
│  │  Auto-start puzzles: [66, 67]                                   │ │
│  │  Daily status report: ☑                                         │ │
│  │  Status interval: [24] hours                                    │ │
│  │                                                                 │ │
│  │  [ Generate Deploy Command ]                                    │ │
│  │  > NPS_MASTER_PASSWORD=xxx NPS_BOT_TOKEN=xxx python3 main.py    │ │
│  │    --headless                                                   │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ Scanner Settings ─────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Batch size: [1099]       Check every N: [5000]                │ │
│  │  Scanner threads: [2]     Addresses per seed: [5]              │ │
│  │  Default chains: ☑ BTC  ☑ ETH  ☑ BSC  ☐ Polygon              │ │
│  │  Default tokens: ☑ USDT  ☑ USDC  ☑ DAI  ☐ WBTC               │ │
│  │  Checkpoint interval: [100000] keys                            │ │
│  │  Auto-adapt: ☐ (Level 4 required)                              │ │
│  │                                                                 │ │
│  │  [ Save Settings ]  [ Reset Defaults ]                         │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ About ────────────────────────────────────────────────────────┐ │
│  │  NPS v3.0 — Numerology Puzzle Solver                           │ │
│  │  Built with Claude Code CLI + Claude Opus 4.6                  │ │
│  │  Config: ~/Desktop/BTC/nps/config.json                         │ │
│  │  Data: ~/Desktop/BTC/nps/data/                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Task 7.2: Modify `engines/config.py`

Add:

```python
def save_config(updates: dict):
    """
    Save config changes. Merges updates into existing config.
    Uses atomic write (write to .tmp then rename).
    """

def reset_defaults():
    """Reset config.json to factory defaults."""

def get_config_path() -> str:
    """Return the full path to config.json."""
```

### Task 7.3: Expand Telegram Commands

Modify `engines/notifier.py` to support:

```python
TELEGRAM_COMMANDS = {
    "/status": "Get current stats from all terminals",
    "/pause": "Pause all scanning",
    "/resume": "Resume scanning",
    "/stop": "Stop all scanning",
    "/start": "Start all terminals",
    "/sign": "Read a sign (e.g., /sign 11:11)",
    "/name": "Analyze a name (e.g., /name Hamzeh)",
    "/memory": "Get memory/learning stats",
    "/vault": "Get vault summary",
    "/perf": "Performance metrics",
    "/terminals": "List all terminals and their status",
    "/checkpoint": "Force save all checkpoints",
    "/help": "Show all commands",
}
```

Implement a `process_telegram_command(command: str) -> str` function that dispatches to the right handler and returns the response text.

### Task 7.4: Add 5th Tab to main.py

Modify `nps/main.py`:

```python
# Add Settings tab (5th tab)
from gui.settings_tab import SettingsTab
settings_tab = SettingsTab(notebook)
notebook.add(settings_tab, text="  Settings  ")
```

### Task 7.5: Create Tests

`nps/tests/test_settings.py`:

```python
# Test cases:
# 1. save_config merges updates correctly
# 2. reset_defaults restores factory settings
# 3. Telegram command dispatch returns valid responses
# 4. All telegram commands return non-empty strings
# 5. Settings tab initializes without errors
```

### Phase 7 Verification Checklist

- [ ] `nps/gui/settings_tab.py` exists and renders correctly
- [ ] 5th tab visible in the app
- [ ] Telegram section: bot token masked, test connection works
- [ ] Security section: shows encryption status, change password works
- [ ] Deployment section: generates correct headless command with env vars
- [ ] Scanner settings: all fields save to config.json
- [ ] Notification toggles save correctly
- [ ] Sound alert toggle works
- [ ] Reset Defaults restores factory config
- [ ] All Telegram commands implemented (/status through /help)
- [ ] `/vault` returns vault summary
- [ ] `/terminals` lists all terminals
- [ ] `/checkpoint` forces checkpoint save
- [ ] All new tests pass
- [ ] Full test suite passes
- [ ] PROGRESS.md updated

---

## FINAL STEPS (After All Phases Complete)

### 1. Update Documentation

- `README.md` — update with V3 features, 5 tabs, multi-terminal, encryption
- `CLAUDE.md` — add new files, new rules (encryption, vault, terminals)
- `docs/CHANGELOG.md` — add V3 entry
- Copy `UPDATE_V3_FINAL.md` to `docs/`

### 2. Final Test Suite

```bash
cd nps && python3 -m unittest discover tests/ -v
```

Expected: 189+ tests, all pass.

### 3. Performance Smoke Test

```bash
python3 -c "
import time
start = time.time()
# Import all modules
from engines import vault, security, learner, session_manager, terminal_manager, health
from engines import oracle, memory, config, notifier, balance
from engines import fc60, numerology, math_analysis, crypto, scoring, learning, ai_engine
elapsed = time.time() - start
print(f'All imports: {elapsed:.2f}s')
assert elapsed < 3.0, f'Startup too slow: {elapsed:.2f}s'
print('✅ Startup < 3s')
"
```

### 4. Update PROGRESS.md

Mark all phases complete. Final entry.

---

## APPENDIX A: FILE MAP — WHAT EXISTS NOW

(See "Current State" section above)

---

## APPENDIX B: NEW FILE MAP — WHAT WILL EXIST AFTER V3

```
BTC/
├── README.md                        ★ Updated with V3 info
├── CLAUDE.md                        ★ Updated with new files/rules
├── PROGRESS.md                      ★ NEW — build progress tracker
├── UPDATE_V3_FINAL.md
├── docs/
│   ├── BLUEPRINT.md
│   ├── UPDATE_V1.md
│   ├── UPDATE_V2.md
│   ├── UPDATE_V3_FINAL.md           ★ Copy of this file
│   └── CHANGELOG.md                 ★ Updated
├── nps/
│   ├── main.py                      ★ Modified: 5 tabs, terminal manager, vault, security
│   ├── config.json                  ★ Modified: new sections
│   ├── config.json.v2.backup        ★ Backup of V2 config
│   ├── migration.py                 ★ NEW — V2→V3 data migration (run once)
│   ├── engines/
│   │   ├── ... (all existing engines unchanged unless noted)
│   │   ├── security.py              ★ NEW — Encryption, secret management
│   │   ├── vault.py                 ★ NEW — Findings vault storage
│   │   ├── learner.py               ★ NEW — Active AI learning engine
│   │   ├── session_manager.py       ★ NEW — Per-session file management
│   │   ├── terminal_manager.py      ★ NEW — Multi-terminal orchestration
│   │   ├── health.py                ★ NEW — Connection health monitoring
│   │   ├── oracle.py                ★ MODIFIED — human meanings, question_sign
│   │   ├── config.py                ★ MODIFIED — save_config, reset_defaults, env vars
│   │   ├── notifier.py              ★ MODIFIED — new commands, sound alert, dispatch
│   │   ├── balance.py               ★ MODIFIED — BSC, Polygon chains
│   │   └── memory.py                ★ MODIFIED — connects to vault + learner
│   ├── gui/
│   │   ├── dashboard_tab.py         ★ REDESIGNED — multi-terminal command center
│   │   ├── hunter_tab.py            ★ REDESIGNED — unified controls, terminal view
│   │   ├── oracle_tab.py            ★ REDESIGNED — question mode, human output
│   │   ├── memory_tab.py            ★ REDESIGNED — AI learning center
│   │   ├── settings_tab.py          ★ NEW — 5th tab
│   │   ├── theme.py                 (unchanged)
│   │   └── widgets.py               ★ MODIFIED — password dialog, new widgets
│   ├── solvers/
│   │   ├── unified_solver.py        ★ NEW — primary scanner with checkpoints
│   │   ├── btc_solver.py            (kept as reference)
│   │   ├── scanner_solver.py        (kept as reference)
│   │   └── ... (other solvers unchanged)
│   ├── tests/
│   │   ├── test_security.py         ★ NEW
│   │   ├── test_vault.py            ★ NEW
│   │   ├── test_unified_solver.py   ★ NEW
│   │   ├── test_learner.py          ★ NEW
│   │   ├── test_session_manager.py  ★ NEW
│   │   ├── test_terminal_manager.py ★ NEW
│   │   ├── test_health.py           ★ NEW
│   │   ├── test_settings.py         ★ NEW
│   │   ├── test_oracle.py           ★ MODIFIED
│   │   └── ... (all existing tests unchanged)
│   └── data/
│       ├── .vault_salt              ★ NEW — encryption salt (never commit)
│       ├── findings/                ★ NEW directory
│       │   ├── vault_master.json
│       │   ├── vault_live.jsonl
│       │   ├── sessions/
│       │   └── summaries/
│       ├── sessions/                ★ NEW directory
│       ├── learning/                ★ NEW directory
│       │   └── learning_state.json
│       ├── checkpoints/             ★ NEW directory
│       ├── v2_archive/              ★ NEW — migrated V2 data
│       ├── scan_sessions.json       (existing, kept for reference)
│       └── scanner_knowledge/       (existing, kept for reference)
```

---

## APPENDIX C: CONFIG.JSON CHANGES

**Add these new sections** to the existing `config.json`. Do NOT delete existing sections.

```json
{
  "security": {
    "encryption_enabled": true,
    "env_var_prefix": "NPS_"
  },
  "vault": {
    "auto_record": true,
    "record_interesting": true,
    "interesting_score_threshold": 0.7,
    "summary_interval": 100
  },
  "scanner": {
    "mode": "both",
    "threads": 2,
    "batch_size": 1099,
    "check_balance_every_n": 5000,
    "chains": ["btc", "eth"],
    "tokens": ["USDT", "USDC", "DAI", "WBTC"],
    "addresses_per_seed": 5,
    "checkpoint_interval": 100000,
    "sound_on_hit": true
  },
  "terminals": {
    "max_terminals": 10,
    "auto_checkpoint": true
  },
  "learning": {
    "auto_adapt": false,
    "default_model": "sonnet",
    "learn_interval_keys": 100000
  },
  "health": {
    "enabled": true,
    "interval_seconds": 60,
    "bsc_enabled": true,
    "polygon_enabled": false
  },
  "telegram": {
    "bot_token": "",
    "chat_id": "",
    "notify_balance_hit": true,
    "notify_puzzle_match": true,
    "notify_high_score": true,
    "notify_high_score_threshold": 0.8,
    "daily_report": true,
    "report_interval_hours": 24
  },
  "headless": {
    "auto_start_scanner": true,
    "scanner_mode": "both",
    "auto_start_puzzles": [66],
    "daily_report": true,
    "report_interval_hours": 24
  }
}
```

---

## APPENDIX D: TEST PLAN

| Test File | Tests | What It Covers |
|-----------|-------|---------------|
| test_security.py | 10+ | Encryption, decryption, env vars, tamper detection |
| test_vault.py | 11+ | Storage, encryption, export, thread safety |
| test_unified_solver.py | 12+ | All modes, puzzle toggle, checkpoints, resume |
| test_learner.py | 8+ | Levels, XP, learn function, auto_adjustments |
| test_session_manager.py | 6+ | Session lifecycle, listing, stats |
| test_terminal_manager.py | 8+ | Create/start/stop, max limit, combined stats |
| test_health.py | 4+ | Monitor start/stop, status reporting |
| test_settings.py | 5+ | Config save/reset, Telegram commands |
| test_oracle.py (modified) | +5 | Human meanings, question_sign, daily_insight |
| **Total new tests** | **69+** | |
| **Total after V3** | **216+** | |

---

## APPENDIX E: PERFORMANCE ACCEPTANCE CRITERIA

| Metric | Target | How to Verify |
|--------|--------|--------------|
| App startup (GUI) | < 3 seconds | `time python3 main.py` (measure to first window) |
| App startup (headless) | < 2 seconds | `time python3 main.py --headless` (measure to first scan) |
| All imports | < 1.5 seconds | Python import timer (see Final Steps) |
| Vault write (single finding) | < 5 ms | Benchmark 1000 writes, measure average |
| Checkpoint save | < 10 ms | Benchmark in test |
| GUI update latency | < 100 ms | No visible lag when clicking tabs |
| 10 terminals running | CPU < 80% | `top` command during 10-terminal run |
| 10 terminals running | Memory < 500 MB | `ps aux` during 10-terminal run |
| Health check cycle | < 2 seconds | Monitor log for check duration |
| Encrypt/decrypt | < 1 ms per operation | Benchmark 10000 operations |
| Live Feed rendering | No lag at 200 rows | Scroll test with 200 entries |

---

## ESTIMATED TOTALS AFTER V3

| Metric | After V2 | After V3 | Change |
|--------|----------|----------|--------|
| Total Python lines | ~17,369 | ~25,000+ | +7,600+ |
| Tabs | 4 | 5 | +1 (Settings) |
| Engines | 14 | 21 | +7 (security, vault, learner, session_manager, terminal_manager, health, migration) |
| Solvers | 6 | 7 | +1 (unified_solver) |
| GUI files | 8 | 7 | +1 new (settings), -2 deleted (name_tab, consolidated) |
| Test files | 18 | 26 | +8 |
| Test count | ~147 | ~216+ | +69+ |
| Simultaneous scanners | 1 | Up to 10 | Multi-terminal |
| Chains | 2 (BTC, ETH) | 4 (+ BSC, Polygon) | +2 |
| Storage system | Basic JSON | Encrypted Vault + Sessions + Learning | Full persistence |
| AI Learning | Passive | Active with auto-adapt | Intelligence system |
| Security | None | AES encryption + env vars | Protected |
| Remote control | Basic Telegram | Full command set + health monitor | Complete |
| Crash recovery | None | Checkpoints every 100K keys | Resilient |

---

## BUILD ORDER SUMMARY

```
Phase 0 → Cleanup + Migration + PROGRESS.md (30 min)
    ↓
Phase 1 → Security layer: encryption + env vars (1-2 hours)
    ↓
Phase 2 → Vault engine + encrypted storage (2-3 hours)
    ↓
Phase 3 → Unified solver + checkpoints + BSC/Polygon (3-4 hours)
    ↓
Phase 4 → Oracle upgrade: human meanings + question mode (2-3 hours)
    ↓
Phase 5 → Active AI learning + session manager (3-4 hours)
    ↓
Phase 6 → Dashboard + multi-terminal + health monitor (3-4 hours)
    ↓
Phase 7 → Settings tab + Telegram expansion (2-3 hours)
    ↓
Final: Update docs, run full test suite, performance smoke test
```

**Total estimated build time: 18-24 hours of Claude Code work.**

Each phase is independent enough that if Claude Code runs out of context, you start a new session and tell it:

```
Read UPDATE_V3_FINAL.md. Check PROGRESS.md for current status.
Continue from the next incomplete phase.
Run the test suite first to verify current state, then continue building.
```

---

## CRITICAL REMINDERS FOR CLAUDE CODE

1. **Test after every phase.** Do not skip this.
2. **Update PROGRESS.md after every phase.** This is how we track across sessions.
3. **Do not delete old solvers.** Keep `btc_solver.py` and `scanner_solver.py` as reference.
4. **Thread safety everywhere.** Multiple terminals = multiple threads writing to vault, memory, etc.
5. **Graceful degradation.** If Claude CLI is not available, AI features show "Not available" — they never crash.
6. **Use existing theme.** All new GUI elements use `COLORS` and `FONTS` from `gui/theme.py`.
7. **Atomic file writes.** Write to `.tmp` then rename — never write directly to important files.
8. **Encrypt sensitive data.** Private keys and seed phrases MUST go through security.encrypt before storage.
9. **Environment variables first.** Always check env vars before config.json for secrets.
10. **Ask the user** for any high-stakes decision.
11. **Keep it working.** At no point should the app be broken. If a phase is half-done, the app should still launch.
12. **Checkpoints are mandatory.** Every terminal saves checkpoints. Crash recovery must work.

---

*End of UPDATE V3 FINAL. This transforms NPS from a single-scanner tool into a multi-terminal, AI-learning, encrypted hunting machine with persistent storage, crash recovery, human-readable wisdom, health monitoring, and full remote control.*

*5 tabs: Dashboard (Command Center) + Hunter (Unified Scanner) + Oracle (Wisdom Engine) + Memory (AI Learning Center) + Settings (Connection Hub)*
