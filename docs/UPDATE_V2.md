# NPS — UPDATE V2 (FINAL): Architecture Overhaul + Performance + Claude Code CLI

> **Created:** February 6, 2026
> **Author:** Dave (The Dave) + Claude Opus 4.6
> **Prerequisite:** UPDATE_V1 must be fully built and working before starting V2.
> **Purpose:** Restructure the entire app based on real-world usage feedback.
> **Executor:** Claude Code CLI — reads this file and builds autonomously with approval gates.

---

## CHANGE LOG FROM PREVIOUS V2 DRAFT

| # | What Changed | Why |
|---|-------------|-----|
| 1 | **Added Section 16: Performance Architecture** | App was slow — no caching, disk I/O on every operation, GUI freezes |
| 2 | **Added Section 17: Claude Code CLI Execution Protocol** | Previous V2 had vague "paste this prompt" — now has full agent directives |
| 3 | **Memory system redesigned** | Old design: `load_memory()` + `save_memory()` on every call = disk thrash. New: in-memory cache with periodic flush |
| 4 | **GUI threading model documented** | Tkinter is single-threaded — worker threads need `root.after()` for safe updates |
| 5 | **Added batch balance checking** | Checking one address at a time is slow. New: batch API calls |
| 6 | **Added performance targets** | No way to verify "fast enough" without measurable benchmarks |
| 7 | **Added error recovery strategy** | Old V2 had no plan for crashes, corrupt files, API failures |
| 8 | **Added profiling phase** | Build order now includes Phase 0: measure what's slow before fixing |
| 9 | **Expanded Claude Code CLI instructions** | Task subagents, ULTRATHINK, structured verification, WebSearch directives |
| 10 | **Added graceful degradation rules** | What happens when Claude CLI unavailable, no internet, corrupt memory file |

---

## TABLE OF CONTENTS

1. [What Changed and Why](#1-what-changed-and-why)
2. [New App Structure](#2-new-app-structure)
3. [Tab 1: Dashboard — The War Room](#3-tab-1-dashboard--the-war-room)
4. [Tab 2: Hunter — Unified Puzzle + Scanner](#4-tab-2-hunter--unified-puzzle--scanner)
5. [Tab 3: Oracle — Sign Reader + Numerology](#5-tab-3-oracle--sign-reader--numerology)
6. [Tab 4: Memory — AI Learning Dashboard](#6-tab-4-memory--ai-learning-dashboard)
7. [Telegram Command Center](#7-telegram-command-center)
8. [Adaptive Memory System](#8-adaptive-memory-system)
9. [Files to Delete](#9-files-to-delete)
10. [Files to Create](#10-files-to-create)
11. [Files to Modify](#11-files-to-modify)
12. [Build Order](#12-build-order)
13. [Test Plan](#13-test-plan)
14. [Quality Checklist](#14-quality-checklist)
15. [Design Rules](#15-design-rules)
16. [Performance Architecture](#16-performance-architecture) ← NEW
17. [Claude Code CLI Execution Protocol](#17-claude-code-cli-execution-protocol) ← NEW
18. [Error Recovery & Graceful Degradation](#18-error-recovery--graceful-degradation) ← NEW

---

## 1. WHAT CHANGED AND WHY

Dave ran the V1 build and identified these problems:

### Tabs to DELETE (not useful):
| Tab | Why Delete |
|-----|-----------|
| **Number Oracle** | Not needed. Nobody uses standalone number prediction. |
| **Date Decoder** | Not needed. Overlaps with Oracle functionality. |
| **Validation Dashboard** | Not useful as a full tab. Move the useful stats (Pearson, Score Gap) into Dashboard. |

### Tabs to MERGE:
| What | Into What | Why |
|------|-----------|-----|
| **BTC Hunter** + **Scanner** | → **Hunter** (one unified tab) | "With one move, hit two targets." While solving puzzles, also scan for wallets. Same keys, same addresses, same thread pool. |

### Tabs to REDESIGN:
| Tab | Problem | Fix |
|-----|---------|-----|
| **Dashboard** | AI Strategic Advisor is a purple box showing "Timeout after 20s". Wasted space. | Redesign: clean war room with live dual-mission stats. AI advisor becomes an inline compact section that actually works. |
| **Name Cipher** | Too basic. Just name + birthday → reading. | Upgrade to **Oracle**: reads signs, synchronicities, multiple calendar systems, location, time. Accessible from Telegram too. |
| **Scanner** | Separate from puzzle solving. No memory. Doesn't get smarter. | Merge into Hunter. Add adaptive memory. AI learns patterns over time. |

### New tab to ADD:
| Tab | Purpose |
|-----|---------|
| **Memory** | Shows what the AI has learned. Scan history, pattern analysis, score distributions, recommendations. Replaces Validation tab. |

### Result: 7 tabs → 4 tabs

| Before (V1) | After (V2) |
|-------------|-----------|
| Dashboard | **Dashboard** (redesigned) |
| BTC Hunter | → merged into **Hunter** |
| Number Oracle | ❌ deleted |
| Name Cipher | → upgraded to **Oracle** |
| Date Decoder | ❌ deleted |
| Validation | → parts moved to Dashboard + **Memory** tab |
| Scanner | → merged into **Hunter** |

---

## 2. NEW APP STRUCTURE

```
┌──────────────────────────────────────────────────────────────┐
│             NPS — Numerology Puzzle Solver                    │
├──────────┬──────────┬──────────┬──────────┐                  │
│Dashboard │  Hunter  │  Oracle  │  Memory  │                  │
├──────────┴──────────┴──────────┴──────────┘                  │
│                                                              │
│  [Tab content fills this space]                              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Ready  Learning: 10  AI: ON  TG: ON  Confidence: 0.10  •••  │
└──────────────────────────────────────────────────────────────┘
```

### File Structure After V2

```
nps/
├── main.py                    # Modified: 4 tabs, --headless, --profile flag
├── config.json                # Modified: new Oracle + memory + perf settings
│
├── engines/
│   ├── fc60.py               # Unchanged
│   ├── numerology.py         # Unchanged
│   ├── math_analysis.py      # Unchanged
│   ├── crypto.py             # Unchanged
│   ├── scoring.py            # Unchanged
│   ├── learning.py           # Modified: scan session memory, pattern learning
│   ├── ai_engine.py          # Modified: scanner brain, oracle brain, non-blocking calls
│   ├── config.py             # From V1 (unchanged)
│   ├── keccak.py             # From V1 (unchanged)
│   ├── notifier.py           # Modified: Telegram interactive commands, Oracle bot
│   ├── balance.py            # Modified: batch checking, connection pooling
│   ├── bip39.py              # From V1 (unchanged)
│   ├── oracle.py             # NEW: sign reader engine (multi-calendar, location, synchronicity)
│   ├── memory.py             # NEW: adaptive memory system with in-memory cache
│   └── perf.py               # NEW: performance monitoring + profiling hooks
│
├── solvers/
│   ├── btc_solver.py         # Modified: emits to unified Hunter callback
│   ├── scanner_solver.py     # Modified: shares thread pool with btc_solver, uses adaptive memory
│   ├── name_solver.py        # Unchanged (used by Oracle)
│   ├── date_solver.py        # Kept as engine (Oracle uses it), but no dedicated tab
│   └── number_solver.py      # Kept as engine (Oracle may reference), but no dedicated tab
│
├── gui/
│   ├── theme.py              # Modified: currency colors, Oracle theme elements
│   ├── widgets.py            # Modified: new widgets (LiveFeedTable, OracleCard, MemoryGraph)
│   ├── dashboard_tab.py      # REWRITTEN: War Room layout
│   ├── hunter_tab.py         # NEW: Unified puzzle + scanner
│   ├── oracle_tab.py         # NEW: Sign reader + name cipher + Telegram
│   ├── memory_tab.py         # NEW: AI learning dashboard
│   ├── btc_tab.py            # DELETED (merged into hunter_tab)
│   ├── number_tab.py         # DELETED
│   ├── date_tab.py           # DELETED
│   ├── validation_tab.py     # DELETED (merged into memory_tab + dashboard)
│   └── scanner_tab.py        # DELETED (merged into hunter_tab)
│
├── tools/
│   └── get_chat_id.py        # Unchanged
│
├── data/
│   ├── rich_addresses.txt    # Unchanged
│   ├── solve_history.json    # Unchanged
│   ├── factor_weights.json   # Unchanged
│   ├── scanner_hits.json     # Unchanged
│   ├── scan_memory.json      # NEW: adaptive memory storage
│   └── oracle_readings.json  # NEW: oracle reading history
│
└── tests/
    ├── test_fc60.py          # Unchanged
    ├── test_numerology.py    # Unchanged
    ├── test_crypto.py        # Unchanged
    ├── test_scoring.py       # Unchanged
    ├── test_math.py          # Unchanged
    ├── test_validation.py    # Unchanged
    ├── test_btc_solver.py    # Modified (Hunter integration)
    ├── test_learning.py      # Unchanged
    ├── test_config.py        # From V1
    ├── test_keccak.py        # From V1
    ├── test_notifier.py      # From V1
    ├── test_balance.py       # From V1
    ├── test_bip39.py         # From V1
    ├── test_scanner.py       # Modified (Hunter integration)
    ├── test_oracle.py        # NEW
    ├── test_memory.py        # NEW
    └── test_perf.py          # NEW: performance benchmarks
```

---

## 3. TAB 1: DASHBOARD — THE WAR ROOM

The Dashboard is the command center. At a glance, you see everything: puzzle progress, scanner activity, balance hits, AI status, Telegram status.

### Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  Dashboard                                                         │
│                                                                    │
│  ┌─ Current Moment ────────────────────────────────────────────┐   │
│  │  FC60: VE-OX-OXFI *MO-SNER-RAMT                            │   │
│  │  🌙 Waning Gibbous (81%)  GZ: 丙午 Fire Horse               │   │
│  │  Gratitude, sharing, distribution                            │   │
│  │  Morning engine — clarity peaks, resistance lowest           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌─ Mission Status ──────────────────────────────────────────────┐ │
│  │                                                                │ │
│  │  🎯 PUZZLE #71 (Hybrid)        🔍 SCANNER (Both Mode)        │ │
│  │  ─────────────────────         ──────────────────────         │ │
│  │  Keys tested: 1,234,567        Keys: 5,678,901               │ │
│  │  Speed: 23,456/s               Seeds: 12,345                 │ │
│  │  Progress: 0.23%               Speed: 45,000/s               │ │
│  │  Elapsed: 01:23:45             Hits: 0                       │ │
│  │                                                                │ │
│  │  ══════════════════════════════════════════════════════════    │ │
│  │  COMBINED: 6,913,468 operations | 68,456/s | Running 01:23   │ │
│  │  ₿ 0 found | Ξ 0 found | ₮ 0 found | Online: 123 checks    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─ Quick Stats ──────┐  ┌─ AI Brain ────────┐  ┌─ Comms ──────┐ │
│  │ Solved: 10         │  │ Confidence: 10%   │  │ TG: ✅ ON    │ │
│  │ Success: 100%      │  │ Memory: 2.1 MB    │  │ Chat: ✅     │ │
│  │ Score Gap: +0.305  │  │ Patterns: 47      │  │ Alerts: 3    │ │
│  │ Pearson: 0.000     │  │ Last insight: 2m  │  │ Uptime: 4h   │ │
│  └────────────────────┘  └───────────────────┘  └──────────────┘ │
│                                                                    │
│  ┌─ Live Activity (last 10 operations) ──────────────────────────┐ │
│  │  14:30:01 🔍 KEY 0x3a7f... → 1Abc... / 0xabc... → ₿0 Ξ0    │ │
│  │  14:30:01 🎯 #71 Testing key 891234 → score 0.42             │ │
│  │  14:30:02 🔍 SEED abandon ab... → 10 addr checked            │ │
│  │  14:30:02 🎯 #71 Testing key 891235 → score 0.38             │ │
│  │  14:30:03 🔍 KEY 0x5f88... → 1Jkl... / 0xjkl... → API ✓    │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

### Key Changes from V1 Dashboard

1. **No "AI Strategic Advisor" purple box.** The AI insight is compact and inline (inside "AI Brain" card). No timeout display. If AI times out, just show "—" and try again silently.

2. **Mission Status replaces "Active Solvers" and "Scanner Activity".** Both are shown side-by-side in ONE card with combined totals.

3. **Validation stats (Score Gap, Pearson) moved here** from the deleted Validation tab. Compact. No full-page display needed.

4. **Live Activity shows BOTH puzzle and scanner** operations interleaved. Color-coded: 🎯 gold for puzzle, 🔍 blue for scanner.

5. **"Recent Solves" section stays** but only shows if there are actual solves. Hidden when empty.

### Implementation

**File:** `gui/dashboard_tab.py` — REWRITE from scratch (~350 lines)

```python
class DashboardTab(tk.Frame):
    """War Room dashboard — everything at a glance."""
    
    def __init__(self, parent, **kwargs):
        # Top: Current Moment (FC60 reading)
        # Middle: Mission Status (puzzle + scanner side-by-side)
        # Stats Row: Quick Stats | AI Brain | Comms (3 compact cards)
        # Bottom: Live Activity (10 most recent operations, mixed)
    
    def update_puzzle_status(self, data: dict):
        """Called by Hunter tab when puzzle solver emits."""
    
    def update_scanner_status(self, data: dict):
        """Called by Hunter tab when scanner emits."""
    
    def update_live_activity(self, entry: dict):
        """Add an entry to the live activity feed."""
    
    def refresh_stats(self):
        """Refresh Quick Stats + AI Brain + Comms cards."""
```

### GUI Update Rule (CRITICAL — applies to ALL tabs)

Tkinter is single-threaded. Worker threads CANNOT touch widgets directly.

```python
# ❌ WRONG — will crash or freeze the GUI
def _solver_callback(self, data):
    self.speed_label.config(text=f"{data['speed']}/s")  # Called from worker thread

# ✅ CORRECT — schedule on main thread
def _solver_callback(self, data):
    self.after(0, self._update_speed, data['speed'])

def _update_speed(self, speed):
    self.speed_label.config(text=f"{speed}/s")
```

**Every callback from solver/scanner threads MUST use `self.after(0, ...)` to update GUI widgets.**

### GUI Update Throttling (PERFORMANCE)

Don't update the GUI on every single key tested. Throttle updates:

```python
# Update live feed: max 10 updates/second
# Update stats cards: max 2 updates/second
# Update progress bar: max 4 updates/second

import time

class ThrottledUpdater:
    """Prevents GUI from being overwhelmed with updates."""
    
    def __init__(self, min_interval_ms=100):
        self._last_update = 0
        self._interval = min_interval_ms / 1000
        self._pending = None
    
    def maybe_update(self, widget, callback, data):
        """Only calls callback if enough time has passed."""
        now = time.monotonic()
        if now - self._last_update >= self._interval:
            widget.after(0, callback, data)
            self._last_update = now
        else:
            self._pending = data  # Keep latest, discard intermediate
```

---

## 4. TAB 2: HUNTER — UNIFIED PUZZLE + SCANNER

This is the core tab. "One move, two targets."

- **Left side:** Puzzle solving (select puzzle, choose strategy, start/stop)
- **Right side:** Scanner (mode, chains, live feed)
- **Both run simultaneously** in separate thread pools
- **Shared:** balance checking, Telegram notifications, AI brain, learning engine

### Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  Hunter — Puzzle + Scanner                                           │
│                                                                      │
│  ┌─ Puzzle Mission ─────────────────┐  ┌─ Scanner Mission ──────────┐│
│  │                                   │  │                            ││
│  │  Puzzle: [#71 ✓ [D] 400 BTC ▼]   │  │  Mode: (●) Both           ││
│  │  Strategy: ● Hybrid  ○ Oracle     │  │  Chains: ☑BTC ☑ETH ☑USDT  ││
│  │                                   │  │                            ││
│  │  ┌─────┐ ┌─────┐ ┌──────────┐    │  │  ┌─────┐ ┌─────┐          ││
│  │  │Start│ │Stop │ │Self-Test │    │  │  │Start│ │Stop │          ││
│  │  └─────┘ └─────┘ └──────────┘    │  │  └─────┘ └─────┘          ││
│  │                                   │  │                            ││
│  │  Puzzle: #71                      │  │  Keys: 5,678,901           ││
│  │  Range: 2^70 to 2^71             │  │  Seeds: 12,345             ││
│  │  Reward: 400 BTC                  │  │  Speed: 45,000/s           ││
│  │  Speed: 23,456/s                  │  │  Online: 123 checks        ││
│  │  Progress: 0.23%                  │  │  Hits: 0                   ││
│  │  Elapsed: 01:23:45                │  │  Memory: 47 patterns       ││
│  │                                   │  │                            ││
│  │  FC60: 🐉 Dragon + 🔥 Fire       │  │  Telegram: ✅ ON           ││
│  │  ████████░░░░░░░ 23%              │  │                            ││
│  └───────────────────────────────────┘  └────────────────────────────┘│
│                                                                      │
│  ┌─ Live Feed ──────────────────────────────────────────────────────┐│
│  │ TIME     SRC  TYPE  SOURCE          BTC ADDR      ETH ADDR       ││
│  │                                     ₿ BTC  Ξ ETH  ₮ USDT  CHK   ││
│  ├──────────────────────────────────────────────────────────────────  ││
│  │ 14:30:01 🎯  PUZ   key:891234      1Abc...Xyz    —              ││
│  │                                     —      —      —       ·      ││
│  │ 14:30:01 🔍  KEY   0x3a7f...8b2c   1Def...Uvw    0xdef...uvw    ││
│  │                                     0.000  0.000  0.000   ·      ││
│  │ 14:30:02 🔍  SEED  abandon ab...   1Ghi...Rst    0xghi...rst    ││
│  │                                     0.000  0.000  0.000   ·      ││
│  │ 14:30:02 🎯  PUZ   key:891235      1Jkl...Mno    —              ││
│  │                                     —      —      —       ·      ││
│  │ 14:30:03 🔍  KEY   0x5f88...1a3b   1Pqr...Stu    0xpqr...stu    ││
│  │                                     0.000  0.000  0.000   API ✓  ││
│  │                                                                   ││
│  │ (green row = BALANCE FOUND | entries from BOTH missions mixed)    ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─ Activity Log ────────────────────┐  ┌─ AI Insight ──────────────┐│
│  │ 14:30:15 Online check complete    │  │ Pattern: keys near 2^70   ││
│  │ 14:30:30 Seed #12,345 checked     │  │ have 12% higher entropy.  ││
│  │ 14:31:00 🔄 Memory saved (47 p.)  │  │ Try focusing on master    ││
│  │ 14:32:00 📊 Daily stats sent TG   │  │ numbers in this range.    ││
│  └────────────────────────────────────┘  └──────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Puzzle and Scanner have SEPARATE start/stop buttons.** You can run just puzzle, just scanner, or both. They are independent but share the same live feed.

2. **Live Feed is UNIFIED.** Puzzle solver entries show 🎯 prefix. Scanner entries show 🔍. Both stream into the same scrolling table. This is the heartbeat of the app — you always see what's happening.

3. **When a puzzle key is tested, the scanner also checks that key's ETH address.** Free bonus check. If the puzzle key happens to have ETH balance, you win twice.

4. **AI Insight is a compact panel** — not a huge purple box. It shows the LATEST useful insight in 2-3 lines. Updates every 100K operations or 30 minutes. Never shows "Timeout" — if it times out, keep the previous insight.

### Live Feed Performance Rule

The live feed is a `ttk.Treeview` widget. Inserting thousands of rows will slow it down.

```python
MAX_FEED_ROWS = 200  # Never more than 200 rows in the treeview

def _add_to_feed(self, source: str, entry: dict):
    """Add entry to unified live feed with automatic trimming."""
    self.after(0, self._insert_feed_row, source, entry)

def _insert_feed_row(self, source, entry):
    """Runs on main thread. Inserts row and trims if needed."""
    item_id = self.feed_tree.insert("", 0, values=(...))  # Insert at top
    
    # Trim excess rows (delete from bottom)
    children = self.feed_tree.get_children()
    if len(children) > MAX_FEED_ROWS:
        for old_id in children[MAX_FEED_ROWS:]:
            self.feed_tree.delete(old_id)
```

### Implementation

**File:** `gui/hunter_tab.py` — NEW (~700 lines)

```python
class HunterTab(tk.Frame):
    """Unified Puzzle + Scanner — one tab, two missions."""
    
    def __init__(self, parent, **kwargs):
        # Left panel: Puzzle controls + stats
        # Right panel: Scanner controls + stats
        # Center: Unified LiveFeedTable
        # Bottom: Activity log + AI Insight
    
    # ── Puzzle Controls ──
    def _on_puzzle_start(self):
        """Start puzzle solver. Also starts bonus ETH check on puzzle keys."""
    
    def _on_puzzle_stop(self):
        """Stop puzzle solver only."""
    
    def _puzzle_callback(self, data: dict):
        """Receive puzzle solver progress. Feed to live table + dashboard."""
    
    # ── Scanner Controls ──
    def _on_scanner_start(self):
        """Start scanner with selected mode and chains."""
    
    def _on_scanner_stop(self):
        """Stop scanner only."""
    
    def _scanner_callback(self, data: dict):
        """Receive scanner progress. Feed to live table + dashboard."""
    
    # ── Unified Feed ──
    def _add_to_feed(self, source: str, entry: dict):
        """Add entry to unified live feed. source = 'puzzle' or 'scanner'."""
    
    # ── Balance Hit Handler ──
    def _on_balance_found(self, addresses: dict, balances: dict, source: str, key_data: dict):
        """CRITICAL: balance found! 
        1. Highlight row green in live feed
        2. Send Telegram alert with buttons
        3. Log to scanner_hits.json
        4. Record in adaptive memory
        5. Play sound (if available)
        """
```

### Puzzle-Scanner Integration Logic

When the puzzle solver tests a key, it follows this flow:

```
Puzzle key candidate
    │
    ├─→ Normal puzzle flow (check against puzzle target address)
    │
    └─→ BONUS: derive ETH address from same key
         │
         ├─→ Local check against rich_addresses.txt (instant)
         │
         └─→ If every Nth key: online multi-chain balance check
              │
              └─→ If any balance found → ALERT + NOTIFY
```

This means every puzzle operation is ALSO a scanner operation. Two for the price of one.

**Modify `solvers/btc_solver.py`** to emit extended data:

```python
def _btc_callback(self, data):
    """Extended callback that includes ETH address for the key being tested."""
    key = data.get('current_key')
    if key:
        from engines.bip39 import privkey_to_eth_address
        data['eth_address'] = privkey_to_eth_address(key)
    
    if self._callback:
        self._callback(data)
```

---

## 5. TAB 3: ORACLE — SIGN READER + NUMEROLOGY

This replaces the old "Name Cipher" tab. It's much more powerful.

### Concept

Dave sees something — a time on a clock, a license plate, a pattern in nature. He enters what he saw, where, when. The Oracle interprets it across multiple systems:

- **Pythagorean numerology** (existing)
- **FC60 encoding** (existing)
- **Chinese calendar** (existing — GanZhi, lunar cycle)
- **Chaldean numerology** (new)
- **Western astrology** (sun sign based on date)
- **Location energy** (latitude/longitude → geomantic interpretation)
- **Time synchronicity** (11:11, 22:22, mirror numbers, angel numbers)

### Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  Oracle — Sign Reader                                                │
│  "Enter what you see. The Oracle reads it across seven systems."     │
│                                                                      │
│  ┌─ What Did You See? ──────────────────────────────────────────────┐│
│  │                                                                   ││
│  │  Sign:  [11:11_________________________________]                  ││
│  │  When:  [2026-02-06] at [14:30]                                   ││
│  │  Where: [Bali, Indonesia___________] (optional)                   ││
│  │  Context: [Looked at clock while thinking about...]  (optional)   ││
│  │                                                                   ││
│  │  ┌──────────────┐  ┌───────┐                                      ││
│  │  │ 🔮 Read Sign │  │ Clear │                                      ││
│  │  └──────────────┘  └───────┘                                      ││
│  └───────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─ Reading ────────────────────────────────────────────────────────┐│
│  │                                                                   ││
│  │  ═══ NUMEROLOGY ═══                                               ││
│  │  Root: 4 (Builder, Foundation)                                    ││
│  │  Master: 11 → 11:11 is a Master Gateway                          ││
│  │  Pythagorean: Stability through change                            ││
│  │  Chaldean: Karmic completion                                      ││
│  │                                                                   ││
│  │  ═══ FC60 ANALYSIS ═══                                            ││
│  │  Token: VE-OX (Earth Ox — patience, hard work rewarded)          ││
│  │  Full: VE-OX-OXFI *MO-SNER-RAMT                                  ││
│  │  Energy: Grounding, material manifestation                        ││
│  │                                                                   ││
│  │  ═══ CHINESE CALENDAR ═══                                         ││
│  │  GanZhi: 丙午 Fire Horse (passion, restlessness, speed)          ││
│  │  Lunar: Waning Gibbous 81% — release, let go, trust              ││
│  │  Hour: 未 (Goat hour) — creativity, gentleness                   ││
│  │                                                                   ││
│  │  ═══ SYNCHRONICITY ═══                                            ││
│  │  Pattern: Mirror number (11:11) — gateway of alignment            ││
│  │  Angel Number: 1111 — new beginnings, manifestation active        ││
│  │  Frequency: You've seen 11:11 three times this week               ││
│  │                                                                   ││
│  │  ═══ INTERPRETATION ═══                                           ││
│  │  "This sign arrives during a Waning Gibbous in Fire Horse         ││
│  │   year. The universe is saying: release old patterns (Moon),      ││
│  │   trust your creative fire (Horse), and step through the          ││
│  │   gateway (11:11). This is a strong YES for new ventures."        ││
│  │                                                                   ││
│  └───────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─ Name Reading ─────────────────┐  ┌─ Reading History ────────────┐│
│  │  Name: [____________________]  │  │  Feb 6 14:30  11:11 → Gateway││
│  │  Birthday: [YYYY-MM-DD]        │  │  Feb 6 09:15  444 → Angels   ││
│  │  Mother: [________________]    │  │  Feb 5 22:00  Name: Hamzeh   ││
│  │  [Generate Full Profile]       │  │  Feb 5 18:30  777 → Luck     ││
│  └─────────────────────────────────┘  └──────────────────────────────┘│
│                                                                      │
│  ┌─ AI Interpretation ──────────────────────────────────────────────┐│
│  │  (Claude's deeper reading — connects current sign to your        ││
│  │   personal numerology profile and recent patterns)               ││
│  └───────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

### Oracle Engine

**File:** `engines/oracle.py` — NEW (~500 lines)

```python
"""
Oracle Engine — Multi-System Sign Reader

Reads signs and synchronicities across 7 systems:
1. Pythagorean numerology
2. Chaldean numerology  
3. FC60 encoding
4. Chinese calendar (GanZhi + lunar)
5. Western zodiac
6. Angel numbers / mirror numbers
7. Geomantic location energy

All outputs are combined into one unified reading.
"""

import logging
from engines import fc60, numerology, math_analysis
from engines.config import get

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════
# Angel Numbers Database
# ═══════════════════════════════════════════════════

ANGEL_NUMBERS = {
    "000": "Infinite potential. The universe is resetting. Start fresh.",
    "111": "New beginnings. Your thoughts are manifesting rapidly. Think positive.",
    "1111": "Master gateway. Alignment with higher purpose. Portal is open.",
    "222": "Balance and harmony. Trust the process. Partnerships forming.",
    "2222": "Double balance. Major alignment in relationships or deals.",
    "333": "Ascended masters are near. Creative expression is blessed.",
    "444": "Angels surround you. Protection and foundation are strong.",
    "555": "Major change coming. Embrace transformation. Let go of old.",
    "666": "Rebalance material and spiritual. Not negative — a recalibration.",
    "777": "Luck and divine alignment. You're on the right path. Keep going.",
    "888": "Abundance flowing. Financial or material harvest approaching.",
    "999": "Completion. A chapter ends. Prepare for what's next.",
    "1010": "Stay positive. Your reality is being shaped by your thoughts now.",
    "1212": "Step out of comfort zone. Growth requires courage.",
    "1234": "Simplify. Take it step by step. Progress is happening.",
}

MIRROR_NUMBERS = {
    "01:10": "What you give, you receive. Karma in action.",
    "02:20": "Patience. The answer comes when you stop forcing.",
    "03:30": "Communicate. Someone needs to hear what you know.",
    "04:40": "Build foundations. Don't skip steps.",
    "05:50": "Freedom calling. Break a pattern that holds you.",
    "10:01": "New cycle. Take initiative now.",
    "12:21": "Reflection. What you see outside is inside you.",
    "13:31": "Creativity + structure. Build something beautiful.",
    "14:41": "Determination. Push through resistance.",
    "15:51": "Change is your friend right now.",
    "21:12": "Trust your intuition over logic today.",
    "23:32": "Community. Reach out. Connection brings answers.",
}

# Chaldean number meanings (different from Pythagorean)
CHALDEAN_MEANINGS = {
    1: "Leadership, independence, solar energy",
    2: "Diplomacy, intuition, lunar energy",
    3: "Expression, joy, expansion (Jupiter)",
    4: "Rebellion, sudden change (Rahu/Uranus)",
    5: "Communication, travel, versatility (Mercury)",
    6: "Love, beauty, responsibility (Venus)",
    7: "Spirituality, analysis, mystery (Ketu/Neptune)",
    8: "Power, karma, material mastery (Saturn)",
    9: "Humanitarian, completion, warrior (Mars)",
}

# Western zodiac date ranges
ZODIAC_SIGNS = [
    ((1, 20), (2, 18), "Aquarius", "♒", "Innovation, humanitarianism, independence"),
    ((2, 19), (3, 20), "Pisces", "♓", "Intuition, compassion, transcendence"),
    ((3, 21), (4, 19), "Aries", "♈", "Initiative, courage, new beginnings"),
    ((4, 20), (5, 20), "Taurus", "♉", "Stability, sensuality, material comfort"),
    ((5, 21), (6, 20), "Gemini", "♊", "Communication, duality, adaptability"),
    ((6, 21), (7, 22), "Cancer", "♋", "Nurturing, home, emotional depth"),
    ((7, 23), (8, 22), "Leo", "♌", "Leadership, creativity, self-expression"),
    ((8, 23), (9, 22), "Virgo", "♍", "Analysis, service, perfection"),
    ((9, 23), (10, 22), "Libra", "♎", "Balance, partnership, justice"),
    ((10, 23), (11, 21), "Scorpio", "♏", "Transformation, intensity, depth"),
    ((11, 22), (12, 21), "Sagittarius", "♐", "Adventure, philosophy, expansion"),
    ((12, 22), (1, 19), "Capricorn", "♑", "Ambition, discipline, mastery"),
]

# Chinese hour animals (12 two-hour periods)
CHINESE_HOURS = {
    (23, 1): ("子", "Rat", "New cycles, cleverness, resourcefulness"),
    (1, 3): ("丑", "Ox", "Patience, hard work, dependability"),
    (3, 5): ("寅", "Tiger", "Courage, risk-taking, intensity"),
    (5, 7): ("卯", "Rabbit", "Diplomacy, gentleness, luck"),
    (7, 9): ("辰", "Dragon", "Power, ambition, success"),
    (9, 11): ("巳", "Snake", "Wisdom, intuition, transformation"),
    (11, 13): ("午", "Horse", "Freedom, speed, passion"),
    (13, 15): ("未", "Goat", "Creativity, peace, artistic expression"),
    (15, 17): ("申", "Monkey", "Intelligence, adaptability, playfulness"),
    (17, 19): ("酉", "Rooster", "Precision, timing, confidence"),
    (19, 21): ("戌", "Dog", "Loyalty, protection, honesty"),
    (21, 23): ("亥", "Pig", "Abundance, generosity, enjoyment"),
}


def read_sign(sign: str, date: str = None, time_str: str = None,
              location: str = None, context: str = None) -> dict:
    """Read a sign across all systems.
    
    Args:
        sign: What was seen (number, time, word, etc.)
        date: When it was seen (YYYY-MM-DD)
        time_str: Time it was seen (HH:MM)
        location: Where (city, country or lat,lng)
        context: What you were thinking/doing
    
    Returns dict with all interpretations.
    """
    reading = {
        "sign": sign,
        "date": date,
        "time": time_str,
        "location": location,
        "context": context,
        "numerology": {},
        "fc60": {},
        "chinese": {},
        "synchronicity": {},
        "zodiac": {},
        "chaldean": {},
        "interpretation": "",
    }
    
    # Extract numbers from the sign
    numbers = _extract_numbers(sign)
    
    # 1. Pythagorean numerology
    if numbers:
        combined = int("".join(str(n) for n in numbers))
        reading["numerology"] = {
            "root": numerology.numerology_reduce(numerology.digit_sum(combined)),
            "digit_sum": numerology.digit_sum(combined),
            "is_master": numerology.is_master_number(combined),
            "meaning": _pythagorean_meaning(numerology.numerology_reduce(numerology.digit_sum(combined))),
        }
    
    # 2. Chaldean numerology
    if numbers:
        chaldean_root = _chaldean_reduce(numbers)
        reading["chaldean"] = {
            "root": chaldean_root,
            "meaning": CHALDEAN_MEANINGS.get(chaldean_root, "Unknown"),
        }
    
    # 3. FC60 encoding
    if numbers:
        combined = int("".join(str(n) for n in numbers))
        if combined > 0:
            reading["fc60"] = {
                "token": fc60.token60(combined % 60),
                "full": fc60.encode_base60(combined),
                "animal": fc60.ANIMALS[(combined % 60) // 5],
                "element": fc60.ELEMENTS[(combined % 60) % 5],
            }
    
    # 4. Chinese calendar (date + time)
    if date:
        year, month, day = _parse_date(date)
        if year:
            jdn = fc60.compute_jdn(year, month, day)
            phase_idx, moon_age = fc60.moon_phase(jdn)
            phase_names = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
                           "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
            
            # Year animal
            year_stem_idx = (year - 4) % 10
            year_branch_idx = (year - 4) % 12
            
            reading["chinese"] = {
                "ganzhi_year": f"{fc60.STEMS[year_stem_idx]}{fc60.BRANCHES[year_branch_idx]}",
                "year_animal": fc60.ANIMALS[year_branch_idx],
                "year_element": fc60.ELEMENTS[year_stem_idx % 5],
                "moon_phase": phase_names[phase_idx],
                "moon_age": round(moon_age, 1),
                "moon_emoji": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"][phase_idx],
            }
            
            # Hour animal
            if time_str:
                hour = _parse_time(time_str)
                if hour is not None:
                    for (start, end), (char, animal, meaning) in CHINESE_HOURS.items():
                        if start <= hour < end or (start == 23 and (hour >= 23 or hour < 1)):
                            reading["chinese"]["hour_animal"] = animal
                            reading["chinese"]["hour_char"] = char
                            reading["chinese"]["hour_meaning"] = meaning
                            break
    
    # 5. Western zodiac
    if date:
        year, month, day = _parse_date(date)
        if month and day:
            reading["zodiac"] = _get_zodiac(month, day)
    
    # 6. Synchronicity / Angel numbers
    reading["synchronicity"] = _check_synchronicity(sign, time_str)
    
    # 7. Generate interpretation
    reading["interpretation"] = _generate_interpretation(reading)
    
    return reading


def read_name(name: str, birthday: str, mother_name: str = None) -> dict:
    """Full numerology profile from name + birthday.
    
    Combines Pythagorean + Chaldean + FC60.
    """
    from solvers.name_solver import NameSolver
    solver = NameSolver(name=name, birthday=birthday, 
                        mother_name=mother_name, callback=lambda d: None)
    # Use existing name solver logic
    result = solver.analyze()
    
    # Add Chaldean layer
    if result.get("life_path_number"):
        result["chaldean_life_path"] = {
            "number": result["life_path_number"],
            "meaning": CHALDEAN_MEANINGS.get(result["life_path_number"], "Unknown"),
        }
    
    return result


def _extract_numbers(sign: str) -> list:
    """Extract all numbers from a sign string."""
    import re
    return [int(n) for n in re.findall(r'\d+', str(sign))]


def _chaldean_reduce(numbers: list) -> int:
    """Chaldean reduction (different from Pythagorean — no 9 reduction)."""
    total = sum(numbers)
    while total > 9:
        total = sum(int(d) for d in str(total))
    return total


def _parse_date(date_str: str):
    """Parse YYYY-MM-DD. Returns (year, month, day) or (None, None, None)."""
    try:
        parts = date_str.split("-")
        return int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        return None, None, None


def _parse_time(time_str: str):
    """Parse HH:MM. Returns hour as int or None."""
    try:
        return int(time_str.split(":")[0])
    except (ValueError, IndexError):
        return None


def _get_zodiac(month: int, day: int) -> dict:
    """Get Western zodiac sign for a date."""
    for (sm, sd), (em, ed), name, symbol, meaning in ZODIAC_SIGNS:
        if (month == sm and day >= sd) or (month == em and day <= ed):
            return {"sign": name, "symbol": symbol, "meaning": meaning}
        # Handle Capricorn wrapping
        if sm == 12 and em == 1:
            if (month == 12 and day >= sd) or (month == 1 and day <= ed):
                return {"sign": name, "symbol": symbol, "meaning": meaning}
    return {"sign": "Unknown", "symbol": "?", "meaning": ""}


def _pythagorean_meaning(root: int) -> str:
    """Get Pythagorean meaning for a root number."""
    meanings = {
        1: "Leadership, independence, new beginnings",
        2: "Partnership, balance, diplomacy",
        3: "Creativity, expression, joy",
        4: "Foundation, stability, hard work",
        5: "Change, freedom, adventure",
        6: "Love, responsibility, home",
        7: "Spirituality, analysis, inner wisdom",
        8: "Power, abundance, material mastery",
        9: "Completion, humanitarian, wisdom",
        11: "Master number — illumination, spiritual insight",
        22: "Master number — master builder, great achievement",
        33: "Master number — master teacher, compassion",
    }
    return meanings.get(root, "Unique vibration")


def _check_synchronicity(sign: str, time_str: str) -> dict:
    """Check for angel numbers, mirror numbers, and patterns."""
    result = {"patterns": [], "angel": None, "mirror": None}
    
    # Check angel numbers
    for pattern, meaning in ANGEL_NUMBERS.items():
        if pattern in str(sign).replace(":", "").replace(" ", ""):
            result["angel"] = {"pattern": pattern, "meaning": meaning}
            result["patterns"].append(f"Angel number {pattern}")
            break
    
    # Check mirror time
    if time_str and time_str in MIRROR_NUMBERS:
        result["mirror"] = {"time": time_str, "meaning": MIRROR_NUMBERS[time_str]}
        result["patterns"].append(f"Mirror time {time_str}")
    
    # Check repeating digits
    clean = str(sign).replace(":", "").replace(" ", "").replace("-", "")
    if clean.isdigit() and len(set(clean)) == 1 and len(clean) >= 3:
        result["patterns"].append(f"Repeating {clean[0]}s — amplified energy of {clean[0]}")
    
    # Check palindrome
    if clean == clean[::-1] and len(clean) >= 3:
        result["patterns"].append("Palindrome — what goes around, comes around")
    
    return result


def _generate_interpretation(reading: dict) -> str:
    """Generate a unified interpretation paragraph from all systems."""
    parts = []
    
    # Numerology
    num = reading.get("numerology", {})
    if num.get("is_master"):
        parts.append(f"Master number {num.get('digit_sum')} — this is a powerful gateway sign")
    elif num.get("root"):
        parts.append(f"Root {num['root']}: {num.get('meaning', '')}")
    
    # Synchronicity
    sync = reading.get("synchronicity", {})
    if sync.get("angel"):
        parts.append(f"Angel number: {sync['angel']['meaning']}")
    if sync.get("mirror"):
        parts.append(f"Mirror time: {sync['mirror']['meaning']}")
    
    # Moon phase
    chinese = reading.get("chinese", {})
    if chinese.get("moon_phase"):
        phase = chinese["moon_phase"]
        if "Waning" in phase:
            parts.append("Moon is waning — time to release, let go, trust")
        elif "Waxing" in phase:
            parts.append("Moon is waxing — time to build, grow, attract")
        elif phase == "Full Moon":
            parts.append("Full Moon — culmination, revelation, peak energy")
        elif phase == "New Moon":
            parts.append("New Moon — plant seeds, set intentions, begin")
    
    # Hour animal
    if chinese.get("hour_animal"):
        parts.append(f"{chinese['hour_animal']} hour: {chinese.get('hour_meaning', '')}")
    
    return ". ".join(parts) + "." if parts else "Enter more details for a deeper reading."
```

### Oracle from Telegram

The Oracle can be triggered from Telegram too:

```
/sign 11:11
/sign 444 at 14:30 in Bali
/name Hamzeh 1990-05-15
```

---

## 6. TAB 4: MEMORY — AI LEARNING DASHBOARD

Replaces the Validation tab. Shows what the AI has learned, not just statistics.

### Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  Memory — AI Learning                                                │
│  "What the AI has learned from all scanning and solving."            │
│                                                                      │
│  ┌─ Lifetime Stats ─────────────────────────────────────────────────┐│
│  │  Total keys tested:    50,234,567    Total runtime: 120.5 hours  ││
│  │  Total seeds tested:   1,234,567     Scan sessions: 47           ││
│  │  Online checks:        12,345        Balances found: 0           ││
│  │  Puzzles solved:       10/160        Avg speed: 42,000/s         ││
│  └───────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─ Scoring Effectiveness ──────────────┐  ┌─ Pattern Memory ──────┐│
│  │  Score Gap: +0.305                    │  │  Patterns learned: 47 ││
│  │  (winners avg - losers avg)           │  │  Last update: 2m ago  ││
│  │                                       │  │                       ││
│  │  Pearson: 0.000 (no correlation yet)  │  │  Top patterns:        ││
│  │                                       │  │  • Entropy < 2.1: 63% ││
│  │  Math:  ████████░░ 40%                │  │  • Master nums: 18%   ││
│  │  Numer: ██████░░░░ 30%                │  │  • Palindrome: 12%    ││
│  │  Learn: ██████░░░░ 30%                │  │  • Power of 2: 7%     ││
│  │                                       │  │                       ││
│  │  [Recalculate] [Export CSV]           │  │  [View All Patterns]  ││
│  └───────────────────────────────────────┘  └───────────────────────┘│
│                                                                      │
│  ┌─ Scan Memory Timeline ───────────────────────────────────────────┐│
│  │  Session 47 | Feb 6, 08:30-12:15 | 3.75h | 168,750,000 keys    ││
│  │  Session 46 | Feb 5, 22:00-02:30 | 4.50h | 202,500,000 keys    ││
│  │  Session 45 | Feb 5, 14:00-18:00 | 4.00h | 180,000,000 keys    ││
│  │  ...                                                              ││
│  │  Memory size: 2.1 MB | Patterns: growing | AI confidence: 0.10  ││
│  └───────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─ AI Recommendations ─────────────────────────────────────────────┐│
│  │  Based on 50M+ keys tested, the AI recommends:                   ││
│  │  • Continue "Both" mode — seeds find different address spaces     ││
│  │  • Enable USDT checking — many wallets hold stablecoins only     ││
│  │  • Run overnight headless — consistent uptime builds memory       ││
│  │  • Score Gap is positive — scoring DOES help for puzzles          ││
│  └───────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  [Reset All Memory]  [Export Full Report]                            │
└──────────────────────────────────────────────────────────────────────┘
```

### Implementation

**File:** `gui/memory_tab.py` — NEW (~300 lines)
**File:** `engines/memory.py` — NEW (~350 lines)

---

## 7. TELEGRAM COMMAND CENTER

Telegram is not just for notifications. It becomes a full remote control.

### Bot Commands

| Command | What It Does | Example |
|---------|-------------|---------|
| `/start` | Start both puzzle and scanner | `/start` |
| `/stop` | Stop everything | `/stop` |
| `/status` | Get current status snapshot | `/status` |
| `/sign <text>` | Read a sign via Oracle | `/sign 11:11` |
| `/sign <text> at <time> in <place>` | Full sign reading | `/sign 444 at 14:30 in Bali` |
| `/name <n> <birthday>` | Name numerology reading | `/name Hamzeh 1990-05-15` |
| `/puzzle <id>` | Switch to puzzle N | `/puzzle 71` |
| `/mode <mode>` | Set scanner mode | `/mode both` |
| `/memory` | Get memory summary | `/memory` |
| `/perf` | Get performance stats | `/perf` ← NEW |

### Inline Buttons on Notifications

When a **balance is found**, the Telegram message includes:

```
🚨🚨🚨 BALANCE FOUND! 🚨🚨🚨

Method: random_key
₿ BTC: 1Abc...Xyz → 0.004 BTC
Ξ ETH: 0xabc...xyz → 1.23 ETH
₮ USDT: 500.00

[🔑 Show Key] [📋 Show Seed] [🔗 View Wallet] [✅ Acknowledge]
```

### Implementation

**Modify:** `engines/notifier.py` — Add command handler (~200 lines added)

```python
COMMANDS = {
    "/start": "_cmd_start",
    "/stop": "_cmd_stop",
    "/status": "_cmd_status",
    "/sign": "_cmd_sign",
    "/name": "_cmd_name",
    "/puzzle": "_cmd_puzzle",
    "/mode": "_cmd_mode",
    "/memory": "_cmd_memory",
    "/perf": "_cmd_perf",
    "/help": "_cmd_help",
}

def start_command_listener(app_controller):
    """Start background thread that listens for Telegram commands + button callbacks.
    
    Uses long-polling with 30s timeout. Non-blocking.
    Reconnects automatically on failure with exponential backoff.
    """
```

---

## 8. ADAPTIVE MEMORY SYSTEM

The scanner's secret weapon. Over time, it learns and improves.

### CRITICAL REDESIGN: In-Memory Cache

The old design loaded/saved JSON on every call. This is why the app was slow.

**New design: cache in RAM, flush to disk periodically.**

**File:** `engines/memory.py` — NEW (~350 lines)
**Storage:** `data/scan_memory.json`

```python
"""
Adaptive Memory — The scanner's brain.

ARCHITECTURE:
- Memory lives in RAM (dict) during the session
- Flushed to disk every 60 seconds OR when session ends
- Thread-safe via RLock (reentrant — avoids deadlocks)
- Lazy loading: first access loads from disk, subsequent reads are instant

This avoids the old pattern of load() + save() on every operation,
which was causing disk I/O bottlenecks and GUI freezes.
"""

import json
import time
import logging
from pathlib import Path
from threading import RLock, Timer

logger = logging.getLogger(__name__)

MEMORY_FILE = Path(__file__).parent.parent / "data" / "scan_memory.json"
MAX_MEMORY_MB = 10
FLUSH_INTERVAL_S = 60  # Write to disk every 60 seconds

_lock = RLock()
_cache = None          # In-memory cache (loaded once, modified in RAM)
_dirty = False         # True if cache has unsaved changes
_flush_timer = None    # Background timer for periodic flush


def _ensure_loaded() -> dict:
    """Lazy-load memory into cache on first access."""
    global _cache
    if _cache is None:
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, "r") as f:
                    _cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.warning("Corrupt memory file, starting fresh")
                _cache = _default_memory()
        else:
            _cache = _default_memory()
        _start_flush_timer()
    return _cache


def _start_flush_timer():
    """Start periodic background flush to disk."""
    global _flush_timer
    if _flush_timer is not None:
        _flush_timer.cancel()
    _flush_timer = Timer(FLUSH_INTERVAL_S, _auto_flush)
    _flush_timer.daemon = True
    _flush_timer.start()


def _auto_flush():
    """Called by timer — flushes dirty cache to disk, restarts timer."""
    flush_to_disk()
    _start_flush_timer()


def flush_to_disk():
    """Write cache to disk if dirty. Thread-safe. Call on app exit."""
    global _dirty
    with _lock:
        if not _dirty or _cache is None:
            return
        try:
            _trim_memory(_cache)
            MEMORY_FILE.parent.mkdir(exist_ok=True)
            # Write to temp file first, then rename (atomic on most OS)
            tmp = MEMORY_FILE.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(_cache, f, indent=2)
            tmp.replace(MEMORY_FILE)
            _dirty = False
            logger.debug("Memory flushed to disk")
        except IOError as e:
            logger.error(f"Failed to flush memory: {e}")


def get_memory() -> dict:
    """Get the in-memory cache (read-only view). Fast — no disk I/O."""
    with _lock:
        return _ensure_loaded()


def record_session(session: dict):
    """Record a completed scan session. Fast — RAM only."""
    global _dirty
    with _lock:
        mem = _ensure_loaded()
        mem["sessions"].append(session)
        mem["total_keys_tested"] += session.get("keys_tested", 0)
        mem["total_seeds_tested"] += session.get("seeds_tested", 0)
        mem["total_online_checks"] += session.get("online_checks", 0)
        mem["total_runtime_seconds"] += session.get("end_time", 0) - session.get("start_time", 0)
        mem["total_hits"] += session.get("hits", 0)
        mem["patterns"]["speed_history"].append(session.get("avg_speed", 0))
        mem["updated"] = time.time()
        
        # Keep only last 1000 sessions
        if len(mem["sessions"]) > 1000:
            mem["sessions"] = mem["sessions"][-1000:]
        
        _dirty = True


def record_high_score(key_hex: str, score: float, addresses: dict):
    """Remember exceptionally high-scoring keys. Fast — RAM only."""
    global _dirty
    with _lock:
        mem = _ensure_loaded()
        mem["patterns"]["high_scores"].append({
            "key": key_hex,
            "score": score,
            "btc": addresses.get("btc", ""),
            "eth": addresses.get("eth", ""),
            "timestamp": time.time(),
        })
        mem["patterns"]["high_scores"].sort(key=lambda x: x["score"], reverse=True)
        mem["patterns"]["high_scores"] = mem["patterns"]["high_scores"][:100]
        _dirty = True


def record_score_distribution(score: float):
    """Record a score for distribution analysis. Fast — RAM only, no disk."""
    global _dirty
    with _lock:
        mem = _ensure_loaded()
        bucket = f"{score:.1f}"
        dist = mem["patterns"]["score_distribution"]
        dist[bucket] = dist.get(bucket, 0) + 1
        _dirty = True
        # No disk write here — periodic flush handles it


def get_recommendations() -> list:
    """Generate AI recommendations based on accumulated memory."""
    with _lock:
        mem = _ensure_loaded()
    
    recs = []
    total = mem.get("total_keys_tested", 0)
    sessions = mem.get("sessions", [])
    
    if total == 0:
        return ["Start scanning to build memory. The AI learns from every session."]
    
    # Speed recommendation
    speeds = mem["patterns"].get("speed_history", [])
    if speeds:
        avg = sum(speeds) / len(speeds)
        latest = speeds[-1] if speeds else 0
        if latest < avg * 0.8:
            recs.append(f"Speed dropped to {latest:.0f}/s (avg: {avg:.0f}/s). Check system load.")
    
    # Runtime recommendation
    runtime_hours = mem.get("total_runtime_seconds", 0) / 3600
    if runtime_hours < 24:
        recs.append("Less than 24h total runtime. More scanning = more learning.")
    
    # Mode recommendation
    if sessions:
        modes = [s.get("mode", "unknown") for s in sessions[-10:]]
        if modes.count("both") < 5:
            recs.append("Try 'Both' mode — seeds explore different address spaces than random keys.")
    
    # Score analysis
    high_scores = mem["patterns"].get("high_scores", [])
    if high_scores:
        avg_high = sum(h["score"] for h in high_scores) / len(high_scores)
        recs.append(f"Highest scores average {avg_high:.3f}. Top: {high_scores[0]['score']:.4f}")
    
    return recs if recs else ["Keep scanning. The AI is building its pattern database."]


def get_summary() -> dict:
    """Get memory summary for display. Fast — reads from RAM cache."""
    with _lock:
        mem = _ensure_loaded()
    return {
        "total_keys_tested": mem.get("total_keys_tested", 0),
        "total_seeds_tested": mem.get("total_seeds_tested", 0),
        "total_runtime_hours": mem.get("total_runtime_seconds", 0) / 3600,
        "total_online_checks": mem.get("total_online_checks", 0),
        "total_hits": mem.get("total_hits", 0),
        "session_count": len(mem.get("sessions", [])),
        "patterns_count": len(mem.get("patterns", {}).get("high_scores", [])),
        "memory_size_kb": MEMORY_FILE.stat().st_size / 1024 if MEMORY_FILE.exists() else 0,
        "recommendations": get_recommendations(),
    }


def shutdown():
    """Call on app exit. Flushes cache and stops timer."""
    global _flush_timer
    if _flush_timer:
        _flush_timer.cancel()
    flush_to_disk()


def _default_memory() -> dict:
    return {
        "version": 2,
        "created": time.time(),
        "updated": time.time(),
        "sessions": [],
        "total_keys_tested": 0,
        "total_seeds_tested": 0,
        "total_runtime_seconds": 0,
        "total_online_checks": 0,
        "total_hits": 0,
        "patterns": {
            "score_distribution": {},
            "address_prefixes_checked": {},
            "high_scores": [],
            "api_reliability": {},
            "speed_history": [],
        },
        "recommendations": [],
    }


def _trim_memory(memory: dict):
    """Trim memory to stay under MAX_MEMORY_MB."""
    if len(memory.get("sessions", [])) > 500:
        memory["sessions"] = memory["sessions"][-500:]
    dist = memory.get("patterns", {}).get("score_distribution", {})
    if len(dist) > 50:
        sorted_dist = sorted(dist.items(), key=lambda x: x[1], reverse=True)[:50]
        memory["patterns"]["score_distribution"] = dict(sorted_dist)
    speeds = memory.get("patterns", {}).get("speed_history", [])
    if len(speeds) > 500:
        memory["patterns"]["speed_history"] = speeds[-500:]
```

### How Memory Makes Scanner Smarter

Every 100,000 keys, the scanner asks the AI brain:

```python
# In scanner_solver.py
if tested % 100000 == 0:
    from engines.memory import get_summary, get_recommendations
    from engines.ai_engine import analyze_scan_pattern
    
    summary = get_summary()  # Fast — reads from RAM cache
    recs = get_recommendations()
    
    # AI brain considers accumulated memory (non-blocking)
    insight = analyze_scan_pattern(
        tested_count=tested,
        speed=speed,
        hits=hits,
        memory_summary=summary,
        recommendations=recs,
    )
    
    if insight.get("should_change_mode"):
        self._emit_insight(insight)
```

---

## 9. FILES TO DELETE

| File | Reason |
|------|--------|
| `gui/number_tab.py` | Number Oracle tab deleted |
| `gui/date_tab.py` | Date Decoder tab deleted |
| `gui/validation_tab.py` | Validation merged into Dashboard + Memory |
| `gui/btc_tab.py` | BTC Hunter merged into Hunter |
| `gui/scanner_tab.py` | Scanner merged into Hunter |

**IMPORTANT:** Don't delete the solver engines — `number_solver.py`, `date_solver.py` stay. The Oracle may use their computation functions. Only the GUI tabs are deleted.

---

## 10. FILES TO CREATE

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `gui/hunter_tab.py` | ~700 | Unified puzzle + scanner tab |
| `gui/oracle_tab.py` | ~450 | Sign reader + name cipher tab |
| `gui/memory_tab.py` | ~300 | AI learning dashboard |
| `engines/oracle.py` | ~500 | Multi-system sign reading engine |
| `engines/memory.py` | ~350 | Adaptive memory system with cache |
| `engines/perf.py` | ~150 | Performance monitor + profiling hooks |
| `tests/test_oracle.py` | ~100 | Oracle engine tests |
| `tests/test_memory.py` | ~80 | Memory system tests |
| `tests/test_perf.py` | ~60 | Performance benchmark tests |
| **Total new code** | **~2,690** | |

---

## 11. FILES TO MODIFY

| File | What Changes | Lines Added/Changed |
|------|-------------|-------------------|
| `main.py` | 4 tabs instead of 7, --profile flag, shutdown hook | ~40 changed |
| `gui/dashboard_tab.py` | REWRITE — War Room layout + throttled updates | ~350 (rewrite) |
| `gui/theme.py` | Add currency colors, Oracle theme colors | ~20 added |
| `gui/widgets.py` | Add LiveFeedTable, ThrottledUpdater | ~80 added |
| `engines/notifier.py` | Command handler, Oracle bot, reconnect logic | ~250 added |
| `engines/ai_engine.py` | Non-blocking AI calls, memory integration | ~120 added |
| `engines/learning.py` | Scan session recording, pattern tracking | ~80 added |
| `engines/balance.py` | Batch checking, connection pooling, retry logic | ~100 added |
| `solvers/btc_solver.py` | ETH address derivation on puzzle keys | ~20 added |
| `solvers/scanner_solver.py` | Adaptive memory, session recording, throttled callbacks | ~80 added |
| `config.json` | Oracle + memory + performance settings | ~30 added |
| **Total modifications** | | **~1,170 lines** |

---

## 12. BUILD ORDER

### Phase 0: Profile First (NEW — measure before fixing)

**Before changing anything, measure what's actually slow.**

| Step | What | How | Output |
|------|------|-----|--------|
| 0a | Profile startup time | `python3 -c "import time; t=time.time(); import main; print(f'Startup: {time.time()-t:.2f}s')"` | Baseline startup seconds |
| 0b | Profile key generation speed | Run solver for 30s, record keys/second | Baseline speed |
| 0c | Profile GUI responsiveness | Start app, click between tabs, note lag | Baseline lag |
| 0d | Profile memory I/O | Count `open()` calls during a 1-minute scan | Baseline disk reads/writes |
| 0e | Profile AI calls | Time each Claude CLI call | Baseline AI latency |

**Phase 0 gate:** You have numbers. Write them down. These are what we're improving.

```bash
git add -A && git commit -m "V2 Phase 0: Performance baseline captured"
```

### Phase 1: Foundation (no GUI changes)

| Step | File | What | Verify |
|------|------|------|--------|
| 1 | `engines/oracle.py` | Multi-system sign reading engine | `python3 -c "from engines.oracle import read_sign; r = read_sign('11:11', '2026-02-06', '14:30'); print(r['interpretation'])"` |
| 2 | `engines/memory.py` | Adaptive memory with in-memory cache | `python3 -c "from engines.memory import get_memory, record_session, flush_to_disk; print(get_memory()['version'])"` |
| 3 | `engines/perf.py` | Performance monitor hooks | `python3 -c "from engines.perf import PerfMonitor; p = PerfMonitor(); print('OK')"` |
| 4 | `tests/test_oracle.py` | Oracle tests | `python3 -m unittest tests/test_oracle -v` |
| 5 | `tests/test_memory.py` | Memory tests (including cache behavior) | `python3 -m unittest tests/test_memory -v` |
| 6 | `tests/test_perf.py` | Performance benchmark tests | `python3 -m unittest tests/test_perf -v` |

**Phase 1 gate:** All tests pass (original + V1 + new ≈ 95+)

```bash
git add -A && git commit -m "V2 Phase 1: Oracle + Memory + Perf engines — all tests pass"
```

### Phase 2: Modify existing engines (performance + features)

| Step | File | What | Verify |
|------|------|------|--------|
| 7 | `engines/balance.py` | Batch checking + connection pooling | Test: batch_check returns results for 10 addresses |
| 8 | `engines/notifier.py` | Telegram commands + reconnect + non-blocking | Test: format a sign reading |
| 9 | `engines/ai_engine.py` | Non-blocking AI calls + memory integration | Test: import succeeds, timeout returns None not crash |
| 10 | `engines/learning.py` | Scan session recording (RAM-based) | Test: record_scan_session works |
| 11 | `solvers/btc_solver.py` | ETH bonus derivation + throttled callback | Test: callback includes eth_address |
| 12 | `solvers/scanner_solver.py` | Memory integration + throttled GUI updates | Test: session gets recorded |
| 13 | `config.json` | Oracle + memory + perf config sections | Test: load_config works |

**Phase 2 gate:** All tests still pass, all imports clean.

```bash
git add -A && git commit -m "V2 Phase 2: Engine mods + performance fixes — all tests pass"
```

### Phase 3: GUI overhaul

| Step | File | What | Verify |
|------|------|------|--------|
| 14 | Delete old tabs | Remove btc_tab, number_tab, date_tab, validation_tab, scanner_tab | Files deleted |
| 15 | `gui/theme.py` | Currency colors, Oracle colors | Import succeeds |
| 16 | `gui/widgets.py` | LiveFeedTable, ThrottledUpdater, OracleCard | Import succeeds |
| 17 | `gui/dashboard_tab.py` | REWRITE — War Room + throttled updates | Import succeeds |
| 18 | `gui/hunter_tab.py` | NEW — Unified puzzle + scanner with throttling | Import succeeds |
| 19 | `gui/oracle_tab.py` | NEW — Sign reader | Import succeeds |
| 20 | `gui/memory_tab.py` | NEW — AI learning dashboard | Import succeeds |
| 21 | `main.py` | 4 tabs + shutdown hook + --profile flag | `python3 main.py --help` works |

**Phase 3 gate:** App launches with 4 tabs, no errors.

```bash
git add -A && git commit -m "V2 Phase 3: GUI overhaul — 4 tabs, app launches clean"
```

### Phase 4: Integration + Polish

| Step | What | Verify |
|------|------|--------|
| 22 | Wire Hunter tab to both solvers | Start puzzle + scanner simultaneously |
| 23 | Wire Dashboard to receive throttled data from Hunter | Dashboard shows live activity without lag |
| 24 | Wire Memory tab to memory engine | Memory stats display correctly |
| 25 | Wire Oracle tab to oracle engine | Sign reading works end-to-end |
| 26 | Test Telegram commands | `/sign 11:11` returns reading (mock) |
| 27 | Test headless mode | `python3 main.py --headless` runs |
| 28 | Add shutdown hooks | `memory.shutdown()` called on app exit |

**Phase 4 gate:** Full integration test passes.

```bash
git add -A && git commit -m "V2 Phase 4: Full integration — everything connected"
```

### Phase 5: Performance verification + final

| Step | What | Target |
|------|------|--------|
| 29 | Re-profile startup time | < 3 seconds |
| 30 | Re-profile key speed | Same or better than Phase 0 baseline |
| 31 | Re-profile GUI responsiveness | Tab switch < 100ms, no visible lag |
| 32 | Re-profile disk I/O | Max 1 write per 60 seconds during scanning |
| 33 | Run ALL tests | 100% pass |
| 34 | Launch GUI, verify all 4 tabs | Visual check |
| 35 | Start puzzle + scanner simultaneously | 60s without crash |
| 36 | Test Oracle sign reading | Correct output |
| 37 | Verify Telegram (after Chat ID set) | Commands work |
| 38 | Headless mode runs for 60s without crash | Stable |

```bash
git add -A && git commit -m "V2 complete — all features + performance verified"
```

---

## 13. TEST PLAN

### New Test Files

**`tests/test_oracle.py`** (~100 lines):
```python
class TestOracle(unittest.TestCase):
    def test_read_sign_basic(self):
        """Read '11:11' and verify numerology + synchronicity."""
    
    def test_read_sign_with_date(self):
        """Read with date — verify Chinese calendar included."""
    
    def test_read_sign_with_time(self):
        """Read with time — verify hour animal included."""
    
    def test_angel_numbers(self):
        """Verify all angel numbers return meanings."""
    
    def test_mirror_numbers(self):
        """Verify mirror times return meanings."""
    
    def test_extract_numbers(self):
        """Test number extraction from various sign formats."""
    
    def test_zodiac(self):
        """Verify zodiac signs for known dates."""
    
    def test_chaldean_reduction(self):
        """Verify Chaldean differs from Pythagorean."""
    
    def test_read_name(self):
        """Name reading returns full profile."""
    
    def test_empty_sign(self):
        """Empty sign doesn't crash, returns default."""
```

**`tests/test_memory.py`** (~80 lines):
```python
class TestMemory(unittest.TestCase):
    def test_load_default_memory(self):
        """Fresh memory has correct structure."""
    
    def test_record_session(self):
        """Session is recorded and totals update."""
    
    def test_record_high_score(self):
        """High scores are stored and sorted."""
    
    def test_trim_memory(self):
        """Memory stays under size limit."""
    
    def test_recommendations(self):
        """Recommendations generate without crash."""
    
    def test_thread_safety(self):
        """Concurrent reads/writes don't crash."""
    
    def test_get_summary(self):
        """Summary returns all required fields."""
    
    def test_cache_no_disk_on_read(self):
        """After first load, get_memory() does NOT touch disk."""
    
    def test_flush_on_shutdown(self):
        """shutdown() writes dirty cache to disk."""
```

**`tests/test_perf.py`** (~60 lines):
```python
class TestPerf(unittest.TestCase):
    def test_key_generation_speed(self):
        """Verify key generation exceeds 10,000 keys/second."""
    
    def test_memory_read_latency(self):
        """get_memory() returns in < 1ms after first load."""
    
    def test_gui_update_throttle(self):
        """ThrottledUpdater drops intermediate updates correctly."""
    
    def test_feed_trim(self):
        """LiveFeedTable never exceeds MAX_FEED_ROWS."""
```

### Expected Total Tests After V2

| Source | Count |
|--------|-------|
| Original (Phase 1-4) | 58 |
| V1 additions | ~25 |
| V2 Oracle tests | ~10 |
| V2 Memory tests | ~9 |
| V2 Perf tests | ~4 |
| **Total** | **~106** |

---

## 14. QUALITY CHECKLIST

### Code Quality
- [ ] No dead code (all deleted tabs removed, no orphan imports)
- [ ] No TODO/FIXME/HACK remaining
- [ ] No bare `except:` — all exceptions specific
- [ ] Every function has a docstring
- [ ] Every file has a module docstring
- [ ] No hardcoded colors or fonts in GUI files (all via COLORS/FONTS)
- [ ] No hardcoded file paths (all relative via pathlib)

### Performance
- [ ] Memory system uses in-memory cache (not load/save per call)
- [ ] GUI updates use `self.after(0, ...)` from worker threads
- [ ] GUI updates are throttled (max 10 updates/second for feed, 2/s for stats)
- [ ] LiveFeedTable never exceeds 200 rows
- [ ] AI engine calls are non-blocking (timeout + fallback to last insight)
- [ ] Balance checks use batching where possible
- [ ] `memory.shutdown()` called on app exit
- [ ] No `time.sleep()` on the main GUI thread
- [ ] Startup time < 3 seconds

### Functionality
- [ ] App launches with exactly 4 tabs: Dashboard, Hunter, Oracle, Memory
- [ ] Dashboard shows combined puzzle + scanner stats
- [ ] Hunter: can start puzzle only, scanner only, or both
- [ ] Hunter: live feed shows both 🎯 puzzle and 🔍 scanner entries
- [ ] Hunter: balance found → green row + Telegram alert
- [ ] Oracle: sign reading works with all 7 systems
- [ ] Oracle: name reading works (kept from old Name Cipher)
- [ ] Memory: shows lifetime stats, patterns, recommendations
- [ ] Headless mode starts and runs indefinitely
- [ ] Telegram commands work: /start, /stop, /status, /sign, /name, /perf

### Edge Cases
- [ ] App works with empty memory (first launch)
- [ ] App works with no internet (Telegram + balance offline, rest works)
- [ ] App works without Claude CLI (AI features show "—" gracefully)
- [ ] Scanner stop is clean (no hanging threads)
- [ ] Config auto-creates on first run
- [ ] Memory file doesn't grow past 10 MB
- [ ] Corrupt memory file doesn't crash app (resets to default)
- [ ] Corrupt config file doesn't crash app (resets to default)

### Design
- [ ] Dark luxury theme consistent across all 4 tabs
- [ ] Currency symbols (₿ Ξ ₮) visible in live feed
- [ ] No "Timeout after 20s" visible anywhere
- [ ] AI insight compact (2-3 lines) — never takes up huge space
- [ ] Math disclaimer visible in Scanner section of Hunter
- [ ] Status bar shows correct info at bottom

---

## 15. DESIGN RULES

### The "Swiss Watch" Principle

Every element serves a purpose. No visual clutter. No wasted space.

1. **No purple AI boxes that show "Timeout".** If AI times out, show the LAST insight or "—". Never show error states to the user.

2. **No empty panels.** If there's no data, show a single line: "Start scanning to see activity here." Not a huge empty box.

3. **Compact cards, not sprawling sections.** Stats go in tight 3-column cards. Not one stat per row.

4. **Color means something:**
   - Gold (accent) = action buttons (Start, Analyze, Read Sign)
   - Green = success (balance found, test passed)
   - Blue = information (scanner activity, AI insight)
   - Red = danger/stop only (Stop button, Reset)
   - Dim gray = secondary info (timestamps, labels)

5. **The live feed IS the app.** It should take up the most space. Everything else is secondary.

6. **Currency symbols are always visible:** ₿ `#F7931A` | Ξ `#627EEA` | ₮ `#26A17B` | ◉ `#2775CA`

7. **Font hierarchy:**
   - Tab title: Large, colored (heading)
   - Section headers: Medium, white (subhead)
   - Data: Monospace, regular size (mono)
   - Labels: Small, dim gray (small)
   - Live feed: Monospace small (mono_sm)

8. **Maximum 3 levels of nesting.** Tab → Section → Content. Never deeper.

---

## 16. PERFORMANCE ARCHITECTURE (NEW)

### Why The App Was Slow — Root Causes

| # | Problem | Impact | Fix |
|---|---------|--------|-----|
| 1 | **Memory load/save on every call** | Disk I/O blocks worker threads, causes GUI freeze | In-memory cache + periodic flush (Section 8) |
| 2 | **GUI updates from worker threads** | Tkinter is single-threaded; cross-thread widget access = crash or freeze | `self.after(0, callback)` pattern everywhere |
| 3 | **No throttling on GUI updates** | Every key tested triggers a widget update = thousands/second | ThrottledUpdater class (Section 3) |
| 4 | **Treeview grows unbounded** | 10,000+ rows in live feed = rendering lag | Cap at 200 rows, trim from bottom |
| 5 | **AI calls block the main thread** | Claude CLI timeout = 20s freeze | Non-blocking: run in thread, use last result on timeout |
| 6 | **Balance API calls one-at-a-time** | Each HTTP request = 200-500ms latency | Batch checking: check multiple addresses per API call |
| 7 | **No connection pooling** | Each API call opens a new TCP connection | `requests.Session()` with keep-alive |
| 8 | **rich_addresses.txt loaded repeatedly** | File read on every local check | Load once into a `set()` at startup, keep in RAM |

### Performance Targets

| Metric | Target | How to Verify |
|--------|--------|--------------|
| Startup time | < 3 seconds | `time python3 main.py --help` |
| Tab switch | < 100ms (no visible lag) | Click between tabs, observe |
| Key generation speed | > 20,000/s (puzzle), > 40,000/s (scanner) | Read speed display during scan |
| GUI responsiveness during scan | Smooth scrolling, no freezing | Run scan + scroll live feed |
| Memory read latency | < 1ms after first load | `test_perf.py` benchmark |
| Disk writes during scan | Max 1 per 60 seconds | Monitor with `inotifywait` or log |
| AI insight update | Non-blocking, < 5s attempt, silent fallback | Start scan, observe AI panel |

### Performance Engine

**File:** `engines/perf.py` — NEW (~150 lines)

```python
"""
Performance Monitor — tracks app performance metrics.

Usage:
    from engines.perf import perf
    
    perf.start("key_generation")
    # ... do work ...
    perf.stop("key_generation")
    
    print(perf.summary())  # Shows avg/min/max for all tracked operations
"""

import time
import logging
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class PerfMonitor:
    """Lightweight performance tracker. Thread-safe."""
    
    def __init__(self):
        self._timers = {}        # operation_name → start_time
        self._stats = defaultdict(list)  # operation_name → [durations]
        self._counters = defaultdict(int)  # operation_name → count
        self._lock = Lock()
    
    def start(self, name: str):
        """Start timing an operation."""
        self._timers[name] = time.monotonic()
    
    def stop(self, name: str) -> float:
        """Stop timing and record duration. Returns duration in seconds."""
        if name not in self._timers:
            return 0.0
        duration = time.monotonic() - self._timers.pop(name)
        with self._lock:
            self._stats[name].append(duration)
            # Keep only last 1000 samples per operation
            if len(self._stats[name]) > 1000:
                self._stats[name] = self._stats[name][-1000:]
        return duration
    
    def count(self, name: str, n: int = 1):
        """Increment a counter (e.g., keys tested, API calls)."""
        with self._lock:
            self._counters[name] += n
    
    def summary(self) -> dict:
        """Get performance summary."""
        with self._lock:
            result = {}
            for name, durations in self._stats.items():
                if durations:
                    result[name] = {
                        "avg_ms": sum(durations) / len(durations) * 1000,
                        "min_ms": min(durations) * 1000,
                        "max_ms": max(durations) * 1000,
                        "samples": len(durations),
                    }
            result["counters"] = dict(self._counters)
            return result


# Global instance
perf = PerfMonitor()
```

### Non-Blocking AI Calls

```python
# In engines/ai_engine.py

import subprocess
import threading

_last_insight = "Analyzing patterns..."  # Always have a fallback
_insight_lock = threading.Lock()

def get_ai_insight_async(prompt: str, callback, timeout: int = 5):
    """Run AI call in background thread. Never blocks GUI.
    
    callback(insight: str) is called on main thread via root.after().
    On timeout: callback receives the last successful insight.
    """
    def _worker():
        global _last_insight
        try:
            result = subprocess.run(
                ["claude", "--print", prompt],
                capture_output=True, text=True, timeout=timeout
            )
            if result.returncode == 0 and result.stdout.strip():
                with _insight_lock:
                    _last_insight = result.stdout.strip()
                callback(_last_insight)
            else:
                callback(_last_insight)  # Use cached insight
        except (subprocess.TimeoutExpired, FileNotFoundError):
            callback(_last_insight)  # Use cached insight, no error shown
    
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
```

### Batch Balance Checking

```python
# In engines/balance.py

import requests

_session = None  # Connection pool — reuse TCP connections

def _get_session() -> requests.Session:
    """Get or create a reusable HTTP session with connection pooling."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"User-Agent": "NPS/2.0"})
        # Connection pool: up to 10 connections, 5 per host
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=5, pool_maxsize=10, max_retries=2
        )
        _session.mount("https://", adapter)
        _session.mount("http://", adapter)
    return _session


def batch_check_balances(addresses: list, chains: list = None) -> dict:
    """Check multiple addresses in one API call where possible.
    
    Args:
        addresses: List of {"btc": "1Abc...", "eth": "0xabc..."}
        chains: Which chains to check ["btc", "eth", "usdt"]
    
    Returns:
        dict mapping address → {chain: balance}
    """
    # Group by chain, use batch endpoints where available
    # Falls back to individual checks if batch not supported
    ...
```

### Rich Addresses: Load Once

```python
# In solvers/scanner_solver.py — at module level or __init__

from pathlib import Path

# Load rich addresses ONCE into a set for O(1) lookup
_RICH_FILE = Path(__file__).parent.parent / "data" / "rich_addresses.txt"
_rich_addresses = set()

def _load_rich_addresses():
    """Load rich addresses into memory once. Called at first use."""
    global _rich_addresses
    if not _rich_addresses and _RICH_FILE.exists():
        with open(_RICH_FILE, "r") as f:
            _rich_addresses = {line.strip() for line in f if line.strip()}
    return _rich_addresses
```

---

## 17. CLAUDE CODE CLI EXECUTION PROTOCOL (NEW)

### How Claude Code Should Read and Execute This File

This section tells Claude Code exactly how to work. Not vague "paste this prompt" — specific agent directives.

### Step 1: Open Claude Code

```bash
cd ~/Desktop/BTC && claude
```

### Step 2: Enter Plan Mode and Give This Directive

```
/plan

Read UPDATE_V2.md completely — every section, every code block, every table.
This is a RESTRUCTURING + PERFORMANCE OVERHAUL of the NPS app.

EXECUTION RULES:
1. Read the existing codebase in nps/ first. Map every file.
2. Follow the Build Order (Section 12) exactly — Phase 0 through Phase 5.
3. Each phase has a GATE. Do not proceed to next phase until gate passes.
4. Use Task subagents for parallel work within each phase.
5. Use WebSearch to verify external API endpoints and library docs.
6. Git checkpoint after every phase.
7. After each phase: run ALL tests (not just new ones) and report results.

QUALITY RULES:
- Every function gets a docstring.
- Every file gets a module docstring.
- No bare except:
- No TODO/FIXME left behind.
- All GUI updates from worker threads use self.after(0, ...).
- Memory system uses in-memory cache (Section 8 — read carefully).
- Performance targets (Section 16) must be met.

SHOW ME THE PLAN FIRST — I approve before you code.
```

### Step 3: Review Plan and Approve

Claude Code will generate a detailed implementation plan for all phases. Dave reviews and approves.

### Step 4: Execution with Subagents

Claude Code should use Task subagents for parallel work:

```
Phase 1 (parallel):
  Task 1: Build engines/oracle.py
  Task 2: Build engines/memory.py  
  Task 3: Build engines/perf.py
  Task 4: Build all 3 test files
  
  (Wait for all 4 tasks → run all tests → Phase 1 gate)

Phase 2 (semi-parallel):
  Task 5: Modify engines/balance.py + engines/notifier.py
  Task 6: Modify engines/ai_engine.py + engines/learning.py
  Task 7: Modify solvers/btc_solver.py + scanner_solver.py + config.json
  
  (Wait → run all tests → Phase 2 gate)

Phase 3 (sequential — GUI depends on previous steps):
  Sequential: Delete old tabs → theme → widgets → dashboard → hunter → oracle → memory → main
  
  (Run app → visual check → Phase 3 gate)

Phase 4 (sequential — integration):
  Wire everything together. Test each connection.
  
  (Full integration test → Phase 4 gate)

Phase 5 (verification):
  Re-run Phase 0 benchmarks. Compare. Report.
```

### Step 5: Verification Protocol

After each phase, Claude Code must:

1. Run `python3 -m unittest discover tests/ -v`
2. Report: `X tests passed, Y failed, Z errors`
3. If any fail: FIX before proceeding
4. Git commit with descriptive message
5. Report phase completion to Dave

### ULTRATHINK Directive

For complex decisions during build, Claude Code should use extended thinking:

```
When encountering:
- Threading race conditions → ULTRATHINK before implementing
- Performance optimization trade-offs → ULTRATHINK before choosing
- Integration logic between tabs → ULTRATHINK before wiring
- Any decision that affects multiple files → ULTRATHINK first
```

---

## 18. ERROR RECOVERY & GRACEFUL DEGRADATION (NEW)

### What Happens When Things Break

| Failure | Behavior | User Sees |
|---------|----------|-----------|
| **Claude CLI not installed** | AI features disabled, app still works | AI Brain card shows "—" |
| **Claude CLI timeout** | Use last cached insight, retry in background | Previous insight stays visible |
| **No internet** | Telegram + balance checking disabled, local scanning continues | Comms card shows "⚠ Offline" |
| **Telegram API error** | Exponential backoff (1s, 2s, 4s, 8s... max 5min), auto-reconnect | TG status shows "Reconnecting..." |
| **Corrupt scan_memory.json** | Reset to default memory, log warning | Memory tab shows "Fresh start" |
| **Corrupt config.json** | Reset to default config, log warning | App starts with defaults |
| **Thread crash in solver** | Catch exception, log, stop that solver, other solver continues | Activity log shows error, app stays up |
| **Disk full** | Memory flush fails, continue in RAM, log warning | Warning in activity log |
| **rich_addresses.txt missing** | Local checking disabled, online checking still works | Scanner runs in online-only mode |

### Shutdown Hook

```python
# In main.py

import atexit
import signal
from engines.memory import shutdown as memory_shutdown

def _cleanup():
    """Called on app exit — flush memory, stop threads."""
    memory_shutdown()      # Flush cache to disk
    # Stop any running solvers
    # Close Telegram listener
    # Close HTTP session

atexit.register(_cleanup)
signal.signal(signal.SIGTERM, lambda s, f: _cleanup())
signal.signal(signal.SIGINT, lambda s, f: _cleanup())
```

### Startup Validation

```python
# In main.py — run before GUI starts

def validate_environment():
    """Check that everything is in place. Fix what's fixable, warn about the rest."""
    issues = []
    
    # Check data directory
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Check config
    config_file = Path(__file__).parent / "config.json"
    if not config_file.exists():
        _create_default_config(config_file)
    
    # Check Claude CLI (optional)
    try:
        subprocess.run(["claude", "--version"], capture_output=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        issues.append("Claude CLI not found — AI features will show '—'")
    
    # Check rich addresses
    rich_file = data_dir / "rich_addresses.txt"
    if not rich_file.exists():
        issues.append("rich_addresses.txt missing — local scanning disabled")
    
    return issues
```

---

## ESTIMATED TOTALS AFTER V2

| Metric | After V1 | After V2 |
|--------|----------|----------|
| Total lines | ~10,880 | ~12,500 |
| Tabs | 7 | 4 |
| Test count | ~83 | ~106 |
| New features | Config, Telegram, Balance, Scanner, Headless | Oracle, Memory, Unified Hunter, Telegram Commands, Perf Monitor |
| Chains | BTC + ETH + 8 tokens | Same |
| Memory | None | Adaptive memory with in-memory cache |
| Performance | Unoptimized | Profiled, throttled, cached, benchmarked |

---

## HOW TO USE THIS FILE

1. Place `UPDATE_V2.md` in `~/Desktop/BTC/` alongside `BLUEPRINT.md` and `UPDATE_V1.md`
2. Open Claude Code: `cd ~/Desktop/BTC && claude`
3. Enter plan mode: `/plan`
4. Paste the directive from **Section 17, Step 2**
5. Review the plan, approve, let it build.
6. Follow the phase gates — each must pass before next begins.

---

*End of UPDATE V2 FINAL. This restructures a 7-tab app into a focused 4-tab machine with performance optimization and proper Claude Code CLI integration.*
*Dashboard (War Room) + Hunter (Puzzle + Scanner) + Oracle (Sign Reader) + Memory (AI Learning)*
*Performance: cached memory, throttled GUI, non-blocking AI, batch APIs, connection pooling*
*Claude Code: Task subagents, ULTRATHINK, phase gates, verification protocol*
