"""Tests for the multi-chain balance checking system."""

import unittest


class TestBTCBalance(unittest.TestCase):

    def test_result_dict_structure(self):
        """check_balance returns dict with expected keys."""
        from engines.balance import check_balance

        result = check_balance("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        self.assertIn("success", result)
        self.assertIn("address", result)
        if result["success"]:
            self.assertIn("balance_btc", result)
            self.assertIn("has_balance", result)
            self.assertIn("balance_sat", result)

    def test_invalid_address_structure(self):
        """Invalid address still returns a result dict (not crash)."""
        from engines.balance import check_balance

        result = check_balance("invalid_address_xxx")
        self.assertIn("success", result)
        self.assertIn("address", result)


class TestETHBalance(unittest.TestCase):

    def test_eth_balance_dict_structure(self):
        """check_eth_balance returns dict with expected keys."""
        from engines.balance import check_eth_balance

        result = check_eth_balance("0x0000000000000000000000000000000000000000")
        self.assertIn("success", result)
        self.assertIn("address", result)

    def test_erc20_unknown_token(self):
        """Unknown token returns error dict."""
        from engines.balance import check_erc20_balance

        result = check_erc20_balance(
            "0x0000000000000000000000000000000000000000", "FAKE"
        )
        self.assertFalse(result["success"])
        self.assertIn("error", result)


class TestMultiChainBalance(unittest.TestCase):

    def test_check_all_balances_structure(self):
        """check_all_balances returns combined result dict."""
        from engines.balance import check_all_balances

        result = check_all_balances(
            btc_address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            eth_address="0x0000000000000000000000000000000000000000",
            tokens=["USDT"],
        )
        self.assertIn("success", result)
        self.assertIn("btc", result)
        self.assertIn("eth", result)
        self.assertIn("tokens", result)
        self.assertIn("has_any_balance", result)

    def test_none_addresses(self):
        """Passing None addresses returns empty results."""
        from engines.balance import check_all_balances

        result = check_all_balances(btc_address=None, eth_address=None, tokens=[])
        self.assertTrue(result["success"])
        self.assertIsNone(result["btc"])
        self.assertIsNone(result["eth"])


if __name__ == "__main__":
    unittest.main()
