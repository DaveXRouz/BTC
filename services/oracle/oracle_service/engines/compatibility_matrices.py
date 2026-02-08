"""
Compatibility Matrices for Multi-User FC60 Analysis
====================================================
Three static matrices for pairwise compatibility scoring:
  - Life Path (13x13: digits 1-9 + master numbers 11, 22, 33)
  - Element (5x5: Wu Xing directional cycle)
  - Animal (12x12: Chinese zodiac triads, harmonies, clashes)

All scores are floats in [0.0, 1.0].
"""

# ════════════════════════════════════════════════════════════
# Life Path Compatibility Matrix
# ════════════════════════════════════════════════════════════
# Symmetric: keys are sorted tuples (min, max).
# Covers 1-9 + master numbers 11, 22, 33.
# Based on traditional Pythagorean numerology compatibility.

_LP_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33]

LIFE_PATH_COMPATIBILITY = {
    # 1 pairs
    (1, 1): 0.6,
    (1, 2): 0.5,
    (1, 3): 0.8,
    (1, 4): 0.4,
    (1, 5): 0.9,
    (1, 6): 0.5,
    (1, 7): 0.7,
    (1, 8): 0.6,
    (1, 9): 0.7,
    (1, 11): 0.7,
    (1, 22): 0.5,
    (1, 33): 0.6,
    # 2 pairs
    (2, 2): 0.7,
    (2, 3): 0.6,
    (2, 4): 0.8,
    (2, 5): 0.4,
    (2, 6): 0.9,
    (2, 7): 0.5,
    (2, 8): 0.7,
    (2, 9): 0.6,
    (2, 11): 0.9,
    (2, 22): 0.7,
    (2, 33): 0.8,
    # 3 pairs
    (3, 3): 0.7,
    (3, 4): 0.3,
    (3, 5): 0.8,
    (3, 6): 0.7,
    (3, 7): 0.5,
    (3, 8): 0.4,
    (3, 9): 0.8,
    (3, 11): 0.7,
    (3, 22): 0.4,
    (3, 33): 0.9,
    # 4 pairs
    (4, 4): 0.7,
    (4, 5): 0.3,
    (4, 6): 0.7,
    (4, 7): 0.6,
    (4, 8): 0.8,
    (4, 9): 0.4,
    (4, 11): 0.5,
    (4, 22): 0.9,
    (4, 33): 0.5,
    # 5 pairs
    (5, 5): 0.6,
    (5, 6): 0.4,
    (5, 7): 0.8,
    (5, 8): 0.5,
    (5, 9): 0.7,
    (5, 11): 0.6,
    (5, 22): 0.4,
    (5, 33): 0.5,
    # 6 pairs
    (6, 6): 0.7,
    (6, 7): 0.3,
    (6, 8): 0.5,
    (6, 9): 0.8,
    (6, 11): 0.7,
    (6, 22): 0.6,
    (6, 33): 0.9,
    # 7 pairs
    (7, 7): 0.7,
    (7, 8): 0.4,
    (7, 9): 0.6,
    (7, 11): 0.8,
    (7, 22): 0.5,
    (7, 33): 0.4,
    # 8 pairs
    (8, 8): 0.7,
    (8, 9): 0.5,
    (8, 11): 0.5,
    (8, 22): 0.8,
    (8, 33): 0.6,
    # 9 pairs
    (9, 9): 0.6,
    (9, 11): 0.7,
    (9, 22): 0.5,
    (9, 33): 0.8,
    # Master pairs
    (11, 11): 0.8,
    (11, 22): 0.7,
    (11, 33): 0.8,
    (22, 22): 0.8,
    (22, 33): 0.7,
    (33, 33): 0.8,
}


# ════════════════════════════════════════════════════════════
# Element Compatibility Matrix (Wu Xing 五行)
# ════════════════════════════════════════════════════════════
# Directional (not symmetric) — generating and controlling cycles matter.
# Index order: Wood=0, Fire=1, Earth=2, Metal=3, Water=4
# Generating (相生): Wood→Fire→Earth→Metal→Water→Wood = 0.9
# Controlling (相克): Wood→Earth, Earth→Water, Water→Fire, Fire→Metal, Metal→Wood
# Same element: 0.6
# Weakening (reverse of generating): 0.4

ELEMENT_COMPATIBILITY = {
    # Same element
    ("Wood", "Wood"): 0.6,
    ("Fire", "Fire"): 0.6,
    ("Earth", "Earth"): 0.6,
    ("Metal", "Metal"): 0.6,
    ("Water", "Water"): 0.6,
    # Generating cycle (parent → child): 0.9
    ("Wood", "Fire"): 0.9,
    ("Fire", "Earth"): 0.9,
    ("Earth", "Metal"): 0.9,
    ("Metal", "Water"): 0.9,
    ("Water", "Wood"): 0.9,
    # Reverse generating (child → parent): 0.4
    ("Fire", "Wood"): 0.4,
    ("Earth", "Fire"): 0.4,
    ("Metal", "Earth"): 0.4,
    ("Water", "Metal"): 0.4,
    ("Wood", "Water"): 0.4,
    # Controlling cycle (controller → controlled): 0.3
    ("Wood", "Earth"): 0.3,
    ("Earth", "Water"): 0.3,
    ("Water", "Fire"): 0.3,
    ("Fire", "Metal"): 0.3,
    ("Metal", "Wood"): 0.3,
    # Reverse controlling (controlled → controller): 0.2
    ("Earth", "Wood"): 0.2,
    ("Water", "Earth"): 0.2,
    ("Fire", "Water"): 0.2,
    ("Metal", "Fire"): 0.2,
    ("Wood", "Metal"): 0.2,
}


# ════════════════════════════════════════════════════════════
# Animal Compatibility Matrix (Chinese Zodiac 生肖)
# ════════════════════════════════════════════════════════════
# Symmetric: keys are sorted tuples.
# Trine groups (三合, every 4th): 0.9
#   Rat-Dragon-Monkey, Ox-Snake-Rooster, Tiger-Horse-Dog, Rabbit-Goat-Pig
# Six harmonies (六合): 0.95
#   Rat-Ox, Tiger-Pig, Rabbit-Dog, Dragon-Rooster, Snake-Monkey, Horse-Goat
# Clashes (相冲, opposite on zodiac wheel): 0.1
#   Rat-Horse, Ox-Goat, Tiger-Monkey, Rabbit-Rooster, Dragon-Dog, Snake-Pig
# Harm (相害): 0.25
#   Rat-Goat, Ox-Horse, Tiger-Snake, Rabbit-Dragon, Monkey-Pig, Rooster-Dog
# Neutral (default): 0.5

_ANIMALS = [
    "Rat",
    "Ox",
    "Tiger",
    "Rabbit",
    "Dragon",
    "Snake",
    "Horse",
    "Goat",
    "Monkey",
    "Rooster",
    "Dog",
    "Pig",
]


def _sorted_pair(a, b):
    return tuple(sorted((a, b)))


# Build animal compatibility
ANIMAL_COMPATIBILITY = {}

# Default: all pairs = 0.5
for i, a in enumerate(_ANIMALS):
    for j, b in enumerate(_ANIMALS):
        if i <= j:
            ANIMAL_COMPATIBILITY[(a, b)] = 0.5 if i != j else 0.7

# Trine groups (三合): 0.9
_TRINE_GROUPS = [
    ("Rat", "Dragon", "Monkey"),
    ("Ox", "Snake", "Rooster"),
    ("Tiger", "Horse", "Dog"),
    ("Rabbit", "Goat", "Pig"),
]
for group in _TRINE_GROUPS:
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            ANIMAL_COMPATIBILITY[_sorted_pair(group[i], group[j])] = 0.9

# Six harmonies (六合): 0.95
_SIX_HARMONIES = [
    ("Rat", "Ox"),
    ("Tiger", "Pig"),
    ("Rabbit", "Dog"),
    ("Dragon", "Rooster"),
    ("Snake", "Monkey"),
    ("Horse", "Goat"),
]
for a, b in _SIX_HARMONIES:
    ANIMAL_COMPATIBILITY[_sorted_pair(a, b)] = 0.95

# Clashes (相冲): 0.1
_CLASHES = [
    ("Rat", "Horse"),
    ("Ox", "Goat"),
    ("Tiger", "Monkey"),
    ("Rabbit", "Rooster"),
    ("Dragon", "Dog"),
    ("Snake", "Pig"),
]
for a, b in _CLASHES:
    ANIMAL_COMPATIBILITY[_sorted_pair(a, b)] = 0.1

# Harms (相害): 0.25
_HARMS = [
    ("Rat", "Goat"),
    ("Ox", "Horse"),
    ("Tiger", "Snake"),
    ("Rabbit", "Dragon"),
    ("Monkey", "Pig"),
    ("Rooster", "Dog"),
]
for a, b in _HARMS:
    ANIMAL_COMPATIBILITY[_sorted_pair(a, b)] = 0.25


# ════════════════════════════════════════════════════════════
# Lookup Functions
# ════════════════════════════════════════════════════════════


def get_life_path_compatibility(lp1, lp2, default=0.5):
    """Look up life path compatibility score. Symmetric."""
    key = tuple(sorted((lp1, lp2)))
    return LIFE_PATH_COMPATIBILITY.get(key, default)


def get_element_compatibility(elem1, elem2, default=0.5):
    """Look up element compatibility score. Directional (Wu Xing)."""
    return ELEMENT_COMPATIBILITY.get((elem1, elem2), default)


def get_animal_compatibility(animal1, animal2, default=0.5):
    """Look up animal compatibility score. Symmetric."""
    key = tuple(sorted((animal1, animal2)))
    return ANIMAL_COMPATIBILITY.get(key, default)
