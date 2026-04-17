"""
ralph_wiggum.py - Claude Code Stop Hook for autonomous task completion.

This script is registered as a Claude Code Stop hook.
When Claude tries to exit, this hook checks if there are still pending
items in /Needs_Action. If yes, it blocks the exit and re-injects the
prompt so Claude keeps working until the task is truly done.

Exit codes:
  0 = allow Claude to stop (all done)
  2 = block stop, feed stdout back to Claude as a new prompt (keep going)

Registration: .claude/settings.json in the vault root
"""
import sys
import json
from pathlib import Path
from datetime import datetime

VAULT = Path("C:/Users/samee/AI_Employee_Vault")
NEEDS_ACTION = VAULT / "Needs_Action"
LOGS = VAULT / "Logs"
MAX_ITERATIONS = 10

# Track iteration count via a state file to prevent infinite loops
STATE_FILE = VAULT / "scripts" / ".ralph_state.json"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"iterations": 0, "session_start": datetime.now().isoformat()}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state))


def reset_state():
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def main():
    pending = [f for f in NEEDS_ACTION.glob("*.md") if f.is_file()]

    if not pending:
        # All done — allow Claude to exit
        reset_state()
        print("RALPH WIGGUM: All items in /Needs_Action processed. Task complete.")
        sys.exit(0)

    # Check iteration count to prevent infinite loops
    state = load_state()
    state["iterations"] = state.get("iterations", 0) + 1

    if state["iterations"] >= MAX_ITERATIONS:
        reset_state()
        print(f"RALPH WIGGUM: Max iterations ({MAX_ITERATIONS}) reached. Stopping to prevent infinite loop.")
        # Log the incomplete state
        log_file = LOGS / f"{datetime.now().date().isoformat()}.json"
        try:
            entries = json.loads(log_file.read_text()) if log_file.exists() else []
            entries.append({
                "timestamp": datetime.now().isoformat(),
                "action_type": "ralph_wiggum_max_iterations",
                "actor": "ralph_wiggum_hook",
                "details": {"pending_items": len(pending)},
                "result": "stopped"
            })
            log_file.write_text(json.dumps(entries, indent=2))
        except Exception:
            pass
        sys.exit(0)

    save_state(state)

    # Still have pending items — block exit and re-inject prompt
    file_list = "\n".join(f"  - {f.name}" for f in pending[:10])
    more = f"\n  ... and {len(pending) - 10} more" if len(pending) > 10 else ""

    print(f"""RALPH WIGGUM LOOP — Iteration {state['iterations']}/{MAX_ITERATIONS}

There are still {len(pending)} unprocessed item(s) in /Needs_Action:
{file_list}{more}

Your task is NOT complete yet. Continue working:
1. Read each file in /Needs_Action
2. Process it (create a Plan, flag sensitive actions to /Pending_Approval)
3. Move processed files to /Done
4. Update Dashboard.md and Logs

When ALL items are moved to /Done, output exactly:
<task_complete>TASK_DONE</task_complete>

Vault path: {VAULT}
""")
    sys.exit(2)


if __name__ == "__main__":
    main()
