"""
Group Dynamics Analyzer
========================
Analyzes group-level dynamics from profiles and pairwise compatibility:
  - Roles: Leader, Supporter, Challenger, Harmonizer (based on life path)
  - Synergies: high-compat pairs, complementary roles, element diversity
  - Challenges: low-compat pairs, role imbalances, element conflicts
  - Growth areas: based on weak pairs, role gaps, element homogeneity
  - Stats: avg compatibility, strongest/weakest bond
"""

from collections import Counter

# Role mapping by life path number
_ROLE_MAP = {
    1: "Leader",
    8: "Leader",
    11: "Leader",
    22: "Leader",
    2: "Supporter",
    6: "Supporter",
    9: "Supporter",
    5: "Challenger",
    7: "Challenger",
    3: "Harmonizer",
    4: "Harmonizer",
    33: "Harmonizer",
}

_ALL_ROLES = {"Leader", "Supporter", "Challenger", "Harmonizer"}

_ROLE_DESCRIPTIONS = {
    "Leader": "Drives vision and initiative",
    "Supporter": "Nurtures connections and stability",
    "Challenger": "Pushes boundaries and questions assumptions",
    "Harmonizer": "Bridges differences and creates flow",
}


class GroupDynamics:
    """Full group dynamics analysis result."""

    __slots__ = (
        "roles",
        "synergies",
        "challenges",
        "growth_areas",
        "avg_compatibility",
        "strongest_bond",
        "weakest_bond",
    )

    def __init__(
        self,
        roles,
        synergies,
        challenges,
        growth_areas,
        avg_compatibility,
        strongest_bond,
        weakest_bond,
    ):
        self.roles = roles
        self.synergies = synergies
        self.challenges = challenges
        self.growth_areas = growth_areas
        self.avg_compatibility = avg_compatibility
        self.strongest_bond = strongest_bond
        self.weakest_bond = weakest_bond

    def to_dict(self):
        return {
            "roles": self.roles,
            "synergies": self.synergies,
            "challenges": self.challenges,
            "growth_areas": self.growth_areas,
            "avg_compatibility": round(self.avg_compatibility, 3),
            "strongest_bond": self.strongest_bond,
            "weakest_bond": self.weakest_bond,
        }


class GroupDynamicsAnalyzer:
    """Analyzes group dynamics from profiles and pairwise results."""

    def analyze(self, profiles, pairwise_results):
        """Analyze group dynamics.

        Args:
            profiles: List of UserFC60Profile
            pairwise_results: List of PairwiseCompatibility from analyzer

        Returns:
            GroupDynamics result.
        """
        # === Roles ===
        roles = {}
        for p in profiles:
            role = _ROLE_MAP.get(p.life_path, "Harmonizer")
            roles[p.name] = {
                "role": role,
                "description": _ROLE_DESCRIPTIONS[role],
                "life_path": p.life_path,
            }

        # === Stats ===
        if pairwise_results:
            scores = [pr.overall_score for pr in pairwise_results]
            avg_compat = sum(scores) / len(scores)

            best = max(pairwise_results, key=lambda pr: pr.overall_score)
            worst = min(pairwise_results, key=lambda pr: pr.overall_score)

            strongest_bond = {
                "pair": f"{best.user1_name} & {best.user2_name}",
                "score": round(best.overall_score, 3),
                "classification": best.classification,
            }
            weakest_bond = {
                "pair": f"{worst.user1_name} & {worst.user2_name}",
                "score": round(worst.overall_score, 3),
                "classification": worst.classification,
            }
        else:
            avg_compat = 0.0
            strongest_bond = None
            weakest_bond = None

        # === Synergies ===
        synergies = []

        # High-compatibility pairs
        high_pairs = [pr for pr in pairwise_results if pr.overall_score >= 0.7]
        for pr in high_pairs:
            synergies.append(
                f"{pr.user1_name} & {pr.user2_name}: strong natural affinity "
                f"({pr.classification}, {pr.overall_score:.0%})"
            )

        # Complementary roles present
        role_counts = Counter(r["role"] for r in roles.values())
        if len(role_counts) >= 3:
            synergies.append(
                "Diverse role coverage: "
                + ", ".join(
                    f"{count} {role}(s)" for role, count in sorted(role_counts.items())
                )
            )

        # Element diversity
        unique_elements = len(set(p.element for p in profiles))
        if unique_elements >= 3:
            synergies.append(
                f"Rich elemental diversity ({unique_elements} elements represented)"
            )

        # === Challenges ===
        challenges = []

        # Low-compatibility pairs
        low_pairs = [pr for pr in pairwise_results if pr.overall_score < 0.4]
        for pr in low_pairs:
            challenges.append(
                f"{pr.user1_name} & {pr.user2_name}: potential friction "
                f"({pr.classification}, {pr.overall_score:.0%})"
            )

        # Role imbalances
        present_roles = set(role_counts.keys())
        missing_roles = _ALL_ROLES - present_roles
        if missing_roles:
            challenges.append(
                f"Missing role energy: {', '.join(sorted(missing_roles))}"
            )

        leader_count = role_counts.get("Leader", 0)
        if leader_count > len(profiles) / 2:
            challenges.append(
                f"Leadership overload ({leader_count} Leaders may create power struggles)"
            )

        # Element conflicts (all same element)
        if unique_elements == 1:
            challenges.append(
                f"Elemental homogeneity (all {profiles[0].element}) — "
                "limited perspective range"
            )

        # === Growth Areas ===
        growth_areas = []

        # Weak pairs suggest growth opportunities
        moderate_pairs = [
            pr for pr in pairwise_results if 0.4 <= pr.overall_score < 0.6
        ]
        if moderate_pairs:
            growth_areas.append(
                f"{len(moderate_pairs)} pair(s) in neutral zone — "
                "conscious effort can strengthen these bonds"
            )

        # Missing roles
        for role in sorted(missing_roles):
            growth_areas.append(f"Cultivate {role} energy: {_ROLE_DESCRIPTIONS[role]}")

        # Element gaps
        all_elements = {"Wood", "Fire", "Earth", "Metal", "Water"}
        present_elements = set(p.element for p in profiles)
        missing_elements = all_elements - present_elements
        if missing_elements:
            growth_areas.append(
                f"Invite {', '.join(sorted(missing_elements))} energy "
                "for fuller elemental balance"
            )

        return GroupDynamics(
            roles=roles,
            synergies=synergies,
            challenges=challenges,
            growth_areas=growth_areas,
            avg_compatibility=avg_compat,
            strongest_bond=strongest_bond,
            weakest_bond=weakest_bond,
        )
