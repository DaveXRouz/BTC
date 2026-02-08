"""Tests for AES-256-GCM encryption service."""

import os
import time

import pytest

from app.services.security import (
    EncryptionService,
    ORACLE_SENSITIVE_KEYS,
    decrypt_aes256gcm,
    decrypt_dict,
    derive_key,
    encrypt_aes256gcm,
    encrypt_dict,
)


@pytest.fixture
def key():
    return derive_key("test_password_32_chars!!", b"salt" * 8)


@pytest.fixture
def wrong_key():
    return derive_key("wrong_password_different!!", b"salt" * 8)


@pytest.fixture
def enc(key):
    return EncryptionService(key)


# ─── Roundtrip Tests ────────────────────────────────────────────────────────


def test_encrypt_decrypt_roundtrip_english(key):
    plaintext = "Hello, World! This is a test."
    encrypted = encrypt_aes256gcm(plaintext, key)
    decrypted = decrypt_aes256gcm(encrypted, key)
    assert decrypted == plaintext


def test_encrypt_decrypt_roundtrip_persian(key):
    plaintext = "علی رضایی"
    encrypted = encrypt_aes256gcm(plaintext, key)
    decrypted = decrypt_aes256gcm(encrypted, key)
    assert decrypted == plaintext


def test_encrypt_decrypt_roundtrip_mixed_utf8(key):
    plaintext = "مریم Karimi — 1990 🌟"
    encrypted = encrypt_aes256gcm(plaintext, key)
    decrypted = decrypt_aes256gcm(encrypted, key)
    assert decrypted == plaintext


def test_encrypt_decrypt_empty_string(key):
    plaintext = ""
    encrypted = encrypt_aes256gcm(plaintext, key)
    decrypted = decrypt_aes256gcm(encrypted, key)
    assert decrypted == plaintext


# ─── Prefix Tests ───────────────────────────────────────────────────────────


def test_enc4_prefix(key):
    encrypted = encrypt_aes256gcm("test", key)
    assert encrypted.startswith("ENC4:")


def test_different_nonce_each_time(key):
    enc1 = encrypt_aes256gcm("same text", key)
    enc2 = encrypt_aes256gcm("same text", key)
    assert enc1 != enc2  # Different nonces


# ─── Error Cases ────────────────────────────────────────────────────────────


def test_wrong_key_rejection(key, wrong_key):
    encrypted = encrypt_aes256gcm("secret data", key)
    with pytest.raises(Exception):
        decrypt_aes256gcm(encrypted, wrong_key)


def test_tampered_data_detection(key):
    encrypted = encrypt_aes256gcm("secret data", key)
    # Tamper with the ciphertext
    import base64

    prefix, b64 = encrypted.split(":", 1)
    payload = bytearray(base64.b64decode(b64))
    payload[15] ^= 0xFF  # Flip a byte in ciphertext
    tampered = f"ENC4:{base64.b64encode(bytes(payload)).decode()}"
    with pytest.raises(Exception):
        decrypt_aes256gcm(tampered, key)


def test_not_enc4_prefix_raises(key):
    with pytest.raises(ValueError, match="Not an ENC4"):
        decrypt_aes256gcm("WRONG:abc", key)


def test_too_short_payload_raises(key):
    import base64

    short = f"ENC4:{base64.b64encode(b'short').decode()}"
    with pytest.raises(ValueError, match="too short"):
        decrypt_aes256gcm(short, key)


# ─── Dict Encryption ───────────────────────────────────────────────────────


def test_encrypt_dict_roundtrip(key):
    data = {
        "mother_name": "Maryam",
        "mother_name_persian": "مریم",
        "name": "Ali",  # Should not be encrypted
    }
    encrypted = encrypt_dict(data, key, ORACLE_SENSITIVE_KEYS)
    assert encrypted["mother_name"].startswith("ENC4:")
    assert encrypted["mother_name_persian"].startswith("ENC4:")
    assert encrypted["name"] == "Ali"  # Plaintext preserved

    decrypted = decrypt_dict(encrypted, key, ORACLE_SENSITIVE_KEYS)
    assert decrypted["mother_name"] == "Maryam"
    assert decrypted["mother_name_persian"] == "مریم"
    assert decrypted["name"] == "Ali"


def test_encrypt_dict_skips_none(key):
    data = {"mother_name": "Test", "mother_name_persian": None}
    encrypted = encrypt_dict(data, key, ORACLE_SENSITIVE_KEYS)
    assert encrypted["mother_name_persian"] is None


def test_encrypt_dict_skips_non_string(key):
    data = {"mother_name": 123}
    encrypted = encrypt_dict(data, key, ORACLE_SENSITIVE_KEYS)
    assert encrypted["mother_name"] == 123


# ─── EncryptionService ──────────────────────────────────────────────────────


def test_service_encrypt_decrypt(enc):
    ct = enc.encrypt("Hello")
    assert ct.startswith("ENC4:")
    assert enc.decrypt(ct) == "Hello"


def test_service_encrypt_field_none(enc):
    assert enc.encrypt_field(None) is None


def test_service_encrypt_field_empty_string(enc):
    assert enc.encrypt_field("") == ""


def test_service_decrypt_field_plaintext(enc):
    assert enc.decrypt_field("just plain text") == "just plain text"


def test_service_decrypt_field_none(enc):
    assert enc.decrypt_field(None) is None


def test_service_oracle_fields_roundtrip(enc):
    data = {
        "mother_name": "Jane",
        "mother_name_persian": "جین",
        "question": "Will I succeed?",
        "question_persian": "آیا موفق خواهم شد؟",
        "ai_interpretation": "Signs point to yes",
        "ai_interpretation_persian": "نشانه‌ها مثبت هستند",
        "name": "Keep plaintext",
    }
    encrypted = enc.encrypt_oracle_fields(data)
    for field in ORACLE_SENSITIVE_KEYS:
        if field in data and data[field]:
            assert encrypted[field].startswith("ENC4:")
    assert encrypted["name"] == "Keep plaintext"

    decrypted = enc.decrypt_oracle_fields(encrypted)
    assert decrypted == data


# ─── Performance ────────────────────────────────────────────────────────────


def test_encrypt_performance(key):
    """Encryption should complete in under 10ms per operation."""
    plaintext = "Performance test string with some Unicode: مریم"
    start = time.perf_counter()
    for _ in range(100):
        encrypt_aes256gcm(plaintext, key)
    elapsed = (time.perf_counter() - start) / 100
    assert elapsed < 0.01, f"Encrypt took {elapsed*1000:.2f}ms (>10ms)"


def test_decrypt_performance(key):
    """Decryption should complete in under 10ms per operation."""
    ct = encrypt_aes256gcm("Performance test", key)
    start = time.perf_counter()
    for _ in range(100):
        decrypt_aes256gcm(ct, key)
    elapsed = (time.perf_counter() - start) / 100
    assert elapsed < 0.01, f"Decrypt took {elapsed*1000:.2f}ms (>10ms)"
