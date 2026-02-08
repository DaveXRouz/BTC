"""
Oracle service alerter — monitors health/metrics and sends Telegram alerts.

Polls the Oracle HTTP sidecar (/health, /metrics) every CHECK_INTERVAL seconds.
Sends Telegram alerts for:
- CRITICAL: Service down or degraded
- WARNING: Error rate >5%, P95 latency >10s
- INFO: Service recovered from degraded/down state

Uses urllib.request for Telegram (no pip dependencies beyond stdlib).

Environment variables:
    ORACLE_HTTP_URL      — Oracle sidecar URL (default http://oracle-service:9090)
    NPS_BOT_TOKEN        — Telegram bot token
    NPS_CHAT_ID          — Telegram chat ID
    ALERT_CHECK_INTERVAL — Seconds between checks (default 30)
    ALERT_COOLDOWN       — Seconds between same-type alerts (default 300)

Usage:
    python -m devops.alerts.oracle_alerts
    python -m devops.alerts.oracle_alerts --test  # send test alert
"""

import json
import logging
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

ORACLE_HTTP_URL = os.environ.get("ORACLE_HTTP_URL", "http://oracle-service:9090")
BOT_TOKEN = os.environ.get("NPS_BOT_TOKEN", "")
CHAT_ID = os.environ.get("NPS_CHAT_ID", "")
CHECK_INTERVAL = int(os.environ.get("ALERT_CHECK_INTERVAL", "30"))
COOLDOWN = int(os.environ.get("ALERT_COOLDOWN", "300"))

# Thresholds
ERROR_RATE_WARN = 5.0  # percent
P95_WARN_MS = 10000  # 10 seconds

# SSL context for Telegram API
try:
    import certifi

    _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _ssl_ctx = ssl._create_unverified_context()


class OracleAlerter:
    """Monitors Oracle HTTP sidecar and sends Telegram alerts."""

    def __init__(self, oracle_url=None, bot_token=None, chat_id=None, cooldown=None):
        self.oracle_url = oracle_url or ORACLE_HTTP_URL
        self.bot_token = bot_token or BOT_TOKEN
        self.chat_id = chat_id or CHAT_ID
        self.cooldown = cooldown if cooldown is not None else COOLDOWN
        self._last_alert_time = {}  # alert_key -> timestamp
        self._last_status = "unknown"

    def _fetch_json(self, path, timeout=5):
        """Fetch JSON from Oracle HTTP sidecar."""
        url = f"{self.oracle_url}{path}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _send_telegram(self, text):
        """Send an alert via Telegram Bot API. Returns True on success."""
        if not self.bot_token or not self.chat_id:
            logger.debug("Telegram not configured, skipping alert")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps(
            {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx) as resp:
                return True
        except Exception as e:
            logger.warning("Telegram send failed: %s", e)
            return False

    def _should_alert(self, key):
        """Check if enough time has passed since last alert of this type."""
        now = time.time()
        last = self._last_alert_time.get(key, 0)
        if now - last < self.cooldown:
            return False
        self._last_alert_time[key] = now
        return True

    def check_and_alert(self):
        """Run one monitoring cycle: fetch health/metrics, send alerts if needed."""
        health = self._fetch_json("/health")
        metrics = self._fetch_json("/metrics")

        # Service unreachable
        if health is None:
            if self._should_alert("critical:unreachable"):
                self._send_telegram(
                    "<b>CRITICAL: Oracle Service Unreachable</b>\n\n"
                    f"Cannot reach {self.oracle_url}/health\n"
                    f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
                )
            self._last_status = "down"
            return

        status = health.get("status", "unknown")

        # Recovery alert
        if self._last_status in ("down", "degraded") and status == "healthy":
            if self._should_alert("info:recovered"):
                uptime = health.get("uptime_seconds", 0)
                self._send_telegram(
                    "<b>INFO: Oracle Service Recovered</b>\n\n"
                    f"Status: {status}\n"
                    f"Uptime: {uptime}s\n"
                    f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
                )

        # Degraded service
        if status == "degraded":
            if self._should_alert("critical:degraded"):
                checks = health.get("checks", {})
                failed = [k for k, v in checks.items() if "error" in str(v)]
                self._send_telegram(
                    "<b>CRITICAL: Oracle Service Degraded</b>\n\n"
                    f"Failed checks: {', '.join(failed) or 'unknown'}\n"
                    f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
                )

        # Metrics-based alerts
        if metrics:
            errors = metrics.get("errors", {})
            error_rate = errors.get("rate_percent", 0)

            if error_rate > ERROR_RATE_WARN:
                if self._should_alert("warning:error_rate"):
                    self._send_telegram(
                        "<b>WARNING: High Error Rate</b>\n\n"
                        f"Error rate: {error_rate:.1f}%\n"
                        f"Total errors: {errors.get('total_count', 0)}\n"
                        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
                    )

            # Check P95 latency across all RPCs
            rpcs = metrics.get("rpcs", {})
            for rpc_name, rpc_data in rpcs.items():
                p95 = rpc_data.get("p95_ms", 0)
                if p95 > P95_WARN_MS:
                    if self._should_alert(f"warning:p95:{rpc_name}"):
                        self._send_telegram(
                            f"<b>WARNING: High Latency — {rpc_name}</b>\n\n"
                            f"P95: {p95:.0f}ms (threshold: {P95_WARN_MS}ms)\n"
                            f"Avg: {rpc_data.get('avg_ms', 0):.0f}ms\n"
                            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
                        )

        self._last_status = status

    def run_loop(self, interval=None):
        """Run the monitoring loop forever."""
        interval = interval or CHECK_INTERVAL
        logger.info(
            "Oracle alerter started: url=%s interval=%ds cooldown=%ds",
            self.oracle_url,
            interval,
            self.cooldown,
        )

        while True:
            try:
                self.check_and_alert()
            except Exception as e:
                logger.error("Alert check failed: %s", e)
            time.sleep(interval)

    def send_test_alert(self):
        """Send a test alert to verify Telegram configuration."""
        return self._send_telegram(
            "<b>TEST: Oracle Alerter</b>\n\n"
            f"Oracle URL: {self.oracle_url}\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
            "Alert system is working."
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    alerter = OracleAlerter()

    if "--test" in sys.argv:
        ok = alerter.send_test_alert()
        print("Test alert sent:" if ok else "Test alert failed (check token/chat_id)")
        sys.exit(0 if ok else 1)

    alerter.run_loop()
