"""
Lightweight HTTP monitoring sidecar for the Oracle service.

Runs alongside gRPC on a separate port (default 9090), exposing:
- GET /health  — service health status (JSON)
- GET /metrics — RPC performance metrics (JSON)
- GET /ready   — readiness probe (JSON)

Uses stdlib http.server — zero external dependencies.
"""

import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


def _make_handler(health_fn, metrics_fn):
    """Create a request handler class with bound health/metrics functions."""

    class MonitoringHandler(BaseHTTPRequestHandler):
        """Handles monitoring HTTP requests."""

        def do_GET(self):
            path = self.path.split("?")[0].rstrip("/")

            if path == "/health":
                self._respond_json(health_fn())
            elif path == "/metrics":
                self._respond_json(metrics_fn())
            elif path == "/ready":
                health = health_fn()
                status = health.get("status", "unknown")
                code = 200 if status == "healthy" else 503
                self._respond_json(
                    {"ready": status == "healthy", "status": status}, code
                )
            else:
                self._respond_json({"error": "not found"}, 404)

        def _respond_json(self, data, code=200):
            body = json.dumps(data, default=str).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            # Suppress default stderr logging to avoid noise
            pass

    return MonitoringHandler


def start_http_server(health_fn, metrics_fn, port=9090):
    """Start the monitoring HTTP server in a daemon thread.

    Parameters
    ----------
    health_fn : callable
        Returns a dict with at least {"status": "healthy"|"degraded"|"down"}.
    metrics_fn : callable
        Returns a dict of metrics (from OracleMetrics.get_snapshot()).
    port : int
        Port to listen on (default 9090).

    Returns
    -------
    HTTPServer
        The server instance (call .shutdown() to stop).
    """
    handler_cls = _make_handler(health_fn, metrics_fn)
    server = HTTPServer(("0.0.0.0", port), handler_cls)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Monitoring HTTP server listening on port %d", port)

    return server
