"""Tests for engines/events.py — Event Bus."""

import threading
import time
import unittest

from engines.events import (
    FINDING_FOUND,
    HEALTH_CHANGED,
    LEVEL_UP,
    SCAN_STARTED,
    SHUTDOWN,
    TERMINAL_STATUS_CHANGED,
    clear,
    emit,
    get_recent_events,
    subscribe,
    unsubscribe,
)


class TestEventBus(unittest.TestCase):
    def setUp(self):
        clear()

    def tearDown(self):
        clear()

    def test_subscribe_and_emit(self):
        received = []
        subscribe(FINDING_FOUND, lambda d: received.append(d))
        emit(FINDING_FOUND, {"address": "1abc"})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["address"], "1abc")

    def test_multiple_subscribers(self):
        r1, r2 = [], []
        subscribe(SCAN_STARTED, lambda d: r1.append(d))
        subscribe(SCAN_STARTED, lambda d: r2.append(d))
        emit(SCAN_STARTED, {"mode": "puzzle"})
        self.assertEqual(len(r1), 1)
        self.assertEqual(len(r2), 1)

    def test_emit_no_subscribers(self):
        # Should not raise
        emit(HEALTH_CHANGED, {"endpoint": "btc", "healthy": True})

    def test_emit_none_data(self):
        received = []
        subscribe(SHUTDOWN, lambda d: received.append(d))
        emit(SHUTDOWN)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], {})

    def test_unsubscribe(self):
        received = []
        handler = lambda d: received.append(d)
        subscribe(LEVEL_UP, handler)
        emit(LEVEL_UP, {"level": 2})
        self.assertEqual(len(received), 1)
        unsubscribe(LEVEL_UP, handler)
        emit(LEVEL_UP, {"level": 3})
        self.assertEqual(len(received), 1)  # No new events

    def test_recent_events(self):
        emit(FINDING_FOUND, {"key": "a"})
        emit(FINDING_FOUND, {"key": "b"})
        emit(SCAN_STARTED, {"mode": "both"})
        recent = get_recent_events(limit=2)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[-1]["event"], SCAN_STARTED)

    def test_handler_error_does_not_break_other_handlers(self):
        r1 = []

        def bad_handler(d):
            raise ValueError("boom")

        subscribe(TERMINAL_STATUS_CHANGED, bad_handler)
        subscribe(TERMINAL_STATUS_CHANGED, lambda d: r1.append(d))
        emit(TERMINAL_STATUS_CHANGED, {"id": "T1"})
        self.assertEqual(len(r1), 1)

    def test_thread_safety(self):
        received = []
        subscribe(FINDING_FOUND, lambda d: received.append(d))

        def emitter():
            for i in range(50):
                emit(FINDING_FOUND, {"i": i})

        threads = [threading.Thread(target=emitter) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(received), 200)


if __name__ == "__main__":
    unittest.main()
