"""
retry_handler.py - Error recovery and graceful degradation for AI Employee.

Provides:
  - @with_retry decorator for transient failures (network, API rate limits)
  - ErrorQueue for offline queuing when services are down
  - GracefulDegradation context manager
"""
import json
import logging
import time
from datetime import datetime
from functools import wraps
from pathlib import Path

VAULT = Path("C:/Users/samee/AI_Employee_Vault")
logger = logging.getLogger("RetryHandler")


# ── Custom exceptions ────────────────────────────────────────────

class TransientError(Exception):
    """Temporary failure — safe to retry (network blip, rate limit)."""
    pass


class PermanentError(Exception):
    """Unrecoverable failure — alert human, do not retry."""
    pass


# ── Retry decorator ──────────────────────────────────────────────

def with_retry(max_attempts: int = 3, base_delay: float = 2.0, max_delay: float = 60.0):
    """
    Decorator for exponential-backoff retry on TransientError.

    Usage:
        @with_retry(max_attempts=3)
        def call_gmail_api():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except TransientError as e:
                    last_error = e
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.0f}s..."
                    )
                    time.sleep(delay)
                except PermanentError as e:
                    logger.error(f"{func.__name__} permanent failure: {e}")
                    _alert_human(f"Permanent error in `{func.__name__}`: {e}")
                    raise
            raise last_error
        return wrapper
    return decorator


# ── Offline queue ────────────────────────────────────────────────

class ErrorQueue:
    """
    Queues failed operations for retry when the service comes back online.
    Stored as JSON in /Logs/error_queue.json
    """

    def __init__(self):
        self.queue_file = VAULT / "Logs" / "error_queue.json"
        self.queue_file.parent.mkdir(exist_ok=True)

    def enqueue(self, operation: str, payload: dict):
        """Add a failed operation to the retry queue."""
        queue = self._load()
        queue.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "payload": payload,
            "attempts": 0,
            "status": "pending"
        })
        self._save(queue)
        logger.info(f"Queued failed operation: {operation}")

    def get_pending(self) -> list:
        return [item for item in self._load() if item["status"] == "pending"]

    def mark_done(self, index: int):
        queue = self._load()
        if 0 <= index < len(queue):
            queue[index]["status"] = "completed"
            queue[index]["completed_at"] = datetime.now().isoformat()
        self._save(queue)

    def mark_failed(self, index: int, reason: str):
        queue = self._load()
        if 0 <= index < len(queue):
            queue[index]["status"] = "failed"
            queue[index]["failure_reason"] = reason
            queue[index]["failed_at"] = datetime.now().isoformat()
        self._save(queue)

    def _load(self) -> list:
        if self.queue_file.exists():
            try:
                return json.loads(self.queue_file.read_text())
            except Exception:
                pass
        return []

    def _save(self, queue: list):
        self.queue_file.write_text(json.dumps(queue, indent=2))


# ── Graceful degradation ─────────────────────────────────────────

class GracefulDegradation:
    """
    Context manager for graceful degradation.
    Logs failures and optionally queues them for retry.

    Usage:
        with GracefulDegradation("gmail_check", queue=error_queue):
            watcher.check_for_updates()
    """

    def __init__(self, component: str, queue: ErrorQueue = None, payload: dict = None):
        self.component = component
        self.queue = queue
        self.payload = payload or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False  # No error

        if exc_type == TransientError:
            logger.warning(f"[{self.component}] Transient failure — degrading gracefully: {exc_val}")
            if self.queue:
                self.queue.enqueue(self.component, self.payload)
            _alert_human(f"`{self.component}` is temporarily unavailable: {exc_val}")
            return True  # Suppress exception, continue

        if exc_type == PermanentError:
            logger.error(f"[{self.component}] Permanent failure: {exc_val}")
            _alert_human(f"`{self.component}` has a permanent failure and needs attention: {exc_val}")
            return True

        # Unknown exception — log but don't suppress
        logger.error(f"[{self.component}] Unexpected error: {exc_val}", exc_info=True)
        _alert_human(f"`{self.component}` crashed unexpectedly: {exc_val}")
        return True  # Suppress to keep other components running


# ── Human alert helper ───────────────────────────────────────────

def _alert_human(message: str):
    """Write a system notification to /Needs_Action for human awareness."""
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        notif = VAULT / "Needs_Action" / f"SYSTEM_{ts}_alert.md"
        notif.write_text(f"""---
type: system_alert
created: {datetime.now().isoformat()}
severity: warning
---

## System Alert

{message}

*This notification was generated automatically by the AI Employee error handler.*
""", encoding="utf-8")
    except Exception as e:
        logger.error(f"Could not write alert notification: {e}")


# ── Audit log helper ─────────────────────────────────────────────

def log_action(action_type: str, actor: str, details: dict, result: str):
    """Append an entry to today's audit log."""
    log_file = VAULT / "Logs" / f"{datetime.now().date().isoformat()}.json"
    try:
        entries = json.loads(log_file.read_text()) if log_file.exists() else []
        entries.append({
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": actor,
            "details": details,
            "result": result
        })
        log_file.write_text(json.dumps(entries, indent=2))
    except Exception as e:
        logger.error(f"Could not write audit log: {e}")
