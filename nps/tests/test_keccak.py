"""Tests for the Keccak-256 implementation."""

import hashlib
import unittest


class TestKeccak256(unittest.TestCase):

    def test_empty_string(self):
        """Keccak-256 of empty string matches known vector."""
        from engines.keccak import keccak256

        result = keccak256(b"").hex()
        self.assertEqual(
            result, "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
        )

    def test_hello(self):
        """Keccak-256 of 'hello' matches known vector."""
        from engines.keccak import keccak256

        result = keccak256(b"hello").hex()
        self.assertEqual(
            result, "1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8"
        )

    def test_not_sha3(self):
        """Keccak-256 differs from SHA3-256 (different padding byte)."""
        from engines.keccak import keccak256

        keccak_result = keccak256(b"test").hex()
        sha3_result = hashlib.sha3_256(b"test").hexdigest()
        self.assertNotEqual(keccak_result, sha3_result)

    def test_returns_32_bytes(self):
        """Output is always 32 bytes."""
        from engines.keccak import keccak256

        for data in [b"", b"a", b"x" * 200, b"\x00" * 1000]:
            self.assertEqual(len(keccak256(data)), 32)


if __name__ == "__main__":
    unittest.main()
