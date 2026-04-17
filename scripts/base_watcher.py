"""
base_watcher.py - Abstract base class for all AI Employee watchers.
All watchers inherit from this and implement check_for_updates() and create_action_file().
"""
import time
import logging
import json
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        # Ensure required directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create a .md file in Needs_Action folder for Claude to process."""
        pass

    def log_event(self, action_type: str, details: dict):
        """Append a structured JSON log entry to today's log file."""
        logs_dir = self.vault_path / "Logs"
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": self.__class__.__name__,
            **details,
        }

        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                entries = []

        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2))

    def run(self):
        self.logger.info(f"Starting {self.__class__.__name__} (interval={self.check_interval}s)")
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    path = self.create_action_file(item)
                    self.logger.info(f"Created action file: {path.name}")
            except Exception as e:
                self.logger.error(f"Error during check: {e}", exc_info=True)
            time.sleep(self.check_interval)
