"""
Unified Hunter — One solver that combines puzzle + scanner modes.

Merges BTC puzzle solving and multi-chain scanning into a single solver
with a unified start/stop, optional puzzle mode, checkpoints for crash
recovery, and vault integration.
"""

import json
import logging
import os
import time
import threading
from pathlib import Path

from solvers.base_solver import BaseSolver

logger = logging.getLogger(__name__)

CHECKPOINT_DIR = Path(__file__).parent.parent / "data" / "checkpoints"
CHECKPOINT_EVERY = 100_000  # keys between checkpoints


class UnifiedSolver(BaseSolver):
    """Combined puzzle + scanner solver with checkpoint support."""

    def __init__(
        self,
        mode="random_key",
        puzzle_enabled=False,
        puzzle_number=None,
        strategy="hybrid",
        chains=None,
        tokens=None,
        online_check=False,
        check_every_n=5000,
        use_brain=False,
        terminal_id=None,
        callback=None,
    ):
        super().__init__(callback)
        self.mode = mode  # random_key, seed_phrase, both
        self.puzzle_enabled = puzzle_enabled
        self.puzzle_number = puzzle_number
        self.strategy = strategy
        self.chains = chains or ["btc", "eth"]
        self.tokens = tokens or ["USDT", "USDC"]
        self.online_check = online_check
        self.check_every_n = check_every_n
        self.use_brain = use_brain
        self.terminal_id = terminal_id or f"terminal_{int(time.time())}"

        # Stats
        self._keys_tested = 0
        self._seeds_tested = 0
        self._hits = 0
        self._online_checks = 0
        self._high_score = 0.0
        self._paused = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # not paused initially
        self._stats_lock = threading.Lock()
        self._last_emit = 0

        # Puzzle range
        self._puzzle_range = None
        if puzzle_enabled and puzzle_number:
            try:
                from engines.crypto import PUZZLES

                puzzle = PUZZLES.get(puzzle_number)
                if puzzle:
                    self._puzzle_range = (puzzle["start"], puzzle["end"])
            except Exception:
                pass

    def get_name(self):
        parts = [f"Unified-{self.mode}"]
        if self.puzzle_enabled:
            parts.append(f"P{self.puzzle_number}")
        return " ".join(parts)

    def get_description(self):
        desc = f"Unified {self.mode} scanner"
        if self.puzzle_enabled:
            desc += f" + Puzzle #{self.puzzle_number}"
        return desc

    def solve(self):
        """Main solve loop — dispatches to mode-specific method."""
        # Start vault session
        try:
            from engines.vault import start_session

            start_session(f"unified_{self.mode}_{self.terminal_id}")
        except Exception:
            pass

        if self.mode == "random_key":
            self._scan_random_keys()
        elif self.mode == "seed_phrase":
            self._scan_seed_phrases()
        elif self.mode == "both":
            self._scan_both()

    def _scan_random_keys(self):
        """Generate random private keys, check puzzle + balance."""
        from engines.bip39 import generate_random_keys_batch, privkey_to_all_addresses

        batch_size = 1000
        check_counter = 0

        while self.running:
            self._pause_event.wait()
            if not self.running:
                break

            keys = generate_random_keys_batch(batch_size)
            feed_entries = []

            for key_int in keys:
                if not self.running:
                    break
                self._pause_event.wait()

                # Puzzle check
                if self.puzzle_enabled and self._puzzle_range:
                    start, end = self._puzzle_range
                    key_int = start + (key_int % (end - start))
                    self._check_puzzle(key_int)

                # Derive addresses
                addrs = privkey_to_all_addresses(key_int)
                with self._stats_lock:
                    self._keys_tested += 1
                    check_counter += 1

                # Build feed entry
                entry = {
                    "source": "random_key",
                    "addresses": addrs,
                    "has_balance": False,
                }
                feed_entries.append(entry)

                # Online balance check
                if self.online_check and check_counter >= self.check_every_n:
                    check_counter = 0
                    self._check_balance_online(addrs, hex(key_int))

                # Checkpoint
                if self._keys_tested % CHECKPOINT_EVERY == 0:
                    self.save_checkpoint()

            self._emit_progress(feed_entries[-10:] if feed_entries else [])

    def _scan_seed_phrases(self):
        """Generate BIP39 seed phrases, derive addresses, check balance."""
        from engines.bip39 import generate_mnemonic, mnemonic_to_seed, derive_all_chains

        check_counter = 0

        while self.running:
            self._pause_event.wait()
            if not self.running:
                break

            mnemonic = generate_mnemonic(128)
            seed = mnemonic_to_seed(mnemonic)
            derived = derive_all_chains(seed, count=5)

            # derived = {"btc": [list of dicts], "eth": [list of dicts]}
            btc_list = derived.get("btc", [])
            eth_list = derived.get("eth", [])
            count = max(len(btc_list), len(eth_list))

            feed_entries = []
            for i in range(count):
                if not self.running:
                    break

                addrs = {}
                if i < len(btc_list):
                    addrs["btc"] = btc_list[i].get("address", "")
                if i < len(eth_list):
                    addrs["eth"] = eth_list[i].get("address", "")

                with self._stats_lock:
                    self._keys_tested += 1
                    check_counter += 1

                entry = {
                    "source": "seed_phrase",
                    "addresses": addrs,
                    "has_balance": False,
                    "mnemonic": mnemonic,
                }
                feed_entries.append(entry)

                if self.online_check and check_counter >= self.check_every_n:
                    check_counter = 0
                    self._check_balance_online(addrs, mnemonic)

            with self._stats_lock:
                self._seeds_tested += 1

            if self._keys_tested % CHECKPOINT_EVERY == 0:
                self.save_checkpoint()

            self._emit_progress(feed_entries[-5:] if feed_entries else [])

    def _scan_both(self):
        """Alternate between random keys and seed phrases."""
        from engines.bip39 import (
            generate_random_keys_batch,
            privkey_to_all_addresses,
            generate_mnemonic,
            mnemonic_to_seed,
            derive_all_chains,
        )

        batch_size = 500
        check_counter = 0
        use_seeds = False

        while self.running:
            self._pause_event.wait()
            if not self.running:
                break

            feed_entries = []

            if use_seeds:
                mnemonic = generate_mnemonic(128)
                seed = mnemonic_to_seed(mnemonic)
                derived = derive_all_chains(seed, count=5)

                btc_list = derived.get("btc", [])
                eth_list = derived.get("eth", [])
                count = max(len(btc_list), len(eth_list))

                for i in range(count):
                    if not self.running:
                        break
                    addrs = {}
                    if i < len(btc_list):
                        addrs["btc"] = btc_list[i].get("address", "")
                    if i < len(eth_list):
                        addrs["eth"] = eth_list[i].get("address", "")

                    with self._stats_lock:
                        self._keys_tested += 1
                        check_counter += 1

                    feed_entries.append(
                        {
                            "source": "seed_phrase",
                            "addresses": addrs,
                            "has_balance": False,
                        }
                    )

                    if self.online_check and check_counter >= self.check_every_n:
                        check_counter = 0
                        self._check_balance_online(addrs, mnemonic)

                with self._stats_lock:
                    self._seeds_tested += 1
            else:
                keys = generate_random_keys_batch(batch_size)
                for key_int in keys:
                    if not self.running:
                        break
                    self._pause_event.wait()

                    if self.puzzle_enabled and self._puzzle_range:
                        start, end = self._puzzle_range
                        key_int = start + (key_int % (end - start))
                        self._check_puzzle(key_int)

                    addrs = privkey_to_all_addresses(key_int)
                    with self._stats_lock:
                        self._keys_tested += 1
                        check_counter += 1

                    feed_entries.append(
                        {
                            "source": "random_key",
                            "addresses": addrs,
                            "has_balance": False,
                        }
                    )

                    if self.online_check and check_counter >= self.check_every_n:
                        check_counter = 0
                        self._check_balance_online(addrs, hex(key_int))

            use_seeds = not use_seeds

            if self._keys_tested % CHECKPOINT_EVERY == 0:
                self.save_checkpoint()

            self._emit_progress(feed_entries[-10:] if feed_entries else [])

    def _check_puzzle(self, key_int):
        """Check if a key solves the puzzle."""
        if not self.puzzle_enabled or not self.puzzle_number:
            return

        try:
            from engines.scoring import hybrid_score

            score_result = hybrid_score(key_int)
            score = score_result.get("total_score", 0)

            with self._stats_lock:
                if score > self._high_score:
                    self._high_score = score
                    self._emit(
                        {
                            "type": "high_score",
                            "score": score,
                            "key": hex(key_int),
                        }
                    )
        except Exception:
            pass

    def _check_balance_online(self, addresses, private_key_str):
        """Online balance check for an address set."""
        with self._stats_lock:
            self._online_checks += 1

        try:
            from engines.balance import check_all_balances

            btc_addr = addresses.get("btc")
            eth_addr = addresses.get("eth")
            result = check_all_balances(
                btc_address=btc_addr,
                eth_address=eth_addr,
                tokens=self.tokens,
                chains=self.chains,
            )

            if result.get("has_any_balance"):
                with self._stats_lock:
                    self._hits += 1

                try:
                    from engines.vault import record_finding

                    for chain in self.chains:
                        chain_result = result.get(chain)
                        if chain_result and chain_result.get("has_balance"):
                            finding = {
                                "address": chain_result.get("address", ""),
                                "private_key": private_key_str,
                                "chain": chain,
                                "balance": chain_result,
                                "source": f"unified_{self.mode}",
                            }
                            record_finding(finding)
                            try:
                                from engines.events import emit, FINDING_FOUND

                                emit(FINDING_FOUND, finding)
                            except Exception:
                                pass
                except Exception:
                    pass

                # Award XP for balance hit
                try:
                    from engines.learner import add_xp

                    add_xp(50, "balance_hit")
                except Exception:
                    pass

                try:
                    from engines.notifier import notify_scanner_hit, is_configured

                    if is_configured():
                        notify_scanner_hit(
                            addresses, private_key_str, result, f"unified_{self.mode}"
                        )
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Online balance check failed: {e}")

    def _emit_progress(self, feed_entries):
        """Send throttled progress update to callback."""
        now = time.time()
        if now - self._last_emit < 0.1:
            return
        self._last_emit = now

        with self._stats_lock:
            elapsed = now - self.start_time if self.start_time else 0
            speed = self._keys_tested / max(0.001, elapsed)

        self._emit(
            {
                "status": "running",
                "keys_tested": self._keys_tested,
                "seeds_tested": self._seeds_tested,
                "speed": speed,
                "hits": self._hits,
                "online_checks": self._online_checks,
                "high_score": self._high_score,
                "live_feed": feed_entries,
                "paused": self._paused,
            }
        )

    def pause(self):
        """Pause the solver (keeps thread alive)."""
        self._paused = True
        self._pause_event.clear()
        logger.info(f"Unified solver {self.terminal_id} paused")

    def resume(self):
        """Resume a paused solver."""
        self._paused = False
        self._pause_event.set()
        logger.info(f"Unified solver {self.terminal_id} resumed")

    def stop(self):
        """Stop the solver, save checkpoint, flush vault."""
        self._pause_event.set()  # unblock if paused
        self.save_checkpoint()

        try:
            from engines.vault import shutdown as vault_shutdown

            vault_shutdown()
        except Exception:
            pass

        super().stop()

    def get_stats(self):
        """Return current solver stats."""
        with self._stats_lock:
            elapsed = time.time() - self.start_time if self.start_time else 0
            speed = self._keys_tested / max(0.001, elapsed)
            return {
                "keys_tested": self._keys_tested,
                "seeds_tested": self._seeds_tested,
                "speed": speed,
                "hits": self._hits,
                "online_checks": self._online_checks,
                "high_score": self._high_score,
                "elapsed": elapsed,
                "paused": self._paused,
                "mode": self.mode,
                "puzzle_enabled": self.puzzle_enabled,
                "puzzle_number": self.puzzle_number,
                "terminal_id": self.terminal_id,
                "chains": self.chains,
            }

    # ── Checkpoint System ──

    def save_checkpoint(self):
        """Save current state to disk for crash recovery."""
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "terminal_id": self.terminal_id,
            "mode": self.mode,
            "puzzle_enabled": self.puzzle_enabled,
            "puzzle_number": self.puzzle_number,
            "strategy": self.strategy,
            "chains": self.chains,
            "tokens": self.tokens,
            "keys_tested": self._keys_tested,
            "seeds_tested": self._seeds_tested,
            "hits": self._hits,
            "online_checks": self._online_checks,
            "high_score": self._high_score,
            "timestamp": time.time(),
            "use_brain": self.use_brain,
            "online_check": self.online_check,
            "check_every_n": self.check_every_n,
        }

        path = CHECKPOINT_DIR / f"{self.terminal_id}.json"
        tmp_path = path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w") as f:
                json.dump(checkpoint, f, indent=2)
            os.replace(str(tmp_path), str(path))
            logger.debug(f"Checkpoint saved: {self.terminal_id}")
            try:
                from engines.events import emit, CHECKPOINT_SAVED

                emit(
                    CHECKPOINT_SAVED,
                    {"terminal_id": self.terminal_id, "path": str(path)},
                )
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Checkpoint save failed: {e}")

    @classmethod
    def resume_from_checkpoint(cls, path, callback=None):
        """Create a UnifiedSolver from a saved checkpoint."""
        with open(path) as f:
            cp = json.load(f)

        solver = cls(
            mode=cp.get("mode", "random_key"),
            puzzle_enabled=cp.get("puzzle_enabled", False),
            puzzle_number=cp.get("puzzle_number"),
            strategy=cp.get("strategy", "hybrid"),
            chains=cp.get("chains", ["btc", "eth"]),
            tokens=cp.get("tokens", ["USDT", "USDC"]),
            online_check=cp.get("online_check", False),
            check_every_n=cp.get("check_every_n", 5000),
            use_brain=cp.get("use_brain", False),
            terminal_id=cp.get("terminal_id"),
            callback=callback,
        )

        # Restore stats
        solver._keys_tested = cp.get("keys_tested", 0)
        solver._seeds_tested = cp.get("seeds_tested", 0)
        solver._hits = cp.get("hits", 0)
        solver._online_checks = cp.get("online_checks", 0)
        solver._high_score = cp.get("high_score", 0.0)

        logger.info(
            f"Resumed from checkpoint: {solver.terminal_id} "
            f"({solver._keys_tested:,} keys)"
        )
        return solver

    @staticmethod
    def list_checkpoints():
        """List available checkpoint files."""
        if not CHECKPOINT_DIR.exists():
            return []
        return sorted(CHECKPOINT_DIR.glob("*.json"))
