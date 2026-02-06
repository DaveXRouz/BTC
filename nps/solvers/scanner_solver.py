"""
Multi-chain scanner solver with 3 modes: random_key, seed_phrase, both.

Generates random private keys or BIP39 mnemonics, derives BTC+ETH addresses,
checks against a local rich address list, and periodically checks online balances.
Emits live_feed batches for the GUI and records hits to disk + Telegram.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path

from solvers.base_solver import BaseSolver

logger = logging.getLogger(__name__)

MODES = ["random_key", "seed_phrase", "both"]

# Module-level rich address cache
_RICH_SET = None
_rich_lock = threading.Lock()


def _load_rich_list():
    """Load rich addresses into a set. Cached at module level."""
    global _RICH_SET
    with _rich_lock:
        if _RICH_SET is not None:
            return _RICH_SET
        _RICH_SET = set()
        rich_path = Path(__file__).parent.parent / "data" / "rich_addresses.txt"
        if rich_path.exists():
            with open(rich_path) as f:
                for line in f:
                    addr = line.strip()
                    if addr and not addr.startswith("#"):
                        _RICH_SET.add(addr)
            logger.info(f"Loaded {len(_RICH_SET)} rich addresses")
        else:
            logger.warning("Rich addresses file not found")
        return _RICH_SET


class ScannerSolver(BaseSolver):
    """Multi-chain address scanner with random keys, seed phrases, or both."""

    def __init__(
        self,
        mode="random_key",
        callback=None,
        check_balance_online=True,
        use_scoring=True,
        chains=None,
        tokens=None,
    ):
        super().__init__(callback)
        if mode not in MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {MODES}")

        self.mode = mode
        self.check_balance_online = check_balance_online
        self.use_scoring = use_scoring

        # Load config
        try:
            from engines.config import load_config, get

            load_config()
            self.batch_size = get("scanner.batch_size", 1000)
            self.check_every_n = get("scanner.check_every_n", 5000)
            self.addresses_per_seed = get("scanner.addresses_per_seed", 5)
            default_chains = get("scanner.chains", ["btc", "eth"])
        except Exception:
            self.batch_size = 1000
            self.check_every_n = 5000
            self.addresses_per_seed = 5
            default_chains = ["btc", "eth"]

        self.chains = chains if chains is not None else default_chains
        self.tokens_to_check = tokens if tokens is not None else ["USDT", "USDC"]

        # Stats
        self._tested = 0
        self._seeds_tested = 0
        self._online_checks = 0
        self._hits = 0
        self._feed_buffer = []
        self._hits_lock = threading.Lock()

        # Callback throttle
        self._last_emit_time = 0

        # AI integration
        self._last_ai_analysis_time = 0
        self._last_ai_analysis_count = 0
        self._recent_addresses = []
        self._score_distribution = []
        self._high_score_threshold = 0.7

        # Load rich list
        self._rich_set = _load_rich_list()

        # Adaptive brain
        try:
            from engines.scanner_brain import ScannerBrain

            self.brain = ScannerBrain()
        except Exception as e:
            logger.debug(f"Scanner brain init failed: {e}")
            self.brain = None

    def get_name(self):
        return "Multi-Chain Scanner"

    def get_description(self):
        return f"Scanning mode: {self.mode}"

    def solve(self):
        """Main solve dispatcher."""
        # Start vault session
        try:
            from engines.vault import start_session as vault_start

            vault_start(f"scanner_{self.mode}")
        except Exception:
            pass

        # Start brain session
        if self.brain:
            try:
                brain_config = self.brain.start_session(
                    self.mode, self.chains, self.tokens_to_check
                )
                self._emit({"status": "brain_strategy", "brain_status": brain_config})
            except Exception as e:
                logger.debug(f"Brain start_session failed: {e}")

        if self.mode == "random_key":
            self._scan_random_keys()
        elif self.mode == "seed_phrase":
            self._scan_seed_phrases()
        elif self.mode == "both":
            self._scan_both()

    def _scan_random_keys(self):
        """Generate random keys, derive BTC+ETH, check rich list + online."""
        from engines.bip39 import generate_random_keys_batch, privkey_to_all_addresses

        emit_interval = 5  # seconds between progress emissions
        last_emit = time.time()

        while self.running:
            if self.brain:
                batch = [
                    self.brain.generate_smart_key() for _ in range(self.batch_size)
                ]
            else:
                batch = generate_random_keys_batch(self.batch_size)
            feed_entries = []

            for key in batch:
                if not self.running:
                    return

                addresses = privkey_to_all_addresses(key)
                addresses = {k: v for k, v in addresses.items() if k in self.chains}
                self._tested += 1
                self._track_address(addresses.get("btc", ""))
                self._maybe_score_key(key, addresses)

                # Local rich list check (BTC only)
                local_hit = self._local_check(addresses.get("btc", ""))
                checked_online = False
                balances = {}

                # Periodic online check
                if self.check_balance_online and self._tested % self.check_every_n == 0:
                    balances = self._online_check_all(addresses)
                    checked_online = True

                if local_hit or balances.get("has_any_balance"):
                    self._record_hit(addresses, key, balances, "random_key")

                # Collect feed entry
                key_hex = hex(key) if isinstance(key, int) else str(key)
                entry = {
                    "timestamp": time.time(),
                    "type": "key",
                    "source": f"random #{self._tested}",
                    "key_hex": key_hex,
                    "addresses": addresses,
                    "balances": balances,
                    "checked_online": checked_online,
                    "has_balance": local_hit or balances.get("has_any_balance", False),
                }
                feed_entries.append(entry)

                # Record interesting findings to brain
                if self.brain and (
                    entry.get("has_balance")
                    or (self.use_scoring and entry.get("score", 0) >= 0.7)
                ):
                    self.brain.record_finding(entry)

                # Brain mid-session check every 50K keys
                if self.brain and self._tested % 50000 == 0 and self._tested > 0:
                    adjustment = self.brain.mid_session_check(self.get_stats())
                    if adjustment:
                        self._emit(
                            {"status": "brain_insight", "brain_insight": adjustment}
                        )

                # Emit intermediate progress so callbacks arrive within seconds
                now = time.time()
                if now - last_emit >= emit_interval and feed_entries:
                    self._emit_progress(feed_entries[-50:])
                    feed_entries.clear()
                    last_emit = now

            # Emit remaining feed entries at end of batch
            if feed_entries:
                self._emit_progress(feed_entries[-50:])
                last_emit = time.time()
                self._maybe_ai_analysis()

    def _scan_seed_phrases(self):
        """Generate BIP39 mnemonics, derive all chains, check addresses."""
        from engines.bip39 import generate_mnemonic, mnemonic_to_seed, derive_all_chains

        while self.running:
            mnemonic = generate_mnemonic(128)
            seed = mnemonic_to_seed(mnemonic)
            chains = derive_all_chains(seed, count=self.addresses_per_seed)
            self._seeds_tested += 1
            feed_entries = []

            for i in range(self.addresses_per_seed):
                if not self.running:
                    return

                btc_entry = chains["btc"][i] if i < len(chains["btc"]) else None
                eth_entry = chains["eth"][i] if i < len(chains["eth"]) else None

                addresses = {}
                if btc_entry:
                    addresses["btc"] = btc_entry["address"]
                if eth_entry:
                    addresses["eth"] = eth_entry["address"]
                addresses = {k: v for k, v in addresses.items() if k in self.chains}

                self._tested += 1
                self._track_address(addresses.get("btc", ""))
                local_hit = self._local_check(addresses.get("btc", ""))
                checked_online = False
                balances = {}

                # Online check every N seeds
                if (
                    self.check_balance_online
                    and self._seeds_tested % 100 == 0
                    and i == 0
                ):
                    balances = self._online_check_all(addresses)
                    checked_online = True

                if local_hit or balances.get("has_any_balance"):
                    key = (
                        btc_entry["private_key"]
                        if btc_entry
                        else eth_entry["private_key"]
                    )
                    self._record_hit(
                        addresses,
                        key,
                        balances,
                        "seed_phrase",
                        extra={"mnemonic": mnemonic, "index": i},
                    )

                privkey = (
                    btc_entry["private_key"]
                    if btc_entry
                    else (eth_entry["private_key"] if eth_entry else "")
                )
                key_hex = hex(privkey) if isinstance(privkey, int) else str(privkey)
                entry = {
                    "timestamp": time.time(),
                    "type": "seed",
                    "source": f"seed #{self._seeds_tested}/{i}",
                    "key_hex": key_hex,
                    "mnemonic": mnemonic,
                    "addresses": addresses,
                    "balances": balances,
                    "checked_online": checked_online,
                    "has_balance": local_hit or balances.get("has_any_balance", False),
                }
                feed_entries.append(entry)

            # Emit after each seed
            if feed_entries:
                self._emit_progress(feed_entries[-50:])
                self._maybe_ai_analysis()

    def _scan_both(self):
        """Alternate between random keys and seed phrases."""
        from engines.bip39 import (
            generate_random_keys_batch,
            privkey_to_all_addresses,
            generate_mnemonic,
            mnemonic_to_seed,
            derive_all_chains,
        )

        emit_interval = 5  # seconds between progress emissions
        last_emit = time.time()

        while self.running:
            # Random key batch
            if self.brain:
                batch = [
                    self.brain.generate_smart_key()
                    for _ in range(min(self.batch_size, 500))
                ]
            else:
                batch = generate_random_keys_batch(min(self.batch_size, 500))
            feed_entries = []

            for key in batch:
                if not self.running:
                    return
                addresses = privkey_to_all_addresses(key)
                addresses = {k: v for k, v in addresses.items() if k in self.chains}
                self._tested += 1
                self._track_address(addresses.get("btc", ""))
                self._maybe_score_key(key, addresses)
                local_hit = self._local_check(addresses.get("btc", ""))
                checked_online = False
                balances = {}

                if self.check_balance_online and self._tested % self.check_every_n == 0:
                    balances = self._online_check_all(addresses)
                    checked_online = True

                if local_hit or balances.get("has_any_balance"):
                    self._record_hit(addresses, key, balances, "random_key")

                key_hex = hex(key) if isinstance(key, int) else str(key)
                entry = {
                    "timestamp": time.time(),
                    "type": "key",
                    "source": f"random #{self._tested}",
                    "key_hex": key_hex,
                    "addresses": addresses,
                    "balances": balances,
                    "checked_online": checked_online,
                    "has_balance": local_hit or balances.get("has_any_balance", False),
                }
                feed_entries.append(entry)

                # Record interesting findings to brain
                if self.brain and (
                    entry.get("has_balance")
                    or (self.use_scoring and entry.get("score", 0) >= 0.7)
                ):
                    self.brain.record_finding(entry)

                # Brain mid-session check every 50K keys
                if self.brain and self._tested % 50000 == 0 and self._tested > 0:
                    adjustment = self.brain.mid_session_check(self.get_stats())
                    if adjustment:
                        self._emit(
                            {"status": "brain_insight", "brain_insight": adjustment}
                        )

                # Emit intermediate progress
                now = time.time()
                if now - last_emit >= emit_interval and feed_entries:
                    self._emit_progress(feed_entries[-50:])
                    feed_entries.clear()
                    last_emit = now

            if feed_entries:
                self._emit_progress(feed_entries[-50:])
                last_emit = time.time()
                self._maybe_ai_analysis()

            if not self.running:
                return

            # Seed phrase batch
            mnemonic = generate_mnemonic(128)
            seed = mnemonic_to_seed(mnemonic)
            chains = derive_all_chains(seed, count=self.addresses_per_seed)
            self._seeds_tested += 1

            seed_entries = []
            for i in range(self.addresses_per_seed):
                if not self.running:
                    return

                btc_entry = chains["btc"][i] if i < len(chains["btc"]) else None
                eth_entry = chains["eth"][i] if i < len(chains["eth"]) else None
                addresses = {}
                if btc_entry:
                    addresses["btc"] = btc_entry["address"]
                if eth_entry:
                    addresses["eth"] = eth_entry["address"]
                addresses = {k: v for k, v in addresses.items() if k in self.chains}

                self._tested += 1
                self._track_address(addresses.get("btc", ""))
                local_hit = self._local_check(addresses.get("btc", ""))
                balances = {}

                if local_hit:
                    key = (
                        btc_entry["private_key"]
                        if btc_entry
                        else eth_entry["private_key"]
                    )
                    self._record_hit(
                        addresses,
                        key,
                        balances,
                        "seed_phrase",
                        extra={"mnemonic": mnemonic, "index": i},
                    )

                privkey = (
                    btc_entry["private_key"]
                    if btc_entry
                    else (eth_entry["private_key"] if eth_entry else "")
                )
                key_hex_s = hex(privkey) if isinstance(privkey, int) else str(privkey)
                seed_entries.append(
                    {
                        "timestamp": time.time(),
                        "type": "seed",
                        "source": f"seed #{self._seeds_tested}/{i}",
                        "key_hex": key_hex_s,
                        "mnemonic": mnemonic,
                        "addresses": addresses,
                        "balances": balances,
                        "checked_online": False,
                        "has_balance": local_hit,
                    }
                )

            if seed_entries:
                self._emit_progress(seed_entries[-50:])
                self._maybe_ai_analysis()

    def _track_address(self, btc_address):
        """Track recent BTC addresses (rolling buffer of 20)."""
        if btc_address:
            self._recent_addresses.append(btc_address)
            if len(self._recent_addresses) > 20:
                self._recent_addresses.pop(0)

    def _maybe_ai_analysis(self):
        """Request AI scan analysis every 100K keys or 30 minutes."""
        try:
            from engines.ai_engine import is_available

            if not is_available():
                return
        except Exception:
            return

        now = time.time()
        keys_since = self._tested - self._last_ai_analysis_count
        time_since = now - self._last_ai_analysis_time

        if keys_since < 100_000 and time_since < 1800:
            return

        self._last_ai_analysis_time = now
        self._last_ai_analysis_count = self._tested

        elapsed = now - self.start_time if self.start_time else 0
        speed = self._tested / max(0.001, elapsed)

        def _do_analysis():
            try:
                from engines.ai_engine import analyze_scan_pattern

                result = analyze_scan_pattern(
                    self._tested,
                    speed,
                    self._hits,
                    list(self._recent_addresses),
                    self.mode,
                )
                if result.get("suggestion"):
                    self._emit(
                        {
                            "status": "ai_scan_insight",
                            "suggestion": result["suggestion"],
                            "confidence": result.get("confidence", 0),
                            "should_change_mode": result.get(
                                "should_change_mode", False
                            ),
                            "recommended_mode": result.get(
                                "recommended_mode", self.mode
                            ),
                        }
                    )
            except Exception as e:
                logger.debug(f"AI analysis failed: {e}")

        threading.Thread(target=_do_analysis, daemon=True).start()

    def _maybe_score_key(self, key, addresses):
        """Score a key if use_scoring is enabled. Emit high scores and request AI insight."""
        if not self.use_scoring:
            return

        try:
            from engines.scoring import hybrid_score

            score_result = hybrid_score(key)
        except Exception:
            return

        score = score_result.get("final_score", 0)
        self._score_distribution.append(score)
        try:
            from engines.memory import record_score_distribution

            record_score_distribution(score)
        except Exception:
            pass
        if len(self._score_distribution) > 1000:
            self._score_distribution.pop(0)

        if score >= self._high_score_threshold:
            self._emit(
                {
                    "status": "high_score",
                    "key": hex(key) if isinstance(key, int) else str(key),
                    "addresses": addresses,
                    "score": score,
                    "fc60_token": score_result.get("fc60_token", "----"),
                    "math_breakdown": score_result.get("math_breakdown", {}),
                    "numerology_breakdown": score_result.get(
                        "numerology_breakdown", {}
                    ),
                }
            )

            # Request AI insight in background
            def _do_insight():
                try:
                    from engines.ai_engine import (
                        is_available,
                        numerology_insight_for_key,
                    )

                    if not is_available():
                        return
                    insight = numerology_insight_for_key(key, addresses)
                    if insight.get("analysis"):
                        self._emit(
                            {
                                "status": "ai_key_insight",
                                "key": hex(key) if isinstance(key, int) else str(key),
                                "insight": insight,
                            }
                        )
                except Exception as e:
                    logger.debug(f"AI key insight failed: {e}")

            threading.Thread(target=_do_insight, daemon=True).start()

    def _local_check(self, address):
        """O(1) lookup in rich address set."""
        if not address:
            return False
        return address in self._rich_set

    def _online_check_all(self, addresses):
        """Check balances online for all chains."""
        self._online_checks += 1
        try:
            from engines.balance import check_all_balances

            result = check_all_balances(
                btc_address=addresses.get("btc"),
                eth_address=addresses.get("eth"),
                tokens=self.tokens_to_check,
            )
            return result
        except Exception as e:
            logger.debug(f"Online check failed: {e}")
            return {}

    def _record_hit(self, addresses, private_key, balance, source, extra=None):
        """Log hit to disk and send Telegram notification."""
        self._hits += 1
        key_hex = hex(private_key) if isinstance(private_key, int) else str(private_key)

        hit = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "addresses": addresses,
            "private_key": key_hex,
            "balance": balance,
            "source": source,
        }
        if extra:
            hit["extra"] = extra

        # Write to scanner_hits.json (encrypt sensitive fields)
        hits_path = Path(__file__).parent.parent / "data" / "scanner_hits.json"
        with self._hits_lock:
            try:
                hits_path.parent.mkdir(parents=True, exist_ok=True)
                # Encrypt sensitive fields before writing
                safe_hit = dict(hit)
                try:
                    from engines.security import encrypt_dict

                    safe_hit = encrypt_dict(safe_hit)
                except ImportError:
                    pass
                existing = []
                if hits_path.exists():
                    with open(hits_path) as f:
                        existing = json.load(f)
                existing.append(safe_hit)
                tmp_path = hits_path.with_suffix(".tmp")
                with open(tmp_path, "w") as f:
                    json.dump(existing, f, indent=2)
                os.replace(str(tmp_path), str(hits_path))
            except Exception as e:
                logger.error(f"Failed to write hit: {e}")

        # Telegram notification
        try:
            from engines.notifier import notify_scanner_hit, is_configured

            if is_configured():
                balances_flat = {}
                if isinstance(balance, dict):
                    if balance.get("btc", {}).get("balance_btc"):
                        balances_flat["btc"] = balance["btc"]["balance_btc"]
                    if balance.get("eth", {}).get("balance_eth"):
                        balances_flat["eth"] = balance["eth"]["balance_eth"]
                notify_scanner_hit(addresses, private_key, balances_flat, source)
        except Exception:
            pass

        # Record to memory engine
        try:
            from engines.memory import record_high_score

            record_high_score(key_hex, 0.0, addresses)
        except Exception:
            pass

        # Record to vault
        try:
            from engines.vault import record_finding

            for chain, addr in addresses.items():
                finding = {
                    "address": addr,
                    "private_key": key_hex,
                    "chain": chain,
                    "balance": (
                        balance.get(chain, {}) if isinstance(balance, dict) else balance
                    ),
                    "source": source,
                }
                if extra:
                    finding["extra"] = extra
                record_finding(finding)
        except Exception:
            pass

        logger.info(f"SCANNER HIT: {addresses} from {source}")

    def _emit_progress(self, feed_entries):
        """Send progress update to GUI via callback (throttled to 10/s max)."""
        now = time.time()
        if now - self._last_emit_time < 0.1:
            return
        self._last_emit_time = now

        elapsed = time.time() - self.start_time if self.start_time else 0
        speed = self._tested / max(0.001, elapsed)

        self._emit(
            {
                "status": "running",
                "message": f"Scanning: {self._tested:,} tested",
                "progress": -1,
                "speed": speed,
                "operations": self._tested,
                "candidates_tested": self._tested,
                "candidates_total": -1,
                "current_best": None,
                "solution": None,
                "keys_tested": self._tested,
                "seeds_tested": self._seeds_tested,
                "online_checks": self._online_checks,
                "hits": self._hits,
                "live_feed": feed_entries,
            }
        )

    def stop(self):
        """Override to record session before stopping."""
        # End brain session
        if self.brain:
            try:
                summary = self.brain.end_session(self.get_stats())
                self._emit({"status": "brain_summary", "brain_summary": summary})
            except Exception as e:
                logger.debug(f"Brain end_session failed: {e}")

        # Flush vault
        try:
            from engines.vault import shutdown as vault_shutdown

            vault_shutdown()
        except Exception:
            pass

        self._record_session()
        super().stop()

    def _record_session(self):
        """Record scan session stats to learning engine AND memory engine."""
        if self._tested == 0:
            return
        elapsed = time.time() - self.start_time if self.start_time else 0
        session = {
            "duration": elapsed,
            "mode": self.mode,
            "keys_tested": self._tested,
            "seeds_tested": self._seeds_tested,
            "hits": self._hits,
            "avg_speed": self._tested / max(0.001, elapsed),
            "online_checks": self._online_checks,
        }
        try:
            from engines.learning import record_scan_session

            record_scan_session(session)
        except Exception as e:
            logger.debug(f"Failed to record scan session to learning: {e}")
        try:
            from engines.memory import record_session

            record_session(session)
        except Exception as e:
            logger.debug(f"Failed to record scan session to memory: {e}")

    def get_stats(self):
        """Return current scanner stats dict."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            "keys_tested": self._tested,
            "seeds_tested": self._seeds_tested,
            "online_checks": self._online_checks,
            "hits": self._hits,
            "speed": self._tested / max(0.001, elapsed),
            "elapsed": elapsed,
        }
