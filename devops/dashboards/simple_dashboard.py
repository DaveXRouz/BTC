"""
Simple monitoring dashboard for NPS Oracle service.

Fetches health and metrics from the Oracle HTTP sidecar and renders
a dark-themed single-page dashboard. Auto-refreshes every 5 seconds.

Requires: flask (pip install flask)

Usage:
    ORACLE_HTTP_URL=http://oracle-service:9090 python simple_dashboard.py

Runs on port 9000 by default (DASHBOARD_PORT env var).
"""

import json
import logging
import os
import urllib.request
import urllib.error

from flask import Flask, jsonify, render_template

logger = logging.getLogger(__name__)

ORACLE_HTTP_URL = os.environ.get("ORACLE_HTTP_URL", "http://localhost:9090")
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "9000"))

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)


def _fetch_json(path, timeout=5):
    """Fetch JSON from Oracle HTTP sidecar. Returns dict or None on error."""
    url = f"{ORACLE_HTTP_URL}{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.debug("Failed to fetch %s: %s", url, e)
        return None


@app.route("/")
def dashboard():
    """Render the dashboard page."""
    return render_template("dashboard.html", oracle_url=ORACLE_HTTP_URL)


@app.route("/api/status")
def api_status():
    """Proxy health + metrics from Oracle sidecar for the dashboard."""
    health = _fetch_json("/health")
    metrics = _fetch_json("/metrics")

    if health is None:
        health = {"status": "unreachable", "checks": {}}
    if metrics is None:
        metrics = {"rpcs": {}, "errors": {"total_count": 0, "rate_percent": 0}}

    return jsonify({"health": health, "metrics": metrics})


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info(
        "Dashboard starting on port %d, Oracle URL: %s", DASHBOARD_PORT, ORACLE_HTTP_URL
    )
    app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=False)
