# Daily Briefing

Generate today's CEO briefing from vault data.

## Steps
1. Read `Business_Goals.md` for current targets
2. Read all files in `/Plans/` for active work
3. Read all files in `/Done/` completed today
4. Read today's log from `/Logs/YYYY-MM-DD.json`
5. Read `/Pending_Approval/` for items awaiting review
6. Generate a briefing file at `Briefings/YYYY-MM-DD_Briefing.md`

## Briefing Structure
- ## Executive Summary
- ## Your Action Items (urgent things needing attention today)
- ## Business Health (revenue vs target)
- ## Completed Today
- ## Active Plans
- ## Pending Approvals
- ## System Status
- ## Recommendations

Keep it concise. Flag anything urgent at the top.
Output: `<task_complete>TASK_DONE</task_complete>` when saved.
