"""Abstract base class that every puzzle solver must implement."""

from abc import ABC, abstractmethod
import threading
import time
import logging

logger = logging.getLogger(__name__)


class BaseSolver(ABC):
    """Every puzzle type implements this interface."""

    def __init__(self, callback=None):
        self.callback = callback
        self.running = False
        self.start_time = 0
        self._thread = None

    @abstractmethod
    def solve(self):
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass

    def start(self):
        """Launch solver in background thread."""
        if self.running:
            return
        self.running = True
        self.start_time = time.time()
        self._thread = threading.Thread(target=self._run_wrapper, daemon=True)
        self._thread.start()

    def stop(self):
        """Request solver to stop."""
        self.running = False

    def _run_wrapper(self):
        """Wrapper that catches exceptions and reports them via callback."""
        try:
            self.solve()
        except Exception as e:
            logger.error(f"Solver error: {e}")
            self._emit(
                {
                    "status": "error",
                    "message": str(e),
                    "progress": 0,
                    "candidates_tested": 0,
                    "candidates_total": -1,
                    "elapsed": time.time() - self.start_time,
                    "current_best": None,
                    "solution": None,
                }
            )

    def _emit(self, data: dict):
        """Send progress update to GUI via callback."""
        if self.callback:
            data.setdefault("elapsed", time.time() - self.start_time)
            self.callback(data)
