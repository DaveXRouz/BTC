"""
Health Monitoring for NPS.

Background thread that periodically checks API endpoint connectivity
and reports health status.
"""

import logging
import threading
import time
import urllib.request
import ssl

logger = logging.getLogger(__name__)

try:
    import certifi

    _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _ssl_ctx = ssl._create_unverified_context()

_lock = threading.Lock()
_running = False
_thread = None
_status = {}

DEFAULT_ENDPOINTS = {
    "blockstream": "https://blockstream.info/api/blocks/tip/height",
    "eth_rpc": "https://eth.llamarpc.com",
    "bsc": "https://bsc-dataseed.binance.org",
    "polygon": "https://polygon-rpc.com",
}


def _check_endpoint(name, url, timeout=5):
    """Check if an endpoint is reachable."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NPS/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
            return resp.status == 200
    except Exception:
        return False


def _monitor_loop(interval):
    """Background monitoring loop."""
    global _status, _running
    while _running:
        for name, url in DEFAULT_ENDPOINTS.items():
            if not _running:
                break
            healthy = _check_endpoint(name, url)
            old_healthy = None
            with _lock:
                old_info = _status.get(name)
                if old_info is not None:
                    old_healthy = old_info.get("healthy")
                _status[name] = {
                    "healthy": healthy,
                    "last_check": time.time(),
                    "url": url,
                }

            # Emit event if health status changed
            if old_healthy is not None and old_healthy != healthy:
                try:
                    from engines.events import emit, HEALTH_CHANGED

                    emit(
                        HEALTH_CHANGED,
                        {"endpoint": name, "healthy": healthy, "url": url},
                    )
                except Exception:
                    pass

        # Sleep in small increments so we can stop quickly
        for _ in range(int(interval)):
            if not _running:
                break
            time.sleep(1)


def start_monitoring(interval=60):
    """Start the health monitoring background thread."""
    global _running, _thread
    if _running:
        return

    _running = True
    _thread = threading.Thread(target=_monitor_loop, args=(interval,), daemon=True)
    _thread.start()
    logger.info("Health monitoring started")


def stop_monitoring():
    """Stop the health monitoring thread."""
    global _running, _thread
    _running = False
    if _thread:
        _thread.join(timeout=5)
        _thread = None
    logger.info("Health monitoring stopped")


def get_status():
    """Get current health status for all endpoints.

    Returns:
        dict: endpoint_name -> {healthy: bool, last_check: float, url: str}
    """
    with _lock:
        return dict(_status)


def is_healthy(endpoint):
    """Check if a specific endpoint is healthy.

    Args:
        endpoint: endpoint name (e.g., "blockstream", "eth_rpc")

    Returns:
        bool
    """
    with _lock:
        info = _status.get(endpoint)
    if info is None:
        return False
    return info.get("healthy", False)


def reset():
    """Reset health state. For testing."""
    global _status, _running
    stop_monitoring()
    with _lock:
        _status = {}
