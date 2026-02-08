"""
Group Energy Calculator
========================
Combines individual profiles into collective energy metrics:
  - Joint life path (numerology_reduce of sum)
  - Dominant element (most frequent, Wu Xing generative order tie-break)
  - Dominant animal (most frequent, alphabetical tie-break)
  - Element / animal / life path distributions
  - Partnership archetype classification
"""

from collections import Counter

from engines.numerology import numerology_reduce

# Wu Xing generative order for tie-breaking (first = highest priority)
_ELEMENT_ORDER = ["Wood", "Fire", "Earth", "Metal", "Water"]


class CombinedGroupEnergy:
    """Combined energy profile for a group of users."""

    __slots__ = (
        "joint_life_path",
        "dominant_element",
        "dominant_animal",
        "archetype",
        "archetype_description",
        "element_distribution",
        "animal_distribution",
        "life_path_distribution",
    )

    def __init__(
        self,
        joint_life_path,
        dominant_element,
        dominant_animal,
        archetype,
        archetype_description,
        element_distribution,
        animal_distribution,
        life_path_distribution,
    ):
        self.joint_life_path = joint_life_path
        self.dominant_element = dominant_element
        self.dominant_animal = dominant_animal
        self.archetype = archetype
        self.archetype_description = archetype_description
        self.element_distribution = element_distribution
        self.animal_distribution = animal_distribution
        self.life_path_distribution = life_path_distribution

    def to_dict(self):
        return {
            "joint_life_path": self.joint_life_path,
            "dominant_element": self.dominant_element,
            "dominant_animal": self.dominant_animal,
            "archetype": self.archetype,
            "archetype_description": self.archetype_description,
            "element_distribution": dict(self.element_distribution),
            "animal_distribution": dict(self.animal_distribution),
            "life_path_distribution": {
                str(k): v for k, v in self.life_path_distribution.items()
            },
        }


# ════════════════════════════════════════════════════════════
# Archetypes
# ════════════════════════════════════════════════════════════

_ARCHETYPES = {
    "Complementary Duo": "Two forces creating balance through difference",
    "Collaborative Builders": "Grounded team focused on steady, structured creation",
    "Dynamic Innovators": "High-energy group driven by change and new ideas",
    "Strategic Thinkers": "Analytical minds combining wisdom with precision",
    "Action Catalysts": "Fast-moving collective of doers and achievers",
    "Growth Explorers": "Seekers and learners pushing boundaries together",
    "Balanced Harmonizers": "Diverse group achieving natural equilibrium",
    "Master Collective": "Group with concentrated master-number energy",
}


def _classify_archetype(profiles, element_dist, lp_dist):
    """Classify partnership archetype based on group patterns."""
    n = len(profiles)
    unique_elements = len(element_dist)
    master_count = sum(1 for p in profiles if p.life_path in (11, 22, 33))
    lp_values = [p.life_path for p in profiles]
    lp_spread = max(lp_values) - min(lp_values) if lp_values else 0

    # Special: duo
    if n == 2:
        return "Complementary Duo", _ARCHETYPES["Complementary Duo"]

    # Master collective: majority have master numbers
    if master_count >= n / 2:
        return "Master Collective", _ARCHETYPES["Master Collective"]

    # Element diversity drives archetype
    if unique_elements >= 4:
        return "Balanced Harmonizers", _ARCHETYPES["Balanced Harmonizers"]

    # Check dominant element theme
    top_element = max(
        element_dist, key=lambda e: (element_dist[e], -_ELEMENT_ORDER.index(e))
    )
    top_ratio = element_dist[top_element] / n

    if top_element == "Earth" and top_ratio >= 0.5:
        return "Collaborative Builders", _ARCHETYPES["Collaborative Builders"]
    if top_element == "Fire" and top_ratio >= 0.5:
        return "Dynamic Innovators", _ARCHETYPES["Dynamic Innovators"]
    if top_element == "Water" and top_ratio >= 0.5:
        return "Strategic Thinkers", _ARCHETYPES["Strategic Thinkers"]
    if top_element == "Metal" and top_ratio >= 0.5:
        return "Action Catalysts", _ARCHETYPES["Action Catalysts"]
    if top_element == "Wood" and top_ratio >= 0.5:
        return "Growth Explorers", _ARCHETYPES["Growth Explorers"]

    # High life path spread → growth explorers
    if lp_spread >= 7:
        return "Growth Explorers", _ARCHETYPES["Growth Explorers"]

    # Default
    return "Balanced Harmonizers", _ARCHETYPES["Balanced Harmonizers"]


class GroupEnergyCalculator:
    """Calculates combined energy metrics for a group of profiles."""

    def calculate(self, profiles):
        """Calculate group energy from a list of UserFC60Profile objects.

        Args:
            profiles: List of UserFC60Profile (2-10 items)

        Returns:
            CombinedGroupEnergy with all fields populated.
        """
        # Joint life path: reduce sum of all life paths
        lp_sum = sum(p.life_path for p in profiles)
        joint_lp = numerology_reduce(lp_sum)

        # Distributions
        element_counter = Counter(p.element for p in profiles)
        animal_counter = Counter(p.animal for p in profiles)
        lp_counter = Counter(p.life_path for p in profiles)

        # Dominant element: highest count, tie-break by Wu Xing order
        dominant_element = max(
            element_counter,
            key=lambda e: (element_counter[e], -_ELEMENT_ORDER.index(e)),
        )

        # Dominant animal: highest count, tie-break alphabetical
        dominant_animal = max(
            animal_counter,
            key=lambda a: (animal_counter[a], a),
        )

        # Archetype
        archetype, archetype_desc = _classify_archetype(
            profiles,
            element_counter,
            lp_counter,
        )

        return CombinedGroupEnergy(
            joint_life_path=joint_lp,
            dominant_element=dominant_element,
            dominant_animal=dominant_animal,
            archetype=archetype,
            archetype_description=archetype_desc,
            element_distribution=dict(element_counter),
            animal_distribution=dict(animal_counter),
            life_path_distribution=dict(lp_counter),
        )
