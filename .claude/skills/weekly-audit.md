# Weekly Audit

Generate a full weekly business and accounting audit.

## Steps
1. Read `Business_Goals.md` for targets and metrics
2. Read all log files in `/Logs/` from the past 7 days
3. Read all files in `/Done/` completed this week
4. Read `/Accounting/` for any financial records
5. Read all daily briefings in `/Briefings/` from this week
6. Generate audit at `Briefings/YYYY-MM-DD_Weekly_Audit.md`

## Audit Structure
- ## Weekly Executive Summary
- ## Revenue This Week (vs Target)
- ## Tasks Completed
- ## Tasks Still Pending
- ## Bottlenecks Identified
- ## Subscription & Cost Audit (flag unused services)
- ## Error & System Health Report
- ## Recommendations for Next Week

Be proactive — suggest cancellations, optimizations, and priorities.
Output: `<task_complete>TASK_DONE</task_complete>` when saved.
