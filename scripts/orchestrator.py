"""
orchestrator.py - Master process for the AI Employee.

Responsibilities:
  - Watches /Needs_Action for new files, triggers Claude Code to process them
  - Watches /Approved for approved actions and executes them
  - Scheduled tasks (daily briefing, weekly audit)
  - Updates Dashboard.md with current stats

Usage:
    python orchestrator.py [--vault PATH] [--dry-run]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, date
from pathlib import Path

VAULT = Path(os.getenv("VAULT_PATH", "C:/Users/samee/AI_Employee_Vault"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Orchestrator] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Orchestrator")


# ── Folder helpers ──────────────────────────────────────────────────────────

def count_files(folder: Path) -> int:
    return len(list(folder.glob("*.md"))) if folder.exists() else 0


def update_dashboard():
    """Refresh Dashboard.md with current vault stats."""
    dashboard = VAULT / "Dashboard.md"
    needs_action = count_files(VAULT / "Needs_Action")
    plans = count_files(VAULT / "Plans")
    done = count_files(VAULT / "Done")
    pending = count_files(VAULT / "Pending_Approval")

    content = f"""# AI Employee Dashboard
> Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Status
- **Agent**: Online
- **Mode**: Active Monitoring
- **Vault**: `{VAULT}`

## Quick Stats
| Metric | Value |
|--------|-------|
| Needs Action | {needs_action} items |
| Plans Active | {plans} |
| Done This Week | {done} |
| Pending Approval | {pending} |

## Recent Activity
"""
    # Append last 5 log entries
    log_file = VAULT / "Logs" / f"{date.today().isoformat()}.json"
    if log_file.exists():
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))[-5:]
            for e in reversed(entries):
                ts = e.get("timestamp", "")[:16]
                atype = e.get("action_type", "")
                actor = e.get("actor", "")
                content += f"- [{ts}] `{actor}` → {atype}\n"
        except Exception:
            content += "_Error reading logs._\n"
    else:
        content += "_No activity today._\n"

    content += "\n---\n*AI Employee v0.1 | Local-First, Human-in-the-Loop*\n"
    dashboard.write_text(content, encoding="utf-8")
    logger.info("Dashboard updated")


# ── Claude Code trigger ─────────────────────────────────────────────────────

def trigger_claude(prompt: str):
    """Invoke Claude Code non-interactively to process a prompt."""
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would trigger Claude with: {prompt[:80]}...")
        return

    cmd = [
        r"C:\Users\samee\AppData\Roaming\npm\claude.cmd",
        "--print",          # non-interactive output mode
        "--dangerously-skip-permissions",  # allow file writes
        "-p", prompt,
    ]
    logger.info(f"Triggering Claude: {prompt[:80]}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(VAULT))
        if result.returncode == 0:
            logger.info("Claude completed successfully")
        else:
            logger.error(f"Claude error: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        logger.error("Claude timed out after 5 minutes")
    except FileNotFoundError:
        logger.error("'claude' command not found. Ensure Claude Code is installed and in PATH.")


def process_needs_action():
    """If there are files in /Needs_Action, trigger Claude to process them."""
    folder = VAULT / "Needs_Action"
    files = list(folder.glob("*.md"))
    if not files:
        return

    file_list = "\n".join(f"- {f.name}" for f in files[:10])
    prompt = f"""You are an AI Employee assistant. The following files are in /Needs_Action and need to be processed:

{file_list}

Please:
1. Read each file in the /Needs_Action folder
2. Understand what action is needed
3. Create a Plan.md in /Plans with checkboxes for next steps
4. For any sensitive action (payments, emails to unknown contacts), create an approval file in /Pending_Approval
5. Update Dashboard.md with your assessment
6. Follow the rules in Company_Handbook.md at all times

Vault path: {VAULT}
"""
    trigger_claude(prompt)


def process_approved():
    """Handle files moved to /Approved — execute the approved action."""
    folder = VAULT / "Approved"
    files = list(folder.glob("*.md"))
    if not files:
        return

    for f in files:
        logger.info(f"Processing approved action: {f.name}")
        content = f.read_text(encoding="utf-8")
        prompt = f"""An action has been approved by the human. Execute it now.

File: {f.name}
Content:
{content}

After executing:
1. Log the result to /Logs/{date.today().isoformat()}.json
2. Move the file to /Done
3. Update Dashboard.md

Vault path: {VAULT}
"""
        trigger_claude(prompt)


def generate_daily_briefing():
    """Generate a CEO briefing (runs once per day at ~8am)."""
    briefing_file = VAULT / "Briefings" / f"{date.today().isoformat()}_Briefing.md"
    if briefing_file.exists():
        return  # Already generated today

    prompt = f"""Generate a daily CEO briefing for today ({date.today().isoformat()}).

Read the following files:
- Business_Goals.md — current goals and targets
- Accounting/Current_Month.md — if it exists, financial summary
- Plans/ — active plans
- Done/ — completed tasks

Write the briefing to: Briefings/{date.today().isoformat()}_Briefing.md

Include:
## Executive Summary
## Revenue / Financial Status
## Completed Tasks
## Active Plans
## Bottlenecks
## Proactive Suggestions
## Upcoming Deadlines

Vault path: {VAULT}
"""
    trigger_claude(prompt)


# ── Main loop ───────────────────────────────────────────────────────────────

def generate_weekly_audit():
    """Generate a weekly business + accounting audit every Monday at 8am."""
    audit_file = VAULT / "Briefings" / f"{date.today().isoformat()}_Weekly_Audit.md"
    if audit_file.exists():
        return

    prompt = f"""Generate a weekly business and accounting audit for the week ending {date.today().isoformat()}.

Read the following:
- Business_Goals.md — goals and revenue targets
- Logs/ — all log files from the past 7 days
- Done/ — all completed tasks this week
- Accounting/ — any financial records
- Briefings/ — daily briefings from this week

Write the audit to: Briefings/{date.today().isoformat()}_Weekly_Audit.md

Include:
## Weekly Executive Summary
## Revenue This Week (vs Target)
## Tasks Completed This Week
## Tasks Still Pending
## Bottlenecks Identified
## Subscription & Cost Audit
## Error & System Health Report
## Recommendations for Next Week

Vault path: {VAULT}
"""
    trigger_claude(prompt)


def main(interval: int = 60):
    logger.info(f"Orchestrator starting | Vault: {VAULT} | DRY_RUN: {DRY_RUN}")
    last_briefing_check = None
    last_weekly_audit_check = None

    while True:
        try:
            # Always update dashboard
            update_dashboard()

            # Process new action items
            process_needs_action()

            # Process approved actions
            process_approved()

            now = datetime.now()

            # Daily briefing at 8am (once per day)
            if now.hour >= 8 and last_briefing_check != date.today():
                generate_daily_briefing()
                last_briefing_check = date.today()

            # Weekly audit every Monday at 8am
            if now.weekday() == 0 and now.hour >= 8 and last_weekly_audit_check != date.today():
                generate_weekly_audit()
                last_weekly_audit_check = date.today()

        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)

        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Employee Orchestrator")
    parser.add_argument("--vault", default="C:/Users/samee/AI_Employee_Vault")
    parser.add_argument("--interval", type=int, default=60, help="Loop interval in seconds")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    VAULT = Path(args.vault)
    if args.dry_run:
        os.environ["DRY_RUN"] = "true"

    main(interval=args.interval)
