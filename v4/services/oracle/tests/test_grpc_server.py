"""gRPC server integration tests — start in-process server, test all 8 RPCs."""

import unittest
import threading
import time
from concurrent import futures

import grpc

import oracle_service  # triggers sys.path shim
from oracle_service.grpc_gen import oracle_pb2, oracle_pb2_grpc
from oracle_service.server import OracleServiceImpl


def _start_server():
    """Start an in-process gRPC server on a random port, return (server, port)."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    oracle_pb2_grpc.add_OracleServiceServicer_to_server(OracleServiceImpl(), server)
    port = server.add_insecure_port("[::]:0")  # random available port
    server.start()
    return server, port


class TestGRPCServer(unittest.TestCase):
    """Test all 8 gRPC RPCs against an in-process server."""

    @classmethod
    def setUpClass(cls):
        cls.server, cls.port = _start_server()
        cls.channel = grpc.insecure_channel(f"localhost:{cls.port}")
        cls.stub = oracle_pb2_grpc.OracleServiceStub(cls.channel)

    @classmethod
    def tearDownClass(cls):
        cls.channel.close()
        cls.server.stop(grace=0)

    def test_health_check(self):
        resp = self.stub.HealthCheck(oracle_pb2.Empty())
        self.assertEqual(resp.status, "healthy")
        self.assertEqual(resp.version, "4.0.0")
        self.assertGreaterEqual(resp.uptime_seconds, 0)
        self.assertIn("fc60", resp.checks)
        self.assertIn("numerology", resp.checks)
        self.assertIn("oracle", resp.checks)
        self.assertIn("timing", resp.checks)

    def test_get_reading_default(self):
        """GetReading with no datetime defaults to now."""
        resp = self.stub.GetReading(oracle_pb2.ReadingRequest())
        self.assertIsNotNone(resp.fc60)
        self.assertIsNotNone(resp.numerology)
        self.assertIsNotNone(resp.zodiac)
        self.assertIsNotNone(resp.chinese)
        self.assertGreater(resp.generated_at, 0)
        # FC60 fields populated
        self.assertNotEqual(resp.fc60.stem, "")
        self.assertNotEqual(resp.fc60.branch, "")
        self.assertNotEqual(resp.fc60.element, "")
        # Numerology fields populated
        self.assertGreater(resp.numerology.life_path, 0)
        self.assertGreater(resp.numerology.day_vibration, 0)

    def test_get_reading_specific_date(self):
        """GetReading with specific ISO datetime."""
        resp = self.stub.GetReading(
            oracle_pb2.ReadingRequest(datetime="2026-02-08T14:30:00+00:00")
        )
        self.assertIsNotNone(resp.fc60)
        self.assertEqual(resp.zodiac.sign, "Aquarius")
        self.assertNotEqual(resp.summary, "")

    def test_get_reading_date_only(self):
        """GetReading with date-only string."""
        resp = self.stub.GetReading(oracle_pb2.ReadingRequest(datetime="2026-02-08"))
        self.assertIsNotNone(resp.fc60)

    def test_get_name_reading_john(self):
        """GetNameReading: JOHN -> destiny_number==2."""
        resp = self.stub.GetNameReading(oracle_pb2.NameRequest(name="JOHN"))
        self.assertEqual(resp.name, "JOHN")
        self.assertEqual(resp.destiny_number, 2)
        self.assertEqual(resp.soul_urge, 6)
        self.assertEqual(resp.personality, 5)
        self.assertGreater(len(resp.letters), 0)
        self.assertNotEqual(resp.interpretation, "")

    def test_get_name_reading_dave(self):
        """GetNameReading: DAVE -> destiny_number==5."""
        resp = self.stub.GetNameReading(oracle_pb2.NameRequest(name="DAVE"))
        self.assertEqual(resp.destiny_number, 5)

    def test_get_name_reading_empty(self):
        """GetNameReading with empty name returns error."""
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.GetNameReading(oracle_pb2.NameRequest(name=""))
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)

    def test_get_question_sign(self):
        """GetQuestionSign returns valid answer."""
        resp = self.stub.GetQuestionSign(
            oracle_pb2.QuestionRequest(question="Will I find it today?")
        )
        self.assertEqual(resp.question, "Will I find it today?")
        self.assertIn(resp.answer, ["yes", "no", "maybe"])
        self.assertGreater(resp.sign_number, 0)
        self.assertNotEqual(resp.interpretation, "")
        self.assertGreater(resp.confidence, 0)

    def test_get_question_sign_with_numbers(self):
        """GetQuestionSign with numeric question."""
        resp = self.stub.GetQuestionSign(oracle_pb2.QuestionRequest(question="11:11"))
        self.assertIn(resp.answer, ["yes", "no", "maybe"])

    def test_get_question_sign_empty(self):
        """GetQuestionSign with empty question returns error."""
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.GetQuestionSign(oracle_pb2.QuestionRequest(question=""))
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)

    def test_get_daily_insight(self):
        """GetDailyInsight for a specific date."""
        resp = self.stub.GetDailyInsight(oracle_pb2.DateRequest(date="2026-02-08"))
        self.assertEqual(resp.date, "2026-02-08")
        self.assertNotEqual(resp.insight, "")
        self.assertIsNotNone(resp.fc60)
        self.assertIsNotNone(resp.numerology)
        self.assertGreater(len(resp.lucky_numbers), 0)

    def test_get_daily_insight_default(self):
        """GetDailyInsight with no date defaults to today."""
        resp = self.stub.GetDailyInsight(oracle_pb2.DateRequest())
        self.assertNotEqual(resp.date, "")
        self.assertNotEqual(resp.insight, "")

    def test_get_timing_alignment(self):
        """GetTimingAlignment returns valid quality and score."""
        resp = self.stub.GetTimingAlignment(oracle_pb2.TimingRequest())
        self.assertIn(resp.quality, ["excellent", "good", "fair", "poor"])
        self.assertGreaterEqual(resp.alignment_score, 0.0)
        self.assertLessEqual(resp.alignment_score, 1.0)
        self.assertGreater(len(resp.optimal_hours), 0)
        self.assertLessEqual(len(resp.optimal_hours), 5)
        self.assertNotEqual(resp.moon_phase, "")

    def test_suggest_range(self):
        """SuggestRange returns valid hex range and strategy."""
        resp = self.stub.SuggestRange(
            oracle_pb2.RangeRequest(puzzle_number=66, ai_level=1)
        )
        self.assertNotEqual(resp.range_start, "")
        self.assertNotEqual(resp.range_end, "")
        self.assertTrue(resp.range_start.startswith("0x"))
        self.assertTrue(resp.range_end.startswith("0x"))
        self.assertIn(resp.strategy, ["random", "sequential", "cosmic", "gap_fill"])
        self.assertGreater(resp.confidence, 0)
        self.assertNotEqual(resp.reasoning, "")

    def test_suggest_range_default_puzzle(self):
        """SuggestRange with no puzzle defaults sensibly."""
        resp = self.stub.SuggestRange(oracle_pb2.RangeRequest())
        self.assertNotEqual(resp.range_start, "")

    def test_analyze_session(self):
        """AnalyzeSession returns insights."""
        resp = self.stub.AnalyzeSession(
            oracle_pb2.SessionData(
                session_id="test-001",
                keys_tested=50000,
                seeds_tested=0,
                hits=0,
                speed=2500.0,
                elapsed=20.0,
                mode="random_key",
            )
        )
        self.assertGreater(len(resp.insights), 0)
        self.assertGreater(len(resp.recommendations), 0)

    def test_analyze_session_empty(self):
        """AnalyzeSession with empty data still returns."""
        resp = self.stub.AnalyzeSession(oracle_pb2.SessionData())
        self.assertGreater(len(resp.insights), 0)


if __name__ == "__main__":
    unittest.main()
