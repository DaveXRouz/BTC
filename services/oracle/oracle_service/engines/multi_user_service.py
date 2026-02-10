"""
Multi-User FC60 Service Orchestrator
======================================
Single entry point for multi-user analysis. Composes:
  1. Profile calculation (multi_user_fc60)
  2. Pairwise compatibility (compatibility_analyzer)
  3. Group energy (group_energy)
  4. Group dynamics (group_dynamics)

Returns a fully JSON-serializable result with computation time.
"""

import time

# These modules were removed in Session 6 (framework integration).
# Session 7 will rewrite multi-user analysis using the framework bridge.
try:
    from engines.multi_user_fc60 import calculate_profiles
    from engines.compatibility_analyzer import CompatibilityAnalyzer
    from engines.group_energy import GroupEnergyCalculator
    from engines.group_dynamics import GroupDynamicsAnalyzer
except ImportError:
    calculate_profiles = None
    CompatibilityAnalyzer = None
    GroupEnergyCalculator = None
    GroupDynamicsAnalyzer = None


class MultiUserAnalysisResult:
    """Complete multi-user analysis result."""

    __slots__ = (
        "profiles",
        "pairwise_compatibility",
        "group_energy",
        "group_dynamics",
        "user_count",
        "pair_count",
        "computation_ms",
    )

    def __init__(
        self,
        profiles,
        pairwise_compatibility,
        group_energy,
        group_dynamics,
        user_count,
        pair_count,
        computation_ms,
    ):
        self.profiles = profiles
        self.pairwise_compatibility = pairwise_compatibility
        self.group_energy = group_energy
        self.group_dynamics = group_dynamics
        self.user_count = user_count
        self.pair_count = pair_count
        self.computation_ms = computation_ms

    def to_dict(self):
        return {
            "user_count": self.user_count,
            "pair_count": self.pair_count,
            "computation_ms": round(self.computation_ms, 1),
            "profiles": [p.to_dict() for p in self.profiles],
            "pairwise_compatibility": [pc.to_dict() for pc in self.pairwise_compatibility],
            "group_energy": self.group_energy.to_dict(),
            "group_dynamics": self.group_dynamics.to_dict(),
        }


class MultiUserFC60Service:
    """Orchestrates multi-user FC60 analysis."""

    def __init__(self):
        self._compat_analyzer = CompatibilityAnalyzer()
        self._energy_calculator = GroupEnergyCalculator()
        self._dynamics_analyzer = GroupDynamicsAnalyzer()

    def analyze(self, users):
        """Run complete multi-user analysis.

        Args:
            users: List of dicts with keys: name, birth_year, birth_month, birth_day
                   (2-10 users)

        Returns:
            MultiUserAnalysisResult with all analysis data.

        Raises:
            ValueError: If input validation fails.
        """
        start = time.monotonic()

        # 1. Calculate profiles (includes validation)
        profiles = calculate_profiles(users)

        # 2. Pairwise compatibility
        pairwise = self._compat_analyzer.analyze_all_pairs(profiles)

        # 3. Group energy
        energy = self._energy_calculator.calculate(profiles)

        # 4. Group dynamics
        dynamics = self._dynamics_analyzer.analyze(profiles, pairwise)

        elapsed_ms = (time.monotonic() - start) * 1000

        n = len(profiles)
        pair_count = n * (n - 1) // 2

        return MultiUserAnalysisResult(
            profiles=profiles,
            pairwise_compatibility=pairwise,
            group_energy=energy,
            group_dynamics=dynamics,
            user_count=n,
            pair_count=pair_count,
            computation_ms=elapsed_ms,
        )
