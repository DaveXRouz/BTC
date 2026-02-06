"""
Scanner Brain — Adaptive learning engine for the multi-chain scanner.

Persists a knowledge base across sessions, selects scanning strategies
adaptively, learns patterns from findings, and uses AI for mid-session
adjustments and post-session analysis.
"""

import json
import logging
import os
import secrets
import threading
import time
import uuid
from pathlib import Path
from random import random, choice

logger = logging.getLogger(__name__)

# secp256k1 curve order
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

STRATEGIES = [
    "random",
    "numerology_guided",
    "entropy_targeted",
    "pattern_replay",
    "time_aligned",
]

KNOWLEDGE_DIR = Path(__file__).parent.parent / "data" / "scanner_knowledge"

# Score weights for strategy ranking
W_HIGH_SCORE_RATE = 0.30
W_PATTERN_RATE = 0.25
W_HIT_BONUS = 0.40
W_EFFICIENCY = 0.05


class ScannerBrain:
    """Adaptive brain that makes the scanner smarter over time."""

    def __init__(self):
        self._knowledge_dir = KNOWLEDGE_DIR
        self._strategy_log = (
            {}
        )  # {strategy_name: {runs, total_keys, high_scores, patterns, hits, last_used}}
        self._pattern_discoveries = []  # [{timestamp, key_hex, score, strategy, ...}]
        self._ai_insights = []  # [{timestamp, type, recommendation, outcome}]

        self._current_strategy = "random"
        self._current_session_id = None
        self._session_findings = []
        self._session_start_time = 0

        self._save_lock = threading.Lock()
        self._dirty = False

        self._load_knowledge()

    # ─── Session lifecycle ───

    def start_session(self, mode, chains, tokens) -> dict:
        """Initialize a new scanning session. Returns config dict for the scanner."""
        self._current_session_id = (
            f"{time.strftime('%Y-%m-%d_%H%M')}_{uuid.uuid4().hex[:6]}"
        )
        self._session_findings = []
        self._session_start_time = time.time()

        strategy = self.select_strategy()
        self._current_strategy = strategy
        params = self.get_strategy_params(strategy)

        # Try AI recommendation in background (non-blocking)
        ai_rec = None
        try:
            from engines.ai_engine import is_available

            if is_available():
                ai_rec = self._get_ai_strategy_recommendation()
        except Exception:
            pass

        config = {
            "strategy": strategy,
            "params": params,
            "session_id": self._current_session_id,
            "ai_recommendation": ai_rec,
        }
        logger.info(
            f"Brain session started: {self._current_session_id} strategy={strategy}"
        )
        return config

    def end_session(self, stats) -> dict:
        """End session, save data, update strategy scores, get AI summary."""
        if not self._current_session_id:
            return {
                "session_summary": "",
                "learning_outcomes": [],
                "next_recommendations": [],
            }

        elapsed = time.time() - self._session_start_time
        session_data = {
            "session_id": self._current_session_id,
            "strategy": self._current_strategy,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "elapsed": elapsed,
            "stats": stats,
            "findings_count": len(self._session_findings),
            "findings": self._session_findings[:50],  # cap stored findings
        }

        # Update strategy log
        self._update_strategy_log(stats)

        # Save session file
        self._save_session(session_data)
        self._save_knowledge()

        # AI summary (async, returns placeholder if slow)
        summary = self._get_ai_session_summary(session_data)

        self._current_session_id = None
        return summary

    # ─── Strategy selection ───

    def select_strategy(self, exploration_rate=0.2) -> str:
        """Epsilon-greedy strategy selection with recency bonus."""
        if not self._strategy_log:
            return "numerology_guided"

        if random() < exploration_rate:
            # Explore: pick random strategy excluding most recent
            candidates = [s for s in STRATEGIES if s != self._current_strategy]
            return choice(candidates) if candidates else choice(STRATEGIES)

        # Exploit: pick strategy with highest success_score
        best_strategy = "random"
        best_score = -1.0

        for name, log in self._strategy_log.items():
            score = self._compute_strategy_score(name, log)
            if score > best_score:
                best_score = score
                best_strategy = name

        return best_strategy

    def _compute_strategy_score(self, name, log) -> float:
        """Compute success score for a strategy."""
        runs = log.get("runs", 0)
        if runs == 0:
            return 0.0

        total_keys = max(log.get("total_keys", 1), 1)
        high_scores = log.get("high_scores", 0)
        patterns = log.get("patterns", 0)
        hits = log.get("hits", 0)

        high_score_rate = high_scores / total_keys * 1000  # per 1K keys
        pattern_rate = patterns / total_keys * 1000
        hit_bonus = min(hits * 10.0, 1.0)  # cap at 1.0
        efficiency = min(total_keys / runs / 10000, 1.0)  # normalize by 10K keys/run

        score = (
            W_HIGH_SCORE_RATE * min(high_score_rate, 1.0)
            + W_PATTERN_RATE * min(pattern_rate, 1.0)
            + W_HIT_BONUS * hit_bonus
            + W_EFFICIENCY * efficiency
        )

        # Recency bonus: 1.1x if used in last 7 days
        last_used = log.get("last_used", 0)
        if time.time() - last_used < 7 * 86400:
            score *= 1.1

        return score

    def get_strategy_params(self, strategy_name) -> dict:
        """Return learned params for the given strategy."""
        params = {"strategy": strategy_name}

        if strategy_name == "numerology_guided":
            params["candidates_per_pick"] = 10
            params["min_score_threshold"] = 0.6
        elif strategy_name == "entropy_targeted":
            # Learned optimal entropy range from past findings
            params["min_entropy"] = self._learned_entropy_range()[0]
            params["max_entropy"] = self._learned_entropy_range()[1]
        elif strategy_name == "pattern_replay":
            params["reference_keys"] = self._get_high_scoring_reference_keys()
        elif strategy_name == "time_aligned":
            params["use_moon_phase"] = True
            params["use_ganzhi"] = True
            params["use_date_bias"] = True
        else:
            # random — no special params
            pass

        return params

    def generate_smart_key(self) -> int:
        """Generate a private key using the current strategy."""
        try:
            if self._current_strategy == "numerology_guided":
                return self._generate_numerology_biased_key()
            elif self._current_strategy == "entropy_targeted":
                return self._generate_entropy_targeted_key()
            elif self._current_strategy == "pattern_replay":
                return self._generate_pattern_replay_key()
            elif self._current_strategy == "time_aligned":
                return self._generate_time_aligned_key()
            else:
                return self._generate_random_key()
        except Exception as e:
            logger.debug(f"Smart key generation failed ({self._current_strategy}): {e}")
            return self._generate_random_key()

    # ─── Key generation strategies ───

    def _generate_random_key(self) -> int:
        """Pure random key (baseline)."""
        while True:
            key = secrets.randbits(256)
            if 1 <= key < N:
                return key

    def _generate_numerology_biased_key(self) -> int:
        """Generate 10 candidates, pick highest numerology score."""
        try:
            from engines.scoring import numerology_score
        except ImportError:
            return self._generate_random_key()

        candidates = []
        for _ in range(10):
            k = secrets.randbits(256)
            if 1 <= k < N:
                candidates.append(k)

        if not candidates:
            return self._generate_random_key()

        best = max(candidates, key=lambda k: numerology_score(k)[0])
        score = numerology_score(best)[0]
        return best if score >= 0.6 else candidates[0]

    def _generate_entropy_targeted_key(self) -> int:
        """Reject keys outside learned optimal entropy range."""
        lo, hi = self._learned_entropy_range()
        for _ in range(20):  # max attempts
            key = secrets.randbits(256)
            if 1 <= key < N:
                ent = self._key_entropy(key)
                if lo <= ent <= hi:
                    return key
        return self._generate_random_key()

    def _generate_pattern_replay_key(self) -> int:
        """Generate keys near previously high-scoring ranges."""
        refs = self._get_high_scoring_reference_keys()
        if not refs:
            return self._generate_random_key()

        ref = choice(refs)
        # Perturb reference key by flipping random bits
        mask = secrets.randbits(128)  # flip up to 128 low bits
        key = ref ^ mask
        if 1 <= key < N:
            return key
        return self._generate_random_key()

    def _generate_time_aligned_key(self) -> int:
        """Bias key toward current date/numerology alignment."""
        try:
            from engines.scoring import numerology_score
            from engines.numerology import numerology_reduce
        except ImportError:
            return self._generate_random_key()

        # Compute date-based seed bias
        now = time.localtime()
        date_num = now.tm_year + now.tm_mon + now.tm_mday
        date_reduced = numerology_reduce(date_num)

        candidates = []
        for _ in range(10):
            k = secrets.randbits(256)
            if 1 <= k < N:
                candidates.append(k)

        if not candidates:
            return self._generate_random_key()

        # Prefer keys whose digit sum reduces to match the date number
        def alignment_score(k):
            digit_sum = sum(int(d) for d in str(k))
            reduced = numerology_reduce(digit_sum)
            base_score = numerology_score(k)[0]
            alignment = 1.0 if reduced == date_reduced else 0.0
            return base_score * 0.7 + alignment * 0.3

        best = max(candidates, key=alignment_score)
        return best

    # ─── Learning helpers ───

    def _key_entropy(self, key: int) -> float:
        """Compute a simple entropy measure for a key (digit distribution)."""
        hex_str = format(key, "064x")
        counts = {}
        for c in hex_str:
            counts[c] = counts.get(c, 0) + 1
        total = len(hex_str)
        import math

        entropy = -sum(
            (cnt / total) * math.log2(cnt / total) for cnt in counts.values()
        )
        return entropy

    def _learned_entropy_range(self) -> tuple:
        """Return (min, max) entropy from past high-scoring findings, or defaults."""
        if not self._pattern_discoveries:
            return (3.0, 4.0)  # default reasonable range for hex strings

        entropies = []
        for p in self._pattern_discoveries:
            if p.get("entropy"):
                entropies.append(p["entropy"])

        if len(entropies) < 3:
            return (3.0, 4.0)

        entropies.sort()
        # Use 10th-90th percentile
        lo_idx = max(0, len(entropies) // 10)
        hi_idx = min(len(entropies) - 1, len(entropies) * 9 // 10)
        return (entropies[lo_idx], entropies[hi_idx])

    def _get_high_scoring_reference_keys(self) -> list:
        """Return list of int keys from past high-scoring findings."""
        refs = []
        for p in self._pattern_discoveries[-100:]:  # last 100
            key_hex = p.get("key_hex", "")
            if key_hex:
                try:
                    refs.append(int(key_hex, 16))
                except (ValueError, TypeError):
                    pass
        return refs[:20]  # cap at 20 reference keys

    # ─── During-scan learning ───

    def record_finding(self, entry) -> None:
        """Buffer interesting entries (score>=0.7, rich list match, etc.)."""
        finding = {
            "timestamp": time.time(),
            "key_hex": entry.get("key_hex", ""),
            "addresses": entry.get("addresses", {}),
            "has_balance": entry.get("has_balance", False),
            "score": entry.get("score", 0),
            "strategy": self._current_strategy,
        }

        # Compute entropy for learning
        key_hex = entry.get("key_hex", "")
        if key_hex.startswith("0x"):
            key_hex = key_hex[2:]
        if key_hex:
            try:
                finding["entropy"] = self._key_entropy(int(key_hex, 16))
            except (ValueError, TypeError):
                pass

        self._session_findings.append(finding)
        self._pattern_discoveries.append(finding)

        # Keep pattern discoveries bounded
        if len(self._pattern_discoveries) > 1000:
            self._pattern_discoveries = self._pattern_discoveries[-500:]

        self._dirty = True

    def mid_session_check(self, stats) -> dict | None:
        """Every 50K keys: optionally ask AI for adjustments."""
        try:
            from engines.ai_engine import is_available, brain_mid_session_analysis

            if not is_available():
                return None
        except ImportError:
            return None

        session_stats = {
            **stats,
            "strategy": self._current_strategy,
            "session_id": self._current_session_id,
            "findings_this_session": len(self._session_findings),
            "elapsed": time.time() - self._session_start_time,
        }

        try:
            result = brain_mid_session_analysis(session_stats)
            if result and result.get("recommendation"):
                self._ai_insights.append(
                    {
                        "timestamp": time.time(),
                        "type": "mid_session",
                        "recommendation": result.get("recommendation", ""),
                        "confidence": result.get("confidence", 0),
                    }
                )
                self._dirty = True
                return result
        except Exception as e:
            logger.debug(f"Brain mid-session check failed: {e}")

        return None

    # ─── Strategy log update ───

    def _update_strategy_log(self, stats):
        """Update strategy performance metrics after a session."""
        name = self._current_strategy
        if name not in self._strategy_log:
            self._strategy_log[name] = {
                "runs": 0,
                "total_keys": 0,
                "high_scores": 0,
                "patterns": 0,
                "hits": 0,
                "last_used": 0,
            }

        log = self._strategy_log[name]
        log["runs"] += 1
        log["total_keys"] += stats.get("keys_tested", 0)
        log["hits"] += stats.get("hits", 0)
        log["patterns"] += len(self._session_findings)
        log["high_scores"] += sum(
            1 for f in self._session_findings if f.get("score", 0) >= 0.7
        )
        log["last_used"] = time.time()
        self._dirty = True

    # ─── AI helpers ───

    def _get_ai_strategy_recommendation(self) -> str | None:
        """Ask AI which strategy to try. Returns recommendation string or None."""
        try:
            from engines.ai_engine import brain_strategy_recommendation

            history = {
                name: {
                    "runs": log.get("runs", 0),
                    "score": round(self._compute_strategy_score(name, log), 3),
                }
                for name, log in self._strategy_log.items()
            }
            result = brain_strategy_recommendation(json.dumps(history, indent=2))
            if result and result.get("reasoning"):
                return result["reasoning"]
        except Exception as e:
            logger.debug(f"AI strategy recommendation failed: {e}")
        return None

    def _get_ai_session_summary(self, session_data) -> dict:
        """Ask AI for session summary. Returns dict with summary info."""
        defaults = {
            "session_summary": f"Session {session_data['session_id']} completed. "
            f"Strategy: {session_data['strategy']}, "
            f"Findings: {session_data['findings_count']}",
            "learning_outcomes": [],
            "next_recommendations": [],
        }

        try:
            from engines.ai_engine import brain_session_summary

            result = brain_session_summary(
                json.dumps(session_data, indent=2, default=str)
            )
            if result and result.get("effectiveness"):
                return {
                    "session_summary": result.get(
                        "effectiveness", defaults["session_summary"]
                    ),
                    "learning_outcomes": result.get("key_learnings", []),
                    "next_recommendations": result.get("recommendations", []),
                }
        except Exception as e:
            logger.debug(f"AI session summary failed: {e}")

        return defaults

    # ─── Persistence ───

    def _load_knowledge(self):
        """Load knowledge base from disk."""
        self._knowledge_dir.mkdir(parents=True, exist_ok=True)
        (self._knowledge_dir / "sessions").mkdir(exist_ok=True)

        # Strategy log
        strat_path = self._knowledge_dir / "strategy_log.json"
        if strat_path.exists():
            try:
                self._strategy_log = json.loads(strat_path.read_text())
            except (json.JSONDecodeError, OSError) as e:
                logger.debug(f"Failed to load strategy log: {e}")

        # Pattern discoveries
        pattern_path = self._knowledge_dir / "pattern_discoveries.json"
        if pattern_path.exists():
            try:
                self._pattern_discoveries = json.loads(pattern_path.read_text())
            except (json.JSONDecodeError, OSError) as e:
                logger.debug(f"Failed to load pattern discoveries: {e}")

        # AI insights
        insights_path = self._knowledge_dir / "ai_insights.json"
        if insights_path.exists():
            try:
                self._ai_insights = json.loads(insights_path.read_text())
            except (json.JSONDecodeError, OSError) as e:
                logger.debug(f"Failed to load AI insights: {e}")

    def _save_knowledge(self):
        """Save knowledge base to disk (atomic: write tmp then rename)."""
        with self._save_lock:
            try:
                self._knowledge_dir.mkdir(parents=True, exist_ok=True)

                self._atomic_write(
                    self._knowledge_dir / "strategy_log.json",
                    json.dumps(self._strategy_log, indent=2),
                )
                self._atomic_write(
                    self._knowledge_dir / "pattern_discoveries.json",
                    json.dumps(self._pattern_discoveries[-500:], indent=2, default=str),
                )
                self._atomic_write(
                    self._knowledge_dir / "ai_insights.json",
                    json.dumps(self._ai_insights[-200:], indent=2, default=str),
                )
                self._dirty = False
            except Exception as e:
                logger.error(f"Failed to save knowledge: {e}")

    def _save_session(self, session_data):
        """Save individual session file."""
        sessions_dir = self._knowledge_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{session_data['session_id']}.json"
        try:
            self._atomic_write(
                sessions_dir / filename,
                json.dumps(session_data, indent=2, default=str),
            )
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def _atomic_write(self, path: Path, content: str):
        """Write content to file atomically (tmp + rename)."""
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(content)
        tmp_path.rename(path)
