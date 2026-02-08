"""
Multi-User FC60 Profile Calculation
====================================
Composes fc60 + numerology engines to build UserFC60Profile for each user.
Supports batch calculation for 2-10 users with input validation.
"""

from engines.fc60 import (
    encode_fc60,
    ganzhi_year,
    STEM_ELEMENTS,
    ANIMAL_NAMES,
)
from engines.numerology import life_path, name_to_number, name_soul_urge


class UserFC60Profile:
    """Complete FC60 + numerology profile for a single user."""

    __slots__ = (
        "name",
        "birth_year",
        "birth_month",
        "birth_day",
        "fc60_sign",
        "element",
        "animal",
        "life_path",
        "destiny_number",
        "name_energy",
    )

    def __init__(
        self,
        name,
        birth_year,
        birth_month,
        birth_day,
        fc60_sign,
        element,
        animal,
        lp,
        destiny_number,
        name_energy,
    ):
        self.name = name
        self.birth_year = birth_year
        self.birth_month = birth_month
        self.birth_day = birth_day
        self.fc60_sign = fc60_sign
        self.element = element
        self.animal = animal
        self.life_path = lp
        self.destiny_number = destiny_number
        self.name_energy = name_energy

    def to_dict(self):
        return {
            "name": self.name,
            "birth_year": self.birth_year,
            "birth_month": self.birth_month,
            "birth_day": self.birth_day,
            "fc60_sign": self.fc60_sign,
            "element": self.element,
            "animal": self.animal,
            "life_path": self.life_path,
            "destiny_number": self.destiny_number,
            "name_energy": self.name_energy,
        }

    def __repr__(self):
        return (
            f"UserFC60Profile({self.name!r}, {self.animal} {self.element}, "
            f"LP={self.life_path})"
        )


def calculate_profile(name, birth_year, birth_month, birth_day):
    """Calculate a complete FC60 + numerology profile for one user.

    Args:
        name: User's name (string)
        birth_year: 4-digit year
        birth_month: 1-12
        birth_day: 1-31

    Returns:
        UserFC60Profile with all fields populated.

    Raises:
        ValueError: If inputs are invalid.
    """
    if not name or not isinstance(name, str):
        raise ValueError("Name must be a non-empty string")
    if not isinstance(birth_year, int) or birth_year < 1:
        raise ValueError(f"Invalid birth year: {birth_year}")
    if not isinstance(birth_month, int) or not (1 <= birth_month <= 12):
        raise ValueError(f"Invalid birth month: {birth_month}")
    if not isinstance(birth_day, int) or not (1 <= birth_day <= 31):
        raise ValueError(f"Invalid birth day: {birth_day}")

    # FC60 stamp
    fc60_data = encode_fc60(birth_year, birth_month, birth_day, include_time=False)
    fc60_sign = fc60_data["stamp"]

    # Ganzhi year → element + animal
    stem_idx, branch_idx = ganzhi_year(birth_year)
    element = STEM_ELEMENTS[stem_idx]
    animal = ANIMAL_NAMES[branch_idx]

    # Numerology
    lp = life_path(birth_year, birth_month, birth_day)
    destiny = name_to_number(name)
    energy = name_soul_urge(name)

    return UserFC60Profile(
        name=name,
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        fc60_sign=fc60_sign,
        element=element,
        animal=animal,
        lp=lp,
        destiny_number=destiny,
        name_energy=energy,
    )


def calculate_profiles(users):
    """Calculate profiles for a batch of 2-10 users.

    Args:
        users: List of dicts with keys: name, birth_year, birth_month, birth_day

    Returns:
        List of UserFC60Profile objects.

    Raises:
        ValueError: If user count is out of range or user data is invalid.
    """
    if not isinstance(users, (list, tuple)):
        raise ValueError("Users must be a list")
    if len(users) < 2:
        raise ValueError("At least 2 users required for multi-user analysis")
    if len(users) > 10:
        raise ValueError("Maximum 10 users supported")

    profiles = []
    for i, user in enumerate(users):
        if not isinstance(user, dict):
            raise ValueError(f"User at index {i} must be a dict")
        required = ("name", "birth_year", "birth_month", "birth_day")
        missing = [k for k in required if k not in user]
        if missing:
            raise ValueError(f"User at index {i} missing fields: {missing}")

        profiles.append(
            calculate_profile(
                user["name"],
                user["birth_year"],
                user["birth_month"],
                user["birth_day"],
            )
        )

    return profiles
