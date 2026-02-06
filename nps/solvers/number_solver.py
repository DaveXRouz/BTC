"""Number Oracle — sequence pattern detection and prediction."""

import math
import logging
from solvers.base_solver import BaseSolver

logger = logging.getLogger(__name__)


class NumberSolver(BaseSolver):

    def __init__(self, sequence: list, callback=None):
        super().__init__(callback)
        self.sequence = [int(x) for x in sequence]

    def solve(self):
        predictions = []

        predictions.extend(self._check_arithmetic())
        predictions.extend(self._check_geometric())
        predictions.extend(self._check_fibonacci())
        predictions.extend(self._check_polynomial())
        predictions.extend(self._check_power())
        predictions.extend(self._check_fc60_pattern())
        predictions.extend(self._check_ai_pattern())

        # Score each prediction
        from engines.scoring import hybrid_score

        for pred in predictions:
            score = hybrid_score(pred["prediction"])
            pred["harmony_score"] = score["final_score"]
            pred["fc60_token"] = score["fc60_token"]

        # Sort by confidence * harmony
        predictions.sort(
            key=lambda p: p["confidence"] * 0.7 + p["harmony_score"] * 0.3, reverse=True
        )

        # Remove duplicates
        seen = set()
        unique = []
        for p in predictions:
            if p["prediction"] not in seen:
                seen.add(p["prediction"])
                unique.append(p)

        self._emit(
            {
                "status": "solved",
                "message": f"Found {len(unique)} predictions",
                "progress": 100,
                "candidates_tested": len(self.sequence),
                "candidates_total": len(self.sequence),
                "current_best": unique[0] if unique else None,
                "solution": unique,
            }
        )

    def _check_arithmetic(self) -> list:
        if len(self.sequence) < 2:
            return []
        diffs = [
            self.sequence[i + 1] - self.sequence[i]
            for i in range(len(self.sequence) - 1)
        ]
        if len(set(diffs)) == 1:
            return [
                {
                    "prediction": self.sequence[-1] + diffs[0],
                    "confidence": 0.95,
                    "method": "Arithmetic sequence",
                    "explanation": f"Constant difference = {diffs[0]}",
                }
            ]
        return []

    def _check_geometric(self) -> list:
        if len(self.sequence) < 2 or 0 in self.sequence:
            return []
        ratios = [
            self.sequence[i + 1] / self.sequence[i]
            for i in range(len(self.sequence) - 1)
        ]
        if all(abs(r - ratios[0]) < 0.0001 for r in ratios):
            next_val = round(self.sequence[-1] * ratios[0])
            return [
                {
                    "prediction": next_val,
                    "confidence": 0.93,
                    "method": "Geometric sequence",
                    "explanation": f"Constant ratio = {ratios[0]:.4g}",
                }
            ]
        return []

    def _check_fibonacci(self) -> list:
        if len(self.sequence) < 3:
            return []
        is_fib = all(
            self.sequence[i] == self.sequence[i - 1] + self.sequence[i - 2]
            for i in range(2, len(self.sequence))
        )
        if is_fib:
            return [
                {
                    "prediction": self.sequence[-1] + self.sequence[-2],
                    "confidence": 0.92,
                    "method": "Fibonacci-like",
                    "explanation": "Each number = sum of previous two",
                }
            ]
        return []

    def _check_polynomial(self) -> list:
        if len(self.sequence) < 3:
            return []

        current = list(self.sequence)
        depth = 0
        while len(current) > 1 and depth < 5:
            diffs = [current[i + 1] - current[i] for i in range(len(current) - 1)]
            if len(set(diffs)) == 1:
                # Found constant difference at this depth - reconstruct forward
                last_diffs = [list(self.sequence)]
                temp = list(self.sequence)
                for _ in range(depth + 1):
                    temp = [temp[i + 1] - temp[i] for i in range(len(temp) - 1)]
                    last_diffs.append(temp)

                for level in reversed(range(len(last_diffs) - 1)):
                    last_diffs[level].append(
                        last_diffs[level][-1] + last_diffs[level + 1][-1]
                    )

                pred = last_diffs[0][-1]
                degree = depth + 1
                return [
                    {
                        "prediction": pred,
                        "confidence": max(0.5, 0.90 - depth * 0.1),
                        "method": f"Polynomial (degree {degree})",
                        "explanation": f"Differences become constant at depth {degree}",
                    }
                ]
            current = diffs
            depth += 1
        return []

    def _check_power(self) -> list:
        if len(self.sequence) < 3 or any(x <= 0 for x in self.sequence):
            return []

        for exp in [2, 3, 4, 5]:
            bases = []
            valid = True
            for val in self.sequence:
                base = round(val ** (1.0 / exp))
                if base**exp == val:
                    bases.append(base)
                else:
                    valid = False
                    break

            if valid and len(bases) >= 3:
                base_diffs = [bases[i + 1] - bases[i] for i in range(len(bases) - 1)]
                if len(set(base_diffs)) == 1:
                    next_base = bases[-1] + base_diffs[0]
                    return [
                        {
                            "prediction": next_base**exp,
                            "confidence": 0.91,
                            "method": f"Power sequence (n^{exp})",
                            "explanation": f'Base sequence [{",".join(str(b) for b in bases)}] with step {base_diffs[0]}',
                        }
                    ]
        return []

    def _check_fc60_pattern(self) -> list:
        from engines.fc60 import ANIMALS, ELEMENTS

        if len(self.sequence) < 3:
            return []

        tokens = [(n % 60, (n % 60) // 5, (n % 60) % 5) for n in self.sequence]
        animal_indices = [t[1] for t in tokens]
        element_indices = [t[2] for t in tokens]

        predictions = []

        # Check animal index arithmetic sequence
        animal_diffs = [
            animal_indices[i + 1] - animal_indices[i]
            for i in range(len(animal_indices) - 1)
        ]
        if len(set(animal_diffs)) == 1 and animal_diffs[0] != 0:
            next_animal = (animal_indices[-1] + animal_diffs[0]) % 12
            next_token_val = next_animal * 5 + element_indices[-1]
            last = self.sequence[-1]
            for offset in range(0, 120):
                candidate = last + offset
                if candidate % 60 == next_token_val:
                    predictions.append(
                        {
                            "prediction": candidate,
                            "confidence": 0.50,
                            "method": "FC60 animal cycle",
                            "explanation": f"Animals advance by {animal_diffs[0]}: {ANIMALS[next_animal]}",
                        }
                    )
                    break

        # Check element index cycle
        element_diffs = [
            element_indices[i + 1] - element_indices[i]
            for i in range(len(element_indices) - 1)
        ]
        if len(set(element_diffs)) == 1 and element_diffs[0] != 0:
            next_element = (element_indices[-1] + element_diffs[0]) % 5
            predictions.append(
                {
                    "prediction": self.sequence[-1]
                    + (self.sequence[-1] - self.sequence[-2]),
                    "confidence": 0.40,
                    "method": "FC60 element cycle",
                    "explanation": f"Elements advance by {element_diffs[0]}: {ELEMENTS[next_element]}",
                }
            )

        return predictions

    def _check_ai_pattern(self) -> list:
        """Ask Claude to analyze the sequence for patterns beyond deterministic checks."""
        from engines.ai_engine import is_available, ask_claude

        if not is_available():
            return []

        seq_str = ", ".join(str(x) for x in self.sequence)
        prompt = (
            f"Analyze this number sequence: {seq_str}\n"
            f"Find patterns the standard checks might miss.\n"
            f"For each pattern found, output one line in this exact format:\n"
            f"PREDICTION|CONFIDENCE|METHOD|EXPLANATION\n"
            f"Where PREDICTION is the next number (integer), CONFIDENCE is 0.0-1.0, "
            f"METHOD is 1-3 words, EXPLANATION is a brief description.\n"
            f"Output only these lines, nothing else. Max 3 predictions."
        )
        result = ask_claude(prompt, timeout=15)
        if not result["success"]:
            return []

        predictions = []
        for line in result["response"].strip().split("\n"):
            parts = line.strip().split("|")
            if len(parts) >= 4:
                try:
                    pred = int(parts[0].strip())
                    conf = float(parts[1].strip())
                    conf = max(0.0, min(0.85, conf))  # Cap AI confidence
                    method = f"AI: {parts[2].strip()}"
                    explanation = parts[3].strip()
                    predictions.append(
                        {
                            "prediction": pred,
                            "confidence": conf,
                            "method": method,
                            "explanation": explanation,
                        }
                    )
                except (ValueError, TypeError):
                    continue
        return predictions[:3]

    def get_name(self):
        return "Number Oracle"

    def get_description(self):
        return f"Sequence: {self.sequence}"
