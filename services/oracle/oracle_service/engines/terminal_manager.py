"""
Terminal Manager — Multi-Terminal Command Center for NPS.

Manages multiple simultaneous scan terminals, each running its own
UnifiedSolver instance in a dedicated thread.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)

MAX_TERMINALS = 10

_lock = threading.Lock()
_terminals = {}  # terminal_id -> terminal info dict


def create_terminal(settings=None):
    """Create a new terminal. Returns terminal_id.

    Args:
        settings: dict with mode, puzzle_enabled, chains, etc.

    Returns:
        terminal_id string, or None if max reached.
    """
    with _lock:
        if len(_terminals) >= MAX_TERMINALS:
            logger.warning(f"Max terminals ({MAX_TERMINALS}) reached")
            return None

        terminal_id = f"T{len(_terminals) + 1}_{int(time.time())}"
        _terminals[terminal_id] = {
            "id": terminal_id,
            "settings": settings or {},
            "solver": None,
            "status": "created",
            "created": time.time(),
        }

    logger.info(f"Terminal created: {terminal_id}")
    return terminal_id


def start_terminal(terminal_id):
    """Start a terminal's solver. Returns True on success."""
    with _lock:
        term = _terminals.get(terminal_id)
        if not term:
            return False
        if term["status"] == "running":
            return False

    try:
        from solvers.unified_solver import UnifiedSolver

        settings = term["settings"]
        solver = UnifiedSolver(
            mode=settings.get("mode", "random_key"),
            puzzle_enabled=settings.get("puzzle_enabled", False),
            puzzle_number=settings.get("puzzle_number"),
            strategy=settings.get("strategy", "hybrid"),
            chains=settings.get("chains", ["btc", "eth"]),
            tokens=settings.get("tokens", ["USDT", "USDC"]),
            online_check=settings.get("online_check", False),
            check_every_n=settings.get("check_every_n", 5000),
            use_brain=settings.get("use_brain", False),
            terminal_id=terminal_id,
            callback=settings.get("callback"),
        )
        solver.start()

        with _lock:
            _terminals[terminal_id]["solver"] = solver
            _terminals[terminal_id]["status"] = "running"

        logger.info(f"Terminal started: {terminal_id}")
        try:
            from engines.events import emit, TERMINAL_STATUS_CHANGED

            emit(TERMINAL_STATUS_CHANGED, {"id": terminal_id, "status": "running"})
        except Exception:
            pass
        return True
    except Exception as e:
        logger.error(f"Failed to start terminal {terminal_id}: {e}")
        return False


def stop_terminal(terminal_id):
    """Stop a terminal's solver. Returns True on success."""
    with _lock:
        term = _terminals.get(terminal_id)
        if not term:
            return False
        solver = term.get("solver")

    if solver and solver.running:
        solver.stop()
        if solver._thread:
            solver._thread.join(timeout=3)

    with _lock:
        if terminal_id in _terminals:
            _terminals[terminal_id]["status"] = "stopped"

    logger.info(f"Terminal stopped: {terminal_id}")
    try:
        from engines.events import emit, TERMINAL_STATUS_CHANGED

        emit(TERMINAL_STATUS_CHANGED, {"id": terminal_id, "status": "stopped"})
    except Exception:
        pass
    return True


def pause_terminal(terminal_id):
    """Pause a terminal's solver. Returns True on success."""
    with _lock:
        term = _terminals.get(terminal_id)
        if not term:
            return False
        solver = term.get("solver")

    if solver and solver.running:
        solver.pause()
        with _lock:
            _terminals[terminal_id]["status"] = "paused"
        try:
            from engines.events import emit, TERMINAL_STATUS_CHANGED

            emit(TERMINAL_STATUS_CHANGED, {"id": terminal_id, "status": "paused"})
        except Exception:
            pass
        return True
    return False


def resume_terminal(terminal_id):
    """Resume a paused terminal. Returns True on success."""
    with _lock:
        term = _terminals.get(terminal_id)
        if not term:
            return False
        solver = term.get("solver")

    if solver and solver.running:
        solver.resume()
        with _lock:
            _terminals[terminal_id]["status"] = "running"
        try:
            from engines.events import emit, TERMINAL_STATUS_CHANGED

            emit(TERMINAL_STATUS_CHANGED, {"id": terminal_id, "status": "running"})
        except Exception:
            pass
        return True
    return False


def remove_terminal(terminal_id):
    """Remove a terminal. Must be stopped first. Returns True on success."""
    with _lock:
        term = _terminals.get(terminal_id)
        if not term:
            return False
        if term["status"] == "running":
            return False
        del _terminals[terminal_id]

    logger.info(f"Terminal removed: {terminal_id}")
    return True


def start_all():
    """Start all stopped terminals. Returns count started."""
    count = 0
    with _lock:
        ids = list(_terminals.keys())
    for tid in ids:
        with _lock:
            status = _terminals.get(tid, {}).get("status")
        if status in ("created", "stopped"):
            if start_terminal(tid):
                count += 1
    return count


def stop_all():
    """Stop all running terminals. Returns count stopped."""
    count = 0
    with _lock:
        ids = list(_terminals.keys())
    for tid in ids:
        with _lock:
            status = _terminals.get(tid, {}).get("status")
        if status in ("running", "paused"):
            if stop_terminal(tid):
                count += 1
    return count


def get_terminal_stats(terminal_id):
    """Get stats for a specific terminal."""
    with _lock:
        term = _terminals.get(terminal_id)
        if not term:
            return None
        solver = term.get("solver")

    if solver:
        stats = solver.get_stats()
        stats["status"] = term["status"]
        return stats

    return {"status": term["status"], "keys_tested": 0, "speed": 0}


def get_all_stats():
    """Get stats for all terminals."""
    result = {}
    with _lock:
        ids = list(_terminals.keys())
    for tid in ids:
        result[tid] = get_terminal_stats(tid)
    return result


def get_active_count():
    """Return number of running terminals."""
    with _lock:
        return sum(1 for t in _terminals.values() if t["status"] == "running")


def list_terminals():
    """List all terminal IDs and their status."""
    with _lock:
        return [
            {"id": tid, "status": info["status"], "settings": info["settings"]}
            for tid, info in _terminals.items()
        ]


def reset():
    """Reset all terminals. For testing."""
    global _terminals
    with _lock:
        for term in _terminals.values():
            solver = term.get("solver")
            if solver and solver.running:
                solver.stop()
        _terminals = {}
