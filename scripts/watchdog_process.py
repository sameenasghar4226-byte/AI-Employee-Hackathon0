"""
watchdog_process.py - Monitors and auto-restarts critical AI Employee processes.

Usage:
    python watchdog_process.py [--vault PATH]

Monitors: orchestrator.py, filesystem_watcher.py, gmail_watcher.py (if configured)
"""
import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Watchdog] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Watchdog")

VAULT = Path(os.getenv("VAULT_PATH", "C:/Users/samee/AI_Employee_Vault"))
SCRIPTS = VAULT / "scripts"

# Processes to manage: name -> command
MANAGED_PROCESSES = {
    "orchestrator": [sys.executable, str(SCRIPTS / "orchestrator.py")],
    "filesystem_watcher": [sys.executable, str(SCRIPTS / "filesystem_watcher.py")],
    # Gmail watcher (credentials configured)
    "gmail_watcher": [sys.executable, str(SCRIPTS / "gmail_watcher.py")],
}

running_processes: dict = {}


def start_process(name: str, cmd: list) -> subprocess.Popen:
    logger.info(f"Starting {name}: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        stdout=open(VAULT / "Logs" / f"{name}.log", "a"),
        stderr=subprocess.STDOUT,
    )
    return proc


def notify_human(message: str):
    """Write a notification to Needs_Action for human awareness."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    notif = VAULT / "Needs_Action" / f"SYSTEM_{ts}_notification.md"
    notif.write_text(f"""---
type: system_notification
created: {datetime.now().isoformat()}
---

## System Notification

{message}
""", encoding="utf-8")


def main():
    logger.info(f"Watchdog starting | Vault: {VAULT}")
    (VAULT / "Logs").mkdir(exist_ok=True)

    # Initial start
    for name, cmd in MANAGED_PROCESSES.items():
        running_processes[name] = start_process(name, cmd)
        time.sleep(1)

    while True:
        time.sleep(30)
        for name, cmd in MANAGED_PROCESSES.items():
            proc = running_processes.get(name)
            if proc is None or proc.poll() is not None:
                exit_code = proc.returncode if proc else "unknown"
                logger.warning(f"{name} exited (code={exit_code}), restarting...")
                notify_human(f"Process `{name}` crashed (exit={exit_code}) and was restarted by Watchdog.")
                running_processes[name] = start_process(name, cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Employee Watchdog")
    parser.add_argument("--vault", default="C:/Users/samee/AI_Employee_Vault")
    args = parser.parse_args()
    VAULT = Path(args.vault)
    main()
