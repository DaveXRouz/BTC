"""V4 Security module — AES-256-GCM encryption + V3 legacy decrypt.

Replaces V3's HMAC-SHA256 stream cipher with AES-256-GCM.
Keeps PBKDF2-HMAC-SHA256 for key derivation (same as V3).
Provides V3 decrypt() fallback for data migration.
"""

import base64
import hashlib
import hmac
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Shared with V3
SENSITIVE_KEYS = ["private_key", "seed_phrase", "wif", "extended_private_key"]

# Oracle fields that contain personal data
ORACLE_SENSITIVE_KEYS = [
    "mother_name",
    "mother_name_persian",
    "question",
    "question_persian",
    "ai_interpretation",
    "ai_interpretation_persian",
]

_PBKDF2_ITERATIONS = 600_000
_SALT_LENGTH = 32
_KEY_LENGTH = 32
_NONCE_LENGTH = 12  # 96-bit nonce for AES-GCM


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from password + salt using PBKDF2-HMAC-SHA256.

    Compatible with V3's _derive_key().
    """
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_KEY_LENGTH,
    )


def encrypt_aes256gcm(plaintext: str, key: bytes) -> str:
    """Encrypt with AES-256-GCM. Returns 'ENC4:<base64>' prefixed string."""
    nonce = os.urandom(_NONCE_LENGTH)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + ciphertext  # nonce (12) + ciphertext + tag (16)
    return f"ENC4:{base64.b64encode(payload).decode()}"


def decrypt_aes256gcm(encoded: str, key: bytes) -> str:
    """Decrypt AES-256-GCM 'ENC4:' prefixed string."""
    if not encoded.startswith("ENC4:"):
        raise ValueError("Not an ENC4-prefixed string")
    payload = base64.b64decode(encoded[5:])
    if len(payload) < _NONCE_LENGTH + 16:  # nonce + minimum tag
        raise ValueError("Encrypted data too short")
    nonce = payload[:_NONCE_LENGTH]
    ciphertext = payload[_NONCE_LENGTH:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def decrypt_v3_legacy(encoded: str, master_key: bytes) -> str:
    """Decrypt V3 'ENC:' prefixed data using HMAC-SHA256 stream cipher.

    Exact copy of V3's decrypt() for migration compatibility.
    """
    if encoded.startswith("PLAIN:"):
        return encoded[6:]

    if not encoded.startswith("ENC:"):
        return encoded

    payload = bytes.fromhex(encoded[4:])

    if len(payload) < 32:
        raise ValueError("Encrypted data too short")

    nonce = payload[:16]
    auth_tag = payload[-16:]
    ciphertext = payload[16:-16]

    # Verify authentication tag
    expected_tag = hmac.new(master_key, nonce + ciphertext, hashlib.sha256).digest()[
        :16
    ]
    if not hmac.compare_digest(auth_tag, expected_tag):
        raise ValueError("Decryption failed — wrong password or tampered data")

    # Decrypt using same keystream
    keystream = bytearray()
    for i in range((len(ciphertext) + 31) // 32):
        counter = i.to_bytes(4, "big")
        block = hmac.new(master_key, nonce + counter, hashlib.sha256).digest()
        keystream.extend(block)

    plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
    return plaintext.decode("utf-8")


def encrypt_dict(data: dict, key: bytes, sensitive_keys: list = None) -> dict:
    """Encrypt sensitive fields in a dict using AES-256-GCM."""
    if sensitive_keys is None:
        sensitive_keys = SENSITIVE_KEYS

    result = {}
    for k, v in data.items():
        if k in sensitive_keys and isinstance(v, str):
            result[k] = encrypt_aes256gcm(v, key)
        elif isinstance(v, dict):
            result[k] = encrypt_dict(v, key, sensitive_keys)
        else:
            result[k] = v
    return result


def decrypt_dict(data: dict, key: bytes, sensitive_keys: list = None) -> dict:
    """Decrypt sensitive fields. Handles both V3 (ENC:) and V4 (ENC4:) prefixes."""
    if sensitive_keys is None:
        sensitive_keys = SENSITIVE_KEYS

    result = {}
    for k, v in data.items():
        if k in sensitive_keys and isinstance(v, str):
            if v.startswith("ENC4:"):
                result[k] = decrypt_aes256gcm(v, key)
            elif v.startswith("ENC:") or v.startswith("PLAIN:"):
                result[k] = decrypt_v3_legacy(v, key)
            else:
                result[k] = v
        elif isinstance(v, dict):
            result[k] = decrypt_dict(v, key, sensitive_keys)
        else:
            result[k] = v
    return result


class EncryptionService:
    """High-level encryption service for Oracle field-level encryption."""

    def __init__(self, key: bytes):
        self._key = key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string. Returns ENC4: prefixed ciphertext."""
        return encrypt_aes256gcm(plaintext, self._key)

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ENC4: or ENC: prefixed string."""
        if ciphertext.startswith("ENC4:"):
            return decrypt_aes256gcm(ciphertext, self._key)
        if ciphertext.startswith("ENC:") or ciphertext.startswith("PLAIN:"):
            return decrypt_v3_legacy(ciphertext, self._key)
        return ciphertext

    def encrypt_field(self, value: Any) -> Any:
        """Encrypt a field value if it's a non-empty string."""
        if isinstance(value, str) and value:
            return self.encrypt(value)
        return value

    def decrypt_field(self, value: Any) -> Any:
        """Decrypt a field value if it's an encrypted string."""
        if isinstance(value, str) and (
            value.startswith("ENC4:") or value.startswith("ENC:")
        ):
            return self.decrypt(value)
        return value

    def encrypt_oracle_fields(self, data: dict) -> dict:
        """Encrypt Oracle-specific sensitive fields in a dict."""
        return encrypt_dict(data, self._key, ORACLE_SENSITIVE_KEYS)

    def decrypt_oracle_fields(self, data: dict) -> dict:
        """Decrypt Oracle-specific sensitive fields in a dict."""
        return decrypt_dict(data, self._key, ORACLE_SENSITIVE_KEYS)


# Module-level singleton
_encryption_service: EncryptionService | None = None


def init_encryption(settings) -> None:
    """Initialize the encryption service from app settings."""
    global _encryption_service
    if not settings.nps_encryption_key:
        _encryption_service = None
        return
    salt = (settings.nps_encryption_salt or "nps-v4-default-salt").encode("utf-8")
    # Pad or hash salt to 32 bytes
    if len(salt) < _SALT_LENGTH:
        salt = salt.ljust(_SALT_LENGTH, b"\x00")
    else:
        salt = salt[:_SALT_LENGTH]
    key = derive_key(settings.nps_encryption_key, salt)
    _encryption_service = EncryptionService(key)


def get_encryption_service() -> EncryptionService | None:
    """FastAPI dependency — returns the encryption service or None if not configured."""
    return _encryption_service
