# AI Employee — Architecture & Lessons Learned

> Panaversity Hackathon 0 | Gold Tier | Built by Sameen Asghar

---

## Overview

A Personal AI Employee (Digital FTE) that proactively manages personal and business affairs 24/7. Built on a local-first, human-in-the-loop architecture using Claude Code as the reasoning engine and Obsidian as the management dashboard.

---

## System Architecture

```
EXTERNAL SOURCES
│
├── Gmail API ──────────────────┐
├── Instagram (Playwright) ─────┤
└── File System (Drop/) ────────┤
                                ▼
                    ┌─────────────────────┐
                    │   PERCEPTION LAYER  │
                    │  (Python Watchers)  │
                    │  gmail_watcher.py   │
                    │  instagram_watcher  │
                    │  filesystem_watcher │
                    └──────────┬──────────┘
                               │ writes .md files
                               ▼
                    ┌─────────────────────┐
                    │   OBSIDIAN VAULT    │
                    │  /Needs_Action/     │ ← inbox
                    │  /Plans/            │ ← AI plans
                    │  /Pending_Approval/ │ ← awaiting you
                    │  /Approved/         │ ← ready to act
                    │  /Done/             │ ← completed
                    │  /Logs/             │ ← audit trail
                    │  /Briefings/        │ ← CEO reports
                    │  Dashboard.md       │ ← live status
                    └──────────┬──────────┘
                               │ triggers
                               ▼
                    ┌─────────────────────┐
                    │   REASONING LAYER   │
                    │    Claude Code      │
                    │  + Ralph Wiggum     │ ← keeps working
                    │    Stop Hook        │   until done
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
  ┌─────────────────────┐           ┌─────────────────────┐
  │  HUMAN-IN-THE-LOOP  │           │   ORCHESTRATION     │
  │  Review approvals   │           │  orchestrator.py    │
  │  Move to /Approved  │           │  watchdog_process   │
  └─────────────────────┘           └─────────────────────┘
```

---

## Components

### 1. Watchers (Perception Layer)

| Script | Purpose | Trigger |
|--------|---------|---------|
| `gmail_watcher.py` | Monitors Gmail for unread emails | Every 2 minutes |
| `instagram_watcher.py` | Monitors Instagram DMs + notifications | On demand / scheduled |
| `filesystem_watcher.py` | Monitors Drop/ folder for new files | Instant (watchdog) |

All watchers write `.md` files to `/Needs_Action/` — this is the AI's inbox.

### 2. Orchestrator (Coordination Layer)

`orchestrator.py` is the master loop that:
- Updates `Dashboard.md` every 60 seconds
- Triggers Claude Code to process `/Needs_Action/`
- Processes approved actions from `/Approved/`
- Generates daily CEO briefing at 8am
- Generates weekly business audit every Monday at 8am

### 3. Ralph Wiggum Loop (Persistence Layer)

`ralph_wiggum.py` is a Claude Code **Stop Hook** that:
- Intercepts Claude's exit signal
- Checks if `/Needs_Action/` is empty
- If items remain → blocks exit, re-injects prompt (Claude keeps working)
- If empty → allows exit (task complete)
- Safety cap: max 10 iterations to prevent infinite loops

### 4. Error Recovery (Resilience Layer)

`retry_handler.py` provides:
- `@with_retry` decorator — exponential backoff for API failures
- `ErrorQueue` — offline queue for failed operations
- `GracefulDegradation` — one failure doesn't crash everything
- Human alert notifications for permanent failures

### 5. Agent Skills (`.claude/skills/`)

Reusable Claude Code slash commands:

| Skill | Command | Purpose |
|-------|---------|---------|
| Process Inbox | `/process-inbox` | Process all Needs_Action items |
| Daily Briefing | `/daily-briefing` | Generate CEO briefing |
| Weekly Audit | `/weekly-audit` | Full business audit |
| Draft Reply | `/draft-reply` | Draft email reply for approval |
| Instagram Post | `/instagram-post` | Queue Instagram post for approval |
| Subscription Audit | `/subscription-audit` | Flag unused subscriptions |

### 6. Human-in-the-Loop (Safety Layer)

For any sensitive action, Claude writes an approval file to `/Pending_Approval/` instead of acting directly. You approve by moving the file to `/Approved/`. The orchestrator detects this and executes the action.

**Actions that always require approval:**
- Sending emails to new contacts
- Instagram posts
- Any payment or financial action
- Deletions

---

## Tier Summary

### Bronze ✅
- Obsidian vault with Dashboard.md and Company_Handbook.md
- Filesystem watcher (Drop/ folder monitoring)
- Claude Code reading/writing to vault
- Full folder structure

### Silver ✅
- Gmail watcher (OAuth, live email monitoring)
- Auto-generated daily CEO briefings
- Human-in-the-loop approval workflow
- Watchdog process manager (auto-restarts crashed processes)
- Audit logging to /Logs/YYYY-MM-DD.json

### Gold ✅ (partial)
- Instagram watcher via Playwright (session-based, no Facebook required)
- Ralph Wiggum Stop Hook (autonomous multi-step task completion)
- Error recovery with retry logic and graceful degradation
- Weekly business + accounting audit
- 6 Agent Skills implemented
- Comprehensive audit logging

---

## Security Architecture

- **Credentials**: Never stored in vault. `.env` file is gitignored.
- **Token storage**: `token.json` and `instagram_session/` are gitignored.
- **DRY_RUN mode**: All watchers default to `DRY_RUN=true` — safe until you're ready.
- **HITL safeguards**: No sensitive action executes without human approval file.
- **Audit trail**: Every action logged to `/Logs/YYYY-MM-DD.json`.

---

## Setup Instructions

```bash
# 1. Install dependencies
python -m pip install watchdog python-dotenv google-auth google-auth-oauthlib \
  google-auth-httplib2 google-api-python-client playwright
python -m playwright install chromium

# 2. Configure environment
cp .env.example .env
# Edit .env: set DRY_RUN=false when ready

# 3. Gmail OAuth (one-time)
python scripts/gmail_watcher.py --credentials credentials.json

# 4. Instagram session (one-time)
python scripts/instagram_watcher.py --setup

# 5. Start AI Employee
python scripts/watchdog_process.py
```

---

## Lessons Learned

1. **Local-first beats cloud-first for privacy** — keeping everything in Obsidian means no data leaves your machine except through explicit API calls.

2. **File-based communication is surprisingly robust** — using `.md` files as the message bus between watchers, Claude, and humans is simple, auditable, and works without any database.

3. **Human-in-the-loop is not optional** — autonomous systems need a safety valve. The `/Pending_Approval/` pattern proved elegant: Claude writes intent, human confirms, system executes.

4. **The Ralph Wiggum pattern solves "lazy agent" problem** — without the Stop hook, Claude would process one file and stop. The hook forces it to keep going until the inbox is truly empty.

5. **DRY_RUN mode should be default** — starting with `DRY_RUN=true` meant we could test safely without accidentally sending emails or posting to social media.

6. **Playwright is more fragile than APIs** — Instagram's UI changes can break selectors. Official APIs are more reliable where available (Gmail proved this).

---

*AI Employee v0.1 | Panaversity Hackathon 0 | Built with Claude Code*
