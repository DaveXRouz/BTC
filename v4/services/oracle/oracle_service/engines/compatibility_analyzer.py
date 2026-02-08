"""
Pairwise Compatibility Analyzer
================================
Weighted scoring across 5 dimensions:
  - Life Path:    30%
  - Element:      25% (bidirectional average for Wu Xing)
  - Animal:       25%
  - Destiny:      10%
  - Name Energy:  10%

Classification: Excellent (>=0.8), Good (>=0.6), Neutral (>=0.4), Challenging (<0.4).
"""

from engines.compatibility_matrices import (
    get_life_path_compatibility,
    get_element_compatibility,
    get_animal_compatibility,
)

# Weights
W_LIFE_PATH = 0.30
W_ELEMENT = 0.25
W_ANIMAL = 0.25
W_DESTINY = 0.10
W_NAME_ENERGY = 0.10


class PairwiseCompatibility:
    """Result of compatibility analysis between two users."""

    __slots__ = (
        "user1_name",
        "user2_name",
        "life_path_score",
        "element_score",
        "animal_score",
        "destiny_score",
        "name_energy_score",
        "overall_score",
        "classification",
        "strengths",
        "challenges",
    )

    def __init__(
        self,
        user1_name,
        user2_name,
        life_path_score,
        element_score,
        animal_score,
        destiny_score,
        name_energy_score,
        overall_score,
        classification,
        strengths,
        challenges,
    ):
        self.user1_name = user1_name
        self.user2_name = user2_name
        self.life_path_score = life_path_score
        self.element_score = element_score
        self.animal_score = animal_score
        self.destiny_score = destiny_score
        self.name_energy_score = name_energy_score
        self.overall_score = overall_score
        self.classification = classification
        self.strengths = strengths
        self.challenges = challenges

    def to_dict(self):
        return {
            "user1": self.user1_name,
            "user2": self.user2_name,
            "scores": {
                "life_path": round(self.life_path_score, 3),
                "element": round(self.element_score, 3),
                "animal": round(self.animal_score, 3),
                "destiny": round(self.destiny_score, 3),
                "name_energy": round(self.name_energy_score, 3),
            },
            "overall": round(self.overall_score, 3),
            "classification": self.classification,
            "strengths": self.strengths,
            "challenges": self.challenges,
        }


def _classify(score):
    """Classify overall compatibility score."""
    if score >= 0.8:
        return "Excellent"
    elif score >= 0.6:
        return "Good"
    elif score >= 0.4:
        return "Neutral"
    else:
        return "Challenging"


def _generate_strengths_challenges(
    lp_score, elem_score, animal_score, destiny_score, energy_score, profile1, profile2
):
    """Generate human-readable strengths and challenges from component scores."""
    strengths = []
    challenges = []

    # Life path
    if lp_score >= 0.8:
        strengths.append(
            f"Strong life path alignment ({profile1.life_path} & {profile2.life_path})"
        )
    elif lp_score <= 0.3:
        challenges.append(
            f"Divergent life paths ({profile1.life_path} & {profile2.life_path})"
        )

    # Element
    if elem_score >= 0.8:
        strengths.append(
            f"Harmonious elements ({profile1.element} & {profile2.element})"
        )
    elif elem_score <= 0.3:
        challenges.append(
            f"Elemental tension ({profile1.element} & {profile2.element})"
        )

    # Animal
    if animal_score >= 0.9:
        strengths.append(f"Zodiac harmony ({profile1.animal} & {profile2.animal})")
    elif animal_score <= 0.2:
        challenges.append(f"Zodiac clash ({profile1.animal} & {profile2.animal})")

    # Destiny
    if destiny_score >= 0.8:
        strengths.append("Aligned destiny numbers")
    elif destiny_score <= 0.3:
        challenges.append("Different destiny vibrations")

    # Name energy
    if energy_score >= 0.8:
        strengths.append("Resonant name energies")
    elif energy_score <= 0.3:
        challenges.append("Contrasting name energies")

    return strengths, challenges


class CompatibilityAnalyzer:
    """Analyzes pairwise compatibility between UserFC60Profile objects."""

    def analyze_pair(self, profile1, profile2):
        """Analyze compatibility between two profiles.

        Args:
            profile1: UserFC60Profile
            profile2: UserFC60Profile

        Returns:
            PairwiseCompatibility result.
        """
        # Life path from matrix
        lp_score = get_life_path_compatibility(profile1.life_path, profile2.life_path)

        # Element: bidirectional average (Wu Xing is directional)
        elem_fwd = get_element_compatibility(profile1.element, profile2.element)
        elem_rev = get_element_compatibility(profile2.element, profile1.element)
        elem_score = (elem_fwd + elem_rev) / 2.0

        # Animal from matrix
        animal_score = get_animal_compatibility(profile1.animal, profile2.animal)

        # Destiny number: inverse distance scaled to [0, 1]
        destiny_diff = abs(profile1.destiny_number - profile2.destiny_number)
        destiny_score = max(0.0, 1.0 - destiny_diff / 9.0)

        # Name energy: inverse distance scaled to [0, 1]
        energy_diff = abs(profile1.name_energy - profile2.name_energy)
        energy_score = max(0.0, 1.0 - energy_diff / 9.0)

        # Weighted overall
        overall = (
            lp_score * W_LIFE_PATH
            + elem_score * W_ELEMENT
            + animal_score * W_ANIMAL
            + destiny_score * W_DESTINY
            + energy_score * W_NAME_ENERGY
        )

        classification = _classify(overall)

        strengths, challenges = _generate_strengths_challenges(
            lp_score,
            elem_score,
            animal_score,
            destiny_score,
            energy_score,
            profile1,
            profile2,
        )

        return PairwiseCompatibility(
            user1_name=profile1.name,
            user2_name=profile2.name,
            life_path_score=lp_score,
            element_score=elem_score,
            animal_score=animal_score,
            destiny_score=destiny_score,
            name_energy_score=energy_score,
            overall_score=overall,
            classification=classification,
            strengths=strengths,
            challenges=challenges,
        )

    def analyze_all_pairs(self, profiles):
        """Analyze all unique pairs from a list of profiles.

        Args:
            profiles: List of UserFC60Profile (2-10 items)

        Returns:
            List of PairwiseCompatibility results (N*(N-1)/2 items).
        """
        results = []
        n = len(profiles)
        for i in range(n):
            for j in range(i + 1, n):
                results.append(self.analyze_pair(profiles[i], profiles[j]))
        return results
