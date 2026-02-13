# NPS Encryption Specification

Technical specification for NPS field-level encryption.

---

## Overview

NPS uses AES-256-GCM for encrypting sensitive fields (private keys, seed phrases, personal data). The implementation lives in `api/app/services/security.py`.

Two formats are supported:

| Prefix  | Algorithm                 | Status                                     |
| ------- | ------------------------- | ------------------------------------------ |
| `ENC4:` | AES-256-GCM               | **Current** — all new encryption uses this |
| `ENC:`  | HMAC-SHA256 stream cipher | **Legacy** — decrypt-only for migration    |

---

## Current Format: ENC4

### Key Derivation

- **Algorithm:** PBKDF2-HMAC-SHA256
- **Iterations:** 600,000
- **Salt length:** 32 bytes
- **Derived key length:** 32 bytes (256 bits)
- **Input:** `NPS_ENCRYPTION_KEY` (hex string from `.env`) + `NPS_ENCRYPTION_SALT` (hex string from `.env`)

```python
key = hashlib.pbkdf2_hmac(
    "sha256",
    password.encode("utf-8"),  # NPS_ENCRYPTION_KEY
    salt,                       # NPS_ENCRYPTION_SALT (padded/truncated to 32 bytes)
    600_000,
    dklen=32,
)
```

### Encryption

- **Algorithm:** AES-256-GCM (via `cryptography.hazmat.primitives.ciphers.aead.AESGCM`)
- **Nonce:** 12 bytes (96-bit), cryptographically random (`os.urandom`)
- **Authentication tag:** 16 bytes (128-bit), appended by GCM mode
- **Associated data:** None (AAD is not used)

### Wire Format

```
ENC4:<base64(nonce + ciphertext + tag)>
```

Where:

- `nonce`: 12 bytes
- `ciphertext`: variable length (same as plaintext)
- `tag`: 16 bytes (GCM authentication tag, appended to ciphertext by the library)

Total payload: 12 + len(plaintext) + 16 bytes, then base64-encoded.

### Decryption

1. Strip `ENC4:` prefix
2. Base64-decode the payload
3. Split: first 12 bytes = nonce, remainder = ciphertext + tag
4. Decrypt with AES-256-GCM using the derived key and nonce
5. GCM verifies the authentication tag automatically

### Example Flow

```
plaintext: "5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ"

encrypt:
  nonce = os.urandom(12)                    # e.g., b'\xa3\x4f...' (12 bytes)
  aesgcm = AESGCM(derived_key)
  ct = aesgcm.encrypt(nonce, plaintext_bytes, None)  # ciphertext + tag
  payload = nonce + ct                       # 12 + N + 16 bytes
  result = "ENC4:" + base64.b64encode(payload)

decrypt:
  payload = base64.b64decode(encoded[5:])
  nonce = payload[:12]
  ct = payload[12:]                          # ciphertext + tag
  plaintext = aesgcm.decrypt(nonce, ct, None)
```

---

## Legacy Format: ENC

### Overview

Used in NPS v3. Decrypt-only support retained for data migration.

- **Key derivation:** Same PBKDF2-HMAC-SHA256 (600K iterations)
- **Encryption:** HMAC-SHA256 stream cipher (custom, not standard AES)
- **Nonce:** 16 bytes
- **Auth tag:** 16 bytes (first 16 bytes of HMAC-SHA256 over nonce + ciphertext)

### Wire Format

```
ENC:<hex(nonce + ciphertext + auth_tag)>
```

Where:

- `nonce`: 16 bytes
- `ciphertext`: variable length
- `auth_tag`: 16 bytes (last 16 bytes of payload)

### Stream Cipher

```python
keystream = b""
for i in range(blocks_needed):
    counter = i.to_bytes(4, "big")
    block = hmac.new(master_key, nonce + counter, sha256).digest()
    keystream += block

plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
```

---

## Sensitive Fields

### Scanner Fields (private key data)

```python
SENSITIVE_KEYS = ["private_key", "seed_phrase", "wif", "extended_private_key"]
```

### Oracle Fields (personal data)

```python
ORACLE_SENSITIVE_KEYS = [
    "mother_name",
    "mother_name_persian",
    "question",
    "question_persian",
    "ai_interpretation",
    "ai_interpretation_persian",
]
```

---

## PLAIN Prefix

The `PLAIN:` prefix indicates an unencrypted value stored in a field that normally holds encrypted data. Used during development or when encryption is disabled.

```
PLAIN:some_value  ->  decrypt returns "some_value"
```

---

## Environment Variables

| Variable              | Purpose                    | Format                           |
| --------------------- | -------------------------- | -------------------------------- |
| `NPS_ENCRYPTION_KEY`  | Master encryption password | Hex string (64 chars = 256 bits) |
| `NPS_ENCRYPTION_SALT` | PBKDF2 salt                | Hex string (32 chars = 128 bits) |

Both are required for encryption. If `NPS_ENCRYPTION_KEY` is not set, the `EncryptionService` is not initialized and encryption is disabled (graceful degradation).

---

## Security Properties

1. **Authenticated encryption** — GCM mode prevents tampering (tag verification)
2. **Unique nonces** — Each encryption generates a fresh 12-byte random nonce
3. **Key stretching** — 600K PBKDF2 iterations resist brute force
4. **No key reuse** — Derived key is unique per encryption key + salt combination
5. **Legacy migration** — Old `ENC:` data can be decrypted and re-encrypted as `ENC4:`

## Migration Path

To migrate legacy data:

1. Read field with `ENC:` prefix
2. Decrypt using `decrypt_v3_legacy()`
3. Re-encrypt using `encrypt_aes256gcm()`
4. Store with `ENC4:` prefix

The `decrypt_dict()` function handles both formats automatically.
