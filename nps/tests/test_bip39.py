"""Tests for BIP39 mnemonic, BIP32 derivation, ETH addresses, and random keys."""

import unittest


class TestMnemonic(unittest.TestCase):

    def test_generates_12_words(self):
        """generate_mnemonic(128) produces 12 words."""
        from engines.bip39 import generate_mnemonic

        m = generate_mnemonic(128)
        self.assertEqual(len(m.split()), 12)

    def test_all_words_in_wordlist(self):
        """All generated words exist in BIP39 wordlist."""
        from engines.bip39 import generate_mnemonic, WORDLIST

        m = generate_mnemonic(128)
        for word in m.split():
            self.assertIn(word, WORDLIST)

    def test_different_each_time(self):
        """Two consecutive mnemonics are different."""
        from engines.bip39 import generate_mnemonic

        m1 = generate_mnemonic(128)
        m2 = generate_mnemonic(128)
        self.assertNotEqual(m1, m2)

    def test_known_mnemonic_valid(self):
        """The 'abandon...about' test vector validates correctly."""
        from engines.bip39 import validate_mnemonic

        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        self.assertTrue(validate_mnemonic(mnemonic))

    def test_invalid_mnemonic(self):
        """Invalid mnemonic fails validation."""
        from engines.bip39 import validate_mnemonic

        self.assertFalse(
            validate_mnemonic(
                "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"
            )
        )

    def test_known_seed(self):
        """Known mnemonic produces expected seed prefix."""
        from engines.bip39 import mnemonic_to_seed

        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        seed = mnemonic_to_seed(mnemonic)
        self.assertEqual(len(seed), 64)
        # Known seed hex prefix for this mnemonic (no passphrase)
        expected_prefix = (
            "5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc1"
        )
        self.assertTrue(seed.hex().startswith(expected_prefix[:16]))

    def test_24_words(self):
        """generate_mnemonic(256) produces 24 words."""
        from engines.bip39 import generate_mnemonic

        m = generate_mnemonic(256)
        self.assertEqual(len(m.split()), 24)


class TestBIP32(unittest.TestCase):

    def test_known_master_key(self):
        """BIP32 test vector 1: seed -> master key."""
        from engines.bip39 import seed_to_master_key

        seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        key, chain = seed_to_master_key(seed)
        self.assertEqual(
            key.hex(),
            "e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35",
        )

    def test_child_key_derivation(self):
        """Child key derivation produces valid 32-byte keys."""
        from engines.bip39 import seed_to_master_key, derive_child_key

        seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        key, chain = seed_to_master_key(seed)
        child_key, child_chain = derive_child_key(key, chain, 0, hardened=True)
        self.assertEqual(len(child_key), 32)
        self.assertEqual(len(child_chain), 32)


class TestBIP44(unittest.TestCase):

    def test_derives_20_btc_addresses(self):
        """derive_btc_keys returns 20 unique addresses."""
        from engines.bip39 import mnemonic_to_seed, derive_btc_keys

        seed = mnemonic_to_seed(
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        )
        keys = derive_btc_keys(seed, count=20)
        self.assertEqual(len(keys), 20)
        addresses = [k["address"] for k in keys]
        self.assertEqual(len(set(addresses)), 20)

    def test_btc_addresses_start_with_1(self):
        """All derived BTC addresses start with '1'."""
        from engines.bip39 import mnemonic_to_seed, derive_btc_keys

        seed = mnemonic_to_seed(
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        )
        keys = derive_btc_keys(seed, count=5)
        for k in keys:
            self.assertTrue(k["address"].startswith("1"))

    def test_derives_eth_addresses(self):
        """derive_eth_keys returns valid ETH addresses."""
        from engines.bip39 import mnemonic_to_seed, derive_eth_keys

        seed = mnemonic_to_seed(
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        )
        keys = derive_eth_keys(seed, count=5)
        self.assertEqual(len(keys), 5)
        for k in keys:
            self.assertTrue(k["address"].startswith("0x"))
            self.assertEqual(len(k["address"]), 42)

    def test_derive_all_chains(self):
        """derive_all_chains returns both btc and eth keys."""
        from engines.bip39 import mnemonic_to_seed, derive_all_chains

        seed = mnemonic_to_seed(
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        )
        result = derive_all_chains(seed, count=3)
        self.assertIn("btc", result)
        self.assertIn("eth", result)
        self.assertEqual(len(result["btc"]), 3)
        self.assertEqual(len(result["eth"]), 3)


class TestETH(unittest.TestCase):

    def test_eth_address_key_1(self):
        """ETH address for private key=1 matches known value."""
        from engines.bip39 import privkey_to_eth_address

        addr = privkey_to_eth_address(1)
        self.assertEqual(addr.lower(), "0x7e5f4552091a69125d5dfcb7b8c2659029395bdf")

    def test_eip55_mixed_case(self):
        """EIP-55 checksum produces mixed-case address."""
        from engines.bip39 import privkey_to_eth_address

        addr = privkey_to_eth_address(1)
        # Should have both upper and lower case letters
        hex_part = addr[2:]
        has_upper = any(c.isupper() for c in hex_part)
        has_lower = any(c.islower() for c in hex_part)
        self.assertTrue(has_upper and has_lower)

    def test_privkey_to_all_addresses(self):
        """privkey_to_all_addresses returns both BTC and ETH."""
        from engines.bip39 import privkey_to_all_addresses

        result = privkey_to_all_addresses(1)
        self.assertIn("btc", result)
        self.assertIn("eth", result)
        self.assertTrue(result["btc"].startswith("1"))
        self.assertTrue(result["eth"].startswith("0x"))


class TestRandomKey(unittest.TestCase):

    def test_in_valid_range(self):
        """Random key is in valid secp256k1 range."""
        from engines.bip39 import generate_random_key
        from engines.crypto import N

        key = generate_random_key()
        self.assertGreaterEqual(key, 1)
        self.assertLess(key, N)

    def test_batch_size(self):
        """Batch generation returns correct count."""
        from engines.bip39 import generate_random_keys_batch

        keys = generate_random_keys_batch(10)
        self.assertEqual(len(keys), 10)

    def test_batch_unique(self):
        """Batch keys are all unique."""
        from engines.bip39 import generate_random_keys_batch

        keys = generate_random_keys_batch(100)
        self.assertEqual(len(set(keys)), 100)


if __name__ == "__main__":
    unittest.main()
