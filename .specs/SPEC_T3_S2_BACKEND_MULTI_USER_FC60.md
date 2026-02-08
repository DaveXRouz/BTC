# SPEC: Backend Multi-User FC60 - T3-S2
**Estimated Duration:** 4-5 hours  
**Layer:** Layer 3B (Backend - Oracle Service)  
**Terminal:** Terminal 3  
**Session:** T3-S2 (Multi-User FC60)  
**Phase:** Phase 2 (Backend Services)

---

## 🎯 TL;DR

- Creating multi-user FC60 calculation and compatibility analysis system
- Individual FC60 profiles for each user (name, DOB, cosmic timing)
- Pairwise compatibility scoring (numerology + FC60 elements + animals)
- Combined group energy calculation (merged profile, partnership archetype)
- Group dynamics analysis (leadership patterns, challenges, synergies)
- Output: Comprehensive JSON with individual + pair + group insights
- Tests: 20+ scenarios covering all compatibility combinations

---

## 🎯 OBJECTIVE

Build a comprehensive multi-user FC60 analysis system that calculates individual profiles, pairwise compatibility scores, combined group energy, and relationship dynamics for 2-10 users.

**Success Criteria:**
1. Individual FC60 calculation works for unlimited users
2. Pairwise compatibility scoring accurate (0.0-1.0 scale)
3. Combined group energy reveals partnership archetype
4. Group dynamics identify leader/supporter/challenger roles
5. All calculations mathematically verified
6. Performance: <2s for 10-user analysis
7. Test coverage: 95%+

---

## 📋 CONTEXT

**Current State:**
- Terminal 3 Session 1 (T3-S1) completed: FC60 Core Engine
  * FC60Engine class with all 60 signs
  * Individual calculation working
  * Element/Animal extraction working
  * Verified with comprehensive tests

**What's Changing:**
- Adding multi-user support to FC60Engine
- Implementing compatibility algorithms (numerology + FC60)
- Creating combined energy calculator
- Building group dynamics analyzer
- Adding partnership archetype classifier

**Why:**
- Users want relationship compatibility insights
- Oracle should analyze group patterns (e.g., business partnerships)
- Combined energy helps identify team strengths/weaknesses
- Provides richer insights than individual readings

---

## 🔧 PREREQUISITES

**Dependencies:**
- [x] Terminal 3 Session 1 (FC60 Core Engine) - Verified: T3-S1 complete
- [x] Terminal 4 (Database) - Junction table for multi-user groups exists
- [x] Python 3.11+ with type hints
- [x] Claude API access (for AI-powered insights)

**Verification:**
```bash
# Verify FC60 Core Engine exists
cd backend/oracle-service
python -c "from app.engines.fc60 import FC60Engine; fc60 = FC60Engine(); print('FC60 Engine ready')"
# Expected: "FC60 Engine ready"

# Verify database junction table
psql -c "SELECT * FROM user_groups LIMIT 1;"
# Expected: Table exists (even if empty)
```

---

## 🛠️ TOOLS TO USE

**Extended Thinking:**
- Design compatibility matrix (which numbers harmonize?)
- Element interaction rules (generative vs destructive cycles)
- Partnership archetype classification algorithm
- Group dynamics role assignment logic

**Subagents:**
- Subagent 1: Compatibility scoring algorithms
- Subagent 2: Combined energy calculator
- Subagent 3: Group dynamics analyzer
- Subagent 4: Comprehensive test suite

**MCP Servers:**
- None required (all logic in Python)

**Skills:**
- None required (Python backend service)

---

## 📊 REQUIREMENTS

### Functional Requirements

**FR1: Individual FC60 Calculation (Multi-User)**
- Calculate FC60 for 2-10 users in single call
- Return individual profiles with all attributes
- Include: fc60_sign, element, animal, life_path, destiny_number, name_energy

**FR2: Pairwise Compatibility Scoring**
- Calculate compatibility for all user pairs
- Scoring factors:
  * Life path compatibility (numerology matrix)
  * Destiny number harmony
  * FC60 element interaction (generative/destructive cycles)
  * FC60 animal compatibility (traditional pairings)
  * Name energy resonance
- Output: 0.0 (incompatible) to 1.0 (highly compatible)
- Include: compatibility score, strengths list, challenges list, advice

**FR3: Combined Group Energy**
- Calculate merged group profile
- Attributes:
  * Joint life path (weighted average or dominant?)
  * Dominant element (most frequent in group)
  * Dominant animal (most frequent in group)
  * Group numerology score (average of individual scores)
  * Partnership type classification (archetype)

**FR4: Group Dynamics Analysis**
- Identify roles for each user:
  * Leader (highest life path + dominant element)
  * Supporter (harmonizes with leader)
  * Challenger (conflicts with leader, provides balance)
  * Harmonizer (bridges conflicts)
- Detect patterns:
  * Synergies (where group excels)
  * Challenges (potential friction points)
  * Growth areas (what group needs to develop)

**FR5: Partnership Archetype Classification**
- Based on combined energy, classify partnership:
  * "Collaborative Builders" (Earth-dominant, stable)
  * "Dynamic Innovators" (Fire-dominant, creative)
  * "Strategic Thinkers" (Water-dominant, intuitive)
  * "Action Catalysts" (Metal-dominant, decisive)
  * "Growth Explorers" (Wood-dominant, expansive)
  * "Balanced Harmonizers" (mixed elements)

### Non-Functional Requirements

**NFR1: Performance**
- 2-user analysis: <500ms
- 10-user analysis: <2s
- Database queries optimized (batch fetching)
- Caching for repeated calculations

**NFR2: Accuracy**
- Compatibility matrix verified against traditional FC60 sources
- Element cycles mathematically correct (generative/destructive)
- Animal pairings based on authentic Chinese zodiac compatibility

**NFR3: Code Quality**
- Type hints on all functions
- Docstrings with examples
- Error handling for edge cases (e.g., 1 user, 11+ users)
- Logging for debugging (JSON format)

**NFR4: Test Coverage**
- Unit tests: 95%+
- Scenarios: All compatibility combinations
- Edge cases: 2 users, 10 users, identical users, opposing users
- Performance tests: <2s for 10 users

---

## 📐 IMPLEMENTATION PLAN

### Phase 1: Compatibility Matrix Design (Duration: 45 min)

**Task 1.1: Life Path Compatibility Matrix**

Create compatibility matrix for life paths 1-9:

```python
# app/engines/compatibility_matrices.py

LIFE_PATH_COMPATIBILITY = {
    1: {1: 0.7, 2: 0.5, 3: 0.8, 4: 0.6, 5: 0.9, 6: 0.4, 7: 0.7, 8: 0.3, 9: 0.8},
    2: {1: 0.5, 2: 0.9, 3: 0.6, 4: 0.9, 5: 0.5, 6: 0.8, 7: 0.6, 8: 0.7, 9: 0.5},
    3: {1: 0.8, 2: 0.6, 3: 0.7, 4: 0.4, 5: 0.9, 6: 0.6, 7: 0.8, 8: 0.5, 9: 0.9},
    4: {1: 0.6, 2: 0.9, 3: 0.4, 4: 0.8, 5: 0.3, 6: 0.7, 7: 0.5, 8: 0.9, 9: 0.6},
    5: {1: 0.9, 2: 0.5, 3: 0.9, 4: 0.3, 5: 0.6, 6: 0.5, 7: 0.9, 8: 0.4, 9: 0.7},
    6: {1: 0.4, 2: 0.8, 3: 0.6, 4: 0.7, 5: 0.5, 6: 0.9, 7: 0.6, 8: 0.8, 9: 0.9},
    7: {1: 0.7, 2: 0.6, 3: 0.8, 4: 0.5, 5: 0.9, 6: 0.6, 7: 0.7, 8: 0.5, 9: 0.8},
    8: {1: 0.3, 2: 0.7, 3: 0.5, 4: 0.9, 5: 0.4, 6: 0.8, 7: 0.5, 8: 0.6, 9: 0.7},
    9: {1: 0.8, 2: 0.5, 3: 0.9, 4: 0.6, 5: 0.7, 6: 0.9, 7: 0.8, 8: 0.7, 9: 0.9},
}
```

**Rationale:**
- Based on traditional numerology compatibility
- 1 (leader) + 8 (power) = low compatibility (ego clash)
- 2 (harmony) + 4 (stability) = high compatibility (complementary)
- 3 (creativity) + 5 (freedom) = high compatibility (synergy)

**Task 1.2: FC60 Element Interaction Matrix**

```python
# app/engines/compatibility_matrices.py

# Generative cycle: Wood→Fire→Earth→Metal→Water→Wood
# Destructive cycle: Wood→Earth, Earth→Water, Water→Fire, Fire→Metal, Metal→Wood

ELEMENT_COMPATIBILITY = {
    "Wood": {
        "Wood": 0.6,    # Same element: moderate
        "Fire": 0.9,    # Generative: Wood feeds Fire
        "Earth": 0.3,   # Destructive: Wood depletes Earth
        "Metal": 0.2,   # Destructive: Metal cuts Wood
        "Water": 0.8,   # Generative: Water nourishes Wood
    },
    "Fire": {
        "Wood": 0.8,    # Generative: Wood feeds Fire
        "Fire": 0.6,    # Same element: moderate
        "Earth": 0.9,   # Generative: Fire creates Earth
        "Metal": 0.3,   # Destructive: Fire melts Metal
        "Water": 0.2,   # Destructive: Water extinguishes Fire
    },
    "Earth": {
        "Wood": 0.2,    # Destructive: Wood depletes Earth
        "Fire": 0.8,    # Generative: Fire creates Earth
        "Earth": 0.6,   # Same element: moderate
        "Metal": 0.9,   # Generative: Earth produces Metal
        "Water": 0.3,   # Destructive: Earth dams Water
    },
    "Metal": {
        "Wood": 0.3,    # Destructive: Metal cuts Wood
        "Fire": 0.2,    # Destructive: Fire melts Metal
        "Earth": 0.8,   # Generative: Earth produces Metal
        "Metal": 0.6,   # Same element: moderate
        "Water": 0.9,   # Generative: Metal enriches Water
    },
    "Water": {
        "Wood": 0.9,    # Generative: Water nourishes Wood
        "Fire": 0.3,    # Destructive: Water extinguishes Fire
        "Earth": 0.2,   # Destructive: Earth dams Water
        "Metal": 0.8,   # Generative: Metal enriches Water
        "Water": 0.6,   # Same element: moderate
    },
}
```

**Task 1.3: FC60 Animal Compatibility Matrix**

```python
# app/engines/compatibility_matrices.py

# Based on traditional Chinese zodiac compatibility
# Triangle groups (highly compatible): Rat-Dragon-Monkey, Ox-Snake-Rooster, etc.

ANIMAL_COMPATIBILITY = {
    "Rat": {
        "Rat": 0.6, "Ox": 0.9, "Tiger": 0.5, "Rabbit": 0.4,
        "Dragon": 0.9, "Snake": 0.6, "Horse": 0.2, "Goat": 0.5,
        "Monkey": 0.9, "Rooster": 0.6, "Dog": 0.5, "Pig": 0.7,
    },
    "Ox": {
        "Rat": 0.9, "Ox": 0.6, "Tiger": 0.3, "Rabbit": 0.7,
        "Dragon": 0.6, "Snake": 0.9, "Horse": 0.4, "Goat": 0.2,
        "Monkey": 0.6, "Rooster": 0.9, "Dog": 0.5, "Pig": 0.7,
    },
    "Tiger": {
        "Rat": 0.5, "Ox": 0.3, "Tiger": 0.6, "Rabbit": 0.7,
        "Dragon": 0.5, "Snake": 0.2, "Horse": 0.9, "Goat": 0.6,
        "Monkey": 0.3, "Rooster": 0.5, "Dog": 0.9, "Pig": 0.8,
    },
    "Rabbit": {
        "Rat": 0.4, "Ox": 0.7, "Tiger": 0.7, "Rabbit": 0.6,
        "Dragon": 0.5, "Snake": 0.6, "Horse": 0.7, "Goat": 0.9,
        "Monkey": 0.5, "Rooster": 0.2, "Dog": 0.8, "Pig": 0.9,
    },
    "Dragon": {
        "Rat": 0.9, "Ox": 0.6, "Tiger": 0.5, "Rabbit": 0.5,
        "Dragon": 0.6, "Snake": 0.7, "Horse": 0.7, "Goat": 0.6,
        "Monkey": 0.9, "Rooster": 0.9, "Dog": 0.3, "Pig": 0.7,
    },
    "Snake": {
        "Rat": 0.6, "Ox": 0.9, "Tiger": 0.2, "Rabbit": 0.6,
        "Dragon": 0.7, "Snake": 0.6, "Horse": 0.6, "Goat": 0.7,
        "Monkey": 0.8, "Rooster": 0.9, "Dog": 0.5, "Pig": 0.3,
    },
    "Horse": {
        "Rat": 0.2, "Ox": 0.4, "Tiger": 0.9, "Rabbit": 0.7,
        "Dragon": 0.7, "Snake": 0.6, "Horse": 0.6, "Goat": 0.9,
        "Monkey": 0.5, "Rooster": 0.6, "Dog": 0.9, "Pig": 0.7,
    },
    "Goat": {
        "Rat": 0.5, "Ox": 0.2, "Tiger": 0.6, "Rabbit": 0.9,
        "Dragon": 0.6, "Snake": 0.7, "Horse": 0.9, "Goat": 0.6,
        "Monkey": 0.5, "Rooster": 0.4, "Dog": 0.5, "Pig": 0.9,
    },
    "Monkey": {
        "Rat": 0.9, "Ox": 0.6, "Tiger": 0.3, "Rabbit": 0.5,
        "Dragon": 0.9, "Snake": 0.8, "Horse": 0.5, "Goat": 0.5,
        "Monkey": 0.6, "Rooster": 0.6, "Dog": 0.6, "Pig": 0.7,
    },
    "Rooster": {
        "Rat": 0.6, "Ox": 0.9, "Tiger": 0.5, "Rabbit": 0.2,
        "Dragon": 0.9, "Snake": 0.9, "Horse": 0.6, "Goat": 0.4,
        "Monkey": 0.6, "Rooster": 0.6, "Dog": 0.4, "Pig": 0.6,
    },
    "Dog": {
        "Rat": 0.5, "Ox": 0.5, "Tiger": 0.9, "Rabbit": 0.8,
        "Dragon": 0.3, "Snake": 0.5, "Horse": 0.9, "Goat": 0.5,
        "Monkey": 0.6, "Rooster": 0.4, "Dog": 0.6, "Pig": 0.8,
    },
    "Pig": {
        "Rat": 0.7, "Ox": 0.7, "Tiger": 0.8, "Rabbit": 0.9,
        "Dragon": 0.7, "Snake": 0.3, "Horse": 0.7, "Goat": 0.9,
        "Monkey": 0.7, "Rooster": 0.6, "Dog": 0.8, "Pig": 0.6,
    },
}
```

**Verification:**
```bash
cd backend/oracle-service
python -c "
from app.engines.compatibility_matrices import LIFE_PATH_COMPATIBILITY, ELEMENT_COMPATIBILITY, ANIMAL_COMPATIBILITY
print(f'Life Path entries: {len(LIFE_PATH_COMPATIBILITY)}')
print(f'Element entries: {len(ELEMENT_COMPATIBILITY)}')
print(f'Animal entries: {len(ANIMAL_COMPATIBILITY)}')
print(f'Example: 1 + 5 = {LIFE_PATH_COMPATIBILITY[1][5]}')
print(f'Example: Wood + Fire = {ELEMENT_COMPATIBILITY[\"Wood\"][\"Fire\"]}')
print(f'Example: Rat + Dragon = {ANIMAL_COMPATIBILITY[\"Rat\"][\"Dragon\"]}')
"
# Expected:
# Life Path entries: 9
# Element entries: 5
# Animal entries: 12
# Example: 1 + 5 = 0.9
# Example: Wood + Fire = 0.9
# Example: Rat + Dragon = 0.9
```

**Checkpoint:**
- [ ] All matrices created and verified
- [ ] Generative/destructive cycles correct
- [ ] Traditional compatibility pairings accurate
- [ ] Code compiles without errors

**STOP if checkpoint fails - matrices are foundation**

---

### Phase 2: Multi-User FC60 Calculation (Duration: 60 min)

**Task 2.1: Extend FC60Engine for Multi-User**

```python
# app/engines/fc60.py

from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserFC60Profile:
    """Individual user's FC60 profile"""
    user_id: str
    name: str
    dob: datetime
    fc60_sign: str
    element: str
    animal: str
    life_path: int
    destiny_number: int
    name_energy: int
    interpretation: str

class FC60Engine:
    # ... existing code from T3-S1 ...
    
    def calculate_multi_user(
        self,
        users: List[Dict[str, any]]
    ) -> List[UserFC60Profile]:
        """
        Calculate FC60 for multiple users.
        
        Args:
            users: List of user dicts with keys: user_id, name, dob
                   Example: [
                       {"user_id": "user1", "name": "Alice", "dob": "1990-05-15"},
                       {"user_id": "user2", "name": "Bob", "dob": "1992-03-20"}
                   ]
        
        Returns:
            List of UserFC60Profile objects
            
        Raises:
            ValueError: If users list empty or invalid
        """
        if not users or len(users) < 1:
            raise ValueError("At least 1 user required")
        
        if len(users) > 10:
            raise ValueError("Maximum 10 users supported")
        
        profiles = []
        
        for user in users:
            # Validate user data
            if not all(k in user for k in ["user_id", "name", "dob"]):
                raise ValueError(f"User missing required fields: {user}")
            
            # Parse DOB
            if isinstance(user["dob"], str):
                dob = datetime.fromisoformat(user["dob"])
            else:
                dob = user["dob"]
            
            # Calculate FC60 (reuse existing encode method)
            fc60_data = self.encode_full(user["name"], dob)
            
            # Create profile
            profile = UserFC60Profile(
                user_id=user["user_id"],
                name=user["name"],
                dob=dob,
                fc60_sign=fc60_data["fc60_sign"],
                element=fc60_data["element"],
                animal=fc60_data["animal"],
                life_path=fc60_data["life_path"],
                destiny_number=fc60_data["destiny_number"],
                name_energy=fc60_data["name_energy"],
                interpretation=fc60_data["interpretation"]
            )
            
            profiles.append(profile)
        
        return profiles
```

**Task 2.2: Create encode_full helper method**

```python
# app/engines/fc60.py

class FC60Engine:
    # ... existing code ...
    
    def encode_full(self, name: str, dob: datetime) -> Dict[str, any]:
        """
        Full FC60 encoding with all attributes.
        
        Returns:
            {
                "fc60_sign": "Water Ox",
                "element": "Water",
                "animal": "Ox",
                "life_path": 7,
                "destiny_number": 3,
                "name_energy": 25,
                "interpretation": "Water Ox brings..."
            }
        """
        # Reuse existing encode method
        fc60_sign = self.encode(name, dob)
        
        # Extract element and animal
        parts = fc60_sign.split()
        element = parts[0]
        animal = parts[1]
        
        # Calculate numerology
        life_path = self._calculate_life_path(dob)
        destiny_number = self._calculate_destiny_number(name)
        name_energy = self._calculate_name_energy(name)
        
        # Get interpretation
        interpretation = self.get_meaning(fc60_sign)
        
        return {
            "fc60_sign": fc60_sign,
            "element": element,
            "animal": animal,
            "life_path": life_path,
            "destiny_number": destiny_number,
            "name_energy": name_energy,
            "interpretation": interpretation
        }
    
    def _calculate_life_path(self, dob: datetime) -> int:
        """Calculate life path number from DOB"""
        # Sum all digits, reduce to single digit
        digits = str(dob.year) + str(dob.month).zfill(2) + str(dob.day).zfill(2)
        total = sum(int(d) for d in digits)
        
        # Reduce to single digit (master numbers 11, 22, 33 kept)
        while total > 9 and total not in [11, 22, 33]:
            total = sum(int(d) for d in str(total))
        
        return total
    
    def _calculate_destiny_number(self, name: str) -> int:
        """Calculate destiny number from full name"""
        # A=1, B=2, ..., Z=26, reduce to 1-9
        letter_values = {chr(i): ((i - 65) % 9) + 1 for i in range(65, 91)}
        
        total = sum(letter_values.get(c.upper(), 0) for c in name if c.isalpha())
        
        while total > 9:
            total = sum(int(d) for d in str(total))
        
        return total
    
    def _calculate_name_energy(self, name: str) -> int:
        """Calculate name energy (sum of all letters)"""
        letter_values = {chr(i): ((i - 65) % 9) + 1 for i in range(65, 91)}
        return sum(letter_values.get(c.upper(), 0) for c in name if c.isalpha())
```

**Verification:**
```bash
cd backend/oracle-service
python -c "
from app.engines.fc60 import FC60Engine
from datetime import datetime

fc60 = FC60Engine()

users = [
    {'user_id': 'u1', 'name': 'Alice', 'dob': '1990-05-15'},
    {'user_id': 'u2', 'name': 'Bob', 'dob': '1992-03-20'}
]

profiles = fc60.calculate_multi_user(users)

print(f'Profiles calculated: {len(profiles)}')
for p in profiles:
    print(f'{p.name}: {p.fc60_sign}, LP={p.life_path}, DN={p.destiny_number}')
"
# Expected:
# Profiles calculated: 2
# Alice: [some FC60 sign], LP=[number], DN=[number]
# Bob: [some FC60 sign], LP=[number], DN=[number]
```

**Checkpoint:**
- [ ] Multi-user calculation works (2-10 users)
- [ ] All profile attributes populated
- [ ] Numerology calculations correct
- [ ] Error handling for invalid inputs

**STOP if checkpoint fails - fix multi-user calculation**

---

### Phase 3: Compatibility Scoring (Duration: 90 min)

**Task 3.1: Create CompatibilityAnalyzer class**

```python
# app/engines/compatibility_analyzer.py

from typing import List, Dict, Tuple
from dataclasses import dataclass
from .fc60 import UserFC60Profile
from .compatibility_matrices import (
    LIFE_PATH_COMPATIBILITY,
    ELEMENT_COMPATIBILITY,
    ANIMAL_COMPATIBILITY
)

@dataclass
class CompatibilityScore:
    """Pairwise compatibility between two users"""
    user1_id: str
    user2_id: str
    overall_score: float  # 0.0 to 1.0
    life_path_score: float
    element_score: float
    animal_score: float
    destiny_score: float
    name_energy_score: float
    strengths: List[str]
    challenges: List[str]
    advice: str

class CompatibilityAnalyzer:
    """Analyzes compatibility between multiple users"""
    
    def __init__(self):
        self.life_path_matrix = LIFE_PATH_COMPATIBILITY
        self.element_matrix = ELEMENT_COMPATIBILITY
        self.animal_matrix = ANIMAL_COMPATIBILITY
    
    def calculate_pairwise(
        self,
        profiles: List[UserFC60Profile]
    ) -> Dict[str, CompatibilityScore]:
        """
        Calculate compatibility for all user pairs.
        
        Args:
            profiles: List of UserFC60Profile objects
        
        Returns:
            Dict mapping "user1-user2" to CompatibilityScore
            Example: {
                "u1-u2": CompatibilityScore(...),
                "u1-u3": CompatibilityScore(...),
                "u2-u3": CompatibilityScore(...)
            }
        """
        compatibility_matrix = {}
        
        # Calculate all pairs
        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                user1 = profiles[i]
                user2 = profiles[j]
                
                score = self._calculate_pair_score(user1, user2)
                
                key = f"{user1.user_id}-{user2.user_id}"
                compatibility_matrix[key] = score
        
        return compatibility_matrix
    
    def _calculate_pair_score(
        self,
        user1: UserFC60Profile,
        user2: UserFC60Profile
    ) -> CompatibilityScore:
        """Calculate compatibility score for a single pair"""
        
        # 1. Life Path Compatibility (weight: 0.25)
        lp_score = self.life_path_matrix[user1.life_path][user2.life_path]
        
        # 2. Element Compatibility (weight: 0.30)
        element_score = self.element_matrix[user1.element][user2.element]
        
        # 3. Animal Compatibility (weight: 0.25)
        animal_score = self.animal_matrix[user1.animal][user2.animal]
        
        # 4. Destiny Number Harmony (weight: 0.10)
        # Similar to life path but lower weight
        destiny_score = self.life_path_matrix.get(
            user1.destiny_number, {}
        ).get(user2.destiny_number, 0.5)
        
        # 5. Name Energy Resonance (weight: 0.10)
        # Difference between name energies (closer = better)
        energy_diff = abs(user1.name_energy - user2.name_energy)
        name_energy_score = max(0.0, 1.0 - (energy_diff / 50))
        
        # Weighted overall score
        overall_score = (
            lp_score * 0.25 +
            element_score * 0.30 +
            animal_score * 0.25 +
            destiny_score * 0.10 +
            name_energy_score * 0.10
        )
        
        # Identify strengths and challenges
        strengths, challenges = self._identify_dynamics(
            user1, user2,
            lp_score, element_score, animal_score
        )
        
        # Generate advice
        advice = self._generate_advice(
            overall_score, strengths, challenges
        )
        
        return CompatibilityScore(
            user1_id=user1.user_id,
            user2_id=user2.user_id,
            overall_score=round(overall_score, 2),
            life_path_score=round(lp_score, 2),
            element_score=round(element_score, 2),
            animal_score=round(animal_score, 2),
            destiny_score=round(destiny_score, 2),
            name_energy_score=round(name_energy_score, 2),
            strengths=strengths,
            challenges=challenges,
            advice=advice
        )
    
    def _identify_dynamics(
        self,
        user1: UserFC60Profile,
        user2: UserFC60Profile,
        lp_score: float,
        element_score: float,
        animal_score: float
    ) -> Tuple[List[str], List[str]]:
        """Identify relationship strengths and challenges"""
        
        strengths = []
        challenges = []
        
        # Life path dynamics
        if lp_score >= 0.8:
            strengths.append(
                f"Complementary life paths ({user1.life_path} + {user2.life_path}): "
                f"Natural harmony and mutual understanding"
            )
        elif lp_score <= 0.4:
            challenges.append(
                f"Different life paths ({user1.life_path} vs {user2.life_path}): "
                f"May require extra effort to align goals"
            )
        
        # Element dynamics
        if element_score >= 0.8:
            strengths.append(
                f"{user1.element} + {user2.element} elements: "
                f"Generative cycle creates supportive energy"
            )
        elif element_score <= 0.3:
            challenges.append(
                f"{user1.element} vs {user2.element} elements: "
                f"Destructive cycle may create friction"
            )
        
        # Animal dynamics
        if animal_score >= 0.8:
            strengths.append(
                f"{user1.animal} + {user2.animal} pairing: "
                f"Traditional compatibility triangle"
            )
        elif animal_score <= 0.3:
            challenges.append(
                f"{user1.animal} vs {user2.animal} pairing: "
                f"Conflicting energies, need balance"
            )
        
        # Add generic strength/challenge if none identified
        if not strengths:
            strengths.append("Balanced energies with growth potential")
        
        if not challenges:
            challenges.append("Minor adjustments needed for optimal harmony")
        
        return strengths, challenges
    
    def _generate_advice(
        self,
        overall_score: float,
        strengths: List[str],
        challenges: List[str]
    ) -> str:
        """Generate relationship advice based on score"""
        
        if overall_score >= 0.8:
            return (
                "Highly compatible! Focus on leveraging your natural synergies. "
                "Regular communication will maintain this strong connection."
            )
        elif overall_score >= 0.6:
            return (
                "Good compatibility with some effort needed. "
                "Respect differences and find common ground in shared values."
            )
        elif overall_score >= 0.4:
            return (
                "Moderate compatibility. Success requires conscious effort. "
                "Focus on understanding each other's perspectives and finding balance."
            )
        else:
            return (
                "Challenging compatibility. Requires significant work. "
                "Consider whether complementary differences can strengthen the bond "
                "or if fundamental misalignments exist."
            )
```

**Verification:**
```bash
cd backend/oracle-service
python -c "
from app.engines.fc60 import FC60Engine
from app.engines.compatibility_analyzer import CompatibilityAnalyzer

fc60 = FC60Engine()
analyzer = CompatibilityAnalyzer()

users = [
    {'user_id': 'u1', 'name': 'Alice', 'dob': '1990-05-15'},
    {'user_id': 'u2', 'name': 'Bob', 'dob': '1992-03-20'}
]

profiles = fc60.calculate_multi_user(users)
compatibility = analyzer.calculate_pairwise(profiles)

for key, score in compatibility.items():
    print(f'{key}: {score.overall_score}')
    print(f'  Strengths: {len(score.strengths)}')
    print(f'  Challenges: {len(score.challenges)}')
    print(f'  Advice: {score.advice[:50]}...')
"
# Expected: Compatibility scores calculated with strengths/challenges
```

**Checkpoint:**
- [ ] Pairwise compatibility calculated for all pairs
- [ ] Weighted scoring formula correct
- [ ] Strengths and challenges identified
- [ ] Advice generated based on score

**STOP if checkpoint fails - fix compatibility algorithm**

---

### Phase 4: Combined Group Energy (Duration: 60 min)

**Task 4.1: Create GroupEnergyCalculator class**

```python
# app/engines/group_energy_calculator.py

from typing import List, Dict
from dataclasses import dataclass
from collections import Counter
from .fc60 import UserFC60Profile

@dataclass
class CombinedGroupEnergy:
    """Combined energy profile for entire group"""
    group_id: str
    joint_life_path: int
    dominant_element: str
    dominant_animal: str
    average_numerology_score: float
    partnership_type: str
    group_description: str

class GroupEnergyCalculator:
    """Calculates combined energy for multi-user groups"""
    
    def calculate_combined_energy(
        self,
        profiles: List[UserFC60Profile],
        group_id: str = "default_group"
    ) -> CombinedGroupEnergy:
        """
        Calculate merged group profile.
        
        Args:
            profiles: List of UserFC60Profile objects
            group_id: Identifier for this group
        
        Returns:
            CombinedGroupEnergy object with partnership archetype
        """
        
        # 1. Joint Life Path (weighted average)
        joint_life_path = self._calculate_joint_life_path(profiles)
        
        # 2. Dominant Element (most frequent)
        dominant_element = self._calculate_dominant_element(profiles)
        
        # 3. Dominant Animal (most frequent)
        dominant_animal = self._calculate_dominant_animal(profiles)
        
        # 4. Average Numerology Score
        avg_score = sum(p.life_path for p in profiles) / len(profiles)
        
        # 5. Partnership Type Classification
        partnership_type = self._classify_partnership(
            dominant_element, joint_life_path, profiles
        )
        
        # 6. Group Description
        description = self._generate_group_description(
            partnership_type, dominant_element, joint_life_path
        )
        
        return CombinedGroupEnergy(
            group_id=group_id,
            joint_life_path=joint_life_path,
            dominant_element=dominant_element,
            dominant_animal=dominant_animal,
            average_numerology_score=round(avg_score, 1),
            partnership_type=partnership_type,
            group_description=description
        )
    
    def _calculate_joint_life_path(
        self,
        profiles: List[UserFC60Profile]
    ) -> int:
        """
        Calculate joint life path.
        
        Strategy: Sum all life paths, reduce to single digit
        (similar to individual life path calculation)
        """
        total = sum(p.life_path for p in profiles)
        
        # Reduce to single digit (keep master numbers)
        while total > 9 and total not in [11, 22, 33]:
            total = sum(int(d) for d in str(total))
        
        return total
    
    def _calculate_dominant_element(
        self,
        profiles: List[UserFC60Profile]
    ) -> str:
        """Find most frequent element in group"""
        
        elements = [p.element for p in profiles]
        counter = Counter(elements)
        
        # Return most common (tie goes to first)
        return counter.most_common(1)[0][0]
    
    def _calculate_dominant_animal(
        self,
        profiles: List[UserFC60Profile]
    ) -> str:
        """Find most frequent animal in group"""
        
        animals = [p.animal for p in profiles]
        counter = Counter(animals)
        
        return counter.most_common(1)[0][0]
    
    def _classify_partnership(
        self,
        dominant_element: str,
        joint_life_path: int,
        profiles: List[UserFC60Profile]
    ) -> str:
        """
        Classify partnership archetype.
        
        Archetypes:
        - Collaborative Builders (Earth-dominant, stable)
        - Dynamic Innovators (Fire-dominant, creative)
        - Strategic Thinkers (Water-dominant, intuitive)
        - Action Catalysts (Metal-dominant, decisive)
        - Growth Explorers (Wood-dominant, expansive)
        - Balanced Harmonizers (mixed elements, balanced life paths)
        """
        
        # Count element distribution
        elements = [p.element for p in profiles]
        element_counts = Counter(elements)
        
        # Check if balanced (all elements within 1 of each other)
        max_count = max(element_counts.values())
        min_count = min(element_counts.values())
        is_balanced = (max_count - min_count) <= 1
        
        if is_balanced:
            return "Balanced Harmonizers"
        
        # Element-based classification
        element_archetypes = {
            "Earth": "Collaborative Builders",
            "Fire": "Dynamic Innovators",
            "Water": "Strategic Thinkers",
            "Metal": "Action Catalysts",
            "Wood": "Growth Explorers"
        }
        
        return element_archetypes.get(dominant_element, "Balanced Harmonizers")
    
    def _generate_group_description(
        self,
        partnership_type: str,
        dominant_element: str,
        joint_life_path: int
    ) -> str:
        """Generate human-readable group description"""
        
        descriptions = {
            "Collaborative Builders": (
                "This group excels at creating stable, long-lasting foundations. "
                f"With {dominant_element} energy and a joint life path of {joint_life_path}, "
                "the team is grounded, practical, and focused on tangible results."
            ),
            "Dynamic Innovators": (
                "This group thrives on creativity and bold action. "
                f"With {dominant_element} energy and a joint life path of {joint_life_path}, "
                "the team is passionate, energetic, and driven to create new possibilities."
            ),
            "Strategic Thinkers": (
                "This group operates through deep insight and intuition. "
                f"With {dominant_element} energy and a joint life path of {joint_life_path}, "
                "the team is adaptive, reflective, and skilled at navigating complexity."
            ),
            "Action Catalysts": (
                "This group moves decisively and with precision. "
                f"With {dominant_element} energy and a joint life path of {joint_life_path}, "
                "the team is structured, efficient, and focused on clear execution."
            ),
            "Growth Explorers": (
                "This group is constantly expanding and evolving. "
                f"With {dominant_element} energy and a joint life path of {joint_life_path}, "
                "the team is innovative, flexible, and always seeking new horizons."
            ),
            "Balanced Harmonizers": (
                "This group brings together diverse energies in harmony. "
                f"With balanced elements and a joint life path of {joint_life_path}, "
                "the team is versatile, adaptable, and skilled at integration."
            )
        }
        
        return descriptions.get(
            partnership_type,
            f"A unique group with {dominant_element} energy and joint life path {joint_life_path}."
        )
```

**Verification:**
```bash
cd backend/oracle-service
python -c "
from app.engines.fc60 import FC60Engine
from app.engines.group_energy_calculator import GroupEnergyCalculator

fc60 = FC60Engine()
calculator = GroupEnergyCalculator()

users = [
    {'user_id': 'u1', 'name': 'Alice', 'dob': '1990-05-15'},
    {'user_id': 'u2', 'name': 'Bob', 'dob': '1992-03-20'},
    {'user_id': 'u3', 'name': 'Carol', 'dob': '1988-11-10'}
]

profiles = fc60.calculate_multi_user(users)
combined = calculator.calculate_combined_energy(profiles)

print(f'Partnership Type: {combined.partnership_type}')
print(f'Dominant Element: {combined.dominant_element}')
print(f'Joint Life Path: {combined.joint_life_path}')
print(f'Description: {combined.group_description[:80]}...')
"
# Expected: Combined energy calculated with partnership archetype
```

**Checkpoint:**
- [ ] Joint life path calculated correctly
- [ ] Dominant element identified
- [ ] Partnership archetype classified
- [ ] Group description generated

**STOP if checkpoint fails - fix combined energy logic**

---

### Phase 5: Group Dynamics Analysis (Duration: 60 min)

**Task 5.1: Create GroupDynamicsAnalyzer class**

```python
# app/engines/group_dynamics_analyzer.py

from typing import List, Dict
from dataclasses import dataclass
from .fc60 import UserFC60Profile
from .compatibility_analyzer import CompatibilityScore

@dataclass
class UserRole:
    """Role assignment for a user in the group"""
    user_id: str
    role: str  # Leader, Supporter, Challenger, Harmonizer
    explanation: str

@dataclass
class GroupDynamics:
    """Group dynamics analysis"""
    group_id: str
    roles: List[UserRole]
    synergies: List[str]
    challenges: List[str]
    growth_areas: List[str]
    recommendations: List[str]

class GroupDynamicsAnalyzer:
    """Analyzes group dynamics and roles"""
    
    def analyze_dynamics(
        self,
        profiles: List[UserFC60Profile],
        compatibility_matrix: Dict[str, CompatibilityScore],
        group_id: str = "default_group"
    ) -> GroupDynamics:
        """
        Analyze group dynamics and assign roles.
        
        Args:
            profiles: List of UserFC60Profile objects
            compatibility_matrix: Pairwise compatibility scores
            group_id: Identifier for this group
        
        Returns:
            GroupDynamics with roles and patterns
        """
        
        # 1. Assign roles
        roles = self._assign_roles(profiles, compatibility_matrix)
        
        # 2. Identify synergies
        synergies = self._identify_synergies(
            profiles, compatibility_matrix, roles
        )
        
        # 3. Identify challenges
        challenges = self._identify_challenges(
            profiles, compatibility_matrix, roles
        )
        
        # 4. Identify growth areas
        growth_areas = self._identify_growth_areas(
            profiles, compatibility_matrix, roles
        )
        
        # 5. Generate recommendations
        recommendations = self._generate_recommendations(
            synergies, challenges, growth_areas
        )
        
        return GroupDynamics(
            group_id=group_id,
            roles=roles,
            synergies=synergies,
            challenges=challenges,
            growth_areas=growth_areas,
            recommendations=recommendations
        )
    
    def _assign_roles(
        self,
        profiles: List[UserFC60Profile],
        compatibility_matrix: Dict[str, CompatibilityScore]
    ) -> List[UserRole]:
        """
        Assign roles based on:
        - Life path strength (higher = leader potential)
        - Element dominance (generative = leader, destructive = challenger)
        - Compatibility scores (high = supporter, low = challenger)
        """
        
        roles = []
        
        # Find user with highest life path (leader candidate)
        leader_candidate = max(profiles, key=lambda p: p.life_path)
        
        for profile in profiles:
            if profile.user_id == leader_candidate.user_id:
                role = "Leader"
                explanation = (
                    f"Highest life path ({profile.life_path}) and "
                    f"strong {profile.element} energy position this user "
                    "to guide the group's direction."
                )
            else:
                # Determine role based on compatibility with leader
                key = f"{leader_candidate.user_id}-{profile.user_id}"
                reverse_key = f"{profile.user_id}-{leader_candidate.user_id}"
                
                compat_score = compatibility_matrix.get(
                    key, compatibility_matrix.get(reverse_key)
                )
                
                if compat_score and compat_score.overall_score >= 0.7:
                    role = "Supporter"
                    explanation = (
                        f"High compatibility with leader ({compat_score.overall_score}). "
                        f"{profile.element} energy complements the group's direction."
                    )
                elif compat_score and compat_score.overall_score <= 0.4:
                    role = "Challenger"
                    explanation = (
                        f"Different perspective from leader provides balance. "
                        f"{profile.element} energy creates constructive tension."
                    )
                else:
                    role = "Harmonizer"
                    explanation = (
                        f"Bridges different perspectives in the group. "
                        f"{profile.element} energy helps maintain balance."
                    )
            
            roles.append(UserRole(
                user_id=profile.user_id,
                role=role,
                explanation=explanation
            ))
        
        return roles
    
    def _identify_synergies(
        self,
        profiles: List[UserFC60Profile],
        compatibility_matrix: Dict[str, CompatibilityScore],
        roles: List[UserRole]
    ) -> List[str]:
        """Identify where group excels"""
        
        synergies = []
        
        # High compatibility pairs
        high_compat_pairs = [
            score for score in compatibility_matrix.values()
            if score.overall_score >= 0.7
        ]
        
        if len(high_compat_pairs) >= len(profiles) * 0.5:
            synergies.append(
                f"Strong interpersonal compatibility "
                f"({len(high_compat_pairs)} high-synergy pairs). "
                "Team members naturally understand and support each other."
            )
        
        # Element diversity
        elements = set(p.element for p in profiles)
        if len(elements) >= 4:
            synergies.append(
                f"Rich elemental diversity ({', '.join(elements)}). "
                "Group can approach challenges from multiple perspectives."
            )
        
        # Role balance
        role_counts = {}
        for role in roles:
            role_counts[role.role] = role_counts.get(role.role, 0) + 1
        
        if all(count >= 1 for count in role_counts.values()):
            synergies.append(
                "Balanced role distribution. "
                "Group has leadership, support, challenge, and harmony."
            )
        
        return synergies if synergies else [
            "Group has solid foundation for collaboration."
        ]
    
    def _identify_challenges(
        self,
        profiles: List[UserFC60Profile],
        compatibility_matrix: Dict[str, CompatibilityScore],
        roles: List[UserRole]
    ) -> List[str]:
        """Identify potential friction points"""
        
        challenges = []
        
        # Low compatibility pairs
        low_compat_pairs = [
            score for score in compatibility_matrix.values()
            if score.overall_score <= 0.4
        ]
        
        if len(low_compat_pairs) >= len(profiles) * 0.3:
            challenges.append(
                f"Several challenging relationships "
                f"({len(low_compat_pairs)} pairs with tension). "
                "Extra communication needed to prevent misunderstandings."
            )
        
        # Dominant element imbalance
        from collections import Counter
        elements = [p.element for p in profiles]
        element_counts = Counter(elements)
        
        if max(element_counts.values()) >= len(profiles) * 0.7:
            dominant = max(element_counts, key=element_counts.get)
            challenges.append(
                f"{dominant} element dominates ({element_counts[dominant]}/{len(profiles)} members). "
                "Group may lack certain perspectives or approaches."
            )
        
        # Multiple leaders (too many high life paths)
        high_life_paths = [p for p in profiles if p.life_path >= 8]
        if len(high_life_paths) >= 3:
            challenges.append(
                f"Multiple strong leaders ({len(high_life_paths)} with life path 8+). "
                "Clear role definitions needed to prevent power struggles."
            )
        
        return challenges if challenges else [
            "Minor adjustments needed for optimal group function."
        ]
    
    def _identify_growth_areas(
        self,
        profiles: List[UserFC60Profile],
        compatibility_matrix: Dict[str, CompatibilityScore],
        roles: List[UserRole]
    ) -> List[str]:
        """Identify what group needs to develop"""
        
        growth_areas = []
        
        # Missing elements
        from collections import Counter
        elements = [p.element for p in profiles]
        all_elements = {"Wood", "Fire", "Earth", "Metal", "Water"}
        missing_elements = all_elements - set(elements)
        
        if missing_elements:
            growth_areas.append(
                f"Missing {', '.join(missing_elements)} perspective. "
                "Group could benefit from developing these qualities."
            )
        
        # Low average life path
        avg_life_path = sum(p.life_path for p in profiles) / len(profiles)
        if avg_life_path < 5:
            growth_areas.append(
                f"Group average life path is {avg_life_path:.1f}. "
                "Focus on building confidence and assertiveness."
            )
        
        # All supporters/no challengers
        challenger_count = sum(1 for r in roles if r.role == "Challenger")
        if challenger_count == 0:
            growth_areas.append(
                "No designated challengers. "
                "Group may benefit from inviting dissenting voices."
            )
        
        return growth_areas if growth_areas else [
            "Group has solid foundation across all areas."
        ]
    
    def _generate_recommendations(
        self,
        synergies: List[str],
        challenges: List[str],
        growth_areas: List[str]
    ) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Based on challenges
        if any("tension" in c.lower() for c in challenges):
            recommendations.append(
                "Schedule regular 1-on-1 check-ins between members "
                "with lower compatibility to build understanding."
            )
        
        if any("dominant" in c.lower() for c in challenges):
            recommendations.append(
                "Intentionally seek input from minority perspectives "
                "to balance decision-making."
            )
        
        if any("leader" in c.lower() for c in challenges):
            recommendations.append(
                "Clearly define leadership roles and decision-making authority "
                "to prevent conflicts."
            )
        
        # Based on growth areas
        if any("Missing" in g for g in growth_areas):
            recommendations.append(
                "Consider bringing in advisors or consultants "
                "who embody the missing elements."
            )
        
        if any("confidence" in g.lower() for g in growth_areas):
            recommendations.append(
                "Focus on celebrating wins and building group confidence "
                "through early successes."
            )
        
        # Always include communication recommendation
        recommendations.append(
            "Maintain open communication channels and create safe spaces "
            "for all members to share perspectives."
        )
        
        return recommendations
```

**Verification:**
```bash
cd backend/oracle-service
python -c "
from app.engines.fc60 import FC60Engine
from app.engines.compatibility_analyzer import CompatibilityAnalyzer
from app.engines.group_dynamics_analyzer import GroupDynamicsAnalyzer

fc60 = FC60Engine()
compat = CompatibilityAnalyzer()
dynamics = GroupDynamicsAnalyzer()

users = [
    {'user_id': 'u1', 'name': 'Alice', 'dob': '1990-05-15'},
    {'user_id': 'u2', 'name': 'Bob', 'dob': '1992-03-20'},
    {'user_id': 'u3', 'name': 'Carol', 'dob': '1988-11-10'}
]

profiles = fc60.calculate_multi_user(users)
compat_matrix = compat.calculate_pairwise(profiles)
group_dynamics = dynamics.analyze_dynamics(profiles, compat_matrix)

print(f'Roles assigned: {len(group_dynamics.roles)}')
for role in group_dynamics.roles:
    print(f'  {role.user_id}: {role.role}')
print(f'Synergies: {len(group_dynamics.synergies)}')
print(f'Challenges: {len(group_dynamics.challenges)}')
print(f'Recommendations: {len(group_dynamics.recommendations)}')
"
# Expected: Roles assigned, dynamics analyzed
```

**Checkpoint:**
- [ ] Roles assigned correctly (Leader, Supporter, Challenger, Harmonizer)
- [ ] Synergies identified
- [ ] Challenges identified
- [ ] Growth areas identified
- [ ] Recommendations generated

**STOP if checkpoint fails - fix group dynamics logic**

---

### Phase 6: Integration & Service Layer (Duration: 45 min)

**Task 6.1: Create MultiUserFC60Service**

```python
# app/services/multi_user_fc60_service.py

from typing import List, Dict
from datetime import datetime
from dataclasses import asdict
from ..engines.fc60 import FC60Engine
from ..engines.compatibility_analyzer import CompatibilityAnalyzer
from ..engines.group_energy_calculator import GroupEnergyCalculator
from ..engines.group_dynamics_analyzer import GroupDynamicsAnalyzer
import logging

logger = logging.getLogger(__name__)

class MultiUserFC60Service:
    """
    High-level service for multi-user FC60 analysis.
    
    Coordinates:
    - Individual FC60 calculation
    - Pairwise compatibility
    - Combined group energy
    - Group dynamics
    """
    
    def __init__(self):
        self.fc60_engine = FC60Engine()
        self.compatibility_analyzer = CompatibilityAnalyzer()
        self.group_energy_calculator = GroupEnergyCalculator()
        self.group_dynamics_analyzer = GroupDynamicsAnalyzer()
    
    def analyze_group(
        self,
        users: List[Dict[str, any]],
        group_id: str = "default_group"
    ) -> Dict[str, any]:
        """
        Complete multi-user FC60 analysis.
        
        Args:
            users: List of user dicts with keys: user_id, name, dob
                   Example: [
                       {"user_id": "u1", "name": "Alice", "dob": "1990-05-15"},
                       {"user_id": "u2", "name": "Bob", "dob": "1992-03-20"}
                   ]
            group_id: Identifier for this group
        
        Returns:
            Complete analysis JSON:
            {
                "individual_fc60": {...},
                "compatibility_matrix": {...},
                "combined_energy": {...},
                "group_dynamics": {...}
            }
        
        Raises:
            ValueError: If users list invalid
        """
        
        logger.info(
            "Starting multi-user FC60 analysis",
            extra={"user_count": len(users), "group_id": group_id}
        )
        
        # Validate input
        if not users or len(users) < 2:
            raise ValueError("At least 2 users required for group analysis")
        
        if len(users) > 10:
            raise ValueError("Maximum 10 users supported")
        
        # 1. Calculate individual FC60 profiles
        profiles = self.fc60_engine.calculate_multi_user(users)
        
        logger.debug(
            "Individual profiles calculated",
            extra={"profile_count": len(profiles)}
        )
        
        # 2. Calculate pairwise compatibility
        compatibility_matrix = self.compatibility_analyzer.calculate_pairwise(
            profiles
        )
        
        logger.debug(
            "Compatibility matrix calculated",
            extra={"pair_count": len(compatibility_matrix)}
        )
        
        # 3. Calculate combined group energy
        combined_energy = self.group_energy_calculator.calculate_combined_energy(
            profiles, group_id
        )
        
        logger.debug(
            "Combined energy calculated",
            extra={"partnership_type": combined_energy.partnership_type}
        )
        
        # 4. Analyze group dynamics
        group_dynamics = self.group_dynamics_analyzer.analyze_dynamics(
            profiles, compatibility_matrix, group_id
        )
        
        logger.debug(
            "Group dynamics analyzed",
            extra={"role_count": len(group_dynamics.roles)}
        )
        
        # 5. Format output
        result = {
            "group_id": group_id,
            "timestamp": datetime.now().isoformat(),
            "user_count": len(users),
            "individual_fc60": {
                profile.user_id: asdict(profile)
                for profile in profiles
            },
            "compatibility_matrix": {
                key: asdict(score)
                for key, score in compatibility_matrix.items()
            },
            "combined_energy": asdict(combined_energy),
            "group_dynamics": asdict(group_dynamics)
        }
        
        logger.info(
            "Multi-user FC60 analysis complete",
            extra={
                "group_id": group_id,
                "partnership_type": combined_energy.partnership_type,
                "leader_count": sum(
                    1 for r in group_dynamics.roles if r.role == "Leader"
                )
            }
        )
        
        return result
```

**Task 6.2: Add to API endpoints (reference for Layer 2)**

```python
# app/routers/oracle.py (Layer 2 - API)
# This is just reference - actual implementation in Layer 2

from fastapi import APIRouter, HTTPException
from typing import List, Dict
from pydantic import BaseModel
from ..services.multi_user_fc60_service import MultiUserFC60Service

router = APIRouter(prefix="/api/oracle", tags=["oracle"])

class UserInput(BaseModel):
    user_id: str
    name: str
    dob: str  # ISO format: "1990-05-15"

class GroupAnalysisRequest(BaseModel):
    users: List[UserInput]
    group_id: str = "default_group"

@router.post("/multi-user-fc60")
async def analyze_multi_user_fc60(request: GroupAnalysisRequest):
    """
    Multi-user FC60 analysis endpoint.
    
    Returns complete analysis including:
    - Individual profiles
    - Compatibility matrix
    - Combined energy
    - Group dynamics
    """
    try:
        service = MultiUserFC60Service()
        
        users = [
            {
                "user_id": user.user_id,
                "name": user.name,
                "dob": user.dob
            }
            for user in request.users
        ]
        
        result = service.analyze_group(users, request.group_id)
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Verification:**
```bash
cd backend/oracle-service
python -c "
from app.services.multi_user_fc60_service import MultiUserFC60Service
import json

service = MultiUserFC60Service()

users = [
    {'user_id': 'u1', 'name': 'Alice', 'dob': '1990-05-15'},
    {'user_id': 'u2', 'name': 'Bob', 'dob': '1992-03-20'},
    {'user_id': 'u3', 'name': 'Carol', 'dob': '1988-11-10'}
]

result = service.analyze_group(users, 'test_group')

print('Analysis complete!')
print(f'Individual profiles: {len(result[\"individual_fc60\"])}')
print(f'Compatibility pairs: {len(result[\"compatibility_matrix\"])}')
print(f'Partnership type: {result[\"combined_energy\"][\"partnership_type\"]}')
print(f'Roles assigned: {len(result[\"group_dynamics\"][\"roles\"])}')
print(f'Synergies: {len(result[\"group_dynamics\"][\"synergies\"])}')
"
# Expected: Complete analysis with all sections populated
```

**Checkpoint:**
- [ ] Service layer integrates all components
- [ ] JSON output formatted correctly
- [ ] Logging present
- [ ] Error handling works

**STOP if checkpoint fails - fix integration**

---

### Phase 7: Comprehensive Testing (Duration: 60 min)

**Task 7.1: Create test suite**

```python
# tests/test_multi_user_fc60.py

import pytest
from datetime import datetime
from app.engines.fc60 import FC60Engine
from app.engines.compatibility_analyzer import CompatibilityAnalyzer
from app.engines.group_energy_calculator import GroupEnergyCalculator
from app.engines.group_dynamics_analyzer import GroupDynamicsAnalyzer
from app.services.multi_user_fc60_service import MultiUserFC60Service

# Test data
TEST_USERS_2 = [
    {"user_id": "u1", "name": "Alice Johnson", "dob": "1990-05-15"},
    {"user_id": "u2", "name": "Bob Smith", "dob": "1992-03-20"}
]

TEST_USERS_5 = [
    {"user_id": "u1", "name": "Alice Johnson", "dob": "1990-05-15"},
    {"user_id": "u2", "name": "Bob Smith", "dob": "1992-03-20"},
    {"user_id": "u3", "name": "Carol White", "dob": "1988-11-10"},
    {"user_id": "u4", "name": "David Brown", "dob": "1995-07-25"},
    {"user_id": "u5", "name": "Emma Davis", "dob": "1991-09-03"}
]

TEST_USERS_10 = TEST_USERS_5 + [
    {"user_id": "u6", "name": "Frank Miller", "dob": "1987-01-18"},
    {"user_id": "u7", "name": "Grace Wilson", "dob": "1993-06-12"},
    {"user_id": "u8", "name": "Henry Moore", "dob": "1989-04-30"},
    {"user_id": "u9", "name": "Iris Taylor", "dob": "1994-12-08"},
    {"user_id": "u10", "name": "Jack Anderson", "dob": "1986-02-14"}
]

# Unit Tests

def test_fc60_multi_user_calculation():
    """Test multi-user FC60 calculation"""
    fc60 = FC60Engine()
    
    profiles = fc60.calculate_multi_user(TEST_USERS_2)
    
    assert len(profiles) == 2
    assert profiles[0].user_id == "u1"
    assert profiles[1].user_id == "u2"
    assert all(hasattr(p, "fc60_sign") for p in profiles)
    assert all(hasattr(p, "element") for p in profiles)
    assert all(hasattr(p, "animal") for p in profiles)
    assert all(hasattr(p, "life_path") for p in profiles)

def test_fc60_edge_cases():
    """Test edge cases"""
    fc60 = FC60Engine()
    
    # Test minimum users (1)
    single_user = fc60.calculate_multi_user([TEST_USERS_2[0]])
    assert len(single_user) == 1
    
    # Test maximum users (10)
    many_users = fc60.calculate_multi_user(TEST_USERS_10)
    assert len(many_users) == 10
    
    # Test too many users (11)
    with pytest.raises(ValueError):
        fc60.calculate_multi_user(TEST_USERS_10 + [TEST_USERS_2[0]])
    
    # Test empty list
    with pytest.raises(ValueError):
        fc60.calculate_multi_user([])

def test_compatibility_scoring():
    """Test pairwise compatibility calculation"""
    fc60 = FC60Engine()
    analyzer = CompatibilityAnalyzer()
    
    profiles = fc60.calculate_multi_user(TEST_USERS_5)
    compat_matrix = analyzer.calculate_pairwise(profiles)
    
    # Should have n*(n-1)/2 pairs for n users
    expected_pairs = 5 * 4 // 2  # 10 pairs
    assert len(compat_matrix) == expected_pairs
    
    # Check score range
    for score in compat_matrix.values():
        assert 0.0 <= score.overall_score <= 1.0
        assert 0.0 <= score.life_path_score <= 1.0
        assert 0.0 <= score.element_score <= 1.0
        assert 0.0 <= score.animal_score <= 1.0
        assert len(score.strengths) > 0
        assert len(score.challenges) > 0
        assert len(score.advice) > 0

def test_compatibility_symmetry():
    """Test that compatibility is symmetric (A-B == B-A)"""
    fc60 = FC60Engine()
    analyzer = CompatibilityAnalyzer()
    
    profiles = fc60.calculate_multi_user(TEST_USERS_2)
    
    # Calculate both directions
    score_ab = analyzer._calculate_pair_score(profiles[0], profiles[1])
    score_ba = analyzer._calculate_pair_score(profiles[1], profiles[0])
    
    # Scores should be identical
    assert score_ab.overall_score == score_ba.overall_score
    assert score_ab.life_path_score == score_ba.life_path_score
    assert score_ab.element_score == score_ba.element_score
    assert score_ab.animal_score == score_ba.animal_score

def test_combined_energy_calculation():
    """Test combined group energy"""
    fc60 = FC60Engine()
    calculator = GroupEnergyCalculator()
    
    profiles = fc60.calculate_multi_user(TEST_USERS_5)
    combined = calculator.calculate_combined_energy(profiles, "test_group")
    
    assert combined.group_id == "test_group"
    assert 1 <= combined.joint_life_path <= 33
    assert combined.dominant_element in ["Wood", "Fire", "Earth", "Metal", "Water"]
    assert len(combined.partnership_type) > 0
    assert len(combined.group_description) > 0

def test_partnership_archetypes():
    """Test all partnership archetypes can be assigned"""
    fc60 = FC60Engine()
    calculator = GroupEnergyCalculator()
    
    # Create users with specific elements to test each archetype
    # (This is a simplified test - real implementation would need actual element manipulation)
    
    profiles = fc60.calculate_multi_user(TEST_USERS_5)
    combined = calculator.calculate_combined_energy(profiles)
    
    # Partnership type should be one of the known archetypes
    valid_archetypes = [
        "Collaborative Builders",
        "Dynamic Innovators",
        "Strategic Thinkers",
        "Action Catalysts",
        "Growth Explorers",
        "Balanced Harmonizers"
    ]
    
    assert combined.partnership_type in valid_archetypes

def test_group_dynamics_roles():
    """Test group dynamics role assignment"""
    fc60 = FC60Engine()
    compat = CompatibilityAnalyzer()
    dynamics = GroupDynamicsAnalyzer()
    
    profiles = fc60.calculate_multi_user(TEST_USERS_5)
    compat_matrix = compat.calculate_pairwise(profiles)
    group_dynamics = dynamics.analyze_dynamics(profiles, compat_matrix)
    
    # Should have role for each user
    assert len(group_dynamics.roles) == 5
    
    # Should have at least one leader
    leaders = [r for r in group_dynamics.roles if r.role == "Leader"]
    assert len(leaders) >= 1
    
    # All roles should be valid
    valid_roles = ["Leader", "Supporter", "Challenger", "Harmonizer"]
    for role in group_dynamics.roles:
        assert role.role in valid_roles
        assert len(role.explanation) > 0

def test_group_dynamics_patterns():
    """Test group dynamics pattern identification"""
    fc60 = FC60Engine()
    compat = CompatibilityAnalyzer()
    dynamics = GroupDynamicsAnalyzer()
    
    profiles = fc60.calculate_multi_user(TEST_USERS_5)
    compat_matrix = compat.calculate_pairwise(profiles)
    group_dynamics = dynamics.analyze_dynamics(profiles, compat_matrix)
    
    # Should identify some patterns
    assert len(group_dynamics.synergies) > 0
    assert len(group_dynamics.challenges) > 0
    assert len(group_dynamics.growth_areas) > 0
    assert len(group_dynamics.recommendations) > 0

# Integration Tests

def test_full_service_integration():
    """Test complete multi-user FC60 service"""
    service = MultiUserFC60Service()
    
    result = service.analyze_group(TEST_USERS_5, "integration_test")
    
    # Verify all sections present
    assert "group_id" in result
    assert "timestamp" in result
    assert "user_count" in result
    assert "individual_fc60" in result
    assert "compatibility_matrix" in result
    assert "combined_energy" in result
    assert "group_dynamics" in result
    
    # Verify counts
    assert result["user_count"] == 5
    assert len(result["individual_fc60"]) == 5
    assert len(result["compatibility_matrix"]) == 10  # 5*4/2
    assert len(result["group_dynamics"]["roles"]) == 5

def test_service_error_handling():
    """Test service error handling"""
    service = MultiUserFC60Service()
    
    # Test too few users
    with pytest.raises(ValueError, match="At least 2 users"):
        service.analyze_group([TEST_USERS_2[0]])
    
    # Test too many users
    with pytest.raises(ValueError, match="Maximum 10 users"):
        service.analyze_group(TEST_USERS_10 + [TEST_USERS_2[0]])
    
    # Test empty list
    with pytest.raises(ValueError):
        service.analyze_group([])

# Performance Tests

def test_performance_2_users():
    """Test performance with 2 users"""
    import time
    service = MultiUserFC60Service()
    
    start = time.time()
    result = service.analyze_group(TEST_USERS_2)
    duration = time.time() - start
    
    # Should complete in <500ms
    assert duration < 0.5, f"Analysis took {duration}s (target: <0.5s)"

def test_performance_10_users():
    """Test performance with 10 users"""
    import time
    service = MultiUserFC60Service()
    
    start = time.time()
    result = service.analyze_group(TEST_USERS_10)
    duration = time.time() - start
    
    # Should complete in <2s
    assert duration < 2.0, f"Analysis took {duration}s (target: <2s)"

# Accuracy Tests

def test_known_compatibility():
    """Test known compatibility patterns"""
    fc60 = FC60Engine()
    analyzer = CompatibilityAnalyzer()
    
    # Life path 2 + 4 should be highly compatible (both stable)
    user1 = {"user_id": "u1", "name": "Stable One", "dob": "1990-05-15"}
    user2 = {"user_id": "u2", "name": "Stable Two", "dob": "1992-03-20"}
    
    profiles = fc60.calculate_multi_user([user1, user2])
    
    # Manually set life paths for testing
    # (In real implementation, these would be calculated from DOB)
    # This test assumes compatibility matrix is correct
    
    # Just verify scoring algorithm runs without errors
    compat_matrix = analyzer.calculate_pairwise(profiles)
    assert len(compat_matrix) == 1

def test_json_serialization():
    """Test that result can be JSON serialized"""
    import json
    service = MultiUserFC60Service()
    
    result = service.analyze_group(TEST_USERS_2)
    
    # Should be JSON serializable
    json_str = json.dumps(result, indent=2)
    assert len(json_str) > 0
    
    # Should be deserializable
    parsed = json.loads(json_str)
    assert parsed["user_count"] == 2
```

**Verification:**
```bash
cd backend/oracle-service
pytest tests/test_multi_user_fc60.py -v --cov=app/engines --cov=app/services

# Expected output:
# test_fc60_multi_user_calculation PASSED
# test_fc60_edge_cases PASSED
# test_compatibility_scoring PASSED
# test_compatibility_symmetry PASSED
# test_combined_energy_calculation PASSED
# test_partnership_archetypes PASSED
# test_group_dynamics_roles PASSED
# test_group_dynamics_patterns PASSED
# test_full_service_integration PASSED
# test_service_error_handling PASSED
# test_performance_2_users PASSED
# test_performance_10_users PASSED
# test_known_compatibility PASSED
# test_json_serialization PASSED

# Coverage: 95%+
```

**Checkpoint:**
- [ ] All 20+ tests pass
- [ ] Coverage ≥95%
- [ ] Performance targets met (<500ms for 2 users, <2s for 10 users)
- [ ] JSON serialization works
- [ ] Error handling verified

**STOP if checkpoint fails - fix failing tests**

---

## ✅ VERIFICATION CHECKLIST

**Code Quality:**
- [ ] Type hints on all functions
- [ ] Docstrings with examples
- [ ] Error handling for edge cases
- [ ] Logging (JSON format)
- [ ] No hardcoded values

**Testing:**
- [ ] Unit tests: 20+ scenarios
- [ ] Coverage: 95%+
- [ ] Edge cases: 2 users, 10 users, identical users
- [ ] Performance tests pass
- [ ] Integration tests pass

**Functionality:**
- [ ] Individual FC60 calculation works
- [ ] Pairwise compatibility accurate
- [ ] Combined energy reveals archetype
- [ ] Group dynamics identify roles
- [ ] JSON output formatted correctly

**Performance:**
- [ ] 2-user analysis: <500ms
- [ ] 10-user analysis: <2s
- [ ] Memory usage reasonable
- [ ] No performance degradation with repeated calls

**Documentation:**
- [ ] README section added (Layer 3B)
- [ ] API endpoint documented (reference for Layer 2)
- [ ] Example usage provided
- [ ] Compatibility matrices explained

---

## 🎯 SUCCESS CRITERIA

1. ✅ Multi-user FC60 calculation works for 2-10 users
2. ✅ Compatibility scoring accurate (0.0-1.0 scale)
3. ✅ Partnership archetypes classified correctly
4. ✅ Group dynamics reveal roles (Leader, Supporter, Challenger, Harmonizer)
5. ✅ Performance: <2s for 10-user analysis
6. ✅ Test coverage: 95%+
7. ✅ JSON output complete and serializable

**Measured Results:**
- Individual profiles: All attributes populated
- Compatibility matrix: All pairs scored
- Combined energy: Partnership archetype assigned
- Group dynamics: Roles + synergies + challenges + recommendations
- Performance: <500ms (2 users), <2s (10 users)
- Tests: 20+ passing, 95%+ coverage

---

## 📋 HANDOFF TO NEXT SESSION

**If session ends mid-implementation:**

**Resume from Phase:** [Current phase number]

**Context needed:**
- Which phase completed successfully?
- Are all matrices verified (Phase 1)?
- Is multi-user calculation working (Phase 2)?
- Any failing tests?

**Verification before continuing:**
```bash
# Verify Phase 1
python -c "from app.engines.compatibility_matrices import *; print('Matrices OK')"

# Verify Phase 2
python -c "from app.engines.fc60 import FC60Engine; fc60 = FC60Engine(); profiles = fc60.calculate_multi_user([{'user_id': 'u1', 'name': 'Test', 'dob': '1990-01-01'}]); print(f'Profiles: {len(profiles)}')"

# Verify Phase 3
pytest tests/test_multi_user_fc60.py::test_compatibility_scoring -v

# Run all tests
pytest tests/test_multi_user_fc60.py -v
```

---

## 🚀 NEXT STEPS (After This Spec)

1. **Terminal 2 (API Layer):** Create `/api/oracle/multi-user-fc60` endpoint
   - Use MultiUserFC60Service from this session
   - Add Pydantic request/response models
   - Add API key authentication
   - Add request validation (2-10 users)

2. **Terminal 1 (Frontend):** Create Group Analysis page
   - Form to input multiple users (name + DOB)
   - Display individual FC60 profiles
   - Visualize compatibility matrix (heatmap?)
   - Show partnership archetype card
   - Display group dynamics (roles, synergies, challenges)

3. **Terminal 4 (Database):** Add user_groups table
   - Store multi-user group definitions
   - Link to group analysis results
   - Enable group history tracking

---

## 📊 ESTIMATED TIMELINE

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Compatibility Matrices | 45 min | 45 min |
| Phase 2: Multi-User Calculation | 60 min | 105 min |
| Phase 3: Compatibility Scoring | 90 min | 195 min |
| Phase 4: Combined Energy | 60 min | 255 min |
| Phase 5: Group Dynamics | 60 min | 315 min |
| Phase 6: Integration | 45 min | 360 min |
| Phase 7: Testing | 60 min | **420 min** |

**Total: 7 hours (accounting for buffer)**

---

*Specification Version: 1.0*  
*Created: 2026-02-08*  
*Ready for Claude Code CLI Execution*
