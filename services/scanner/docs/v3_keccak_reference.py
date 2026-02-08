"""
Pure Python Keccak-256 implementation.

This is Keccak-256 (NOT SHA3-256). The difference is the padding byte:
Keccak uses 0x01, SHA3 uses 0x06. This is critical for Ethereum address
derivation which requires original Keccak-256.
"""

# Keccak-f[1600] round constants
ROUND_CONSTANTS = [
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
]

# Rotation offsets for rho step
ROTATION_OFFSETS = [
    [0, 1, 62, 28, 27],
    [36, 44, 6, 55, 20],
    [3, 10, 43, 25, 39],
    [41, 45, 15, 21, 8],
    [18, 2, 61, 56, 14],
]

MASK64 = (1 << 64) - 1


def _rol64(x, n):
    """64-bit rotate left."""
    n = n % 64
    return ((x << n) | (x >> (64 - n))) & MASK64


def _keccak_f1600(state):
    """Apply 24 rounds of Keccak-f[1600] permutation to 5x5 state array."""
    for rc in ROUND_CONSTANTS:
        # Theta step
        c = [
            state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4]
            for x in range(5)
        ]
        d = [c[(x - 1) % 5] ^ _rol64(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x][y] ^= d[x]

        # Rho and Pi steps
        b = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                b[y][(2 * x + 3 * y) % 5] = _rol64(state[x][y], ROTATION_OFFSETS[y][x])

        # Chi step
        for x in range(5):
            for y in range(5):
                state[x][y] = b[x][y] ^ (
                    (~b[(x + 1) % 5][y] & MASK64) & b[(x + 2) % 5][y]
                )

        # Iota step
        state[0][0] ^= rc

    return state


def keccak256(data: bytes) -> bytes:
    """Compute Keccak-256 hash of data. Returns 32 bytes.

    This is the original Keccak-256 used by Ethereum, NOT NIST SHA3-256.
    The only difference is the domain separation byte: 0x01 for Keccak, 0x06 for SHA3.
    """
    rate = 136  # (1600 - 512) / 8 = 136 bytes
    capacity_bytes = 64  # 512 / 8

    # Initialize state: 5x5 array of 64-bit words
    state = [[0] * 5 for _ in range(5)]

    # Absorb phase
    # Pad the message: Keccak padding is multi-rate padding (pad10*1)
    # Append 0x01 byte, then zeros, then set last bit of rate block
    msg = bytearray(data)
    # Keccak padding: append 0x01, pad with 0x00, set last byte |= 0x80
    msg.append(0x01)
    while len(msg) % rate != 0:
        msg.append(0x00)
    # Set the last bit of the last byte in the block
    msg[-1] |= 0x80

    # Process each rate-sized block
    for block_start in range(0, len(msg), rate):
        block = msg[block_start : block_start + rate]
        # XOR block into state (rate portion only)
        for i in range(len(block) // 8):
            x = i % 5
            y = i // 5
            lane = int.from_bytes(block[i * 8 : (i + 1) * 8], "little")
            state[x][y] ^= lane
        state = _keccak_f1600(state)

    # Squeeze phase: extract 256 bits (32 bytes)
    output = bytearray()
    for y in range(5):
        for x in range(5):
            output.extend(state[x][y].to_bytes(8, "little"))
            if len(output) >= 32:
                return bytes(output[:32])

    return bytes(output[:32])
