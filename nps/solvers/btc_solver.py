"""BTC Puzzle Hunter solver with 4 strategies: lightning, mystic, hybrid, oracle."""

import logging
import time
from solvers.base_solver import BaseSolver
from engines.crypto import (
    PUZZLES,
    decompress_pubkey,
    pubkey_to_address,
    privkey_to_address,
    KangarooSolver,
    BruteForceSolver,
)

logger = logging.getLogger(__name__)


class BTCSolver(BaseSolver):

    SAMPLE_SIZE = 10_000

    def __init__(
        self,
        puzzle_id: int,
        strategy: str = "hybrid",
        public_key_hex: str = None,
        callback=None,
    ):
        super().__init__(callback)
        self.puzzle_id = puzzle_id
        self.strategy = strategy
        self.puzzle = PUZZLES[puzzle_id]
        self.public_key_hex = public_key_hex
        self._last_callback_time = 0

    def solve(self):
        if self.strategy == "lightning":
            self._solve_lightning()
        elif self.strategy == "mystic":
            self._solve_mystic()
        elif self.strategy == "hybrid":
            self._solve_hybrid()
        elif self.strategy == "oracle":
            self._solve_oracle()
        else:
            self._emit(
                {"status": "error", "message": f"Unknown strategy: {self.strategy}"}
            )

    def _solve_lightning(self):
        """Pure brute force — no scoring overhead."""
        if self.puzzle["type"] == "B" and self.public_key_hex:
            pubkey = decompress_pubkey(self.public_key_hex)
            solver = KangarooSolver(
                pubkey,
                self.puzzle["range_start"],
                self.puzzle["range_end"],
                callback=self._btc_callback,
            )
        else:
            solver = BruteForceSolver(
                self.puzzle["address"],
                self.puzzle["range_start"],
                self.puzzle["range_end"],
                callback=self._btc_callback,
            )
        self._inner_solver = solver
        result = solver.solve()
        if result:
            self._record_win(result)

    def _solve_mystic(self):
        """Score a sample -> try best-scored regions first."""
        import random
        import time as _time

        range_start = self.puzzle["range_start"]
        range_end = self.puzzle["range_end"]

        sample = [
            random.randint(range_start, range_end) for _ in range(self.SAMPLE_SIZE)
        ]

        from engines.scoring import hybrid_score

        scored = []
        phase_start = _time.time()
        for i, candidate in enumerate(sample):
            if not self.running:
                return
            score = hybrid_score(candidate)
            scored.append((candidate, score["final_score"]))
            if i % 1000 == 0:
                elapsed = _time.time() - phase_start
                speed = i / max(0.001, elapsed)
                self._emit(
                    {
                        "status": "running",
                        "message": f"Scoring sample: {i}/{self.SAMPLE_SIZE}",
                        "progress": (i / self.SAMPLE_SIZE) * 20,
                        "speed": speed,
                        "operations": i,
                        "candidates_tested": 0,
                        "candidates_total": -1,
                        "current_best": None,
                        "solution": None,
                    }
                )

        scored.sort(key=lambda x: x[1], reverse=True)

        test_start = _time.time()
        for i, (candidate, score) in enumerate(scored):
            if not self.running:
                break
            address = privkey_to_address(candidate)
            if address == self.puzzle["address"]:
                self._record_win(candidate)
                return

            if i % 100 == 0:
                elapsed = _time.time() - test_start
                speed = i / max(0.001, elapsed)
                self._emit(
                    {
                        "status": "running",
                        "message": f"Testing scored candidates: {i}/{len(scored)}",
                        "progress": 20 + (i / len(scored)) * 80,
                        "speed": speed,
                        "operations": i,
                        "candidates_tested": i,
                        "candidates_total": len(scored),
                        "current_best": {
                            "candidate": scored[0][0],
                            "score": scored[0][1],
                        },
                        "solution": None,
                    }
                )

        # Fall back to brute force
        self._solve_lightning()

    def _solve_hybrid(self):
        """Alternate: 100 scored candidates, then 100 random, repeat."""
        import random
        import time as _time

        range_start = self.puzzle["range_start"]
        range_end = self.puzzle["range_end"]
        from engines.scoring import hybrid_score

        batch_size = 100
        tested = 0
        hybrid_start = _time.time()

        while self.running:
            # Scored batch
            sample = [random.randint(range_start, range_end) for _ in range(batch_size)]
            scored = [(c, hybrid_score(c)["final_score"]) for c in sample]
            scored.sort(key=lambda x: x[1], reverse=True)

            for candidate, score in scored:
                if not self.running:
                    return
                address = privkey_to_address(candidate)
                tested += 1
                if address == self.puzzle["address"]:
                    self._record_win(candidate)
                    return

            # Random batch
            for _ in range(batch_size):
                if not self.running:
                    return
                candidate = random.randint(range_start, range_end)
                address = privkey_to_address(candidate)
                tested += 1
                if address == self.puzzle["address"]:
                    self._record_win(candidate)
                    return

            elapsed = _time.time() - hybrid_start
            speed = tested / max(0.001, elapsed)
            self._emit(
                {
                    "status": "running",
                    "message": f"Hybrid search: {tested} tested",
                    "progress": -1,
                    "speed": speed,
                    "operations": tested,
                    "candidates_tested": tested,
                    "candidates_total": -1,
                    "current_best": (
                        {"candidate": scored[0][0], "score": scored[0][1]}
                        if scored
                        else None
                    ),
                    "solution": None,
                }
            )

    def _solve_oracle(self):
        """AI-guided search — asks Claude to suggest hex ranges each round."""
        import random
        import time as _time
        from engines.ai_engine import is_available, ask_claude
        from engines.scoring import hybrid_score

        range_start = self.puzzle["range_start"]
        range_end = self.puzzle["range_end"]
        tested = 0
        round_num = 0
        oracle_start = _time.time()

        if not is_available():
            self._emit(
                {
                    "status": "running",
                    "message": "AI unavailable, falling back to hybrid",
                    "progress": 0,
                    "candidates_tested": 0,
                    "candidates_total": -1,
                    "current_best": None,
                    "solution": None,
                }
            )
            self._solve_hybrid()
            return

        while self.running:
            round_num += 1

            # Ask Claude for search regions
            prompt = (
                f"Bitcoin puzzle #{self.puzzle_id}: searching for private key in "
                f"hex range [{hex(range_start)}, {hex(range_end)}].\n"
                f"Round {round_num}, tested {tested} candidates so far.\n"
                f"Suggest 5 specific hex values within this range that might be "
                f"interesting based on mathematical patterns, numerological "
                f"significance, or common key patterns.\n"
                f"Format: one hex value per line, nothing else."
            )
            result = ask_claude(prompt, timeout=15, use_cache=False)

            suggested_regions = []
            if result["success"]:
                # Emit AI reasoning
                elapsed = _time.time() - oracle_start
                speed = tested / max(0.001, elapsed)
                self._emit(
                    {
                        "status": "running",
                        "message": f"Oracle round {round_num}",
                        "progress": -1,
                        "speed": speed,
                        "operations": tested,
                        "candidates_tested": tested,
                        "candidates_total": -1,
                        "current_best": None,
                        "solution": None,
                        "ai_insight": f"Round {round_num}: {result['response'][:200]}",
                    }
                )
                suggested_regions = self._parse_oracle_regions(
                    result["response"], range_start, range_end
                )

            # Search around suggested regions
            for center in suggested_regions:
                if not self.running:
                    return
                # Search a window around each suggestion
                window = max(100, (range_end - range_start) // 10000)
                start = max(range_start, center - window)
                end = min(range_end, center + window)

                batch = [random.randint(start, end) for _ in range(100)]
                scored = [(c, hybrid_score(c)["final_score"]) for c in batch]
                scored.sort(key=lambda x: x[1], reverse=True)

                for candidate, score in scored:
                    if not self.running:
                        return
                    address = privkey_to_address(candidate)
                    tested += 1
                    if address == self.puzzle["address"]:
                        self._record_win(candidate)
                        return

            # Random batch between oracle rounds
            for _ in range(200):
                if not self.running:
                    return
                candidate = random.randint(range_start, range_end)
                address = privkey_to_address(candidate)
                tested += 1
                if address == self.puzzle["address"]:
                    self._record_win(candidate)
                    return

            elapsed = _time.time() - oracle_start
            speed = tested / max(0.001, elapsed)
            self._emit(
                {
                    "status": "running",
                    "message": f"Oracle round {round_num}: {tested} tested",
                    "progress": -1,
                    "speed": speed,
                    "operations": tested,
                    "candidates_tested": tested,
                    "candidates_total": -1,
                    "current_best": None,
                    "solution": None,
                }
            )

    def _parse_oracle_regions(
        self, response: str, range_start: int, range_end: int
    ) -> list:
        """Parse hex values from Claude's response. Safe fallback on parse failure."""
        regions = []
        for line in response.strip().split("\n"):
            line = line.strip().strip("-").strip("*").strip()
            # Extract hex value
            for word in line.split():
                word = word.strip(",.:;")
                if word.startswith("0x") or word.startswith("0X"):
                    try:
                        val = int(word, 16)
                        if range_start <= val <= range_end:
                            regions.append(val)
                    except ValueError:
                        continue
        return regions[:5]  # Max 5 regions

    def _record_win(self, candidate):
        """Record successful solve to learning engine + check balance + notify."""
        from engines.scoring import hybrid_score
        from engines import learning

        score_result = hybrid_score(candidate)
        address = privkey_to_address(candidate)
        learning.record_solve(
            puzzle_type="btc",
            candidate=candidate,
            score_result=score_result,
            was_correct=True,
            metadata={"puzzle_id": self.puzzle_id, "strategy": self.strategy},
        )
        self._emit(
            {
                "status": "solved",
                "message": f"SOLVED! Key: {hex(candidate)}",
                "progress": 100,
                "candidates_tested": -1,
                "candidates_total": -1,
                "current_best": score_result,
                "solution": candidate,
            }
        )

        # Record to vault
        try:
            from engines.vault import record_finding

            record_finding(
                {
                    "address": address,
                    "private_key": hex(candidate),
                    "chain": "btc",
                    "source": "puzzle_solve",
                    "puzzle_id": self.puzzle_id,
                }
            )
        except Exception:
            pass

        # Background balance check + Telegram notification
        import threading

        def _check():
            try:
                from engines.balance import check_balance
                from engines.notifier import (
                    notify_solve,
                    notify_balance_found,
                    is_configured,
                )

                if is_configured():
                    notify_solve(self.puzzle_id, candidate, address)
                result = check_balance(address)
                if result.get("has_balance") and is_configured():
                    notify_balance_found(address, result["balance_btc"], "puzzle_solve")
                    # Update vault with balance
                    try:
                        from engines.vault import record_finding

                        record_finding(
                            {
                                "address": address,
                                "private_key": hex(candidate),
                                "chain": "btc",
                                "balance": result["balance_btc"],
                                "source": "puzzle_solve_balance",
                                "puzzle_id": self.puzzle_id,
                            }
                        )
                    except Exception:
                        pass
            except Exception:
                pass

            # ETH balance check
            try:
                from engines.bip39 import privkey_to_eth_address

                eth_addr = privkey_to_eth_address(candidate)
                from engines.balance import check_eth_balance

                eth_result = check_eth_balance(eth_addr)
                if eth_result.get("has_balance") and is_configured():
                    from engines.notifier import send_message

                    send_message(
                        f"<b>ETH Balance Found!</b>\n"
                        f"Address: <code>{eth_addr}</code>\n"
                        f"Balance: {eth_result['balance_eth']} ETH"
                    )
                    try:
                        from engines.vault import record_finding

                        record_finding(
                            {
                                "address": eth_addr,
                                "private_key": hex(candidate),
                                "chain": "eth",
                                "balance": eth_result["balance_eth"],
                                "source": "puzzle_solve_eth_balance",
                            }
                        )
                    except Exception:
                        pass
            except Exception:
                pass

        threading.Thread(target=_check, daemon=True).start()

    def _btc_callback(self, data):
        """Translate crypto engine callbacks to BaseSolver format."""
        is_solved = data.get("solved")

        # Throttle non-solved callbacks to 10/s max
        now = time.time()
        if not is_solved and (now - self._last_callback_time) < 0.1:
            return
        self._last_callback_time = now

        emit_data = {
            "status": "solved" if is_solved else "running",
            "message": f"Speed: {data.get('speed', 0):.0f}/s",
            "progress": data.get("progress", 0),
            "speed": data.get("speed", 0),
            "operations": data.get("operations", 0),
            "candidates_tested": data.get("operations", 0),
            "candidates_total": data.get("total_keys", -1),
            "current_best": None,
            "solution": data.get("solution"),
        }

        # Derive ETH address if we have a solution
        if data.get("solution"):
            try:
                from engines.bip39 import privkey_to_eth_address

                emit_data["eth_address"] = privkey_to_eth_address(data["solution"])
            except Exception:
                pass

        self._emit(emit_data)
        if is_solved and data.get("solution"):
            self._record_win(data["solution"])

    def stop(self):
        """Stop solver and inner solver if any."""
        self.running = False
        if hasattr(self, "_inner_solver"):
            self._inner_solver.stop()

    def get_name(self):
        return "BTC Puzzle Hunter"

    def get_description(self):
        return f"Puzzle #{self.puzzle_id} — {self.strategy} strategy"
