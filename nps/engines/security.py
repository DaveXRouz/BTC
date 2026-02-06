"""
Encryption at rest for NPS.

Uses PBKDF2 key derivation (600K iterations, SHA-256) and HMAC-SHA256
stream cipher with authentication tag. All stdlib — no pip deps.

Prefixes:
    PLAIN:  — unencrypted (no password set)
    ENC:    — encrypted with master password

Thread safety: _master_key is set once at startup, read-only after.
"""

import hashlib
import hmac
import json
import logging
import os
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

# Module-level state (set once at startup)
_master_key = None  # bytes or None
_salt = None  # bytes or None
_lock = threading.Lock()

DATA_DIR = Path(__file__).parent.parent / "data"
SALT_FILE = DATA_DIR / ".vault_salt"

SENSITIVE_KEYS = ["private_key", "seed_phrase", "wif", "extended_private_key"]

_PBKDF2_ITERATIONS = 600_000
_SALT_LENGTH = 32
_KEY_LENGTH = 32


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from password + salt using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_KEY_LENGTH,
    )


def _load_or_create_salt() -> bytes:
    """Load existing salt from disk or create a new one."""
    global _salt
    if SALT_FILE.exists():
        _salt = SALT_FILE.read_bytes()
    else:
        _salt = os.urandom(_SALT_LENGTH)
        SALT_FILE.parent.mkdir(parents=True, exist_ok=True)
        SALT_FILE.write_bytes(_salt)
    return _salt


def has_salt() -> bool:
    """Check if a vault salt file exists (password was set before)."""
    return SALT_FILE.exists()


def set_master_password(password: str) -> bool:
    """Derive and set the master encryption key from a password.

    Returns True on success. Can only be called once per session.
    """
    global _master_key

    with _lock:
        if _master_key is not None:
            logger.warning("Master password already set for this session")
            return False

        salt = _load_or_create_salt()
        _master_key = _derive_key(password, salt)
        logger.info("Master password set — encryption enabled")
        return True


def change_master_password(old_password: str, new_password: str) -> bool:
    """Change the master password. Re-derives key with new salt."""
    global _master_key, _salt

    with _lock:
        if _salt is None:
            _load_or_create_salt()

        # Verify old password
        if _master_key is not None:
            old_key = _derive_key(old_password, _salt)
            if old_key != _master_key:
                raise ValueError("Old password is incorrect")

        # Generate new salt and key
        _salt = os.urandom(_SALT_LENGTH)
        SALT_FILE.write_bytes(_salt)
        _master_key = _derive_key(new_password, _salt)
        logger.info("Master password changed")
        return True


def is_encrypted_mode() -> bool:
    """Return True if a master password has been set for this session."""
    return _master_key is not None


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string.

    Returns 'ENC:<hex>' if password is set, 'PLAIN:<text>' otherwise.
    Uses HMAC-SHA256 as a stream cipher with a random nonce, plus an
    authentication tag.
    """
    if _master_key is None:
        return f"PLAIN:{plaintext}"

    plaintext_bytes = plaintext.encode("utf-8")
    nonce = os.urandom(16)

    # Generate keystream using HMAC-SHA256 in counter mode
    ciphertext = bytearray()
    for i in range((len(plaintext_bytes) + 31) // 32):
        counter = i.to_bytes(4, "big")
        block = hmac.new(_master_key, nonce + counter, hashlib.sha256).digest()
        ciphertext.extend(block)

    # XOR plaintext with keystream
    encrypted = bytes(a ^ b for a, b in zip(plaintext_bytes, ciphertext))

    # Authentication tag over nonce + ciphertext
    auth_tag = hmac.new(_master_key, nonce + encrypted, hashlib.sha256).digest()[:16]

    # Format: nonce (16) + ciphertext (variable) + auth_tag (16)
    payload = nonce + encrypted + auth_tag
    return f"ENC:{payload.hex()}"


def decrypt(encoded: str) -> str:
    """Decrypt an encoded string.

    Handles both 'ENC:' (encrypted) and 'PLAIN:' (unencrypted) prefixes.
    Raises ValueError on tamper detection or wrong password.
    """
    if encoded.startswith("PLAIN:"):
        return encoded[6:]

    if not encoded.startswith("ENC:"):
        # Legacy unencrypted data — return as-is
        return encoded

    if _master_key is None:
        raise ValueError("No master password set — cannot decrypt")

    try:
        payload = bytes.fromhex(encoded[4:])
    except ValueError:
        raise ValueError("Invalid encrypted data format")

    if len(payload) < 32:  # 16 nonce + 16 tag (0-length ciphertext is valid)
        raise ValueError("Encrypted data too short")

    nonce = payload[:16]
    auth_tag = payload[-16:]
    ciphertext = payload[16:-16]

    # Verify authentication tag
    expected_tag = hmac.new(_master_key, nonce + ciphertext, hashlib.sha256).digest()[
        :16
    ]

    if not hmac.compare_digest(auth_tag, expected_tag):
        raise ValueError("Decryption failed — wrong password or tampered data")

    # Decrypt using same keystream
    keystream = bytearray()
    for i in range((len(ciphertext) + 31) // 32):
        counter = i.to_bytes(4, "big")
        block = hmac.new(_master_key, nonce + counter, hashlib.sha256).digest()
        keystream.extend(block)

    plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
    return plaintext.decode("utf-8")


def encrypt_dict(data: dict, sensitive_keys: list = None) -> dict:
    """Encrypt sensitive fields in a dict. Returns a new dict."""
    if sensitive_keys is None:
        sensitive_keys = SENSITIVE_KEYS

    result = {}
    for key, value in data.items():
        if key in sensitive_keys and isinstance(value, str):
            result[key] = encrypt(value)
        elif isinstance(value, dict):
            result[key] = encrypt_dict(value, sensitive_keys)
        else:
            result[key] = value
    return result


def decrypt_dict(data: dict, sensitive_keys: list = None) -> dict:
    """Decrypt sensitive fields in a dict. Returns a new dict."""
    if sensitive_keys is None:
        sensitive_keys = SENSITIVE_KEYS

    result = {}
    for key, value in data.items():
        if key in sensitive_keys and isinstance(value, str):
            result[key] = decrypt(value)
        elif isinstance(value, dict):
            result[key] = decrypt_dict(value, sensitive_keys)
        else:
            result[key] = value
    return result


def get_env_or_config(key: str, config_value: str = None) -> str:
    """Return env var if set, else config value.

    Env var names: key is like 'bot_token' → NPS_BOT_TOKEN.
    """
    env_key = f"NPS_{key.upper()}"
    env_val = os.environ.get(env_key)
    if env_val:
        return env_val
    return config_value


def reset():
    """Reset module state. For testing only."""
    global _master_key, _salt
    with _lock:
        _master_key = None
        _salt = None
