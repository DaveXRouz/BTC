"""
Base-60 Codec - Core Tier Module 2
===================================
Purpose: Encode/decode integers using FC60's syllabic base-60 alphabet
         Maps 0-59 to animal+element tokens, supports multi-digit base-60 numbers

The Foundation: 60 = 12 × 5
- 12 Animals (Chinese zodiac / Earthly Branches)
- 5 Elements (Wu Xing)
- Creates 60 unique 4-character tokens

All mappings are deterministic and bijective (one-to-one)
"""

from typing import List


class Base60Codec:
    """
    Core encoder/decoder for FC60's base-60 syllabic alphabet.
    
    TOKEN60(n) = ANIMAL[n÷5] + ELEMENT[n mod 5]
    DIGIT60(token) = animal_index × 5 + element_index
    
    All functions are pure - same input always produces same output
    """
    
    # The 12 Animals (Earthly Branches / 地支 Dìzhī)
    ANIMALS = [
        "RA",  # 0  - Rat (子 Zǐ)       - Instinct, resourcefulness
        "OX",  # 1  - Ox (丑 Chǒu)      - Endurance, patience
        "TI",  # 2  - Tiger (寅 Yín)    - Courage, power
        "RU",  # 3  - Rabbit (卯 Mǎo)   - Intuition, diplomacy
        "DR",  # 4  - Dragon (辰 Chén)  - Destiny, transformation
        "SN",  # 5  - Snake (巳 Sì)     - Wisdom, precision
        "HO",  # 6  - Horse (午 Wǔ)     - Freedom, movement
        "GO",  # 7  - Goat (未 Wèi)     - Vision, creativity
        "MO",  # 8  - Monkey (申 Shēn)  - Adaptability, cleverness
        "RO",  # 9  - Rooster (酉 Yǒu)  - Truth, confidence
        "DO",  # 10 - Dog (戌 Xū)       - Loyalty, protection
        "PI",  # 11 - Pig (亥 Hài)      - Abundance, generosity
    ]
    
    # The 5 Elements (Wu Xing / 五行)
    ELEMENTS = [
        "WU",  # 0 - Wood (木 Mù)    - Growth, flexibility
        "FI",  # 1 - Fire (火 Huǒ)   - Transformation, passion
        "ER",  # 2 - Earth (土 Tǔ)   - Grounding, stability
        "MT",  # 3 - Metal (金 Jīn)  - Refinement, structure
        "WA",  # 4 - Water (水 Shuǐ) - Depth, flow
    ]
    
    # Build reverse lookup dictionaries for fast decoding
    ANIMAL_TO_INDEX = {animal: i for i, animal in enumerate(ANIMALS)}
    ELEMENT_TO_INDEX = {element: i for i, element in enumerate(ELEMENTS)}
    
    @staticmethod
    def token60(n: int) -> str:
        """
        Encode integer 0-59 as 4-character FC60 token.
        
        Algorithm:
            quotient = n ÷ 5 (determines animal)
            remainder = n mod 5 (determines element)
            token = ANIMAL[quotient] + ELEMENT[remainder]
        
        Args:
            n: Integer from 0 to 59
            
        Returns:
            4-character token (e.g., "RAWU", "PIWA")
            
        Raises:
            ValueError: If n is not in range 0-59
            
        Examples:
            >>> Base60Codec.token60(0)
            'RAWU'
            >>> Base60Codec.token60(26)
            'SNFI'
            >>> Base60Codec.token60(59)
            'PIWA'
        """
        if not 0 <= n <= 59:
            raise ValueError(f"token60 requires 0 ≤ n ≤ 59, got {n}")
        
        quotient = n // 5
        remainder = n % 5
        
        return Base60Codec.ANIMALS[quotient] + Base60Codec.ELEMENTS[remainder]
    
    @staticmethod
    def digit60(token: str) -> int:
        """
        Decode 4-character FC60 token to integer 0-59.
        
        Algorithm:
            animal_index = lookup(token[0:2])
            element_index = lookup(token[2:4])
            n = animal_index × 5 + element_index
        
        Args:
            token: 4-character token (e.g., "RAWU", "PIWA")
            
        Returns:
            Integer from 0 to 59
            
        Raises:
            ValueError: If token is invalid
            
        Examples:
            >>> Base60Codec.digit60("RAWU")
            0
            >>> Base60Codec.digit60("SNFI")
            26
            >>> Base60Codec.digit60("PIWA")
            59
        """
        if len(token) != 4:
            raise ValueError(f"Token must be 4 characters, got '{token}' ({len(token)} chars)")
        
        animal = token[0:2].upper()
        element = token[2:4].upper()
        
        if animal not in Base60Codec.ANIMAL_TO_INDEX:
            raise ValueError(f"Invalid animal token: '{animal}'")
        if element not in Base60Codec.ELEMENT_TO_INDEX:
            raise ValueError(f"Invalid element token: '{element}'")
        
        animal_idx = Base60Codec.ANIMAL_TO_INDEX[animal]
        element_idx = Base60Codec.ELEMENT_TO_INDEX[element]
        
        return animal_idx * 5 + element_idx
    
    @staticmethod
    def to_base60(n: int) -> List[int]:
        """
        Convert non-negative integer to list of base-60 digits (MSD first).
        
        Args:
            n: Non-negative integer
            
        Returns:
            List of digits (each 0-59), most significant digit first
            
        Raises:
            ValueError: If n is negative
            
        Examples:
            >>> Base60Codec.to_base60(0)
            [0]
            >>> Base60Codec.to_base60(59)
            [59]
            >>> Base60Codec.to_base60(60)
            [1, 0]
            >>> Base60Codec.to_base60(2026)
            [33, 46]
        """
        if n < 0:
            raise ValueError(f"to_base60 requires n ≥ 0, got {n}")
        
        if n == 0:
            return [0]
        
        digits = []
        while n > 0:
            digits.insert(0, n % 60)
            n //= 60
        
        return digits
    
    @staticmethod
    def from_base60(digits: List[int]) -> int:
        """
        Convert list of base-60 digits to integer.
        
        Args:
            digits: List of base-60 digits (each 0-59)
            
        Returns:
            Integer value
            
        Raises:
            ValueError: If any digit is out of range
            
        Examples:
            >>> Base60Codec.from_base60([0])
            0
            >>> Base60Codec.from_base60([59])
            59
            >>> Base60Codec.from_base60([1, 0])
            60
            >>> Base60Codec.from_base60([33, 46])
            2026
        """
        for i, d in enumerate(digits):
            if not 0 <= d <= 59:
                raise ValueError(f"Digit {i} out of range: {d} (must be 0-59)")
        
        result = 0
        for digit in digits:
            result = result * 60 + digit
        
        return result
    
    @staticmethod
    def encode_base60(n: int) -> str:
        """
        Encode integer as hyphen-separated FC60 tokens.
        
        For negative numbers, prefix with "NEG-"
        
        Args:
            n: Any integer
            
        Returns:
            Encoded string (e.g., "HOMT-ROFI", "NEG-OXMT-DRWU")
            
        Examples:
            >>> Base60Codec.encode_base60(0)
            'RAWU'
            >>> Base60Codec.encode_base60(2026)
            'HOMT-ROFI'
            >>> Base60Codec.encode_base60(-500)
            'NEG-OXMT-DRWU'
        """
        if n < 0:
            return "NEG-" + Base60Codec.encode_base60(-n)
        
        digits = Base60Codec.to_base60(n)
        tokens = [Base60Codec.token60(d) for d in digits]
        
        return "-".join(tokens)
    
    @staticmethod
    def decode_base60(encoded: str) -> int:
        """
        Decode hyphen-separated FC60 tokens to integer.
        
        Handles "NEG-" prefix for negative numbers
        
        Args:
            encoded: Encoded string (e.g., "HOMT-ROFI")
            
        Returns:
            Integer value
            
        Raises:
            ValueError: If encoding is invalid
            
        Examples:
            >>> Base60Codec.decode_base60("RAWU")
            0
            >>> Base60Codec.decode_base60("HOMT-ROFI")
            2026
            >>> Base60Codec.decode_base60("NEG-OXMT-DRWU")
            -500
        """
        # Handle negative numbers
        negative = False
        if encoded.startswith("NEG-"):
            negative = True
            encoded = encoded[4:]
        
        # Split into tokens and decode each
        tokens = encoded.split("-")
        digits = [Base60Codec.digit60(tok) for tok in tokens]
        
        # Convert from base-60
        result = Base60Codec.from_base60(digits)
        
        return -result if negative else result
    
    @staticmethod
    def get_animal_name(index: int) -> str:
        """Get the full name of an animal by index (0-11)."""
        names = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
                 "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]
        return names[index]
    
    @staticmethod
    def get_element_name(index: int) -> str:
        """Get the full name of an element by index (0-4)."""
        names = ["Wood", "Fire", "Earth", "Metal", "Water"]
        return names[index]
    
    @staticmethod
    def describe_token(token: str) -> str:
        """
        Get human-readable description of a token.
        
        Args:
            token: 4-character FC60 token
            
        Returns:
            Description string
            
        Example:
            >>> Base60Codec.describe_token("SNFI")
            'SNFI = 26 (Snake Fire)'
        """
        n = Base60Codec.digit60(token)
        animal_idx = n // 5
        element_idx = n % 5
        animal_name = Base60Codec.get_animal_name(animal_idx)
        element_name = Base60Codec.get_element_name(element_idx)
        
        return f"{token} = {n} ({animal_name} {element_name})"


# Complete lookup table (for reference and validation)
TOKEN_TABLE = {i: Base60Codec.token60(i) for i in range(60)}

# Test vectors
TEST_VECTORS = [
    # (number, expected_token)
    (0, "RAWU"),
    (6, "OXFI"),
    (26, "SNFI"),
    (57, "PIER"),
    (59, "PIWA"),
    (60, "RAFI-RAWU"),
    (2026, "HOMT-ROFI"),
    (2461078, "TIFI-DRMT-GOER-PIMT"),  # JDN for 2026-02-06
    (-500, "NEG-OXMT-DRWU"),
]


def run_self_test() -> bool:
    """
    Run comprehensive self-test on the Base-60 Codec.
    
    Returns:
        True if all tests pass, False otherwise
    """
    print("=" * 60)
    print("BASE-60 CODEC - SELF TEST")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # Test 1: Round-trip for all 60 tokens
    print("\n1. Testing round-trip for all 60 tokens (0-59):")
    all_good = True
    for i in range(60):
        token = Base60Codec.token60(i)
        back = Base60Codec.digit60(token)
        if back != i:
            all_good = False
            print(f"   ✗ {i} → {token} → {back}")
            failed += 1
            break
    if all_good:
        print(f"   ✓ All 60 tokens round-trip correctly")
        passed += 1
    
    # Test 2: Specific test vectors
    print("\n2. Testing specific encodings:")
    for number, expected_token in TEST_VECTORS:
        computed = Base60Codec.encode_base60(number)
        if computed == expected_token:
            passed += 1
            print(f"   ✓ {number:10d} → {computed}")
        else:
            failed += 1
            print(f"   ✗ {number:10d} → {computed} (expected {expected_token})")
    
    # Test 3: Decode round-trip
    print("\n3. Testing decode round-trip:")
    for number, token in TEST_VECTORS:
        decoded = Base60Codec.decode_base60(token)
        if decoded == number:
            passed += 1
            print(f"   ✓ {token} → {decoded}")
        else:
            failed += 1
            print(f"   ✗ {token} → {decoded} (expected {number})")
    
    # Test 4: Base-60 arithmetic
    print("\n4. Testing base-60 arithmetic:")
    test_numbers = [0, 59, 60, 3600, 2026]
    for n in test_numbers:
        digits = Base60Codec.to_base60(n)
        back = Base60Codec.from_base60(digits)
        if back == n:
            passed += 1
            print(f"   ✓ {n} → {digits} → {back}")
        else:
            failed += 1
            print(f"   ✗ {n} → {digits} → {back}")
    
    # Test 5: Token descriptions
    print("\n5. Testing token descriptions:")
    sample_tokens = ["RAWU", "SNFI", "PIWA"]
    for token in sample_tokens:
        desc = Base60Codec.describe_token(token)
        print(f"   {desc}")
        passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_self_test()
    exit(0 if success else 1)
