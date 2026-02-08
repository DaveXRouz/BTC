"""
Error Handling Utilities — Value-based error returns and safe wrappers.

Provides:
- Result class for value-based error handling (no exceptions for expected failures)
- @safe_callback decorator for GUI callback protection
- safe_file_read() for robust JSON/text file loading
"""

import json
import logging

logger = logging.getLogger(__name__)


class Result:
    """Value-based error return. Avoids exceptions for expected failures.

    Usage:
        r = Result.ok(42)
        if r.success:
            print(r.value)

        r = Result.fail("file not found")
        if not r.success:
            print(r.error)
    """

    __slots__ = ("success", "value", "error")

    def __init__(self, success, value=None, error=None):
        self.success = success
        self.value = value
        self.error = error

    @classmethod
    def ok(cls, value=None):
        return cls(success=True, value=value)

    @classmethod
    def fail(cls, error="Unknown error"):
        return cls(success=False, error=str(error))

    def __repr__(self):
        if self.success:
            return f"Result.ok({self.value!r})"
        return f"Result.fail({self.error!r})"

    def __bool__(self):
        return self.success


def safe_callback(status_updater=None):
    """Decorator that wraps GUI callbacks in try/except.

    Catches all exceptions, logs them, and optionally calls
    status_updater(error_msg) to show the error in UI.

    Args:
        status_updater: Optional callable(str) for GUI error display.

    Usage:
        @safe_callback(status_updater=self._show_error)
        def _on_click(self):
            ...
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Callback error in {func.__name__}: {e}", exc_info=True)
                if status_updater:
                    try:
                        status_updater(f"Error: {e}")
                    except Exception:
                        pass
                return None

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


def safe_file_read(path, default=None):
    """Safely read and parse a JSON file.

    Handles FileNotFoundError, JSONDecodeError, PermissionError.
    Returns Result.ok(data) on success or Result.fail(error) on failure.
    If default is provided, returns Result.ok(default) on failure instead.

    Args:
        path: Path to JSON file (str or Path).
        default: Default value to return on failure (makes Result.ok).

    Returns:
        Result with parsed data or error.
    """
    try:
        with open(str(path), "r") as f:
            data = json.load(f)
        return Result.ok(data)
    except FileNotFoundError:
        if default is not None:
            return Result.ok(default)
        return Result.fail(f"File not found: {path}")
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error in {path}: {e}")
        if default is not None:
            return Result.ok(default)
        return Result.fail(f"Invalid JSON in {path}: {e}")
    except PermissionError:
        logger.error(f"Permission denied: {path}")
        if default is not None:
            return Result.ok(default)
        return Result.fail(f"Permission denied: {path}")
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        if default is not None:
            return Result.ok(default)
        return Result.fail(f"Error reading {path}: {e}")
