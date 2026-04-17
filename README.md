# Personal AI Employee
> Local-first, agent-driven, human-in-the-loop.

Built from the **Panaversity Hackathon 0** blueprint.

## Quick Start

### 1. Install dependencies
```bash
cd C:\Users\samee\AI_Employee_Vault\scripts
python -m pip install -r requirements.txt
```

### 2. Configure environment
```bash
copy .env.example .env
# Edit .env and fill in your values
# Keep DRY_RUN=true until you're ready for live actions
```

### 3. Start the AI Employee
```bash
# Option A: Double-click
scripts\start_ai_employee.bat

# Option B: Terminal
python scripts\watchdog_process.py
```

### 4. Test it — drop a file
Drop any file into `Drop/` and watch `Needs_Action/` for the generated task file.

---

## Architecture

```
External Sources (Gmail, WhatsApp, Bank, Files)
        ↓
  Perception Layer (Python Watchers)
        ↓
  Obsidian Vault (Local Markdown)
    /Needs_Action → /Plans → /Pending_Approval → /Approved → /Done
        ↓
  Reasoning Layer (Claude Code)
        ↓
  Action Layer (MCP Servers)
        ↓
  External Actions (Send Email, Post, Pay)
```

## Tier Declaration

**Submitting as: Gold Tier**

- [x] **Bronze** — Obsidian vault, Dashboard.md, Company_Handbook.md, filesystem watcher, Claude Code integration
- [x] **Silver** — Gmail OAuth watcher, daily CEO briefings, human-in-the-loop approval workflow, watchdog process manager, audit logging
- [x] **Gold** — Instagram watcher (Playwright), Ralph Wiggum Stop Hook, error recovery + retry logic, weekly business audit, 6 Agent Skills, architecture documentation
- [ ] **Platinum** — Cloud 24/7, multi-agent, A2A communication

## Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Claude's operating instructions (read by Claude Code automatically) |
| `Dashboard.md` | Real-time status dashboard |
| `Company_Handbook.md` | Rules of engagement — edit to change AI behavior |
| `Business_Goals.md` | Your goals and KPIs |
| `scripts/orchestrator.py` | Master process — triggers Claude, watches folders |
| `scripts/filesystem_watcher.py` | Monitors Drop/ folder |
| `scripts/gmail_watcher.py` | Monitors Gmail inbox |
| `scripts/instagram_watcher.py` | Monitors Instagram DMs + posts content |
| `scripts/ralph_wiggum.py` | Claude Code Stop Hook — keeps Claude working until done |
| `scripts/retry_handler.py` | Error recovery, retry logic, graceful degradation |
| `scripts/watchdog_process.py` | Keeps all processes alive |
| `scripts/audit_logic.py` | Subscription/cost analysis |
| `ARCHITECTURE.md` | Full system architecture and lessons learned |

## Security Rules
- **Never** put credentials in vault .md files
- All secrets go in `.env` (already in `.gitignore`)
- Keep `DRY_RUN=true` during development
- All financial actions **always** require human approval

## Hackathon Submission
- Submit at: https://forms.gle/JR9T1SJq5rmQyGkGA
- Include demo video (5-10 min)
- Declare tier: Bronze / Silver / Gold / Platinum
