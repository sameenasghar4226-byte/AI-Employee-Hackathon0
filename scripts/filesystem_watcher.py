"""
filesystem_watcher.py - Watches a "drop folder" for new files and creates action items.

Usage:
    python filesystem_watcher.py [--drop-folder PATH] [--vault PATH]

Default drop folder: C:/Users/samee/AI_Employee_Vault/Drop
"""
import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

# Try to import watchdog; give a clear error if missing
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: 'watchdog' package not installed. Run: pip install watchdog")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher


class DropFolderHandler(FileSystemEventHandler):
    """Handles new file events in the drop folder."""

    def __init__(self, watcher: "FilesystemWatcher"):
        self.watcher = watcher

    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        # Skip hidden/temp files
        if source.name.startswith((".", "~", "$")):
            return
        self.watcher.logger.info(f"New file detected: {source.name}")
        self.watcher.create_action_file(source)


class FilesystemWatcher(BaseWatcher):
    """Monitors a drop folder and creates Needs_Action items for any new file."""

    def __init__(self, vault_path: str, drop_folder: str = None):
        super().__init__(vault_path, check_interval=5)
        if drop_folder:
            self.drop_folder = Path(drop_folder)
        else:
            self.drop_folder = self.vault_path / "Drop"
        self.drop_folder.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Watching drop folder: {self.drop_folder}")

    def check_for_updates(self) -> list:
        # Watchdog handles this via events; not used in polling mode
        return []

    def create_action_file(self, source: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        action_file = self.needs_action / f"FILE_{timestamp}_{source.stem}.md"

        size_kb = source.stat().st_size / 1024 if source.exists() else 0
        content = f"""---
type: file_drop
original_name: {source.name}
original_path: {source}
size_kb: {size_kb:.1f}
received: {datetime.now().isoformat()}
status: pending
---

## New File Dropped

A new file has arrived and needs processing.

**File:** `{source.name}`
**Size:** {size_kb:.1f} KB
**Path:** `{source}`

## Suggested Actions
- [ ] Review file contents
- [ ] Categorize and file appropriately
- [ ] Extract any action items
- [ ] Move to /Done when processed
"""
        action_file.write_text(content, encoding="utf-8")
        self.log_event("file_drop_detected", {"file": source.name, "size_kb": size_kb})
        return action_file

    def run(self):
        self.logger.info(f"Starting FilesystemWatcher on: {self.drop_folder}")
        handler = DropFolderHandler(self)
        observer = Observer()
        observer.schedule(handler, str(self.drop_folder), recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            self.logger.info("FilesystemWatcher stopped.")
        observer.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Employee File System Watcher")
    parser.add_argument("--vault", default="C:/Users/samee/AI_Employee_Vault")
    parser.add_argument("--drop-folder", default=None)
    args = parser.parse_args()

    watcher = FilesystemWatcher(vault_path=args.vault, drop_folder=args.drop_folder)
    watcher.run()
