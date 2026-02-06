# NPS — Numerology Puzzle Solver: Complete Blueprint

> **Purpose of this document:** This is the ONLY instruction file needed. A coding AI (Claude Code in plan mode) reads this file and builds the entire application from scratch. Every file, every function, every formula, every UI element is specified here. Nothing is left to guesswork.

> **V1 Source:** The existing codebase (3 Python files, 2,524 lines) is included in this project folder under `v1_source/`. The new app reuses all engine logic from V1 but restructures it into a proper modular architecture.

---

## TABLE OF CONTENTS

1. [Product Overview](#1-product-overview)
2. [Architecture](#2-architecture)
3. [File Tree](#3-file-tree)
4. [Engine Layer — Detailed Specifications](#4-engine-layer)
5. [Scoring Engine — The Core Innovation](#5-scoring-engine)
6. [Learning Engine — Gets Smarter Over Time](#6-learning-engine)
7. [Puzzle Solvers — All 4 Types](#7-puzzle-solvers)
8. [Data Storage — JSON File Database](#8-data-storage)
9. [GUI Layer — Tkinter Desktop App](#9-gui-layer)
10. [Testing Strategy](#10-testing-strategy)
11. [Build & Run Instructions](#11-build-and-run)
12. [Validation Dashboard](#12-validation-dashboard)
13. [Constants & Reference Tables](#13-constants-and-reference-tables)
14. [Edge Cases & Error Handling](#14-edge-cases)
15. [Quality Checklist](#15-quality-checklist)

---

## 1. PRODUCT OVERVIEW

### What Is This App?

A desktop puzzle-solving application (Python + Tkinter) that combines **four puzzle-solving engines** with a **numerology scoring system** (FC60 + Pythagorean + Chinese Calendar + Lunar). The numerology layer scores and ranks puzzle candidates so the solver tries the most "symbolically interesting" candidates first, instead of random brute force.

### Who Is It For?

- People interested in numerology who want to see patterns in numbers, dates, and names
- Bitcoin puzzle enthusiasts who want a smarter exploration tool
- Anyone who finds number patterns fascinating

### Core Principle

```
Input (number/date/name/puzzle)
  → FC60 Translation (convert to 60-token symbolic language)
  → Math Analysis (entropy, primes, digit patterns)
  → Numerology Scoring (harmony score 0.0 to 1.0)
  → Ranked Results (best candidates first)
  → Verification (does this candidate solve the puzzle?)
  → Learning (store what worked, adjust weights for next time)
```

### Important Honesty Rule

The app NEVER claims numerology "magically solves" puzzles. The UI always shows:
- The numerology score AND the math score separately
- A validation dashboard showing whether scored candidates actually perform better than random
- Clear labels: "Exploration Tool" not "Magic Solver"

### Tech Constraints

- **Python 3.8+ only** — zero pip dependencies (standard library only)
- **Tkinter** for GUI — included with Python by default
- **JSON files** for data storage — no database needed
- **Single command launch:** `python main.py`
- **All engines from V1 are reused** — do NOT rewrite the secp256k1 math or FC60 encoding. Import and wrap them.

---

## 2. ARCHITECTURE

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    GUI LAYER (Tkinter)                       │
│  main.py → builds window with 6 tabs                        │
│  ┌─────────┬──────────┬──────────┬──────────┬─────────────┐ │
│  │Dashboard│BTC Hunter│Number    │Name      │Date         │ │
│  │  Tab    │  Tab     │Oracle Tab│Cipher Tab│Decoder Tab  │ │
│  │         │          │          │          │             │ │
│  │Stats,   │Puzzle    │Sequence  │Name+DOB  │Date input   │ │
│  │history, │selector, │input,    │input,    │multi-date,  │ │
│  │learning │progress, │pattern   │full      │pattern      │ │
│  │charts,  │FC60      │display,  │reading,  │detection,   │ │
│  │validate │overlay   │prediction│FC60 map  │prediction   │ │
│  └────┬────┴────┬─────┴────┬─────┴────┬─────┴──────┬──────┘ │
│       │         │          │          │            │         │
│  ┌────┴─────────┴──────────┴──────────┴────────────┴──────┐ │
│  │              VALIDATION DASHBOARD TAB                   │ │
│  │  Score-to-solve correlation, factor accuracy,           │ │
│  │  hit rate, comparison charts                            │ │
│  └────────────────────────┬───────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                    SOLVER LAYER                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ BTC Solver    │ │ Number Solver│ │ Name/Date Solver     │ │
│  │ (Kangaroo +   │ │ (Pattern     │ │ (Pythagorean +       │ │
│  │  Brute Force) │ │  detection)  │ │  Calendar analysis)  │ │
│  └──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘ │
│         │                │                     │             │
│  ┌──────┴────────────────┴─────────────────────┴───────────┐ │
│  │              SCORING ENGINE (hybrid_score)               │ │
│  │  math_score (40%) + numerology_score (30%)               │ │
│  │  + learned_score (30%, grows over time)                  │ │
│  └──────────────────────┬──────────────────────────────────┘ │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                    ENGINE LAYER                              │
│  ┌────────────┐ ┌───────────────┐ ┌───────────────────────┐ │
│  │ fc60.py    │ │ numerology.py │ │ crypto.py             │ │
│  │ (from V1   │ │ (from V1      │ │ (from V1 engine.py)   │ │
│  │ fc60_engine│ │  fc60_engine) │ │                       │ │
│  │ .py)       │ │               │ │                       │ │
│  └────────────┘ └───────────────┘ └───────────────────────┘ │
│  ┌────────────┐ ┌───────────────┐                           │
│  │ math_anal  │ │ learning.py   │                           │
│  │ ysis.py    │ │ (NEW: pattern │                           │
│  │ (NEW:      │ │  memory +     │                           │
│  │  entropy,  │ │  weight       │                           │
│  │  primes)   │ │  adjustment)  │                           │
│  └────────────┘ └───────────────┘                           │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                    DATA LAYER                                │
│  data/                                                       │
│  ├── solve_history.json    (every solved puzzle + scores)    │
│  ├── factor_weights.json   (learned scoring weights)         │
│  └── session_log.json      (current session data)            │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow (How a Puzzle Gets Solved)

```
Step 1: User picks puzzle type + enters input
Step 2: Solver generates candidate list (or receives candidates)
Step 3: For EACH candidate:
        a) FC60 engine translates candidate → tokens (animal + element)
        b) Math analysis calculates entropy, prime factors, digit frequency
        c) Numerology engine calculates life path, element balance, moon alignment
        d) Scoring engine combines all factors → harmony_score (0.0 to 1.0)
Step 4: Sort candidates by harmony_score (highest first)
Step 5: Solver verifies candidates in scored order
Step 6: If solved → store result in solve_history.json
Step 7: Learning engine recalculates factor weights based on accumulated history
Step 8: Dashboard updates correlation charts
```

---

## 3. FILE TREE

```
nps/
├── main.py                    # Entry point. Builds Tkinter window + 6 tabs. Run this.
│
├── v1_source/                 # ORIGINAL V1 files (read-only reference, do NOT modify)
│   ├── fc60_engine.py         # 915 lines — FC60 encoding, numerology, moon, ganzhi
│   ├── engine.py              # 700 lines — secp256k1, Bitcoin, Kangaroo, Brute-force
│   └── main.py                # 909 lines — V1 GUI (reference only, not used)
│
├── engines/                   # Core computation modules
│   ├── __init__.py            # Exports all public functions
│   ├── fc60.py                # FC60 encoding/decoding (extracted from v1 fc60_engine.py)
│   ├── numerology.py          # Pythagorean numerology (extracted from v1 fc60_engine.py)
│   ├── crypto.py              # secp256k1 + Bitcoin (copy of v1 engine.py, unchanged)
│   ├── math_analysis.py       # NEW: entropy, prime factorization, digit analysis
│   ├── scoring.py             # NEW: hybrid scoring engine (math + numerology + learned)
│   └── learning.py            # NEW: pattern memory + weight adjustment
│
├── solvers/                   # Puzzle-specific solver logic
│   ├── __init__.py
│   ├── base_solver.py         # Abstract base class all solvers implement
│   ├── btc_solver.py          # BTC Puzzle Hunter (wraps Kangaroo + BruteForce from crypto.py)
│   ├── number_solver.py       # Number Oracle (sequence pattern detection)
│   ├── name_solver.py         # Name Cipher (name + DOB analysis)
│   └── date_solver.py         # Date Decoder (date pattern analysis + prediction)
│
├── gui/                       # Tkinter GUI components
│   ├── __init__.py
│   ├── theme.py               # Color palette, fonts, shared styles
│   ├── dashboard_tab.py       # Dashboard: stats, recent solves, current moment reading
│   ├── btc_tab.py             # BTC Hunter tab (adapted from V1 PuzzleHunterTab)
│   ├── number_tab.py          # Number Oracle tab
│   ├── name_tab.py            # Name Cipher tab
│   ├── date_tab.py            # Date Decoder tab
│   ├── validation_tab.py      # Validation Dashboard tab
│   └── widgets.py             # Reusable widgets: ScoreBar, TokenDisplay, AnimatedProgress
│
├── data/                      # JSON file storage (created at first run)
│   ├── solve_history.json     # Log of every solved puzzle
│   ├── factor_weights.json    # Current learned weights for scoring
│   └── session_log.json       # Current session temporary data
│
├── tests/                     # Test suite
│   ├── test_fc60.py           # FC60 round-trip + test vectors (29 from V1 + new)
│   ├── test_numerology.py     # Pythagorean calculations
│   ├── test_math_analysis.py  # Entropy, primes
│   ├── test_scoring.py        # Scoring engine output ranges + edge cases
│   ├── test_solvers.py        # Each solver finds known answers
│   └── test_learning.py       # Weight adjustment behavior
│
├── BLUEPRINT.md               # THIS FILE
└── README.md                  # User-facing quick start + feature overview
```

### File Creation Rules

1. **engines/fc60.py** — Copy ALL functions and ALL constants from `v1_source/fc60_engine.py` EXCEPT the numerology functions. Keep: token60, digit60, to_base60, from_base60, encode_base60, decode_base60, compute_jdn, jdn_to_gregorian, weekday_from_jdn, weekday_token, encode_tz, moon_phase, moon_illumination, ganzhi_year, ganzhi_year_tokens, ganzhi_year_name, ganzhi_day, ganzhi_hour, weighted_check, weighted_check_date_only, encode_fc60, format_full_output, format_compact_output, generate_symbolic_reading, parse_input, self_test. Keep ALL constant tables (ANIMALS, ELEMENTS, WEEKDAYS, STEMS, MOON_PHASES, etc. — every single one).

2. **engines/numerology.py** — Extract from `v1_source/fc60_engine.py`: LETTER_VALUES, VOWELS, LIFE_PATH_MEANINGS, numerology_reduce, name_to_number, name_soul_urge, name_personality, life_path, personal_year, generate_personal_reading. Add the new functions specified in section 4.

3. **engines/crypto.py** — Copy `v1_source/engine.py` entirely. Do NOT modify any cryptographic functions. They are tested and correct.

4. **engines/math_analysis.py** — Brand new file. Specified fully in section 4.

5. **engines/scoring.py** — Brand new file. Specified fully in section 5.

6. **engines/learning.py** — Brand new file. Specified fully in section 6.

---

## 4. ENGINE LAYER — DETAILED SPECIFICATIONS

### 4.1 engines/fc60.py

Source: `v1_source/fc60_engine.py` (lines 1–600 approximately, everything EXCEPT numerology functions and generate_personal_reading).

**Keep everything as-is.** The FC60 math is tested against 29 test vectors and is correct. Do NOT "improve" or refactor the arithmetic — only organize it into this file.

**Public API (functions other modules will call):**

```python
# Encoding/decoding
token60(n: int) -> str                    # int 0-59 → 4-char token like "RAWU"
digit60(tok: str) -> int                  # 4-char token → int 0-59
encode_base60(n: int) -> str              # any int → hyphen-separated tokens
decode_base60(s: str) -> int              # tokens → int

# Calendar
compute_jdn(y, m, d) -> int              # Gregorian → Julian Day Number
jdn_to_gregorian(jdn) -> (y, m, d)       # JDN → Gregorian
weekday_from_jdn(jdn) -> int             # 0=Sunday ... 6=Saturday
weekday_token(jdn) -> str                # JDN → "SO","LU","MA",...

# Moon
moon_phase(jdn) -> (phase_idx, age)      # phase 0-7 + age in days
moon_illumination(age) -> float          # percentage 0-100

# Chinese calendar
ganzhi_year(year) -> (stem_idx, branch_idx)
ganzhi_year_tokens(year) -> (stem_tok, branch_tok)
ganzhi_year_name(year) -> str            # "丙午 Fire Horse"
ganzhi_day(jdn) -> (stem_idx, branch_idx)
ganzhi_hour(hour, day_stem) -> (stem_idx, branch_idx)

# Full encoding
encode_fc60(year, month, day, hour=0, minute=0, second=0,
            tz_hours=0, tz_minutes=0, include_time=True) -> dict

# Formatting
format_full_output(result: dict) -> str
format_compact_output(result: dict) -> str

# Symbolic
generate_symbolic_reading(year, month, day, hour=0, minute=0, second=0) -> str

# Parser
parse_input(text: str, tz_hours=0, tz_minutes=0) -> dict

# Self-test
self_test() -> list[tuple[str, bool, str]]
```

**All constant tables to include (copy exactly from V1):**
ANIMALS, ELEMENTS, WEEKDAYS, STEMS, MOON_PHASES, SYNODIC_MONTH, MOON_REF_JDN,
ANIMAL_NAMES, ANIMAL_CHINESE, ANIMAL_POWER, ANIMAL_ESSENCE,
ELEMENT_NAMES, ELEMENT_CHINESE, ELEMENT_FORCE, ELEMENT_MEANING,
WEEKDAY_NAMES, WEEKDAY_PLANETS, WEEKDAY_DOMAINS,
STEM_NAMES, STEM_CHINESE, STEM_ELEMENTS, STEM_POLARITY,
MOON_PHASE_NAMES, MOON_PHASE_MEANINGS, MOON_PHASE_ENERGY, MOON_PHASE_BEST_FOR,
MOON_BOUNDARIES, MONTH_NAMES, TIME_CONTEXT

### 4.2 engines/numerology.py

Source: extracted from `v1_source/fc60_engine.py` + new functions.

**From V1 (copy exactly):**

```python
LETTER_VALUES: dict           # A=1, B=2 ... Z=8
VOWELS: set                   # {'A','E','I','O','U'}
LIFE_PATH_MEANINGS: dict      # {1: ("The Pioneer", "Lead, start, go first"), ...}

numerology_reduce(n: int) -> int           # Reduce to single digit, keep 11/22/33
name_to_number(name: str) -> int           # Full name → expression number
name_soul_urge(name: str) -> int           # Vowels only → soul urge
name_personality(name: str) -> int         # Consonants only → personality number
life_path(year, month, day) -> int         # DOB → life path number
personal_year(birth_month, birth_day, current_year) -> int
generate_personal_reading(name, birth_year, birth_month, birth_day,
                          current_year, current_month, current_day,
                          current_hour=0, current_minute=0,
                          mother_name=None) -> str
```

**NEW functions to add:**

```python
def digit_sum(n: int) -> int:
    """Sum all digits of n. Example: 347 → 3+4+7 = 14."""
    return sum(int(d) for d in str(abs(n)))


def digit_sum_reduced(n: int) -> int:
    """digit_sum but reduced via numerology_reduce. 347 → 14 → 5."""
    return numerology_reduce(digit_sum(n))


def is_master_number(n: int) -> bool:
    """True if n reduces to 11, 22, or 33 at any stage."""
    total = digit_sum(n)
    while total > 9:
        if total in (11, 22, 33):
            return True
        total = sum(int(d) for d in str(total))
    return total in (11, 22, 33)


def number_vibration(n: int) -> dict:
    """
    Complete numerological profile of any integer.
    Returns: {
        'digit_sum': int,
        'reduced': int,
        'is_master': bool,
        'life_path_meaning': tuple(str, str) or None,
        'fc60_token': str,           # token60(n % 60)
        'fc60_animal': str,          # animal name
        'fc60_element': str,         # element name
        'fc60_animal_power': str,    # animal power keyword
        'fc60_element_force': str,   # element force keyword
    }
    """
    # Import from fc60 module for token data
    # Use the constant tables to look up animal/element at index (n%60)//5 and (n%60)%5


def compatibility_score(num_a: int, num_b: int) -> float:
    """
    How compatible are two numbers in numerological terms.
    0.0 = opposite, 1.0 = perfect match.
    
    Rules:
    - Same reduced number → 1.0
    - Numbers that sum to 9 → 0.8 (completion pair)
    - Master number + its base (11→2, 22→4, 33→6) → 0.9
    - Same FC60 animal → +0.2 bonus
    - Same FC60 element → +0.1 bonus
    - Otherwise → base 0.3 + adjustments
    """
```

### 4.3 engines/math_analysis.py (ENTIRELY NEW)

This module provides the "real math" layer that works alongside numerology.

```python
"""
Math Analysis Engine
====================
Provides mathematical analysis of numbers independent of numerology.
These functions detect REAL patterns: entropy, prime structure, digit distribution.
Combined with numerology scoring, they create the hybrid scoring system.

Zero external dependencies — pure Python stdlib.
"""

import math
from collections import Counter


def entropy(n: int) -> float:
    """
    Shannon entropy of the digit sequence of n.
    Measures how "random" or "patterned" a number is.
    
    Low entropy (< 1.5) = very patterned (like 111111, 123123)
    Medium entropy (1.5–2.5) = somewhat structured
    High entropy (> 2.5) = appears random
    
    Returns: float (0.0 to ~3.32 for base-10 digits)
    
    Examples:
        entropy(111111) → 0.0 (all same digit)
        entropy(123456) → 2.585 (all different digits)
        entropy(112233) → 1.585 (three pairs)
    """
    digits = str(abs(n))
    if len(digits) <= 1:
        return 0.0
    counts = Counter(digits)
    total = len(digits)
    return -sum((c/total) * math.log2(c/total) for c in counts.values())


def digit_frequency(n: int) -> dict:
    """
    Count how often each digit (0-9) appears in n.
    Returns: {'0': count, '1': count, ..., '9': count}
    
    Example: digit_frequency(112233) → {'1':2, '2':2, '3':2, '0':0, ...}
    """
    digits = str(abs(n))
    freq = {str(i): 0 for i in range(10)}
    for d in digits:
        freq[d] += 1
    return freq


def digit_balance(n: int) -> float:
    """
    How evenly distributed are the digits?
    1.0 = perfectly balanced (each digit appears same number of times)
    0.0 = maximally imbalanced (all digits the same)
    
    Uses coefficient of variation of digit frequencies.
    """
    freq = digit_frequency(n)
    present = [v for v in freq.values() if v > 0]
    if len(present) <= 1:
        return 0.0
    mean = sum(present) / len(present)
    variance = sum((x - mean) ** 2 for x in present) / len(present)
    std = math.sqrt(variance)
    if mean == 0:
        return 0.0
    cv = std / mean  # coefficient of variation
    # Normalize: cv=0 → balance=1.0, cv≥2 → balance=0.0
    return max(0.0, 1.0 - cv / 2.0)


def prime_factors(n: int) -> list:
    """
    Return list of prime factors (with repetition).
    Example: prime_factors(60) → [2, 2, 3, 5]
    
    Note: For very large numbers (>10^12), this may be slow.
    Returns empty list for n <= 1.
    """
    if n <= 1:
        return []
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def is_prime(n: int) -> bool:
    """Simple primality test. Works well for n < 10^12."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def modular_properties(n: int) -> dict:
    """
    Properties of n relative to base-60 (the FC60 base).
    
    Returns: {
        'mod60': int,           # n % 60
        'mod12': int,           # n % 12 (animal cycle)
        'mod5': int,            # n % 5 (element cycle)
        'mod10': int,           # n % 10 (stem cycle)
        'divides_60': bool,     # n is a factor of 60
        'divisible_by_60': bool,# 60 divides n evenly
        'gcd_with_60': int,     # greatest common divisor with 60
    }
    """
    return {
        'mod60': n % 60,
        'mod12': n % 12,
        'mod5': n % 5,
        'mod10': n % 10,
        'divides_60': (60 % n == 0) if n > 0 else False,
        'divisible_by_60': (n % 60 == 0) if n > 0 else False,
        'gcd_with_60': math.gcd(abs(n), 60),
    }


def repeating_patterns(n: int) -> list:
    """
    Detect repeating digit patterns in n.
    Returns list of (pattern, count) tuples.
    
    Example: repeating_patterns(123123123) → [('123', 3)]
    Example: repeating_patterns(1111) → [('1', 4), ('11', 2)]
    """
    s = str(abs(n))
    patterns = []
    for length in range(1, len(s) // 2 + 1):
        pattern = s[:length]
        count = 0
        for i in range(0, len(s), length):
            if s[i:i+length] == pattern:
                count += 1
            else:
                break
        if count >= 2 and count * length == len(s):
            patterns.append((pattern, count))
    return patterns


def palindrome_score(n: int) -> float:
    """
    How close to a palindrome is n?
    1.0 = perfect palindrome (12321)
    0.0 = no palindromic similarity
    
    Compares digits from outside in, scoring matches.
    """
    s = str(abs(n))
    if len(s) <= 1:
        return 1.0
    matches = 0
    total = len(s) // 2
    for i in range(total):
        if s[i] == s[-(i+1)]:
            matches += 1
    return matches / total if total > 0 else 1.0


def math_profile(n: int) -> dict:
    """
    Complete mathematical profile of any integer.
    This is the math equivalent of number_vibration() in numerology.
    
    Returns dict with ALL math analysis results combined.
    """
    return {
        'value': n,
        'num_digits': len(str(abs(n))),
        'entropy': entropy(n),
        'digit_balance': digit_balance(n),
        'digit_frequency': digit_frequency(n),
        'is_prime': is_prime(n) if n < 10**12 else None,
        'prime_factors': prime_factors(n) if n < 10**9 else [],
        'modular': modular_properties(n),
        'repeating_patterns': repeating_patterns(n),
        'palindrome_score': palindrome_score(n),
        'is_even': n % 2 == 0,
        'is_power_of_2': (n > 0) and (n & (n - 1) == 0),
    }
```

### 4.4 engines/crypto.py

**Copy `v1_source/engine.py` in its entirety.** Do not modify a single line. The secp256k1 math, Bitcoin address utilities, KangarooSolver, BruteForceSolver, PUZZLES dictionary, and self-test functions are all tested and correct.

The only change: add this import at the top of files that use it:
```python
from engines.crypto import (
    PUZZLES, ECPoint, G, scalar_multiply, decompress_pubkey,
    pubkey_to_address, privkey_to_address, privkey_to_wif,
    KangarooSolver, BruteForceSolver,
    self_test_kangaroo, self_test_bruteforce,
    get_performance_estimate,
)
```

---

## 5. SCORING ENGINE — THE CORE INNOVATION

File: `engines/scoring.py`

This is the most important new piece. It takes ANY number and produces a harmony score from 0.0 to 1.0 by combining three sub-scores.

### 5.1 Architecture

```
                     candidate number
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ MATH     │  │NUMEROLOGY│  │ LEARNED  │
        │ SCORE    │  │ SCORE    │  │ SCORE    │
        │          │  │          │  │          │
        │ entropy  │  │ life_path│  │ "numbers │
        │ digit_bal│  │ fc60_tok │  │  like    │
        │ primes   │  │ master # │  │  this    │
        │ mod60    │  │ element  │  │  solved  │
        │ palindr. │  │ moon     │  │  23% of  │
        │ patterns │  │ ganzhi   │  │  the     │
        │          │  │ repeats  │  │  time"   │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │             │
             │  weight     │  weight     │  weight
             │  (default   │  (default   │  (default
             │   0.40)     │   0.30)     │   0.30)
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                    HYBRID SCORE
                   (0.0 to 1.0)
```

### 5.2 Full Specification

```python
"""
Scoring Engine
==============
Combines math analysis, numerology, and learned patterns
into a single harmony score for any candidate number.

The scoring engine is the BRIDGE between numerology and puzzle solving.
It doesn't claim numerology "works" — it provides a scoring framework
that CAN be validated against real results.
"""

from engines import fc60, numerology, math_analysis, learning


# ── Default weights (overridden by learning engine) ──
DEFAULT_WEIGHTS = {
    'math_weight': 0.40,
    'numerology_weight': 0.30,
    'learned_weight': 0.30,
}

# ── Sub-factor weights within math score ──
MATH_FACTORS = {
    'entropy_low': 0.20,        # Low entropy = more patterned = interesting
    'digit_balance': 0.15,      # Balanced digits
    'is_prime': 0.10,           # Prime numbers
    'palindrome': 0.15,         # Palindromic structure
    'repeating': 0.15,          # Repeating digit patterns
    'mod60_clean': 0.15,        # Clean relationship with 60
    'power_of_2': 0.10,         # Powers of 2 (relevant for BTC puzzles)
}

# ── Sub-factor weights within numerology score ──
NUMEROLOGY_FACTORS = {
    'master_number': 0.25,      # Reduces to 11, 22, or 33
    'animal_repetition': 0.20,  # Same FC60 animal appears in multiple components
    'element_balance': 0.15,    # All 5 elements present across components
    'life_path_power': 0.15,    # Life path is 1, 8, or 9 (power numbers)
    'moon_alignment': 0.10,     # Current moon phase is favorable
    'ganzhi_match': 0.10,       # Chinese calendar year compatibility
    'sacred_geometry': 0.05,    # Fibonacci, golden ratio proximity
}


def math_score(n: int) -> tuple[float, dict]:
    """
    Calculate math sub-score for a candidate number.
    
    Args:
        n: The candidate number
        
    Returns:
        (score: float 0.0-1.0, breakdown: dict of factor→value)
    """
    profile = math_analysis.math_profile(n)
    breakdown = {}
    
    # Entropy: lower = more patterned = higher score
    # Normalize: entropy 0→1.0, entropy 3.3→0.0
    max_entropy = 3.32  # log2(10) for base-10 digits
    ent = profile['entropy']
    breakdown['entropy_low'] = max(0, 1.0 - ent / max_entropy)
    
    # Digit balance
    breakdown['digit_balance'] = profile['digit_balance']
    
    # Prime
    breakdown['is_prime'] = 1.0 if profile.get('is_prime') else 0.0
    
    # Palindrome
    breakdown['palindrome'] = profile['palindrome_score']
    
    # Repeating patterns
    patterns = profile['repeating_patterns']
    breakdown['repeating'] = min(1.0, len(patterns) * 0.5) if patterns else 0.0
    
    # Mod60 cleanliness: high GCD with 60 = cleaner FC60 representation
    gcd = profile['modular']['gcd_with_60']
    breakdown['mod60_clean'] = gcd / 60.0
    
    # Power of 2
    breakdown['power_of_2'] = 1.0 if profile['is_power_of_2'] else 0.0
    
    # Weighted sum
    score = sum(MATH_FACTORS[k] * breakdown[k] for k in MATH_FACTORS)
    
    return score, breakdown


def numerology_score(n: int, context: dict = None) -> tuple[float, dict]:
    """
    Calculate numerology sub-score for a candidate number.
    
    Args:
        n: The candidate number
        context: Optional dict with:
            'current_year', 'current_month', 'current_day',
            'current_hour', 'target_life_path', 'target_animal'
            
    Returns:
        (score: float 0.0-1.0, breakdown: dict of factor→value)
    """
    context = context or {}
    breakdown = {}
    
    # Master number check
    breakdown['master_number'] = 1.0 if numerology.is_master_number(n) else 0.0
    
    # FC60 token analysis
    token = fc60.token60(n % 60)
    animal_idx = (n % 60) // 5
    element_idx = (n % 60) % 5
    
    # Animal repetition: check if encoding n in base-60 repeats same animal
    base60_digits = fc60.to_base60(n) if n > 0 else [0]
    animal_tokens = [fc60.ANIMALS[(d) // 5] for d in base60_digits]
    from collections import Counter
    animal_counts = Counter(animal_tokens)
    max_repeat = max(animal_counts.values()) if animal_counts else 1
    total_digits = len(base60_digits)
    breakdown['animal_repetition'] = (max_repeat / total_digits) if total_digits > 1 else 0.0
    
    # Element balance: how many of the 5 elements appear in base-60 encoding
    element_tokens = [fc60.ELEMENTS[(d) % 5] for d in base60_digits]
    unique_elements = len(set(element_tokens))
    breakdown['element_balance'] = unique_elements / 5.0
    
    # Life path power (1, 8, 9 are "power" numbers in Pythagorean system)
    reduced = numerology.numerology_reduce(numerology.digit_sum(n) if hasattr(numerology, 'digit_sum') else sum(int(d) for d in str(abs(n))))
    power_numbers = {1, 8, 9, 11, 22, 33}
    breakdown['life_path_power'] = 1.0 if reduced in power_numbers else 0.3
    
    # Moon alignment (if current date provided)
    if 'current_year' in context and 'current_month' in context and 'current_day' in context:
        jdn = fc60.compute_jdn(context['current_year'], context['current_month'], context['current_day'])
        phase_idx, age = fc60.moon_phase(jdn)
        # Full moon (4) and new moon (0) = peak energy = higher score
        peak_phases = {0: 0.9, 4: 1.0, 1: 0.6, 3: 0.6, 5: 0.7, 7: 0.5, 2: 0.5, 6: 0.4}
        breakdown['moon_alignment'] = peak_phases.get(phase_idx, 0.5)
    else:
        breakdown['moon_alignment'] = 0.5  # neutral if no date context
    
    # Ganzhi year match
    if 'current_year' in context:
        gz_stem, gz_branch = fc60.ganzhi_year(context['current_year'])
        # Does the number's mod-12 match the year's branch?
        year_animal_idx = (context['current_year'] - 4) % 12
        breakdown['ganzhi_match'] = 1.0 if animal_idx == year_animal_idx else 0.2
    else:
        breakdown['ganzhi_match'] = 0.5
    
    # Sacred geometry: proximity to Fibonacci numbers or golden ratio multiples
    fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584]
    golden = 1.6180339887
    is_fib = n in fib
    # Check if n is close to a golden ratio multiple of any smaller number
    golden_proximity = any(abs(n - round(f * golden)) <= 1 for f in fib if f < n) if n > 1 else False
    breakdown['sacred_geometry'] = 1.0 if is_fib else (0.6 if golden_proximity else 0.0)
    
    # Weighted sum
    score = sum(NUMEROLOGY_FACTORS[k] * breakdown[k] for k in NUMEROLOGY_FACTORS)
    
    return score, breakdown


def hybrid_score(n: int, context: dict = None, weights: dict = None) -> dict:
    """
    THE MAIN SCORING FUNCTION.
    
    Combines math, numerology, and learned scores into one final score.
    
    Args:
        n: The candidate number
        context: Optional context dict (date, target, etc.)
        weights: Optional weight override (from learning engine)
        
    Returns: {
        'final_score': float 0.0–1.0,
        'math_score': float,
        'math_breakdown': dict,
        'numerology_score': float,
        'numerology_breakdown': dict,
        'learned_score': float,
        'weights_used': dict,
        'fc60_token': str,
        'fc60_full': str,  # full base-60 encoding
        'reduced_number': int,
        'is_master': bool,
    }
    """
    w = weights or learning.get_weights() or DEFAULT_WEIGHTS
    
    m_score, m_breakdown = math_score(n)
    n_score, n_breakdown = numerology_score(n, context)
    l_score = learning.get_learned_score(n, context)
    
    # Normalize learned weight: starts at 0.0 (no data) and grows to 0.30
    # The "missing" learned weight gets split between math and numerology
    actual_learned_weight = w.get('learned_weight', 0.30) * learning.confidence_level()
    remaining = 1.0 - actual_learned_weight
    actual_math_weight = w.get('math_weight', 0.40) * remaining / (w.get('math_weight', 0.40) + w.get('numerology_weight', 0.30))
    actual_num_weight = w.get('numerology_weight', 0.30) * remaining / (w.get('math_weight', 0.40) + w.get('numerology_weight', 0.30))
    
    final = (actual_math_weight * m_score +
             actual_num_weight * n_score +
             actual_learned_weight * l_score)
    
    return {
        'final_score': round(final, 4),
        'math_score': round(m_score, 4),
        'math_breakdown': m_breakdown,
        'numerology_score': round(n_score, 4),
        'numerology_breakdown': n_breakdown,
        'learned_score': round(l_score, 4),
        'weights_used': {
            'math': round(actual_math_weight, 3),
            'numerology': round(actual_num_weight, 3),
            'learned': round(actual_learned_weight, 3),
        },
        'fc60_token': fc60.token60(n % 60),
        'fc60_full': fc60.encode_base60(n) if n >= 0 else 'NEG',
        'reduced_number': numerology.numerology_reduce(sum(int(d) for d in str(abs(n)))),
        'is_master': numerology.is_master_number(n),
    }


def score_batch(candidates: list, context: dict = None) -> list:
    """
    Score a list of candidates and return sorted by score (highest first).
    
    Returns: list of (candidate, score_dict) sorted by final_score desc.
    """
    results = [(c, hybrid_score(c, context)) for c in candidates]
    results.sort(key=lambda x: x[1]['final_score'], reverse=True)
    return results
```

---

## 6. LEARNING ENGINE — GETS SMARTER OVER TIME

File: `engines/learning.py`

### 6.1 How It Works (Simple Explanation)

1. Every time a puzzle is solved, we record the winning candidate's scores (all factors)
2. After enough solves (minimum 10), we compare: "Do winning numbers tend to have high entropy? Low entropy? Master numbers?"
3. Factors that appear MORE in winners than in random losers get HIGHER weights
4. Factors that appear EQUALLY in winners and losers get LOWER weights (they don't help)
5. Weights are saved to `data/factor_weights.json` and loaded next session

### 6.2 Full Specification

```python
"""
Learning Engine
===============
Tracks solved puzzles and adjusts scoring weights based on
which factors actually correlate with correct answers.

Storage: JSON files in data/ directory.
No external dependencies.
"""

import json
import os
import math
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
HISTORY_FILE = DATA_DIR / "solve_history.json"
WEIGHTS_FILE = DATA_DIR / "factor_weights.json"

# Minimum solves before learning kicks in
MIN_SOLVES_FOR_LEARNING = 10


def _ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def record_solve(puzzle_type: str, candidate: int, score_result: dict,
                 was_correct: bool, metadata: dict = None):
    """
    Record a puzzle solve attempt (correct or incorrect).
    
    Args:
        puzzle_type: "btc", "number", "name", "date"
        candidate: The number that was tested
        score_result: Output of hybrid_score() for this candidate
        was_correct: Did this candidate solve the puzzle?
        metadata: Optional extra info (puzzle_id, time, etc.)
    """
    _ensure_data_dir()
    
    record = {
        'puzzle_type': puzzle_type,
        'candidate': candidate,
        'final_score': score_result['final_score'],
        'math_score': score_result['math_score'],
        'math_breakdown': score_result['math_breakdown'],
        'numerology_score': score_result['numerology_score'],
        'numerology_breakdown': score_result['numerology_breakdown'],
        'was_correct': was_correct,
        'fc60_token': score_result['fc60_token'],
        'reduced_number': score_result['reduced_number'],
        'is_master': score_result['is_master'],
        'metadata': metadata or {},
    }
    
    # Load existing history
    history = _load_history()
    history.append(record)
    
    # Save (keep last 10,000 records max to prevent file bloat)
    if len(history) > 10000:
        history = history[-10000:]
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def _load_history() -> list:
    """Load solve history from disk."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def get_weights() -> dict:
    """Load current learned weights. Returns None if no learned weights yet."""
    if not WEIGHTS_FILE.exists():
        return None
    try:
        with open(WEIGHTS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def confidence_level() -> float:
    """
    How confident is the learning engine? 0.0 = no data, 1.0 = very confident.
    Based on number of solved puzzles.
    
    0 solves → 0.0
    10 solves → 0.3
    50 solves → 0.7
    100+ solves → 1.0
    """
    history = _load_history()
    correct_count = sum(1 for r in history if r.get('was_correct'))
    if correct_count < MIN_SOLVES_FOR_LEARNING:
        return 0.0
    return min(1.0, correct_count / 100.0)


def get_learned_score(n: int, context: dict = None) -> float:
    """
    Score a candidate based on learned patterns.
    Returns 0.5 (neutral) if not enough data.
    
    Looks at historical winners and checks how similar this candidate
    is to them across all tracked factors.
    """
    history = _load_history()
    winners = [r for r in history if r.get('was_correct')]
    
    if len(winners) < MIN_SOLVES_FOR_LEARNING:
        return 0.5  # Neutral — not enough data
    
    # Compare candidate's profile to average winner profile
    # For each factor, check if candidate is closer to winner average or loser average
    from engines import scoring
    
    candidate_score = scoring.math_score(n)[0]  # Just the math score for comparison
    
    winner_avg = sum(r.get('math_score', 0.5) for r in winners) / len(winners)
    
    # Simple similarity: how close is this candidate's math score to the winner average?
    similarity = 1.0 - abs(candidate_score - winner_avg)
    
    return max(0.0, min(1.0, similarity))


def recalculate_weights():
    """
    Analyze solve history and recalculate optimal weights.
    Called periodically (e.g., after every 10 new solves).
    
    Algorithm:
    1. Separate history into winners and losers
    2. For each scoring factor, calculate average value in winners vs losers
    3. Factors with bigger winner-loser gap get higher weight
    4. Save new weights to disk
    """
    _ensure_data_dir()
    history = _load_history()
    
    winners = [r for r in history if r.get('was_correct')]
    losers = [r for r in history if not r.get('was_correct')]
    
    if len(winners) < MIN_SOLVES_FOR_LEARNING or len(losers) < MIN_SOLVES_FOR_LEARNING:
        return  # Not enough data
    
    # Compare math vs numerology effectiveness
    winner_math_avg = sum(r.get('math_score', 0.5) for r in winners) / len(winners)
    winner_num_avg = sum(r.get('numerology_score', 0.5) for r in winners) / len(winners)
    loser_math_avg = sum(r.get('math_score', 0.5) for r in losers) / len(losers)
    loser_num_avg = sum(r.get('numerology_score', 0.5) for r in losers) / len(losers)
    
    # Gap = how much better do winners score on this factor?
    math_gap = max(0.01, winner_math_avg - loser_math_avg)
    num_gap = max(0.01, winner_num_avg - loser_num_avg)
    total_gap = math_gap + num_gap
    
    # Redistribute weights proportionally to gap
    new_weights = {
        'math_weight': 0.70 * (math_gap / total_gap),       # Max 70% to either
        'numerology_weight': 0.70 * (num_gap / total_gap),   # Max 70% to either
        'learned_weight': 0.30,                               # Always 30%
    }
    
    # Normalize so total = 1.0
    total = sum(new_weights.values())
    new_weights = {k: v/total for k, v in new_weights.items()}
    
    with open(WEIGHTS_FILE, 'w') as f:
        json.dump(new_weights, f, indent=2)


def get_factor_accuracy() -> dict:
    """
    For the Validation Dashboard.
    Returns how often each factor was "high" in winning answers vs. losing answers.
    
    Returns: {
        'total_solves': int,
        'total_correct': int,
        'factors': {
            'master_number': {'winner_rate': float, 'loser_rate': float, 'lift': float},
            'high_entropy': {'winner_rate': float, 'loser_rate': float, 'lift': float},
            ...
        }
    }
    """
    history = _load_history()
    winners = [r for r in history if r.get('was_correct')]
    losers = [r for r in history if not r.get('was_correct')]
    
    result = {
        'total_solves': len(history),
        'total_correct': len(winners),
        'factors': {},
    }
    
    if not winners or not losers:
        return result
    
    # Check each trackable factor
    factor_checks = {
        'is_master_number': lambda r: r.get('is_master', False),
        'high_math_score': lambda r: r.get('math_score', 0) > 0.6,
        'high_numerology_score': lambda r: r.get('numerology_score', 0) > 0.6,
        'power_reduced_number': lambda r: r.get('reduced_number', 0) in (1, 8, 9, 11, 22, 33),
    }
    
    for name, check_fn in factor_checks.items():
        winner_rate = sum(1 for w in winners if check_fn(w)) / len(winners)
        loser_rate = sum(1 for l in losers if check_fn(l)) / len(losers)
        lift = (winner_rate / loser_rate - 1.0) if loser_rate > 0 else 0.0
        
        result['factors'][name] = {
            'winner_rate': round(winner_rate, 4),
            'loser_rate': round(loser_rate, 4),
            'lift': round(lift, 4),  # >0 means this factor predicts winners
        }
    
    return result


def get_solve_stats() -> dict:
    """
    Summary statistics for the dashboard.
    
    Returns: {
        'total_attempts': int,
        'total_correct': int,
        'success_rate': float,
        'avg_winner_score': float,
        'avg_loser_score': float,
        'best_puzzle_type': str,
        'confidence': float,
    }
    """
    history = _load_history()
    winners = [r for r in history if r.get('was_correct')]
    losers = [r for r in history if not r.get('was_correct')]
    
    return {
        'total_attempts': len(history),
        'total_correct': len(winners),
        'success_rate': len(winners) / max(1, len(history)),
        'avg_winner_score': sum(r.get('final_score', 0) for r in winners) / max(1, len(winners)),
        'avg_loser_score': sum(r.get('final_score', 0) for r in losers) / max(1, len(losers)),
        'best_puzzle_type': _most_common_type(winners),
        'confidence': confidence_level(),
    }


def _most_common_type(records: list) -> str:
    """Find the most common puzzle_type in records."""
    if not records:
        return "none"
    from collections import Counter
    types = Counter(r.get('puzzle_type', 'unknown') for r in records)
    return types.most_common(1)[0][0]
```

---

## 7. PUZZLE SOLVERS — ALL 4 TYPES

### 7.1 Base Solver (solvers/base_solver.py)

```python
"""
Abstract base class that every puzzle solver must implement.
Provides the common interface for the GUI to interact with any solver type.
"""

from abc import ABC, abstractmethod
import threading
import time


class BaseSolver(ABC):
    """
    Every puzzle type implements this interface.
    The GUI only calls these methods — it never touches engine internals.
    """
    
    def __init__(self, callback=None):
        """
        callback: function(dict) called with progress updates.
        The dict must contain at minimum:
        {
            'status': str,         # 'running', 'solved', 'stopped', 'error'
            'progress': float,     # 0.0 to 100.0
            'message': str,        # Human-readable status
            'candidates_tested': int,
            'candidates_total': int,  # -1 if unknown
            'elapsed': float,      # seconds
            'current_best': dict,  # highest scored candidate so far
            'solution': any,       # the answer (only when status='solved')
        }
        """
        self.callback = callback
        self.running = False
        self.start_time = 0
        self._thread = None
    
    @abstractmethod
    def solve(self):
        """
        Start solving. This runs in a background thread.
        Must call self._emit() periodically with progress updates.
        Must check self.running to support cancellation.
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Human-readable name: 'BTC Puzzle Hunter', 'Number Oracle', etc."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """One-line description of what this solver does."""
        pass
    
    def start(self):
        """Launch solver in background thread."""
        if self.running:
            return
        self.running = True
        self.start_time = time.time()
        self._thread = threading.Thread(target=self._run_wrapper, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Request solver to stop."""
        self.running = False
    
    def _run_wrapper(self):
        """Wrapper that catches exceptions and reports them via callback."""
        try:
            self.solve()
        except Exception as e:
            self._emit({
                'status': 'error',
                'message': str(e),
                'progress': 0,
                'candidates_tested': 0,
                'candidates_total': -1,
                'elapsed': time.time() - self.start_time,
                'current_best': None,
                'solution': None,
            })
    
    def _emit(self, data: dict):
        """Send progress update to GUI via callback."""
        if self.callback:
            # Ensure elapsed is always fresh
            data.setdefault('elapsed', time.time() - self.start_time)
            self.callback(data)
```

### 7.2 BTC Solver (solvers/btc_solver.py)

Wraps the existing Kangaroo + BruteForce solvers from crypto.py. Adds the FC60 scoring overlay.

**Key behavior:**
- User picks a puzzle number (from PUZZLES dict)
- Solver determines algorithm (Kangaroo if public key available, else BruteForce)
- Before brute-forcing, score a sample of N candidates from the range, sort by harmony score
- Try highest-scored regions first, then fall back to sequential
- Reports progress via callback including FC60 analysis of current candidate
- On solve: record in learning engine

**Strategy modes:**
- `lightning` — pure brute force, no scoring (fastest for small ranges)
- `mystic` — score 10,000 samples, try top candidates first
- `hybrid` — alternate: try 100 scored candidates, then 100 random, repeat

### 7.3 Number Solver (solvers/number_solver.py)

Solves "what comes next" sequence puzzles.

**Input:** List of integers, e.g., `[2, 4, 8, 16]`

**Algorithm:**
1. Check standard math patterns first:
   - Arithmetic sequence (constant difference): `[2,4,6,8]` → diff=2 → next=10
   - Geometric sequence (constant ratio): `[2,4,8,16]` → ratio=2 → next=32
   - Fibonacci-like (sum of previous two): `[1,1,2,3,5]` → next=8
   - Polynomial (differences of differences): `[1,4,9,16]` → squares → next=25
   - Power sequence: `[1,8,27,64]` → cubes → next=125
2. For each detected pattern, predict next number(s)
3. Score each prediction with hybrid_score()
4. Also check FC60 patterns:
   - Convert each number to token60 → look for animal/element patterns
   - If animals follow a cycle (RA, OX, TI, ...) predict next animal → decode back
5. Return ranked predictions with explanations

**Output:** List of `{prediction: int, confidence: float, method: str, harmony_score: float, explanation: str}`

### 7.4 Name Solver (solvers/name_solver.py)

Not really a "solver" — more an analyzer. Produces a complete numerological profile.

**Input:** Name (str), optional DOB (year, month, day), optional mother's name

**Output:** Dictionary with:
- Expression number + meaning
- Soul urge number + meaning
- Personality number + meaning
- Life path number + meaning (if DOB provided)
- Personal year (if DOB provided)
- FC60 encoding of name value
- FC60 encoding of DOB (if provided)
- Birth weekday + planet + domain
- Gānzhī birth year
- Full symbolic reading of current moment
- Compatibility with current year energy
- Letter-by-letter breakdown (each letter → number → running total)

### 7.5 Date Solver (solvers/date_solver.py)

Analyzes dates and predicts future significant dates.

**Input:** One or more dates (as strings: "YYYY-MM-DD")

**Single date analysis:**
- Full FC60 encoding (all 12 fields)
- Symbolic reading
- Moon phase + meaning
- Gānzhī year + meaning
- Weekday + planet + domain
- Numerological analysis of date components

**Multi-date pattern detection:**
- Find common animals/elements across input dates
- Calculate intervals between dates → look for FC60 patterns in intervals
- Detect moon phase patterns (all on full moons? all on new moons?)
- Detect weekday patterns (all on Fridays?)
- Detect Gānzhī patterns (same element? same animal?)

**Prediction:** Given patterns found, predict next date(s) that match the pattern.

Example: Input `["2024-02-10", "2024-05-23", "2024-11-01"]`
→ All are on waning gibbous moon
→ Predict next waning gibbous dates
→ Score each by harmony_score
→ Return ranked predictions

---

## 8. DATA STORAGE — JSON FILE DATABASE

### 8.1 solve_history.json

```json
[
  {
    "puzzle_type": "btc",
    "candidate": 868591084757,
    "final_score": 0.7234,
    "math_score": 0.6812,
    "math_breakdown": {"entropy_low": 0.45, "digit_balance": 0.78, ...},
    "numerology_score": 0.7891,
    "numerology_breakdown": {"master_number": 0.0, "animal_repetition": 0.67, ...},
    "was_correct": true,
    "fc60_token": "DRFI",
    "reduced_number": 8,
    "is_master": false,
    "metadata": {"puzzle_id": 40, "strategy": "mystic", "timestamp": "2026-02-06T12:00:00"}
  }
]
```

### 8.2 factor_weights.json

```json
{
  "math_weight": 0.42,
  "numerology_weight": 0.28,
  "learned_weight": 0.30
}
```

### 8.3 session_log.json

```json
{
  "session_start": "2026-02-06T12:00:00",
  "puzzles_attempted": 3,
  "puzzles_solved": 1,
  "total_candidates_tested": 15420,
  "current_solver": "btc",
  "current_strategy": "hybrid"
}
```

---

## 9. GUI LAYER — TKINTER DESKTOP APP

### 9.1 Design System (gui/theme.py)

**Aesthetic: Dark, minimal, premium. "Luxury watch meets terminal."**

```python
COLORS = {
    # Base
    'bg':           '#0d1117',    # Deep dark background
    'bg_card':      '#161b22',    # Card/panel surface
    'bg_input':     '#21262d',    # Input fields
    'bg_hover':     '#1c2128',    # Hover state
    'border':       '#30363d',    # Subtle borders
    
    # Text
    'text':         '#c9d1d9',    # Primary text
    'text_dim':     '#8b949e',    # Secondary/label text
    'text_bright':  '#f0f6fc',    # Emphasized text
    
    # Accents
    'gold':         '#d4a017',    # Primary accent — quiet luxury gold
    'gold_dim':     '#a67c00',    # Gold hover/secondary
    'accent':       '#58a6ff',    # Links, interactive elements
    'success':      '#238636',    # Solved/verified states
    'warning':      '#d29922',    # Caution states
    'error':        '#f85149',    # Error states
    'purple':       '#a371f7',    # Numerology-specific highlights
    
    # Score colors (gradient: low→high)
    'score_low':    '#f85149',    # 0.0–0.3 (red)
    'score_mid':    '#d29922',    # 0.3–0.6 (amber)
    'score_high':   '#238636',    # 0.6–0.8 (green)
    'score_peak':   '#d4a017',    # 0.8–1.0 (gold)
}

FONTS = {
    'heading':    ('Segoe UI', 16, 'bold'),   # Tab titles
    'subhead':    ('Segoe UI', 12, 'bold'),   # Section headers
    'body':       ('Segoe UI', 10),           # Normal text
    'small':      ('Segoe UI', 9),            # Labels, captions
    'mono':       ('Consolas', 10),           # Code, tokens, numbers
    'mono_lg':    ('Consolas', 12),           # Large monospace (FC60 output)
    'mono_sm':    ('Consolas', 9),            # Small monospace
    'score':      ('Consolas', 18, 'bold'),   # Big score display
    'token':      ('Consolas', 14, 'bold'),   # FC60 token display
}

# Linux/Mac font fallbacks
import sys
if sys.platform != 'win32':
    for key in FONTS:
        f = list(FONTS[key])
        if f[0] == 'Segoe UI': f[0] = 'Helvetica'
        elif f[0] == 'Consolas': f[0] = 'Courier'
        FONTS[key] = tuple(f)
```

### 9.2 Main Window Layout (main.py)

```
┌──────────────────────────────────────────────────────────────┐
│  NPS — Numerology Puzzle Solver                    v1.0  🔮  │
├──────────────────────────────────────────────────────────────┤
│ [Dashboard] [BTC Hunter] [Number Oracle] [Name] [Date] [📊] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                    (active tab content)                       │
│                                                              │
│                                                              │
│                                                              │
│                                                              │
│                                                              │
│                                                              │
│                                                              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ STATUS: Ready │ Learning: 23 solves │ Confidence: 0.23  ◆●○  │
└──────────────────────────────────────────────────────────────┘
```

**Window properties:**
- Title: "NPS — Numerology Puzzle Solver"
- Minimum size: 1000 × 700
- Default size: 1200 × 800
- Background: COLORS['bg']
- Status bar at bottom showing: solver status, learning engine stats, confidence dots

### 9.3 Tab Specifications

#### Dashboard Tab (gui/dashboard_tab.py)

```
┌──────────────────────────────────────────────────────────────┐
│  ⚡ Dashboard                                                │
├──────────────────┬───────────────────┬───────────────────────┤
│ CURRENT MOMENT   │ SOLVE STATS       │ LEARNING ENGINE       │
│                  │                   │                       │
│ FC60: VE-OX-OXFI│ Attempted: 156    │ Confidence: ■■■□□ 60% │
│ Moon: 🌖 Waning  │ Solved: 12        │ Math weight: 42%      │
│ GZ: Fire Horse  │ Success: 7.7%     │ Numr weight: 28%      │
│ Energy: Share   │ Avg score: 0.61   │ Lrnd weight: 30%      │
│                  │                   │                       │
│ "Gratitude,     │ Best type: Number │ Data points: 156      │
│  sharing,       │                   │                       │
│  distribution"  │                   │ [Recalculate Weights] │
├──────────────────┴───────────────────┴───────────────────────┤
│ RECENT SOLVES                                                │
│ ┌──────┬──────────┬──────────┬───────┬────────────────────┐ │
│ │ Type │ Answer   │ Score    │ Token │ Time               │ │
│ ├──────┼──────────┼──────────┼───────┼────────────────────┤ │
│ │ NUM  │ 42       │ 0.82 ●●●│ HOER  │ 2 min ago          │ │
│ │ BTC  │ 0xa3f... │ 0.61 ●●○│ DRFI  │ 15 min ago         │ │
│ │ DATE │ Feb 14   │ 0.74 ●●●│ OXMT  │ 1 hour ago         │ │
│ └──────┴──────────┴──────────┴───────┴────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Updates:** Refreshes "Current Moment" every 60 seconds. Updates solve stats when new solves happen.

#### BTC Hunter Tab (gui/btc_tab.py)

Adapted from V1's PuzzleHunterTab. Keep the same puzzle selector and progress display.

**Additions over V1:**
- Strategy selector dropdown: Lightning / Mystic / Hybrid
- FC60 overlay panel showing current candidate's token, animal, element in real-time
- Harmony score bar updating as solver runs (shows the score of the current candidate)
- Before starting: show FC60 analysis of the search range (range_start and range_end tokens)
- After solving: full FC60 analysis of the answer + record to learning engine

#### Number Oracle Tab (gui/number_tab.py)

```
┌──────────────────────────────────────────────────────────────┐
│  🔢 Number Oracle                                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Enter sequence (comma-separated):                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2, 4, 8, 16                                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  [Analyze Sequence]    [Clear]                               │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  PREDICTIONS                                                 │
│  ┌─────────┬────────────┬─────────┬────────┬──────────────┐ │
│  │ Predict │ Method     │ Score   │ Token  │ Explanation   │ │
│  ├─────────┼────────────┼─────────┼────────┼──────────────┤ │
│  │ 32      │ Geometric  │ 0.78 ●●●│ TIWA   │ ratio = 2    │ │
│  │ 31      │ FC60 cycle │ 0.65 ●●○│ TIFI   │ Tiger loop   │ │
│  │ 30      │ Nearest    │ 0.52 ●○○│ TIWU   │ rounding     │ │
│  └─────────┴────────────┴─────────┴────────┴──────────────┘ │
│                                                              │
│  FC60 PATTERN VIEW                                           │
│  2 → RAWU (Rat-Wood)                                        │
│  4 → RAER (Rat-Earth)                                       │
│  8 → OXMT (Ox-Metal)                                        │
│  16 → RUFI (Rabbit-Fire)                                    │
│  Pattern: Animals advancing (RA→RA→OX→RU), Elements cycling  │
└──────────────────────────────────────────────────────────────┘
```

#### Name Cipher Tab (gui/name_tab.py)

```
┌──────────────────────────────────────────────────────────────┐
│  🔤 Name Cipher                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Full Name: ┌───────────────────────────────────┐            │
│             │                                   │            │
│             └───────────────────────────────────┘            │
│  Birthday:  ┌────────────┐  Mother's Name (opt): ┌────────┐ │
│             │ YYYY-MM-DD │                        │        │ │
│             └────────────┘                        └────────┘ │
│                                                              │
│  [Generate Reading]                                          │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  ═══ NUMEROLOGY PROFILE ═══                                  │
│                                                              │
│  Life Path:    8 — The Powerhouse: Master, achieve, legacy   │
│  Expression:   5 — The Explorer: Change, adapt, experience   │
│  Soul Urge:    3 — The Voice: Create, express, beautify      │
│  Personality:  2 — The Bridge: Connect, harmonize, feel      │
│  Personal Year: 1 — The Pioneer: Lead, start, go first       │
│                                                              │
│  ═══ FC60 BIRTH STAMP ═══                                    │
│                                                              │
│  VE-OX-OXFI                                                  │
│  Born on a Friday (Venus ♀ — Love, values, beauty)           │
│  Birth year: 丙午 Fire Horse                                 │
│                                                              │
│  ═══ LETTER BREAKDOWN ═══                                    │
│  D(4) A(1) V(4) E(5) = 14 → 5                               │
│                                                              │
│  ═══ CURRENT MOMENT READING ═══                              │
│  (symbolic reading for right now)                            │
└──────────────────────────────────────────────────────────────┘
```

#### Date Decoder Tab (gui/date_tab.py)

```
┌──────────────────────────────────────────────────────────────┐
│  📅 Date Decoder                                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Enter date(s), one per line:                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2026-02-06                                           │   │
│  │ 2026-03-14                                           │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  [Analyze]    [Predict Next]    [Clear]                      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  FC60 ANALYSIS (per date — scrollable)                       │
│  ... full FC60 output for each date ...                      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  PATTERNS DETECTED (only if 2+ dates)                        │
│  • Both dates fall on Ox-month energy                        │
│  • Moon phases: Waning Gibbous → Waxing Crescent             │
│  • Interval: 36 days = RAFI in FC60                          │
│                                                              │
│  PREDICTED NEXT SIGNIFICANT DATE                             │
│  2026-04-21 — Score: 0.81 — Reason: completes element cycle  │
└──────────────────────────────────────────────────────────────┘
```

#### Validation Dashboard Tab (gui/validation_tab.py)

```
┌──────────────────────────────────────────────────────────────┐
│  📊 Validation Dashboard                                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Does the scoring system actually work?                      │
│  This dashboard honestly measures if scored candidates        │
│  solve puzzles more often than random ones.                  │
│                                                              │
├───────────────────────────────┬──────────────────────────────┤
│  KEY METRICS                  │  FACTOR ACCURACY             │
│                               │                              │
│  Total attempts: 156          │  Factor        W%   L%  Lift │
│  Total solved: 12             │  ─────────────────────────── │
│  Success rate: 7.7%           │  Master #:    12%   8%  +50% │
│  Avg winner score: 0.71       │  High entropy: 45% 40%  +12% │
│  Avg loser score: 0.54        │  Power LP:    33% 28%  +18% │
│  Score gap: +0.17 ✓           │  High math:   56% 41%  +37% │
│                               │  High numer:  38% 35%  + 9% │
│  Confidence: ■■■□□ 60%        │                              │
│                               │  ✓ = better than random      │
│  Score-to-solve correlation:  │  ✗ = no better than random   │
│  0.23 (weak positive) ✓       │                              │
│                               │                              │
├───────────────────────────────┴──────────────────────────────┤
│  WEIGHT HISTORY                                              │
│                                                              │
│  Math:  ████████████████████░░░░░░░░░░  42%                  │
│  Numer: █████████████░░░░░░░░░░░░░░░░░  28%                  │
│  Learn: ██████████████░░░░░░░░░░░░░░░░  30%                  │
│                                                              │
│  [Recalculate Weights]    [Export History CSV]    [Reset]     │
└──────────────────────────────────────────────────────────────┘
```

### 9.4 Reusable Widgets (gui/widgets.py)

Build these reusable components used across multiple tabs:

1. **ScoreBar** — Horizontal bar showing 0.0 to 1.0, colored by score tier (red/amber/green/gold). Shows numeric score label.

2. **TokenDisplay** — Shows an FC60 token like "DRFI" with the animal name + element name + colored background matching the element (Wood=green, Fire=red, Earth=brown, Metal=silver, Water=blue).

3. **AnimatedProgress** — Progress bar that smoothly animates between values, with percentage label and speed indicator (candidates/sec).

4. **StatsCard** — A bordered card with title, big number, and subtitle. Used on the dashboard for "Total Solved: 12" etc.

5. **FactorBreakdown** — A vertical list of scoring factors with horizontal bars showing each factor's contribution. Used in score details.

6. **LogPanel** — Scrolled text widget with monospace font, auto-scroll, colored output lines (gold for important, green for success, red for errors, gray for info).

---

## 10. TESTING STRATEGY

### Test Files to Create

All tests use Python's built-in `unittest` module. No pytest or other dependencies.

Run all tests: `python -m unittest discover tests/`

### test_fc60.py

Import and run the existing `self_test()` from fc60.py. All 29 test vectors must pass. Add:
- Round-trip test for every integer 0–59 (token60 → digit60)
- Round-trip test for large numbers (encode_base60 → decode_base60) for: 0, 1, 59, 60, 3600, 2461072, 999999
- JDN test vectors: (2000,1,1)→2451545, (2026,2,6)→2461078, (1970,1,1)→2440588
- Weekday test vectors: (2026,2,6)→VE (Friday)
- Gānzhī test vectors: 2024→JA-DR (Wood Dragon), 2026→BI-HO (Fire Horse)

### test_numerology.py

- `numerology_reduce(29)` → 11 (master number preserved)
- `numerology_reduce(38)` → 11 (master number preserved)
- `numerology_reduce(15)` → 6
- `name_to_number("DAVE")` → calculate manually: D=4, A=1, V=4, E=5 → 14 → 5
- `life_path(1990, 1, 15)` → calculate manually
- `is_master_number(29)` → True (2+9=11)
- `is_master_number(13)` → False (1+3=4)

### test_math_analysis.py

- `entropy(111111)` → 0.0
- `entropy(123456)` → close to 2.585
- `is_prime(7)` → True
- `is_prime(8)` → False
- `prime_factors(60)` → [2, 2, 3, 5]
- `palindrome_score(12321)` → 1.0
- `palindrome_score(12345)` → 0.0

### test_scoring.py

- `hybrid_score(any_positive_int)` → final_score between 0.0 and 1.0
- `hybrid_score(11)` → numerology_score > hybrid_score(10) (master number boost)
- `score_batch([1,2,3,4,5])` → returns list of length 5, sorted by score descending
- Scores must be deterministic (same input → same output)

### test_solvers.py

- Number solver: `[2,4,8,16]` → predicts 32 (geometric)
- Number solver: `[1,1,2,3,5]` → predicts 8 (Fibonacci)
- Number solver: `[1,4,9,16]` → predicts 25 (squares)
- Name solver: "DAVE" with DOB 1990-01-15 → returns dict with all required fields
- Date solver: "2026-02-06" → returns dict with FC60 output matching self_test vector

### test_learning.py

- `confidence_level()` starts at 0.0 (no data)
- After recording 10 correct solves, `confidence_level()` > 0.0
- `get_factor_accuracy()` returns dict with expected structure
- `record_solve()` creates/appends to history file
- History file doesn't grow beyond 10,000 records

---

## 11. BUILD & RUN INSTRUCTIONS

### First Run

```bash
cd nps/
python main.py
```

That's it. No pip installs. No virtual environments. No config files.

### Running Tests

```bash
cd nps/
python -m unittest discover tests/ -v
```

### File Structure After First Run

The `data/` directory is created automatically on first solve:
```
nps/data/
├── solve_history.json    # Empty array: []
├── factor_weights.json   # Created after 10+ solves
└── session_log.json      # Current session
```

---

## 12. VALIDATION DASHBOARD — DETAILED SPEC

The validation dashboard answers ONE question: **"Does scoring actually help?"**

### Metrics to Calculate

| Metric | Formula | Good Value | Bad Value |
|--------|---------|------------|-----------|
| **Score gap** | avg_winner_score - avg_loser_score | > 0.05 | ≤ 0 |
| **Lift per factor** | (winner_rate / loser_rate) - 1.0 | > 0.10 (10%) | ≤ 0 |
| **Confidence** | min(1.0, correct_count / 100) | > 0.5 | < 0.1 |
| **Score-to-solve correlation** | Pearson correlation between final_score and was_correct | > 0.1 | ≤ 0 |

### What to Display

1. **Big number cards:** Total attempts, total solved, success rate, score gap
2. **Factor table:** Each factor with winner%, loser%, lift%, and ✓/✗ indicator
3. **Weight bars:** Current learned weights (math/numerology/learned) as horizontal bars
4. **Honesty label:** If score gap ≤ 0, display: "⚠ Scoring is not yet helping. More data needed."

### When to Recalculate

- Automatically after every 10 new solves
- Manually via "Recalculate Weights" button
- On app startup if history file exists

---

## 13. CONSTANTS & REFERENCE TABLES

### FC60 Token Table (60 tokens)

| Index | Token | Animal | Element |
|-------|-------|--------|---------|
| 0 | RAWU | Rat | Wood |
| 1 | RAFI | Rat | Fire |
| 2 | RAER | Rat | Earth |
| 3 | RAMT | Rat | Metal |
| 4 | RAWA | Rat | Water |
| 5 | OXWU | Ox | Wood |
| 6 | OXFI | Ox | Fire |
| 7 | OXER | Ox | Earth |
| 8 | OXMT | Ox | Metal |
| 9 | OXWA | Ox | Water |
| 10 | TIWU | Tiger | Wood |
| ... | ... | ... | ... |
| 55 | PIWU | Pig | Wood |
| 56 | PIFI | Pig | Fire |
| 57 | PIER | Pig | Earth |
| 58 | PIMT | Pig | Metal |
| 59 | PIWA | Pig | Water |

(Full table is computed by the engine: `token60(i)` for i in 0–59)

### Pythagorean Letter Values

```
A=1  B=2  C=3  D=4  E=5  F=6  G=7  H=8  I=9
J=1  K=2  L=3  M=4  N=5  O=6  P=7  Q=8  R=9
S=1  T=2  U=3  V=4  W=5  X=6  Y=7  Z=8
```

### Life Path Meanings

```
1 → The Pioneer: Lead, start, go first
2 → The Bridge: Connect, harmonize, feel
3 → The Voice: Create, express, beautify
4 → The Architect: Build, structure, stabilize
5 → The Explorer: Change, adapt, experience
6 → The Guardian: Nurture, heal, protect
7 → The Seeker: Question, analyze, find meaning
8 → The Powerhouse: Master, achieve, build legacy
9 → The Sage: Complete, teach, transcend
11 → The Visionary: See what hasn't been built (master)
22 → The Master Builder: Turn impossible visions into reality (master)
33 → The Master Teacher: Heal through compassionate leadership (master)
```

### BTC Puzzle Database

Copy the PUZZLES dict from `v1_source/engine.py` exactly. Contains puzzles: 20, 25, 30, 35, 40 (solved/testing), 71, 72, 75, 80, 85, 90, 130 (active).

---

## 14. EDGE CASES & ERROR HANDLING

### Input Validation

| Input | Edge Case | Expected Behavior |
|-------|-----------|-------------------|
| Number sequence | Empty list | Show error: "Enter at least 2 numbers" |
| Number sequence | Single number | Show FC60 analysis only, no prediction |
| Number sequence | Non-numeric input | Show error: "Only numbers and commas allowed" |
| Name input | Empty string | Show error: "Enter a name" |
| Name input | Numbers in name | Ignore non-alpha characters |
| Date input | Invalid date "2026-13-01" | Show error: "Invalid date" |
| Date input | Future date | Allow it — FC60 works for any date |
| BTC puzzle | Puzzle already solved | Allow running (useful for testing) |
| BTC puzzle | User cancels mid-solve | Stop solver cleanly, save partial session |
| Scoring | Negative number | Use abs(n) for digit analysis, note sign |
| Scoring | Zero | Return neutral score 0.5 |
| Scoring | Very large number (>10^15) | Skip prime factorization, note limitation |
| Learning | Corrupted history file | Catch JSONDecodeError, start fresh |
| Learning | File permissions error | Catch IOError, log warning, continue without learning |

### Thread Safety

- All solver work runs in daemon threads
- GUI updates via `widget.after()` callbacks (Tkinter's thread-safe method)
- Use `queue.Queue()` for solver-to-GUI communication (same pattern as V1)
- Never modify Tkinter widgets directly from solver threads

---

## 15. QUALITY CHECKLIST

Before declaring the app "done," verify every item:

### Engine Layer ✓
- [ ] All 29 V1 FC60 test vectors pass
- [ ] All V1 crypto self-tests pass (Kangaroo + BruteForce)
- [ ] `hybrid_score()` returns float between 0.0 and 1.0 for ANY positive integer
- [ ] `math_profile()` handles 0, 1, large numbers without crash
- [ ] `entropy(111111)` returns 0.0
- [ ] `numerology_reduce(29)` returns 11 (master number)
- [ ] `score_batch([1,2,3])` returns sorted list

### Solver Layer ✓
- [ ] BTC solver finds puzzle #20 answer (known solved puzzle, range 2^19 to 2^20-1)
- [ ] Number solver predicts 32 for sequence [2, 4, 8, 16]
- [ ] Number solver predicts 8 for sequence [1, 1, 2, 3, 5]
- [ ] Name solver returns all 5 numerology numbers for any name+DOB
- [ ] Date solver returns full FC60 output for "2026-02-06"
- [ ] All solvers can be started AND stopped without crashing

### Learning Layer ✓
- [ ] `record_solve()` creates file if it doesn't exist
- [ ] History doesn't exceed 10,000 records
- [ ] `confidence_level()` returns 0.0 with empty history
- [ ] `get_factor_accuracy()` returns valid structure
- [ ] Corrupted JSON file doesn't crash the app

### GUI Layer ✓
- [ ] App launches with `python main.py` on Python 3.8+
- [ ] All 6 tabs are visible and clickable
- [ ] Dashboard shows current FC60 moment on launch
- [ ] Solver stop button works (doesn't hang)
- [ ] Score bars show correct colors (red/amber/green/gold)
- [ ] Validation dashboard updates after new solves
- [ ] No crashes when switching tabs during active solve
- [ ] Window minimum size enforced (1000 × 700)

### Data Layer ✓
- [ ] `data/` directory auto-created
- [ ] JSON files are valid JSON after writes
- [ ] App works with no data/ directory (fresh install)
- [ ] App works with empty JSON files
- [ ] App works with corrupted JSON files (graceful fallback)

---

## END OF BLUEPRINT

**Total new code to write:** ~2,500 lines (engines + solvers + GUI + tests)
**Code reused from V1:** ~1,615 lines (fc60_engine.py + engine.py)
**Total app size:** ~4,100 lines

**The V1 engines are the foundation. Do NOT rewrite them — wrap them.**
**The scoring engine is the core innovation. Get it right.**
**The learning engine is what makes this unique. It must be honest about what works.**
**The validation dashboard is the proof. If scoring doesn't help, the dashboard says so.**

---
---

## ADDENDUM A — GAPS FIXED (17 issues)

This addendum patches every gap found during audit. Claude Code: read this section AFTER the main blueprint. These fixes OVERRIDE any conflicting specs above.

---

### FIX 1: Missing FC60 Functions

Two functions from V1 were missing from the fc60.py public API. Add them:

```python
# ADD to engines/fc60.py public API list:

def detect_animal_repetitions(month, day, hour, minute, year):
    """
    Detect repeated animals across all time components.
    Returns (repeated_list, components_dict).
    
    repeated_list: [(animal_token, count, [positions])] sorted by count desc
    components_dict: {"month": "OX", "day": "RA", "hour": "TI", ...}
    
    This is used by generate_symbolic_reading() and by the scoring engine
    to detect when the same animal energy appears multiple times in a moment.
    """
    # COPY implementation from v1_source/fc60_engine.py lines 469-490 exactly


def get_time_context(hour: int) -> str:
    """
    Get symbolic meaning for the given hour.
    Returns a descriptive string like:
    "Morning engine — clarity peaks, resistance lowest" (for hours 8-12)
    
    Uses the TIME_CONTEXT constant table.
    """
    # COPY implementation from v1_source/fc60_engine.py lines 460-465 exactly
```

---

### FIX 2: Circular Import — CRITICAL

**The problem:** `scoring.py` imports `learning.py` (to get weights), and `learning.py` imports `scoring.py` (to calculate math_score). This creates a circular import crash.

**The fix:** Use lazy imports inside the functions that need them, NOT at module top level.

```python
# In engines/learning.py — DO NOT put "from engines import scoring" at the top
# Instead, inside get_learned_score():

def get_learned_score(n: int, context: dict = None) -> float:
    history = _load_history()
    winners = [r for r in history if r.get('was_correct')]
    
    if len(winners) < MIN_SOLVES_FOR_LEARNING:
        return 0.5
    
    # LAZY IMPORT — avoids circular dependency
    from engines.math_analysis import entropy, digit_balance
    
    # Compare candidate's properties to winner averages
    candidate_entropy = entropy(n)
    candidate_balance = digit_balance(n)
    
    winner_entropies = [r.get('math_breakdown', {}).get('entropy_low', 0.5) for r in winners]
    winner_balances = [r.get('math_breakdown', {}).get('digit_balance', 0.5) for r in winners]
    
    avg_winner_entropy = sum(winner_entropies) / len(winner_entropies)
    avg_winner_balance = sum(winner_balances) / len(winner_balances)
    
    # Normalize candidate values to 0-1 range (same scale as stored breakdown values)
    max_entropy = 3.32
    norm_entropy = max(0, 1.0 - candidate_entropy / max_entropy)
    
    # Similarity: how close to the winner profile?
    entropy_sim = 1.0 - abs(norm_entropy - avg_winner_entropy)
    balance_sim = 1.0 - abs(candidate_balance - avg_winner_balance)
    
    # Also check numerology factors from history
    winner_master_rate = sum(1 for r in winners if r.get('is_master', False)) / len(winners)
    from engines.numerology import is_master_number
    candidate_is_master = is_master_number(n)
    master_boost = 0.2 if candidate_is_master and winner_master_rate > 0.15 else 0.0
    
    return max(0.0, min(1.0, (entropy_sim * 0.4 + balance_sim * 0.3 + 0.3 * 0.5 + master_boost)))
```

```python
# In engines/scoring.py — DO NOT put "from engines import learning" at top level
# Instead, inside hybrid_score():

def hybrid_score(n: int, context: dict = None, weights: dict = None) -> dict:
    # LAZY IMPORT — avoids circular dependency
    from engines import learning
    
    w = weights or learning.get_weights() or DEFAULT_WEIGHTS
    # ... rest of function
```

**Rule:** Never import between `scoring.py` and `learning.py` at module level. Always inside functions.

---

### FIX 3: Division by Zero in hybrid_score

Replace the weight normalization block:

```python
# REPLACE this (from section 5.2):
actual_math_weight = w.get('math_weight', 0.40) * remaining / (w.get('math_weight', 0.40) + w.get('numerology_weight', 0.30))

# WITH this safe version:
math_w = w.get('math_weight', 0.40)
num_w = w.get('numerology_weight', 0.30)
denominator = math_w + num_w
if denominator == 0:
    denominator = 1.0  # Fallback: split evenly
    math_w = 0.5
    num_w = 0.5
actual_math_weight = math_w * remaining / denominator
actual_num_weight = num_w * remaining / denominator
```

---

### FIX 4: Implementation Order for Claude Code

**Build files in this exact order. Each step depends on the previous ones.**

```
PHASE 1 — Engines (no GUI, no dependencies between new files)
  Step 1:  engines/__init__.py          (empty, just makes it a package)
  Step 2:  engines/fc60.py              (copy from V1, self-contained)
  Step 3:  engines/numerology.py        (copy from V1 + new functions, imports fc60)
  Step 4:  engines/crypto.py            (copy from V1, self-contained)
  Step 5:  engines/math_analysis.py     (new, self-contained, no imports from project)
  Step 6:  engines/learning.py          (new, imports math_analysis + numerology lazily)
  Step 7:  engines/scoring.py           (new, imports fc60 + numerology + math_analysis, lazy-imports learning)
  
  ✓ CHECKPOINT: Run test_fc60.py, test_numerology.py, test_math_analysis.py, test_scoring.py

PHASE 2 — Solvers (depend on engines)
  Step 8:  solvers/__init__.py          (empty)
  Step 9:  solvers/base_solver.py       (abstract base class, no engine imports)
  Step 10: solvers/btc_solver.py        (imports crypto + scoring)
  Step 11: solvers/number_solver.py     (imports fc60 + numerology + scoring)
  Step 12: solvers/name_solver.py       (imports numerology + fc60)
  Step 13: solvers/date_solver.py       (imports fc60 + numerology + scoring)
  
  ✓ CHECKPOINT: Run test_solvers.py

PHASE 3 — GUI (depends on everything)
  Step 14: gui/__init__.py              (empty)
  Step 15: gui/theme.py                 (colors + fonts, no imports)
  Step 16: gui/widgets.py               (reusable widgets, imports theme)
  Step 17: gui/dashboard_tab.py         (imports fc60 + learning)
  Step 18: gui/btc_tab.py               (imports btc_solver + scoring + fc60)
  Step 19: gui/number_tab.py            (imports number_solver)
  Step 20: gui/name_tab.py              (imports name_solver)
  Step 21: gui/date_tab.py              (imports date_solver)
  Step 22: gui/validation_tab.py        (imports learning)
  Step 23: main.py                      (imports all gui tabs, builds window)
  
  ✓ CHECKPOINT: python main.py launches, all tabs visible

PHASE 4 — Tests + Polish
  Step 24: All test files
  Step 25: README.md
  Step 26: Full quality checklist pass
```

---

### FIX 5: __init__.py Contents

```python
# engines/__init__.py
"""NPS Engine Layer — FC60, Numerology, Math Analysis, Crypto, Scoring, Learning."""

# Re-export key functions for convenient access
from engines.fc60 import token60, encode_fc60, format_full_output, parse_input, self_test
from engines.numerology import life_path, name_to_number, numerology_reduce, personal_year
from engines.math_analysis import math_profile, entropy
from engines.scoring import hybrid_score, score_batch


# solvers/__init__.py
"""NPS Solver Layer — BTC, Number, Name, Date puzzle solvers."""

from solvers.btc_solver import BTCSolver
from solvers.number_solver import NumberSolver
from solvers.name_solver import NameSolver
from solvers.date_solver import DateSolver


# gui/__init__.py
"""NPS GUI Layer — Tkinter desktop interface."""
# Nothing to export — tabs are imported directly by main.py
```

---

### FIX 6: App Shutdown Handling

Add to `main.py`:

```python
class NPSApp:
    def __init__(self):
        self.root = tk.Tk()
        self.active_solvers = []  # Track all running solvers
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _on_close(self):
        """Stop all running solvers before closing."""
        for solver in self.active_solvers:
            solver.stop()
        
        # Give threads 2 seconds to finish
        import time
        deadline = time.time() + 2.0
        for solver in self.active_solvers:
            if solver._thread and solver._thread.is_alive():
                remaining = max(0.1, deadline - time.time())
                solver._thread.join(timeout=remaining)
        
        self.root.destroy()
    
    def register_solver(self, solver):
        """Called by tabs when they start a solver."""
        self.active_solvers.append(solver)
    
    def unregister_solver(self, solver):
        """Called by tabs when solver finishes."""
        if solver in self.active_solvers:
            self.active_solvers.remove(solver)
```

---

### FIX 7: Logging Strategy

Use Python's built-in `logging` module. Every module gets its own logger.

```python
# At the top of EVERY engines/ and solvers/ file, add:
import logging
logger = logging.getLogger(__name__)

# In main.py, configure logging at startup:
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
    )
    # Also log to file
    file_handler = logging.FileHandler('data/nps.log', mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    ))
    logging.getLogger().addHandler(file_handler)

# Usage in any module:
logger.info("Solver started for puzzle #40")
logger.warning("History file corrupted, starting fresh")
logger.error(f"Unexpected error in scoring: {e}")
```

---

### FIX 8: BTC Solver Performance + Strategy Implementation

The `score_batch()` function must NEVER score millions of candidates. Instead, use sampling.

```python
# solvers/btc_solver.py

class BTCSolver(BaseSolver):
    
    SAMPLE_SIZE = 10_000  # Score this many samples, not the full range
    
    def __init__(self, puzzle_id: int, strategy: str = "hybrid", callback=None):
        """
        strategy: "lightning" | "mystic" | "hybrid"
        """
        super().__init__(callback)
        self.puzzle_id = puzzle_id
        self.strategy = strategy
        self.puzzle = PUZZLES[puzzle_id]
    
    def solve(self):
        if self.strategy == "lightning":
            self._solve_lightning()
        elif self.strategy == "mystic":
            self._solve_mystic()
        elif self.strategy == "hybrid":
            self._solve_hybrid()
    
    def _solve_lightning(self):
        """Pure brute force — fastest for small ranges. No scoring overhead."""
        # Use BruteForceSolver or KangarooSolver directly from crypto.py
        # Just wrap with progress callback
        if self.puzzle['type'] == 'B' and self.puzzle.get('public_key'):
            pubkey = decompress_pubkey(self.puzzle['public_key'])
            solver = KangarooSolver(pubkey, self.puzzle['range_start'],
                                    self.puzzle['range_end'], callback=self._btc_callback)
        else:
            solver = BruteForceSolver(self.puzzle['address'], self.puzzle['range_start'],
                                     self.puzzle['range_end'], callback=self._btc_callback)
        result = solver.solve()
        if result:
            self._record_win(result)
    
    def _solve_mystic(self):
        """Score a sample → try best-scored regions first."""
        import random
        range_start = self.puzzle['range_start']
        range_end = self.puzzle['range_end']
        range_size = range_end - range_start
        
        # Step 1: Take random sample from the range
        sample = [random.randint(range_start, range_end) for _ in range(self.SAMPLE_SIZE)]
        
        # Step 2: Score each sample
        from engines.scoring import hybrid_score
        scored = []
        for i, candidate in enumerate(sample):
            score = hybrid_score(candidate)
            scored.append((candidate, score['final_score']))
            if i % 1000 == 0:
                self._emit({
                    'status': 'running',
                    'message': f'Scoring sample: {i}/{self.SAMPLE_SIZE}',
                    'progress': (i / self.SAMPLE_SIZE) * 20,  # First 20% is scoring
                    'candidates_tested': 0,
                    'candidates_total': -1,
                    'current_best': None,
                    'solution': None,
                })
        
        # Step 3: Sort by score, try top candidates first
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Step 4: Test top candidates by checking their Bitcoin address
        for i, (candidate, score) in enumerate(scored):
            if not self.running:
                break
            address = privkey_to_address(candidate)
            if address == self.puzzle['address']:
                self._record_win(candidate)
                return
            
            if i % 100 == 0:
                self._emit({
                    'status': 'running',
                    'message': f'Testing scored candidates: {i}/{len(scored)}',
                    'progress': 20 + (i / len(scored)) * 80,
                    'candidates_tested': i,
                    'candidates_total': len(scored),
                    'current_best': {'candidate': scored[0][0], 'score': scored[0][1]},
                    'solution': None,
                })
        
        # Step 5: If not found in sample, fall back to brute force
        self._solve_lightning()
    
    def _solve_hybrid(self):
        """Alternate: 100 scored candidates, then 100 random, repeat."""
        import random
        range_start = self.puzzle['range_start']
        range_end = self.puzzle['range_end']
        from engines.scoring import hybrid_score
        
        batch_size = 100
        tested = 0
        
        while self.running:
            # Scored batch
            sample = [random.randint(range_start, range_end) for _ in range(batch_size)]
            scored = [(c, hybrid_score(c)['final_score']) for c in sample]
            scored.sort(key=lambda x: x[1], reverse=True)
            
            for candidate, score in scored:
                if not self.running:
                    return
                address = privkey_to_address(candidate)
                tested += 1
                if address == self.puzzle['address']:
                    self._record_win(candidate)
                    return
            
            # Random batch (no scoring overhead)
            for _ in range(batch_size):
                if not self.running:
                    return
                candidate = random.randint(range_start, range_end)
                address = privkey_to_address(candidate)
                tested += 1
                if address == self.puzzle['address']:
                    self._record_win(candidate)
                    return
            
            self._emit({
                'status': 'running',
                'message': f'Hybrid search: {tested} tested',
                'progress': -1,  # Unknown total
                'candidates_tested': tested,
                'candidates_total': -1,
                'current_best': {'candidate': scored[0][0], 'score': scored[0][1]} if scored else None,
                'solution': None,
            })
    
    def _record_win(self, candidate):
        """Record successful solve to learning engine."""
        from engines.scoring import hybrid_score
        from engines import learning
        
        score_result = hybrid_score(candidate)
        learning.record_solve(
            puzzle_type="btc",
            candidate=candidate,
            score_result=score_result,
            was_correct=True,
            metadata={"puzzle_id": self.puzzle_id, "strategy": self.strategy}
        )
        self._emit({
            'status': 'solved',
            'message': f'SOLVED! Key: {hex(candidate)}',
            'progress': 100,
            'candidates_tested': -1,
            'candidates_total': -1,
            'current_best': score_result,
            'solution': candidate,
        })
    
    def _btc_callback(self, data):
        """Translate crypto engine callbacks to BaseSolver format."""
        self._emit({
            'status': 'solved' if data.get('solved') else 'running',
            'message': f"Speed: {data.get('speed', 0):.0f}/s",
            'progress': data.get('progress', 0),
            'candidates_tested': data.get('operations', 0),
            'candidates_total': data.get('total_keys', -1),
            'current_best': None,
            'solution': data.get('solution'),
        })
        if data.get('solved') and data.get('solution'):
            self._record_win(data['solution'])
    
    def get_name(self):
        return "BTC Puzzle Hunter"
    
    def get_description(self):
        return f"Puzzle #{self.puzzle_id} — {self.strategy} strategy"
```

---

### FIX 9: Number Solver — Complete Pattern Detection

```python
# solvers/number_solver.py

class NumberSolver(BaseSolver):
    
    def __init__(self, sequence: list, callback=None):
        super().__init__(callback)
        self.sequence = [int(x) for x in sequence]
    
    def solve(self):
        predictions = []
        
        # Test each pattern type
        predictions.extend(self._check_arithmetic())
        predictions.extend(self._check_geometric())
        predictions.extend(self._check_fibonacci())
        predictions.extend(self._check_polynomial())
        predictions.extend(self._check_power())
        predictions.extend(self._check_fc60_pattern())
        
        # Score each prediction
        from engines.scoring import hybrid_score
        for pred in predictions:
            score = hybrid_score(pred['prediction'])
            pred['harmony_score'] = score['final_score']
            pred['fc60_token'] = score['fc60_token']
        
        # Sort by confidence × harmony
        predictions.sort(key=lambda p: p['confidence'] * 0.7 + p['harmony_score'] * 0.3, reverse=True)
        
        # Remove duplicates (same prediction from different methods)
        seen = set()
        unique = []
        for p in predictions:
            if p['prediction'] not in seen:
                seen.add(p['prediction'])
                unique.append(p)
        
        self._emit({
            'status': 'solved',
            'message': f'Found {len(unique)} predictions',
            'progress': 100,
            'candidates_tested': len(self.sequence),
            'candidates_total': len(self.sequence),
            'current_best': unique[0] if unique else None,
            'solution': unique,
        })
    
    def _check_arithmetic(self) -> list:
        """Check for constant difference: [2,4,6,8] → diff=2 → next=10."""
        if len(self.sequence) < 2:
            return []
        diffs = [self.sequence[i+1] - self.sequence[i] for i in range(len(self.sequence)-1)]
        if len(set(diffs)) == 1:
            return [{
                'prediction': self.sequence[-1] + diffs[0],
                'confidence': 0.95,
                'method': 'Arithmetic sequence',
                'explanation': f'Constant difference = {diffs[0]}',
            }]
        return []
    
    def _check_geometric(self) -> list:
        """Check for constant ratio: [2,4,8,16] → ratio=2 → next=32."""
        if len(self.sequence) < 2 or 0 in self.sequence:
            return []
        ratios = [self.sequence[i+1] / self.sequence[i] for i in range(len(self.sequence)-1)]
        # Check if all ratios are the same (within floating point tolerance)
        if all(abs(r - ratios[0]) < 0.0001 for r in ratios):
            next_val = round(self.sequence[-1] * ratios[0])
            return [{
                'prediction': next_val,
                'confidence': 0.93,
                'method': 'Geometric sequence',
                'explanation': f'Constant ratio = {ratios[0]:.4g}',
            }]
        return []
    
    def _check_fibonacci(self) -> list:
        """Check for sum-of-previous-two: [1,1,2,3,5] → next=8."""
        if len(self.sequence) < 3:
            return []
        is_fib = all(
            self.sequence[i] == self.sequence[i-1] + self.sequence[i-2]
            for i in range(2, len(self.sequence))
        )
        if is_fib:
            return [{
                'prediction': self.sequence[-1] + self.sequence[-2],
                'confidence': 0.92,
                'method': 'Fibonacci-like',
                'explanation': 'Each number = sum of previous two',
            }]
        return []
    
    def _check_polynomial(self) -> list:
        """Check for polynomial pattern via differences of differences.
        [1,4,9,16] → diffs=[3,5,7] → diffs2=[2,2] → quadratic → next=25."""
        if len(self.sequence) < 3:
            return []
        
        # Calculate successive differences
        current = list(self.sequence)
        depth = 0
        while len(current) > 1 and depth < 5:
            diffs = [current[i+1] - current[i] for i in range(len(current)-1)]
            if len(set(diffs)) == 1:
                # Found constant difference at this depth
                # Reconstruct forward
                next_val = self.sequence[-1]
                # Build from differences back up
                last_diffs = [list(self.sequence)]
                temp = list(self.sequence)
                for _ in range(depth + 1):
                    temp = [temp[i+1] - temp[i] for i in range(len(temp)-1)]
                    last_diffs.append(temp)
                
                # Extend each level by one
                for level in reversed(range(len(last_diffs) - 1)):
                    last_diffs[level].append(
                        last_diffs[level][-1] + last_diffs[level + 1][-1]
                    )
                
                pred = last_diffs[0][-1]
                degree = depth + 1
                return [{
                    'prediction': pred,
                    'confidence': max(0.5, 0.90 - depth * 0.1),
                    'method': f'Polynomial (degree {degree})',
                    'explanation': f'Differences become constant at depth {degree}',
                }]
            current = diffs
            depth += 1
        return []
    
    def _check_power(self) -> list:
        """Check for perfect powers: [1,8,27,64] → cubes → next=125."""
        if len(self.sequence) < 3 or any(x <= 0 for x in self.sequence):
            return []
        
        import math
        for exp in [2, 3, 4, 5]:  # Check squares, cubes, 4th, 5th powers
            bases = []
            valid = True
            for val in self.sequence:
                base = round(val ** (1.0 / exp))
                if base ** exp == val:
                    bases.append(base)
                else:
                    valid = False
                    break
            
            if valid and len(bases) >= 3:
                # Check if bases form an arithmetic sequence
                base_diffs = [bases[i+1] - bases[i] for i in range(len(bases)-1)]
                if len(set(base_diffs)) == 1:
                    next_base = bases[-1] + base_diffs[0]
                    return [{
                        'prediction': next_base ** exp,
                        'confidence': 0.91,
                        'method': f'Power sequence (n^{exp})',
                        'explanation': f'Base sequence [{",".join(str(b) for b in bases)}] with step {base_diffs[0]}',
                    }]
        return []
    
    def _check_fc60_pattern(self) -> list:
        """Check for patterns in the FC60 token sequence."""
        from engines.fc60 import token60, ANIMALS, ELEMENTS
        
        if len(self.sequence) < 3:
            return []
        
        # Get FC60 tokens for each number
        tokens = [(n % 60, (n % 60) // 5, (n % 60) % 5) for n in self.sequence]
        animal_indices = [t[1] for t in tokens]
        element_indices = [t[2] for t in tokens]
        
        predictions = []
        
        # Check if animal indices form arithmetic sequence
        animal_diffs = [animal_indices[i+1] - animal_indices[i] for i in range(len(animal_indices)-1)]
        if len(set(animal_diffs)) == 1 and animal_diffs[0] != 0:
            next_animal = (animal_indices[-1] + animal_diffs[0]) % 12
            # Predict: keep same element, advance animal
            next_token_val = next_animal * 5 + element_indices[-1]
            # Find a number near the sequence that has this token
            last = self.sequence[-1]
            for offset in range(0, 120):
                candidate = last + offset
                if candidate % 60 == next_token_val:
                    predictions.append({
                        'prediction': candidate,
                        'confidence': 0.50,
                        'method': 'FC60 animal cycle',
                        'explanation': f'Animals advance by {animal_diffs[0]}: {ANIMALS[next_animal]}',
                    })
                    break
        
        # Check if element indices cycle
        element_diffs = [element_indices[i+1] - element_indices[i] for i in range(len(element_indices)-1)]
        if len(set(element_diffs)) == 1 and element_diffs[0] != 0:
            next_element = (element_indices[-1] + element_diffs[0]) % 5
            predictions.append({
                'prediction': self.sequence[-1] + (self.sequence[-1] - self.sequence[-2]),
                'confidence': 0.40,
                'method': 'FC60 element cycle',
                'explanation': f'Elements advance by {element_diffs[0]}: {ELEMENTS[next_element]}',
            })
        
        return predictions
    
    def get_name(self):
        return "Number Oracle"
    
    def get_description(self):
        return f"Sequence: {self.sequence}"
```

---

### FIX 10: Date Solver — Prediction Logic

```python
# solvers/date_solver.py

class DateSolver(BaseSolver):
    
    def __init__(self, dates: list, callback=None):
        """dates: list of date strings like ['2026-02-06', '2026-03-14']."""
        super().__init__(callback)
        self.date_strings = dates
    
    def solve(self):
        from engines.fc60 import (encode_fc60, format_full_output, compute_jdn,
            moon_phase, ganzhi_year, weekday_from_jdn, jdn_to_gregorian,
            MOON_PHASE_NAMES, WEEKDAY_NAMES, ANIMALS)
        from engines.scoring import hybrid_score
        
        # Parse all dates
        parsed = []
        for ds in self.date_strings:
            parts = ds.strip().split('-')
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            fc60_result = encode_fc60(y, m, d, include_time=False)
            jdn = compute_jdn(y, m, d)
            phase_idx, moon_age = moon_phase(jdn)
            wd = weekday_from_jdn(jdn)
            parsed.append({
                'date_str': ds, 'year': y, 'month': m, 'day': d,
                'jdn': jdn, 'fc60': fc60_result,
                'moon_phase': phase_idx, 'weekday': wd,
                'fc60_output': format_full_output(fc60_result),
            })
        
        # Single date: just analyze
        analyses = [p['fc60_output'] for p in parsed]
        
        # Multi-date: find patterns + predict
        patterns = []
        predictions = []
        
        if len(parsed) >= 2:
            # Pattern: same weekday?
            weekdays = [p['weekday'] for p in parsed]
            if len(set(weekdays)) == 1:
                patterns.append(f"All dates fall on {WEEKDAY_NAMES[weekdays[0]]}")
            
            # Pattern: same moon phase?
            phases = [p['moon_phase'] for p in parsed]
            if len(set(phases)) == 1:
                patterns.append(f"All dates fall on {MOON_PHASE_NAMES[phases[0]]}")
            
            # Pattern: same month-animal?
            month_animals = [ANIMALS[p['month']-1] for p in parsed]
            if len(set(month_animals)) == 1:
                patterns.append(f"All dates in {month_animals[0]}-month energy")
            
            # Pattern: intervals
            jdns = sorted([p['jdn'] for p in parsed])
            intervals = [jdns[i+1] - jdns[i] for i in range(len(jdns)-1)]
            if len(set(intervals)) == 1 and intervals[0] > 0:
                patterns.append(f"Constant interval: {intervals[0]} days")
                # Predict next date at same interval
                next_jdn = jdns[-1] + intervals[0]
                ny, nm, nd = jdn_to_gregorian(next_jdn)
                predictions.append({
                    'date': f"{ny:04d}-{nm:02d}-{nd:02d}",
                    'reason': f"Same interval ({intervals[0]} days)",
                    'jdn': next_jdn,
                })
            
            # Predict: next date matching detected moon phase pattern
            if len(set(phases)) == 1:
                target_phase = phases[0]
                last_jdn = max(jdns)
                for offset in range(1, 60):
                    check_jdn = last_jdn + offset
                    check_phase, _ = moon_phase(check_jdn)
                    if check_phase == target_phase:
                        ny, nm, nd = jdn_to_gregorian(check_jdn)
                        predictions.append({
                            'date': f"{ny:04d}-{nm:02d}-{nd:02d}",
                            'reason': f"Next {MOON_PHASE_NAMES[target_phase]}",
                            'jdn': check_jdn,
                        })
                        break
            
            # Predict: next date matching weekday pattern
            if len(set(weekdays)) == 1:
                target_wd = weekdays[0]
                last_jdn = max(jdns)
                # Next occurrence of same weekday = 7 days later
                next_jdn = last_jdn + 7
                ny, nm, nd = jdn_to_gregorian(next_jdn)
                predictions.append({
                    'date': f"{ny:04d}-{nm:02d}-{nd:02d}",
                    'reason': f"Next {WEEKDAY_NAMES[target_wd]}",
                    'jdn': next_jdn,
                })
        
        # Score predictions
        for pred in predictions:
            jdn_score = hybrid_score(pred['jdn'])
            pred['harmony_score'] = jdn_score['final_score']
            pred['fc60_token'] = jdn_score['fc60_token']
        
        predictions.sort(key=lambda p: p.get('harmony_score', 0), reverse=True)
        
        self._emit({
            'status': 'solved',
            'message': f'{len(analyses)} dates analyzed, {len(patterns)} patterns, {len(predictions)} predictions',
            'progress': 100,
            'candidates_tested': len(parsed),
            'candidates_total': len(parsed),
            'current_best': predictions[0] if predictions else None,
            'solution': {
                'analyses': analyses,
                'patterns': patterns,
                'predictions': predictions,
            },
        })
    
    def get_name(self):
        return "Date Decoder"
    
    def get_description(self):
        return f"Analyzing {len(self.date_strings)} date(s)"
```

---

### FIX 11: Pearson Correlation Implementation

Add to `engines/learning.py`:

```python
def pearson_correlation() -> float:
    """
    Calculate Pearson correlation between final_score and was_correct.
    Returns float from -1.0 to 1.0.
    > 0 means higher scores correlate with correct answers (good!)
    = 0 means no correlation (scoring isn't helping)
    < 0 means inverse correlation (scoring is hurting — rare)
    
    Returns 0.0 if not enough data.
    """
    history = _load_history()
    if len(history) < MIN_SOLVES_FOR_LEARNING:
        return 0.0
    
    scores = [r.get('final_score', 0.5) for r in history]
    correct = [1.0 if r.get('was_correct') else 0.0 for r in history]
    
    n = len(scores)
    mean_s = sum(scores) / n
    mean_c = sum(correct) / n
    
    numerator = sum((scores[i] - mean_s) * (correct[i] - mean_c) for i in range(n))
    denom_s = math.sqrt(sum((scores[i] - mean_s) ** 2 for i in range(n)))
    denom_c = math.sqrt(sum((correct[i] - mean_c) ** 2 for i in range(n)))
    
    if denom_s == 0 or denom_c == 0:
        return 0.0
    
    return numerator / (denom_s * denom_c)
```

---

### FIX 12: CSV Export Implementation

Add to `engines/learning.py`:

```python
def export_history_csv(filepath: str = None) -> str:
    """
    Export solve history to CSV file.
    Returns the filepath written to.
    """
    import csv
    
    if filepath is None:
        filepath = str(DATA_DIR / "solve_history.csv")
    
    history = _load_history()
    if not history:
        return filepath
    
    # Flatten nested dicts for CSV
    fieldnames = [
        'puzzle_type', 'candidate', 'final_score', 'math_score',
        'numerology_score', 'was_correct', 'fc60_token', 'reduced_number',
        'is_master',
    ]
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(history)
    
    return filepath
```

---

### FIX 13: Reset Button Behavior

The "Reset" button on the Validation Dashboard:

```python
def reset_learning_data():
    """
    Delete all learning data. Called by Validation Dashboard reset button.
    Requires user confirmation in GUI before calling.
    
    Deletes:
    - solve_history.json (all solve records)
    - factor_weights.json (learned weights → back to defaults)
    
    Does NOT delete:
    - session_log.json (current session)
    - nps.log (application log)
    """
    _ensure_data_dir()
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
    if WEIGHTS_FILE.exists():
        WEIGHTS_FILE.unlink()
    logger.info("Learning data reset by user")
```

In the GUI, always show a confirmation dialog first:
```python
if messagebox.askyesno("Reset Learning Data",
    "This will delete ALL solve history and learned weights.\n"
    "The scoring engine will restart from scratch.\n\n"
    "Are you sure?"):
    learning.reset_learning_data()
```

---

### FIX 14: README.md Content

```markdown
# NPS — Numerology Puzzle Solver

A desktop puzzle-solving app that combines **numerology** (FC60 + Pythagorean + Chinese Calendar + Lunar) with **mathematical analysis** to explore and solve puzzles.

## Quick Start

python main.py

**Requirements:** Python 3.8+ with tkinter (included on Windows/Mac).

Ubuntu/Debian — if tkinter is missing:
sudo apt install python3-tk

## Features

| Tab | What It Does |
|-----|-------------|
| **Dashboard** | Current moment FC60 reading, solve stats, learning engine status |
| **BTC Hunter** | Bitcoin puzzle solver with 3 strategies (Lightning/Mystic/Hybrid) |
| **Number Oracle** | Predict next number in a sequence using math + FC60 patterns |
| **Name Cipher** | Full numerology profile from name + birthday |
| **Date Decoder** | FC60 analysis of dates + pattern detection + prediction |
| **Validation** | Honest dashboard showing whether scoring actually helps |

## How It Works

1. Every puzzle candidate gets translated into FC60 symbolic tokens (animals + elements)
2. A hybrid scoring engine rates each candidate on math patterns + numerology + learned history
3. Solvers try the highest-scored candidates first
4. A learning engine tracks what works and adjusts weights over time
5. A validation dashboard honestly shows whether scoring improves results

## Project Structure

nps/
├── main.py                # Launch the app
├── engines/               # Core computation (FC60, numerology, math, scoring, learning)
├── solvers/               # Puzzle solvers (BTC, number, name, date)
├── gui/                   # Tkinter interface (tabs, widgets, theme)
├── data/                  # JSON storage (created automatically)
├── tests/                 # Test suite
├── BLUEPRINT.md           # Full technical specification
└── README.md              # This file

## Running Tests

python -m unittest discover tests/ -v

## Credits

- FC60 specification by Dave (FC60-v2.0, 2026)
- Pythagorean numerology system (ancient, adapted)
- Bitcoin Puzzle by anonymous (2015)
- Pollard's Kangaroo by John Pollard (1978)
- secp256k1 curve by Certicom Research
```

---

### FIX 15: Digit Balance Function Access

The `math_analysis.py` blueprint uses `digit_balance` as a function but only returns it inside `math_profile()`. Make sure it's also a standalone function:

```python
# This function IS already specified in section 4.3 — just confirm it's importable:
# In engines/math_analysis.py, digit_balance(n) is a standalone function (not nested).
# The learning.py fix (FIX 2) imports it directly:
#   from engines.math_analysis import entropy, digit_balance
# This works because digit_balance is defined at module level.
```

---

### FIX 16: Name Solver Implementation

```python
# solvers/name_solver.py

class NameSolver(BaseSolver):
    
    def __init__(self, name: str, birth_year=None, birth_month=None,
                 birth_day=None, mother_name=None, callback=None):
        super().__init__(callback)
        self.name = name
        self.birth_year = birth_year
        self.birth_month = birth_month
        self.birth_day = birth_day
        self.mother_name = mother_name
    
    def solve(self):
        from engines.numerology import (
            name_to_number, name_soul_urge, name_personality,
            life_path, personal_year, numerology_reduce,
            LETTER_VALUES, LIFE_PATH_MEANINGS, generate_personal_reading
        )
        from engines.fc60 import encode_fc60, format_full_output, token60
        from datetime import datetime
        
        result = {}
        
        # Core name numbers
        result['expression'] = name_to_number(self.name)
        result['soul_urge'] = name_soul_urge(self.name)
        result['personality'] = name_personality(self.name)
        
        # Meanings
        for key in ['expression', 'soul_urge', 'personality']:
            val = result[key]
            title, msg = LIFE_PATH_MEANINGS.get(val, ("Unknown", ""))
            result[f'{key}_meaning'] = f"{val} — {title}: {msg}"
        
        # Letter breakdown
        breakdown = []
        for char in self.name.upper():
            if char.isalpha():
                val = LETTER_VALUES.get(char, 0)
                breakdown.append(f"{char}({val})")
        result['letter_breakdown'] = " + ".join(breakdown)
        result['letter_sum'] = sum(LETTER_VALUES.get(c, 0) for c in self.name.upper())
        
        # FC60 of expression number
        result['fc60_token'] = token60(result['expression'] % 60)
        
        # Life path (if DOB provided)
        if self.birth_year and self.birth_month and self.birth_day:
            lp = life_path(self.birth_year, self.birth_month, self.birth_day)
            result['life_path'] = lp
            title, msg = LIFE_PATH_MEANINGS.get(lp, ("Unknown", ""))
            result['life_path_meaning'] = f"{lp} — {title}: {msg}"
            
            now = datetime.now()
            py = personal_year(self.birth_month, self.birth_day, now.year)
            result['personal_year'] = py
            py_title, py_msg = LIFE_PATH_MEANINGS.get(py, ("Unknown", ""))
            result['personal_year_meaning'] = f"{py} — {py_title}: {py_msg}"
            
            # Birth FC60
            birth_fc60 = encode_fc60(self.birth_year, self.birth_month,
                                     self.birth_day, include_time=False)
            result['birth_fc60'] = format_full_output(birth_fc60)
            result['birth_weekday'] = birth_fc60['weekday_name']
            result['birth_planet'] = birth_fc60['weekday_planet']
            result['birth_domain'] = birth_fc60['weekday_domain']
            result['birth_gz'] = birth_fc60['gz_name']
            
            # Full personal reading
            result['full_reading'] = generate_personal_reading(
                self.name, self.birth_year, self.birth_month, self.birth_day,
                now.year, now.month, now.day, now.hour, now.minute,
                mother_name=self.mother_name
            )
        
        # Mother's name analysis
        if self.mother_name:
            result['mother_number'] = name_to_number(self.mother_name)
            mt, mm = LIFE_PATH_MEANINGS.get(result['mother_number'], ("Unknown", ""))
            result['mother_meaning'] = f"{result['mother_number']} — {mt}: {mm}"
        
        self._emit({
            'status': 'solved',
            'message': f'Analysis complete for "{self.name}"',
            'progress': 100,
            'candidates_tested': 1,
            'candidates_total': 1,
            'current_best': result,
            'solution': result,
        })
    
    def get_name(self):
        return "Name Cipher"
    
    def get_description(self):
        return f'Analyzing "{self.name}"'
```

---

### FIX 17: Widget — ScoreBar Color Logic

Add explicit color-tier logic so the GUI doesn't have to figure it out:

```python
# gui/widgets.py — ScoreBar color selection

def score_color(score: float) -> str:
    """Return the appropriate color hex for a harmony score."""
    from gui.theme import COLORS
    if score >= 0.8:
        return COLORS['score_peak']    # Gold — exceptional
    elif score >= 0.6:
        return COLORS['score_high']    # Green — good
    elif score >= 0.3:
        return COLORS['score_mid']     # Amber — moderate
    else:
        return COLORS['score_low']     # Red — low


def score_dots(score: float) -> str:
    """Return dot indicator for score: ●●● or ●●○ or ●○○ or ○○○."""
    if score >= 0.75:
        return "●●●"
    elif score >= 0.50:
        return "●●○"
    elif score >= 0.25:
        return "●○○"
    else:
        return "○○○"
```

---

## END OF ADDENDUM A

**Summary of fixes applied:**
- 2 missing functions added (detect_animal_repetitions, get_time_context)
- 1 critical circular import resolved (lazy imports)
- 1 division-by-zero fixed
- 4 complete solver implementations written (BTC, Number, Name, Date)
- 1 implementation order specified (26 steps in 4 phases)
- 5 missing specs written (__init__.py, README, CSV export, reset, Pearson)
- 2 infrastructure gaps filled (shutdown handling, logging)
- 1 widget helper added (score color logic)

**Total blueprint size after addendum: ~3,600 lines of specification.**
