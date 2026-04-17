# Subscription Audit

Audit all active subscriptions and flag unused or expensive ones.

## Steps
1. Read `/Accounting/` for any transaction records
2. Read today's log and recent briefings in `/Briefings/`
3. Look for known subscription patterns (Netflix, Spotify, Adobe, Notion, Slack, etc.)
4. For each subscription found, check:
   - Cost per month
   - Last used (if detectable)
   - Whether it duplicates another tool
5. Generate a report in `/Briefings/YYYY-MM-DD_Subscription_Audit.md`
6. For any subscription that should be cancelled, create an approval file in `/Pending_Approval/`

## Flag for review if:
- No activity detected in 30 days
- Cost increased more than 20%
- Duplicate functionality with another tool
- Cost exceeds budget threshold in `Business_Goals.md`

Output: `<task_complete>TASK_DONE</task_complete>` when report is saved.
