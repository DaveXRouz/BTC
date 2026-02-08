"""Oracle service package smoke tests."""

import unittest

import oracle_service


class TestOracleServicePackage(unittest.TestCase):
    """Verify the oracle_service package imports and initializes correctly."""

    def test_package_imports(self):
        """oracle_service package loads without error."""
        self.assertIsNotNone(oracle_service)

    def test_engines_subpackage(self):
        """Engine functions accessible from oracle_service.engines."""
        from oracle_service.engines import (
            token60,
            encode_fc60,
            life_path,
            numerology_reduce,
            read_sign,
            read_name,
            question_sign,
            daily_insight,
        )

        self.assertTrue(callable(token60))
        self.assertTrue(callable(encode_fc60))
        self.assertTrue(callable(life_path))
        self.assertTrue(callable(read_sign))

    def test_grpc_gen_subpackage(self):
        """Proto stubs accessible from oracle_service.grpc_gen."""
        from oracle_service.grpc_gen import oracle_pb2, oracle_pb2_grpc

        self.assertTrue(hasattr(oracle_pb2, "ReadingRequest"))
        self.assertTrue(hasattr(oracle_pb2, "HealthResponse"))
        self.assertTrue(hasattr(oracle_pb2_grpc, "OracleServiceServicer"))
        self.assertTrue(hasattr(oracle_pb2_grpc, "OracleServiceStub"))

    def test_server_module(self):
        """Server module imports and OracleServiceImpl is available."""
        from oracle_service.server import OracleServiceImpl, serve

        impl = OracleServiceImpl()
        self.assertTrue(hasattr(impl, "HealthCheck"))
        self.assertTrue(hasattr(impl, "GetReading"))
        self.assertTrue(hasattr(impl, "GetNameReading"))
        self.assertTrue(hasattr(impl, "GetQuestionSign"))
        self.assertTrue(hasattr(impl, "GetDailyInsight"))
        self.assertTrue(hasattr(impl, "GetTimingAlignment"))
        self.assertTrue(hasattr(impl, "SuggestRange"))
        self.assertTrue(hasattr(impl, "AnalyzeSession"))


if __name__ == "__main__":
    unittest.main()
