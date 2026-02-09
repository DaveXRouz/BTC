"""
Tests for NPS Oracle DevOps monitoring components.

Covers:
- OracleJSONFormatter (structured logging)
- setup_oracle_logger (rotating file + console handlers)
- OracleMetrics (thread-safe metrics collection)
- HTTP monitoring sidecar (health/metrics/ready endpoints)
- OracleAlerter (Telegram alert logic)
"""

import json
import logging
import os
import sys
import tempfile
import threading
import time
import urllib.request
from unittest import mock

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ════════════════════════════════════════════════════════════════
# OracleJSONFormatter Tests
# ════════════════════════════════════════════════════════════════


class TestOracleJSONFormatter:
    def test_basic_format(self):
        from devops.logging.oracle_logger import OracleJSONFormatter

        fmt = OracleJSONFormatter(service="oracle")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello world",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["service"] == "oracle"
        assert data["message"] == "hello world"
        assert "timestamp" in data

    def test_rpc_method_field(self):
        from devops.logging.oracle_logger import OracleJSONFormatter

        fmt = OracleJSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="rpc call",
            args=(),
            exc_info=None,
        )
        record.rpc_method = "GetReading"
        output = fmt.format(record)
        data = json.loads(output)
        assert data["rpc_method"] == "GetReading"

    def test_duration_ms_field(self):
        from devops.logging.oracle_logger import OracleJSONFormatter

        fmt = OracleJSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="done",
            args=(),
            exc_info=None,
        )
        record.duration_ms = 42.5
        output = fmt.format(record)
        data = json.loads(output)
        assert data["duration_ms"] == 42.5

    def test_exception_format(self):
        from devops.logging.oracle_logger import OracleJSONFormatter

        fmt = OracleJSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys as _sys

            exc_info = _sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="error occurred",
            args=(),
            exc_info=exc_info,
        )
        output = fmt.format(record)
        data = json.loads(output)
        assert "exception" in data
        assert "ValueError" in data["exception"]


# ════════════════════════════════════════════════════════════════
# setup_oracle_logger Tests
# ════════════════════════════════════════════════════════════════


class TestSetupOracleLogger:
    def setup_method(self):
        from devops.logging.oracle_logger import reset

        reset()
        # Remove all handlers to start clean
        root = logging.getLogger()
        root.handlers.clear()

    def teardown_method(self):
        from devops.logging.oracle_logger import reset

        reset()
        root = logging.getLogger()
        root.handlers.clear()

    def test_creates_log_directory(self):
        from devops.logging.oracle_logger import setup_oracle_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "nested", "logs")
            setup_oracle_logger(log_dir)
            assert os.path.isdir(log_dir)

    def test_creates_log_files(self):
        from devops.logging.oracle_logger import setup_oracle_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            setup_oracle_logger(tmpdir)
            logger = logging.getLogger("test_file_creation")
            logger.info("test message")
            logger.error("error message")
            assert os.path.exists(os.path.join(tmpdir, "oracle.log"))
            assert os.path.exists(os.path.join(tmpdir, "error.log"))

    def test_idempotent(self):
        from devops.logging.oracle_logger import setup_oracle_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            setup_oracle_logger(tmpdir)
            handler_count_1 = len(logging.getLogger().handlers)
            setup_oracle_logger(tmpdir)  # should be no-op
            handler_count_2 = len(logging.getLogger().handlers)
            assert handler_count_1 == handler_count_2

    def test_json_output_in_log_file(self):
        from devops.logging.oracle_logger import setup_oracle_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            setup_oracle_logger(tmpdir)
            logger = logging.getLogger("test_json_output")
            logger.info("json check")
            # Flush handlers
            for h in logging.getLogger().handlers:
                h.flush()
            log_path = os.path.join(tmpdir, "oracle.log")
            with open(log_path) as f:
                lines = f.readlines()
            assert len(lines) >= 1
            data = json.loads(lines[-1])
            assert data["message"] == "json check"


# ════════════════════════════════════════════════════════════════
# OracleMetrics Tests
# ════════════════════════════════════════════════════════════════


class TestOracleMetrics:
    def test_record_and_snapshot(self):
        from devops.monitoring.oracle_metrics import OracleMetrics

        m = OracleMetrics(window_seconds=60)
        m.record_rpc("GetReading", 100)
        m.record_rpc("GetReading", 200)
        m.record_rpc("GetReading", 300)

        snap = m.get_snapshot()
        assert "GetReading" in snap["rpcs"]
        rpc = snap["rpcs"]["GetReading"]
        assert rpc["count"] == 3
        assert rpc["avg_ms"] == 200.0

    def test_percentiles(self):
        from devops.monitoring.oracle_metrics import OracleMetrics

        m = OracleMetrics(window_seconds=60)
        # Add 100 samples: 1, 2, 3, ..., 100
        for i in range(1, 101):
            m.record_rpc("Test", float(i))

        snap = m.get_snapshot()
        rpc = snap["rpcs"]["Test"]
        assert rpc["count"] == 100
        assert rpc["p50_ms"] == 51.0  # index 50 of sorted 1..100
        assert rpc["p95_ms"] == 96.0
        assert rpc["p99_ms"] == 100.0
        assert rpc["max_ms"] == 100.0

    def test_error_recording(self):
        from devops.monitoring.oracle_metrics import OracleMetrics

        m = OracleMetrics(window_seconds=60)
        m.record_rpc("GetReading", 100)
        m.record_error("GetReading", "ValueError")
        m.record_error("GetReading", "ValueError")
        m.record_error("GetReading", "TimeoutError")

        snap = m.get_snapshot()
        errors = snap["errors"]
        assert errors["total_count"] == 3
        assert errors["by_rpc"]["GetReading"] == 3
        assert errors["by_type"]["ValueError"] == 2
        assert errors["by_type"]["TimeoutError"] == 1

    def test_error_rate_calculation(self):
        from devops.monitoring.oracle_metrics import OracleMetrics

        m = OracleMetrics(window_seconds=60)
        for _ in range(9):
            m.record_rpc("Test", 50)
        m.record_error("Test", "Error")

        snap = m.get_snapshot()
        # 1 error out of 10 total calls = 10%
        assert snap["errors"]["rate_percent"] == 10.0

    def test_window_cleanup(self):
        from devops.monitoring.oracle_metrics import OracleMetrics

        m = OracleMetrics(window_seconds=1)
        m.record_rpc("Old", 100)
        time.sleep(1.5)
        m.record_rpc("New", 200)

        snap = m.get_snapshot()
        # "Old" should have been cleaned up
        assert (
            "Old" not in snap["rpcs"]
            or snap["rpcs"].get("Old", {}).get("count", 0) == 0
        )

    def test_thread_safety(self):
        from devops.monitoring.oracle_metrics import OracleMetrics

        m = OracleMetrics(window_seconds=60)
        errors = []

        def writer(name, count):
            try:
                for i in range(count):
                    m.record_rpc(name, float(i))
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer, args=(f"RPC{i}", 100)) for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        snap = m.get_snapshot()
        for i in range(5):
            assert snap["rpcs"][f"RPC{i}"]["count"] == 100

    def test_readings_per_hour(self):
        from devops.monitoring.oracle_metrics import OracleMetrics

        m = OracleMetrics(window_seconds=3600)
        for _ in range(100):
            m.record_rpc("Test", 10)

        snap = m.get_snapshot()
        assert snap["readings_per_hour"] > 0

    def test_reset(self):
        from devops.monitoring.oracle_metrics import OracleMetrics

        m = OracleMetrics(window_seconds=60)
        m.record_rpc("Test", 100)
        m.record_error("Test", "Error")
        m.reset()

        snap = m.get_snapshot()
        assert snap["rpcs"] == {}
        assert snap["errors"]["total_count"] == 0


# ════════════════════════════════════════════════════════════════
# HTTP Server Tests
# ════════════════════════════════════════════════════════════════


class TestHTTPServer:
    def _start_server(self, health_fn, metrics_fn, port):
        from devops.monitoring.http_server import start_http_server

        return start_http_server(health_fn, metrics_fn, port=port)

    def test_health_endpoint(self):
        srv = self._start_server(
            lambda: {"status": "healthy", "version": "4.0.0"},
            lambda: {},
            port=19091,
        )
        try:
            time.sleep(0.2)
            resp = urllib.request.urlopen("http://localhost:19091/health")
            data = json.loads(resp.read())
            assert data["status"] == "healthy"
        finally:
            srv.shutdown()

    def test_metrics_endpoint(self):
        srv = self._start_server(
            lambda: {"status": "healthy"},
            lambda: {"rpcs": {"Test": {"count": 5}}, "errors": {"total_count": 0}},
            port=19092,
        )
        try:
            time.sleep(0.2)
            resp = urllib.request.urlopen("http://localhost:19092/metrics")
            data = json.loads(resp.read())
            assert data["rpcs"]["Test"]["count"] == 5
        finally:
            srv.shutdown()

    def test_ready_healthy(self):
        srv = self._start_server(
            lambda: {"status": "healthy"},
            lambda: {},
            port=19093,
        )
        try:
            time.sleep(0.2)
            resp = urllib.request.urlopen("http://localhost:19093/ready")
            data = json.loads(resp.read())
            assert data["ready"] is True
        finally:
            srv.shutdown()

    def test_ready_degraded(self):
        srv = self._start_server(
            lambda: {"status": "degraded"},
            lambda: {},
            port=19094,
        )
        try:
            time.sleep(0.2)
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen("http://localhost:19094/ready")
            assert exc_info.value.code == 503
        finally:
            srv.shutdown()

    def test_404(self):
        srv = self._start_server(
            lambda: {"status": "healthy"},
            lambda: {},
            port=19095,
        )
        try:
            time.sleep(0.2)
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen("http://localhost:19095/nonexistent")
            assert exc_info.value.code == 404
        finally:
            srv.shutdown()


# ════════════════════════════════════════════════════════════════
# OracleAlerter Tests
# ════════════════════════════════════════════════════════════════


class TestOracleAlerter:
    def test_cooldown_prevents_duplicate(self):
        from devops.alerts.oracle_alerts import OracleAlerter

        alerter = OracleAlerter(cooldown=300)
        assert alerter._should_alert("test:key") is True
        assert alerter._should_alert("test:key") is False

    def test_different_keys_alert_independently(self):
        from devops.alerts.oracle_alerts import OracleAlerter

        alerter = OracleAlerter(cooldown=300)
        assert alerter._should_alert("key:a") is True
        assert alerter._should_alert("key:b") is True

    def test_cooldown_expired(self):
        from devops.alerts.oracle_alerts import OracleAlerter

        alerter = OracleAlerter(cooldown=0)
        assert alerter._should_alert("test") is True
        assert alerter._should_alert("test") is True

    @mock.patch("devops.alerts.oracle_alerts.urllib.request.urlopen")
    def test_send_telegram_success(self, mock_urlopen):
        from devops.alerts.oracle_alerts import OracleAlerter

        mock_resp = mock.MagicMock()
        mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = mock.MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        alerter = OracleAlerter(bot_token="test_token", chat_id="12345")
        result = alerter._send_telegram("test message")
        assert result is True
        mock_urlopen.assert_called_once()

    def test_send_telegram_no_config(self):
        from devops.alerts.oracle_alerts import OracleAlerter

        alerter = OracleAlerter(bot_token="", chat_id="")
        result = alerter._send_telegram("test")
        assert result is False

    @mock.patch.object(
        __import__(
            "devops.alerts.oracle_alerts", fromlist=["OracleAlerter"]
        ).OracleAlerter,
        "_fetch_json",
    )
    @mock.patch.object(
        __import__(
            "devops.alerts.oracle_alerts", fromlist=["OracleAlerter"]
        ).OracleAlerter,
        "_send_telegram",
    )
    def test_check_unreachable_sends_critical(self, mock_send, mock_fetch):
        from devops.alerts.oracle_alerts import OracleAlerter

        mock_fetch.return_value = None  # simulate unreachable

        alerter = OracleAlerter(bot_token="tok", chat_id="123", cooldown=0)
        alerter.check_and_alert()

        mock_send.assert_called_once()
        call_text = mock_send.call_args[0][0]
        assert "CRITICAL" in call_text
        assert "Unreachable" in call_text

    @mock.patch.object(
        __import__(
            "devops.alerts.oracle_alerts", fromlist=["OracleAlerter"]
        ).OracleAlerter,
        "_fetch_json",
    )
    @mock.patch.object(
        __import__(
            "devops.alerts.oracle_alerts", fromlist=["OracleAlerter"]
        ).OracleAlerter,
        "_send_telegram",
    )
    def test_check_recovery_sends_info(self, mock_send, mock_fetch):
        from devops.alerts.oracle_alerts import OracleAlerter

        alerter = OracleAlerter(bot_token="tok", chat_id="123", cooldown=0)
        alerter._last_status = "down"

        def side_effect(path):
            if path == "/health":
                return {"status": "healthy", "uptime_seconds": 100, "checks": {}}
            return {"rpcs": {}, "errors": {"total_count": 0, "rate_percent": 0}}

        mock_fetch.side_effect = side_effect
        alerter.check_and_alert()

        mock_send.assert_called_once()
        call_text = mock_send.call_args[0][0]
        assert "Recovered" in call_text
