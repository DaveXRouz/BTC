"""
BTC Puzzle Hunter — Crypto Engine
==================================
secp256k1 elliptic curve math, Bitcoin address utilities,
Pollard's Kangaroo algorithm, and optimized brute-force scanner.

Author: Built with Claude for competitive Bitcoin puzzle solving.
"""

import hashlib
import math
import time
import random
import logging

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# secp256k1 Curve Parameters
# ════════════════════════════════════════════════════════════

P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


# ════════════════════════════════════════════════════════════
# Elliptic Curve Point Arithmetic (Affine Coordinates)
# ════════════════════════════════════════════════════════════


class ECPoint:
    """A point on the secp256k1 elliptic curve (y² = x³ + 7 mod P)."""

    __slots__ = ("x", "y")

    def __init__(self, x=0, y=0):
        self.x = x % P if x else 0
        self.y = y % P if y else 0

    @property
    def is_infinity(self):
        return self.x == 0 and self.y == 0

    def __eq__(self, other):
        if not isinstance(other, ECPoint):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        if self.is_infinity:
            return "O (infinity)"
        return f"({hex(self.x)[:16]}…)"

    def __neg__(self):
        if self.is_infinity:
            return ECPoint(0, 0)
        return ECPoint(self.x, P - self.y)

    def __add__(self, other):
        if self.is_infinity:
            return ECPoint(other.x, other.y)
        if other.is_infinity:
            return ECPoint(self.x, self.y)

        if self.x == other.x:
            if self.y != other.y:
                return ECPoint(0, 0)
            if self.y == 0:
                return ECPoint(0, 0)
            # Point doubling
            lam = (3 * self.x * self.x * pow(2 * self.y, P - 2, P)) % P
        else:
            # Point addition
            lam = ((other.y - self.y) * pow(other.x - self.x, P - 2, P)) % P

        x3 = (lam * lam - self.x - other.x) % P
        y3 = (lam * (self.x - x3) - self.y) % P
        return ECPoint(x3, y3)

    def __mul__(self, scalar):
        return scalar_multiply(scalar, self)

    def __rmul__(self, scalar):
        return scalar_multiply(scalar, self)


# Constant points
INFINITY = ECPoint(0, 0)
G = ECPoint(Gx, Gy)


def scalar_multiply(k, point=None):
    """Compute k * point using double-and-add. Uses precomputed table for G."""
    if point is None:
        point = G
    if k == 0:
        return ECPoint(0, 0)
    if k < 0:
        k = -k
        point = -point
    k = k % N

    # Use precomputed table for generator point (3-4x speedup)
    if point.x == Gx and point.y == Gy:
        return _scalar_multiply_fast(k)

    result = ECPoint(0, 0)
    addend = ECPoint(point.x, point.y)

    while k:
        if k & 1:
            result = result + addend
        addend = addend + addend
        k >>= 1

    return result


# Precomputed table for generator point: _G_TABLE[i] = 2^i * G
_G_TABLE = None
_precompute_lock = __import__("threading").Lock()


def _ensure_g_table():
    """Build precomputed table of 2^i * G for i in 0..255. One-time cost ~0.5s."""
    global _G_TABLE
    if _G_TABLE is not None:
        return
    with _precompute_lock:
        if _G_TABLE is not None:
            return
        table = [None] * 256
        table[0] = ECPoint(G.x, G.y)
        for i in range(1, 256):
            table[i] = table[i - 1] + table[i - 1]
        _G_TABLE = table
        logger.info("EC precomputed table ready (256 entries)")


def _scalar_multiply_fast(k):
    """Compute k * G using precomputed table (no repeated doubling)."""
    _ensure_g_table()
    result = ECPoint(0, 0)
    i = 0
    while k:
        if k & 1:
            result = result + _G_TABLE[i]
        k >>= 1
        i += 1
    return result


# ════════════════════════════════════════════════════════════
# Bitcoin Address Utilities
# ════════════════════════════════════════════════════════════


def sha256(data):
    return hashlib.sha256(data).digest()


def ripemd160(data):
    return hashlib.new("ripemd160", data).digest()


def hash160(data):
    return ripemd160(sha256(data))


def base58_encode(data):
    """Encode bytes to Base58 string."""
    n = int.from_bytes(data, "big")
    result = ""
    while n > 0:
        n, r = divmod(n, 58)
        result = BASE58_ALPHABET[r] + result
    for byte in data:
        if byte == 0:
            result = "1" + result
        else:
            break
    return result or "1"


def base58check_encode(payload):
    """Encode payload with Base58Check (adds 4-byte checksum)."""
    checksum = sha256(sha256(payload))[:4]
    return base58_encode(payload + checksum)


def base58_decode(s):
    """Decode Base58 string to bytes."""
    n = 0
    for c in s:
        n = n * 58 + BASE58_ALPHABET.index(c)
    leading_zeros = 0
    for c in s:
        if c == "1":
            leading_zeros += 1
        else:
            break
    result = []
    while n > 0:
        n, r = divmod(n, 256)
        result.append(r)
    result.reverse()
    result = [0] * leading_zeros + result
    return bytes(result)


def address_to_hash160(address):
    """Decode a Bitcoin address → 20-byte hash160."""
    data = base58_decode(address)
    return data[1:21]


def pubkey_to_compressed(point):
    """Compress an EC point to 33-byte public key."""
    prefix = b"\x02" if point.y % 2 == 0 else b"\x03"
    return prefix + point.x.to_bytes(32, "big")


def pubkey_to_address(point):
    """EC point → Bitcoin P2PKH address (compressed)."""
    compressed = pubkey_to_compressed(point)
    h = hash160(compressed)
    return base58check_encode(b"\x00" + h)


def privkey_to_address(k):
    """Private key (int) → Bitcoin address."""
    pub = scalar_multiply(k)
    return pubkey_to_address(pub)


def privkey_to_wif(k, compressed=True):
    """Private key (int) → Wallet Import Format string."""
    key_bytes = k.to_bytes(32, "big")
    if compressed:
        payload = b"\x80" + key_bytes + b"\x01"
    else:
        payload = b"\x80" + key_bytes
    return base58check_encode(payload)


def decompress_pubkey(hex_str):
    """Decompress a hex-encoded public key → ECPoint."""
    if hex_str.startswith("04"):
        x = int(hex_str[2:66], 16)
        y = int(hex_str[66:130], 16)
    elif hex_str.startswith("02") or hex_str.startswith("03"):
        x = int(hex_str[2:66], 16)
        y_sq = (pow(x, 3, P) + 7) % P
        y = pow(y_sq, (P + 1) // 4, P)
        if hex_str.startswith("02") and y % 2 != 0:
            y = P - y
        elif hex_str.startswith("03") and y % 2 == 0:
            y = P - y
    else:
        raise ValueError(f"Invalid public key prefix: {hex_str[:2]}")
    return ECPoint(x, y)


# ════════════════════════════════════════════════════════════
# Pollard's Kangaroo Algorithm  (for puzzles with known pubkey)
# ════════════════════════════════════════════════════════════
#
# Solves: Given Q = k*G where  a ≤ k ≤ b,  find k.
# Complexity: O(√(b − a))  instead of  O(b − a) for brute-force.
# Requirement: the public key Q must be known.
# ════════════════════════════════════════════════════════════


class KangarooSolver:
    """
    Pollard's Kangaroo (Lambda) algorithm for the Elliptic Curve
    Discrete Logarithm Problem on secp256k1.
    """

    def __init__(self, target_pubkey, range_start, range_end, callback=None):
        """
        target_pubkey : ECPoint — the public key Q = k*G
        range_start   : int — lower bound of k  (inclusive)
        range_end     : int — upper bound of k  (inclusive)
        callback      : callable(dict) — receives progress updates
        """
        self.target = target_pubkey
        self.a = range_start
        self.b = range_end
        self.callback = callback

        # State
        self.running = False
        self.solved = False
        self.solution = None
        self.operations = 0
        self.dp_found = 0
        self.start_time = 0

        # ── Algorithm tuning ──
        range_size = self.b - self.a
        self.range_log = int(math.log2(range_size)) if range_size > 0 else 1
        sqrt_range = int(math.isqrt(range_size))

        # Number of distinct step sizes (more = better mixing)
        self.num_steps = max(8, min(128, self.range_log))

        # Step sizes:  s_i = 2^i  capped so mean ≈ √range / 4
        max_step = max(1, sqrt_range >> 2)
        self.step_sizes = []
        for i in range(self.num_steps):
            s = 1 << min(i, max_step.bit_length() - 1)
            self.step_sizes.append(min(s, max_step))

        # Precompute  s_i * G  for each step size
        self.step_points = []
        for s in self.step_sizes:
            self.step_points.append(scalar_multiply(s))

        # Distinguished-point mask  (density ≈ 1 in 2^dp_bits)
        self.dp_bits = max(2, (self.range_log // 2) - 2)
        self.dp_mask = (1 << self.dp_bits) - 1

        # Tables: x-coordinate → accumulated distance
        self.tame_table = {}
        self.wild_table = {}

        # Expected operations for progress estimation
        self.expected_ops = int(2.1 * math.isqrt(range_size))

    # ── helpers ──

    def _step_index(self, point):
        return point.x % self.num_steps

    def _is_dp(self, point):
        return (point.x & self.dp_mask) == 0

    def _verify(self, k):
        if k < self.a or k > self.b:
            return False
        return scalar_multiply(k) == self.target

    # ── main loop ──

    def solve(self):
        """
        Run Kangaroo. Returns the private key (int) or None if stopped.
        This is a blocking call — run it in a thread.
        """
        self.running = True
        self.solved = False
        self.solution = None
        self.operations = 0
        self.dp_found = 0
        self.start_time = time.time()

        # Tame kangaroo starts at the upper bound
        tame_point = scalar_multiply(self.b)
        tame_dist = 0

        # Wild kangaroo starts at the target public key
        wild_point = ECPoint(self.target.x, self.target.y)
        wild_dist = 0

        while self.running:
            # ── Tame step ──
            idx = self._step_index(tame_point)
            tame_point = tame_point + self.step_points[idx]
            tame_dist += self.step_sizes[idx]
            self.operations += 1

            if self._is_dp(tame_point):
                self.dp_found += 1
                key = tame_point.x
                if key in self.wild_table:
                    k = self.b + tame_dist - self.wild_table[key]
                    if self._verify(k):
                        self.solution = k
                        self.solved = True
                        self.running = False
                        self._emit()
                        return k
                self.tame_table[key] = tame_dist

            # ── Wild step ──
            idx = self._step_index(wild_point)
            wild_point = wild_point + self.step_points[idx]
            wild_dist += self.step_sizes[idx]
            self.operations += 1

            if self._is_dp(wild_point):
                self.dp_found += 1
                key = wild_point.x
                if key in self.tame_table:
                    k = self.b + self.tame_table[key] - wild_dist
                    if self._verify(k):
                        self.solution = k
                        self.solved = True
                        self.running = False
                        self._emit()
                        return k
                self.wild_table[key] = wild_dist

            # ── Progress callback every 500 ops ──
            if self.callback and self.operations % 500 == 0:
                self._emit()

        return None

    def _emit(self):
        if not self.callback:
            return
        elapsed = time.time() - self.start_time
        speed = self.operations / max(0.001, elapsed)
        progress = min(99.9, (self.operations / max(1, self.expected_ops)) * 100)
        if self.solved:
            progress = 100.0
        self.callback(
            {
                "type": "kangaroo",
                "operations": self.operations,
                "dp_found": self.dp_found,
                "progress": progress,
                "speed": speed,
                "elapsed": elapsed,
                "expected_ops": self.expected_ops,
                "solved": self.solved,
                "solution": self.solution,
                "tame_dps": len(self.tame_table),
                "wild_dps": len(self.wild_table),
            }
        )

    def stop(self):
        self.running = False


# ════════════════════════════════════════════════════════════
# Optimized Brute-Force  (for puzzles WITHOUT known pubkey)
# ════════════════════════════════════════════════════════════
#
# Optimization:  P_{k+1} = P_k + G   (one point addition per key,
#                not a full scalar multiplication).
# Compares hash160 directly (avoids base58 encoding overhead).
# ════════════════════════════════════════════════════════════


class BruteForceSolver:
    """
    Sequential key scanner with incremental point addition.
    Compares hash160 instead of full address for speed.
    """

    def __init__(self, target_address, range_start, range_end, callback=None):
        self.target_address = target_address
        self.target_h160 = address_to_hash160(target_address)
        self.a = range_start
        self.b = range_end
        self.callback = callback

        self.running = False
        self.solved = False
        self.solution = None
        self.operations = 0
        self.start_time = 0
        self.total_keys = self.b - self.a + 1

    def solve(self):
        """
        Scan keys from range_start to range_end.
        Returns private key (int) or None if stopped / not found.
        """
        self.running = True
        self.solved = False
        self.solution = None
        self.operations = 0
        self.start_time = time.time()

        # Initial point: P = a * G  (one scalar multiplication)
        current = scalar_multiply(self.a)
        k = self.a

        while self.running and k <= self.b:
            # Check this key's address
            compressed = pubkey_to_compressed(current)
            h = hash160(compressed)

            if h == self.target_h160:
                # Verify with full address
                addr = base58check_encode(b"\x00" + h)
                if addr == self.target_address:
                    self.solution = k
                    self.solved = True
                    self.running = False
                    self._emit()
                    return k

            # Next key: P_{k+1} = P_k + G
            current = current + G
            k += 1
            self.operations += 1

            if self.callback and self.operations % 200 == 0:
                self._emit()

        return None

    def _emit(self):
        if not self.callback:
            return
        elapsed = time.time() - self.start_time
        speed = self.operations / max(0.001, elapsed)
        progress = min(99.9, (self.operations / self.total_keys) * 100)
        if self.solved:
            progress = 100.0
        self.callback(
            {
                "type": "bruteforce",
                "operations": self.operations,
                "progress": progress,
                "speed": speed,
                "elapsed": elapsed,
                "total_keys": self.total_keys,
                "current_key": hex(self.a + self.operations),
                "solved": self.solved,
                "solution": self.solution,
            }
        )

    def stop(self):
        self.running = False


# ════════════════════════════════════════════════════════════
# Self-Test  (proves both algorithms work correctly)
# ════════════════════════════════════════════════════════════


def self_test_kangaroo(bit_size=20, callback=None):
    """
    Generate a random key in [2^(bit_size-1), 2^bit_size),
    compute its public key, then recover it with Kangaroo.
    Returns (success, key, found_key, elapsed).
    """
    range_start = 1 << (bit_size - 1)
    range_end = (1 << bit_size) - 1

    secret = random.randint(range_start, range_end)
    pubkey = scalar_multiply(secret)

    solver = KangarooSolver(pubkey, range_start, range_end, callback=callback)
    found = solver.solve()
    elapsed = time.time() - solver.start_time

    return (found == secret, secret, found, elapsed)


def self_test_bruteforce(bit_size=16, callback=None):
    """
    Generate a random key in a small range, compute its address,
    then recover it with brute-force.
    Returns (success, key, found_key, elapsed).
    """
    range_start = 1 << (bit_size - 1)
    range_end = (1 << bit_size) - 1

    secret = random.randint(range_start, range_end)
    address = privkey_to_address(secret)

    solver = BruteForceSolver(address, range_start, range_end, callback=callback)
    found = solver.solve()
    elapsed = time.time() - solver.start_time

    return (found == secret, secret, found, elapsed)


# ════════════════════════════════════════════════════════════
# Puzzle Database
# ════════════════════════════════════════════════════════════

PUZZLES = {
    # ── Small puzzles (solved) — good for testing ──
    20: {
        "address": "1HsMJxNiV7TLxmoF6uJNkydxPFDog4NQum",
        "range_start": 2**19,
        "range_end": 2**20 - 1,
        "public_key": None,
        "type": "A",
        "reward_btc": 0.020,
        "solved": True,
    },
    25: {
        "address": "15JhYXn6Mx3oF4Y7PcTAv2wVVAuCFFQNiP",
        "range_start": 2**24,
        "range_end": 2**25 - 1,
        "public_key": None,
        "type": "A",
        "reward_btc": 0.025,
        "solved": True,
    },
    30: {
        "address": "1LHtnpd8nU5VHEMkG2TMYYNUjjLc992bps",
        "range_start": 2**29,
        "range_end": 2**30 - 1,
        "public_key": None,
        "type": "A",
        "reward_btc": 0.030,
        "solved": True,
    },
    35: {
        "address": "1PWCx5fovoEaoBowAvF5k91m2Xat9bMgwb",
        "range_start": 2**34,
        "range_end": 2**35 - 1,
        "public_key": None,
        "type": "A",
        "reward_btc": 0.035,
        "solved": True,
    },
    40: {
        "address": "1EeAxcprB2PpCnr34VfZdFrkUWuxyiNEFv",
        "range_start": 2**39,
        "range_end": 2**40 - 1,
        "public_key": None,
        "type": "A",
        "reward_btc": 0.040,
        "solved": True,
    },
    # ── Currently active puzzles ──
    71: {
        "address": "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU",
        "range_start": 2**70,
        "range_end": 2**71 - 1,
        "public_key": None,  # Not exposed — brute-force only
        "type": "A",
        "reward_btc": 7.10,
        "solved": False,
    },
    72: {
        "address": "1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR",
        "range_start": 2**71,
        "range_end": 2**72 - 1,
        "public_key": None,
        "type": "A",
        "reward_btc": 7.20,
        "solved": False,
    },
    75: {
        "address": "1J36UjUByGroXcCvmj13U6uwaVv9caEeAt",
        "range_start": 2**74,
        "range_end": 2**75 - 1,
        "public_key": None,  # Exposed on-chain — user must paste it
        "type": "B",  # Kangaroo eligible!
        "reward_btc": 7.50,
        "solved": False,
        "note": "Public key exposed on-chain. Paste it to use Kangaroo.",
    },
    80: {
        "address": "1BCf6rHUW6m3iH2ptsvnjgLruAiPQQepLe",
        "range_start": 2**79,
        "range_end": 2**80 - 1,
        "public_key": None,
        "type": "B",
        "reward_btc": 8.00,
        "solved": False,
        "note": "Public key exposed on-chain. Paste it to use Kangaroo.",
    },
    85: {
        "address": "1Kh22PvXERd2xpTQk3ur6pPEqFeckCJfAr",
        "range_start": 2**84,
        "range_end": 2**85 - 1,
        "public_key": None,
        "type": "B",
        "reward_btc": 8.50,
        "solved": False,
        "note": "Public key exposed on-chain. Paste it to use Kangaroo.",
    },
    90: {
        "address": "1L12FHH2FHjvTviyanuiFVfmzCy46RRATU",
        "range_start": 2**89,
        "range_end": 2**90 - 1,
        "public_key": None,
        "type": "B",
        "reward_btc": 9.00,
        "solved": False,
        "note": "Public key exposed on-chain. Paste it to use Kangaroo.",
    },
    130: {
        "address": "1Fo65aKq8s8iquMt6weF1rku1moWVEd5Ua",
        "range_start": 2**129,
        "range_end": 2**130 - 1,
        "public_key": "03633cbe3ec02b9401c5effa144c5b4d22f87940259634858fc7e59b1c09937852",
        "type": "B",
        "reward_btc": 13.00,
        "solved": False,
        "note": "Most famous Kangaroo target. Public key known.",
    },
}


def get_performance_estimate(puzzle_num, algo="auto"):
    """
    Estimate solve time in Python for a given puzzle.
    Returns dict with estimates.
    """
    puz = PUZZLES.get(puzzle_num)
    if not puz:
        return None

    range_size = puz["range_end"] - puz["range_start"] + 1
    py_speed_add = 3000  # point additions/sec (pure Python estimate)
    py_speed_brute = 2000  # address checks/sec

    if algo == "auto":
        algo = (
            "kangaroo" if puz["type"] == "B" and puz.get("public_key") else "bruteforce"
        )

    if algo == "kangaroo":
        ops = int(2.1 * math.isqrt(range_size))
        seconds = ops / py_speed_add
    else:
        ops = range_size
        seconds = ops / py_speed_brute

    return {
        "algorithm": algo,
        "operations": ops,
        "python_secs": seconds,
        "python_human": _human_time(seconds),
        "c_gpu_speedup": "~1000–10000x faster with C/CUDA",
    }


def _human_time(seconds):
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    if seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    if seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    if seconds < 86400 * 365:
        return f"{seconds/86400:.1f} days"
    return f"{seconds/(86400*365):.1f} years"
