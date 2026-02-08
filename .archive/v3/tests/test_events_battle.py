"""Battle tests for engines/events.py — stress, edge cases, concurrency."""

import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engines import events
from engines.events import (
    CHECKPOINT_SAVED,
    CONFIG_CHANGED,
    FINDING_FOUND,
    HEALTH_CHANGED,
    HIGH_SCORE,
    LEVEL_UP,
    SCAN_STARTED,
    SCAN_STOPPED,
    SHUTDOWN,
    TERMINAL_STATUS_CHANGED,
    clear,
    emit,
    get_recent_events,
    subscribe,
    unsubscribe,
)


class TestEventsBattle(unittest.TestCase):
    """Battle tests: stress, reentrancy, concurrency, and edge cases."""

    def setUp(self):
        clear()

    def tearDown(self):
        clear()

    # 1. Subscribe 100 different callbacks to the same event, emit reaches all
    def test_100_subscribers(self):
        results = []

        def make_handler(idx):
            def handler(data):
                results.append(idx)

            return handler

        handlers = [make_handler(i) for i in range(100)]
        for h in handlers:
            subscribe(FINDING_FOUND, h)

        emit(FINDING_FOUND, {"test": "mass"})

        self.assertEqual(len(results), 100)
        self.assertEqual(sorted(results), list(range(100)))

    # 2. Handler that emits another event during handling, no deadlock
    def test_reentrant_emit(self):
        outer_received = []
        inner_received = []

        def inner_handler(data):
            inner_received.append(data)

        subscribe(HEALTH_CHANGED, inner_handler)

        def outer_handler(data):
            outer_received.append(data)
            emit(HEALTH_CHANGED, {"reentrant": True})

        subscribe(FINDING_FOUND, outer_handler)

        emit(FINDING_FOUND, {"trigger": "outer"})

        self.assertEqual(len(outer_received), 1)
        self.assertEqual(outer_received[0]["trigger"], "outer")
        self.assertEqual(len(inner_received), 1)
        self.assertTrue(inner_received[0]["reentrant"])

    # 3. Emit 1000 events rapidly, deque stays at maxlen=100
    def test_1000_rapid_emissions(self):
        for i in range(1000):
            emit(SCAN_STARTED, {"i": i})

        recent = get_recent_events(limit=200)
        self.assertLessEqual(len(recent), 100)

        # Verify the deque itself is capped at 100
        with events._lock:
            self.assertEqual(len(events._recent_events), 100)

        # The most recent event should be i=999
        last = recent[-1]
        self.assertEqual(last["data"]["i"], 999)

    # 4. Handler that subscribes a new callback during emit
    def test_subscribe_during_emit(self):
        late_results = []

        def late_handler(data):
            late_results.append(data)

        def subscribing_handler(data):
            subscribe(FINDING_FOUND, late_handler)

        subscribe(FINDING_FOUND, subscribing_handler)

        # First emit: subscribing_handler runs, adds late_handler.
        # late_handler should NOT fire on this emit (snapshot already taken).
        emit(FINDING_FOUND, {"round": 1})
        self.assertEqual(len(late_results), 0)

        # Second emit: both handlers fire, late_handler now included.
        emit(FINDING_FOUND, {"round": 2})
        self.assertEqual(len(late_results), 1)
        self.assertEqual(late_results[0]["round"], 2)

    # 5. Handler that unsubscribes itself during emit
    def test_unsubscribe_during_emit(self):
        call_count = [0]

        def self_removing_handler(data):
            call_count[0] += 1
            unsubscribe(SCAN_STOPPED, self_removing_handler)

        other_results = []

        def other_handler(data):
            other_results.append(data)

        subscribe(SCAN_STOPPED, self_removing_handler)
        subscribe(SCAN_STOPPED, other_handler)

        # First emit: both fire (snapshot taken before unsubscribe)
        emit(SCAN_STOPPED, {"round": 1})
        self.assertEqual(call_count[0], 1)
        self.assertEqual(len(other_results), 1)

        # Second emit: self_removing_handler already unsubscribed
        emit(SCAN_STOPPED, {"round": 2})
        self.assertEqual(call_count[0], 1)  # no additional call
        self.assertEqual(len(other_results), 2)

    # 6. One handler throws, rest still execute
    def test_handler_exception_doesnt_break_others(self):
        results = []

        def handler_before(data):
            results.append("before")

        def bad_handler(data):
            raise RuntimeError("Intentional explosion")

        def handler_after(data):
            results.append("after")

        subscribe(LEVEL_UP, handler_before)
        subscribe(LEVEL_UP, bad_handler)
        subscribe(LEVEL_UP, handler_after)

        emit(LEVEL_UP, {"level": 5})

        self.assertIn("before", results)
        self.assertIn("after", results)
        self.assertEqual(len(results), 2)

    # 7. get_recent_events with custom limit
    def test_get_recent_events_limit(self):
        for i in range(50):
            emit(HIGH_SCORE, {"score": i})

        # Default limit 20
        recent_default = get_recent_events()
        self.assertEqual(len(recent_default), 20)

        # Custom limit 5
        recent_5 = get_recent_events(limit=5)
        self.assertEqual(len(recent_5), 5)
        self.assertEqual(recent_5[-1]["data"]["score"], 49)
        self.assertEqual(recent_5[0]["data"]["score"], 45)

        # Limit larger than available
        recent_all = get_recent_events(limit=200)
        self.assertEqual(len(recent_all), 50)

    # 8. Emit with no subscribers doesn't crash
    def test_emit_no_subscribers(self):
        # Emit to events that have never been subscribed to
        try:
            emit(SHUTDOWN, {"reason": "test"})
            emit(CONFIG_CHANGED, None)
            emit(CHECKPOINT_SAVED)
            emit("NONEXISTENT_EVENT", {"x": 1})
        except Exception as e:
            self.fail(f"emit with no subscribers raised: {e}")

        # Verify events were still recorded
        recent = get_recent_events(limit=10)
        self.assertEqual(len(recent), 4)

    # 9. Subscribe then unsubscribe, emit doesn't call
    def test_subscribe_unsubscribe_same_callback(self):
        call_count = [0]

        def handler(data):
            call_count[0] += 1

        subscribe(FINDING_FOUND, handler)
        emit(FINDING_FOUND, {"round": 1})
        self.assertEqual(call_count[0], 1)

        unsubscribe(FINDING_FOUND, handler)
        emit(FINDING_FOUND, {"round": 2})
        self.assertEqual(call_count[0], 1)  # still 1, not called again

        # Unsubscribing again should be harmless
        unsubscribe(FINDING_FOUND, handler)
        emit(FINDING_FOUND, {"round": 3})
        self.assertEqual(call_count[0], 1)

    # 10. 10 threads emitting simultaneously, no crashes
    def test_concurrent_emit(self):
        results = []
        lock = threading.Lock()

        def handler(data):
            with lock:
                results.append(data["thread_id"])

        subscribe(SCAN_STARTED, handler)

        errors = []

        def emitter(thread_id):
            try:
                for i in range(100):
                    emit(SCAN_STARTED, {"thread_id": thread_id, "i": i})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=emitter, args=(t,)) for t in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent emit errors: {errors}")
        self.assertEqual(len(results), 1000)  # 10 threads * 100 emits

        # Verify deque capped at 100 despite 1000 emits
        with events._lock:
            self.assertEqual(len(events._recent_events), 100)

    # 11. clear removes all subscribers and events
    def test_clear_removes_all(self):
        results = []

        subscribe(FINDING_FOUND, lambda d: results.append("finding"))
        subscribe(SCAN_STARTED, lambda d: results.append("scan"))
        subscribe(LEVEL_UP, lambda d: results.append("level"))

        emit(FINDING_FOUND, {"a": 1})
        emit(SCAN_STARTED, {"b": 2})
        self.assertEqual(len(results), 2)
        self.assertEqual(len(get_recent_events(limit=100)), 2)

        clear()

        # Subscribers gone
        emit(FINDING_FOUND, {"c": 3})
        emit(SCAN_STARTED, {"d": 4})
        emit(LEVEL_UP, {"e": 5})
        self.assertEqual(len(results), 2)  # no new calls

        # Recent events cleared (only the 3 post-clear emits exist)
        recent = get_recent_events(limit=100)
        self.assertEqual(len(recent), 3)

    # 12. Emit with dict data, handler receives exact same data
    def test_event_data_integrity(self):
        received = []
        payload = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "balance": 0.00000001,
            "chains": ["BTC", "ETH", "BSC"],
            "nested": {"deep": {"value": 42}},
            "none_field": None,
            "flag": True,
        }

        def handler(data):
            received.append(data)

        subscribe(FINDING_FOUND, handler)
        emit(FINDING_FOUND, payload)

        self.assertEqual(len(received), 1)
        data = received[0]

        # Verify every field matches exactly
        self.assertEqual(data["address"], payload["address"])
        self.assertEqual(data["balance"], payload["balance"])
        self.assertEqual(data["chains"], ["BTC", "ETH", "BSC"])
        self.assertEqual(data["nested"]["deep"]["value"], 42)
        self.assertIsNone(data["none_field"])
        self.assertTrue(data["flag"])

        # Verify it is the same object (not a copy)
        self.assertIs(data, payload)


if __name__ == "__main__":
    unittest.main()
