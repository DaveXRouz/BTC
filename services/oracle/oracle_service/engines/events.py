"""
Event Bus — Centralized pub/sub for cross-component communication.

Thread-safe, module-level singleton. Supports GUI-safe delivery
via tkinter's after() mechanism.

Usage:
    from engines.events import subscribe, emit

    subscribe(FINDING_FOUND, my_handler)
    emit(FINDING_FOUND, {"address": "1abc...", "balance": 0.5})
"""

import logging
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)

# Event names
FINDING_FOUND = "FINDING_FOUND"
HEALTH_CHANGED = "HEALTH_CHANGED"
AI_ADJUSTED = "AI_ADJUSTED"
LEVEL_UP = "LEVEL_UP"
CHECKPOINT_SAVED = "CHECKPOINT_SAVED"
TERMINAL_STATUS_CHANGED = "TERMINAL_STATUS_CHANGED"
SCAN_STARTED = "SCAN_STARTED"
SCAN_STOPPED = "SCAN_STOPPED"
HIGH_SCORE = "HIGH_SCORE"
CONFIG_CHANGED = "CONFIG_CHANGED"
SHUTDOWN = "SHUTDOWN"

_lock = threading.Lock()
_subscribers = {}  # event_name -> list of (callback, gui_root_or_None)
_recent_events = deque(maxlen=100)


def subscribe(event, callback, gui_root=None):
    """Subscribe to an event.

    Args:
        event: Event name string.
        callback: Callable(data_dict). Called on emit.
        gui_root: If provided (tk.Tk), callback is scheduled via
                  root.after(0, ...) for thread-safe GUI updates.
    """
    with _lock:
        if event not in _subscribers:
            _subscribers[event] = []
        _subscribers[event].append((callback, gui_root))
    logger.debug(f"Subscribed to {event}: {callback.__name__}")


def unsubscribe(event, callback):
    """Remove a callback from an event."""
    with _lock:
        if event in _subscribers:
            _subscribers[event] = [
                (cb, root) for cb, root in _subscribers[event] if cb is not callback
            ]


def emit(event, data=None):
    """Emit an event to all subscribers.

    Args:
        event: Event name string.
        data: Optional dict payload.
    """
    if data is None:
        data = {}

    entry = {"event": event, "data": data, "timestamp": time.time()}

    with _lock:
        _recent_events.append(entry)
        subs = list(_subscribers.get(event, []))

    for callback, gui_root in subs:
        try:
            if gui_root:
                gui_root.after(0, callback, data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"Event handler error for {event}: {e}")


def get_recent_events(limit=20):
    """Return recent events for late-joining components."""
    with _lock:
        events = list(_recent_events)
    return events[-limit:]


def clear():
    """Clear all subscriptions and recent events. For testing."""
    global _subscribers, _recent_events
    with _lock:
        _subscribers = {}
        _recent_events = deque(maxlen=100)
