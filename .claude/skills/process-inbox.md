# Process Inbox

Process all files in /Needs_Action and handle each one appropriately.

## Steps
1. Read every file in `C:/Users/samee/AI_Employee_Vault/Needs_Action/`
2. For each file, determine the type (email, file_drop, instagram, system_alert)
3. Create a Plan.md in `/Plans/` with checkboxes for next steps
4. For sensitive actions (payments, emails to unknown contacts, posts), create an approval file in `/Pending_Approval/`
5. Move processed files to `/Done/`
6. Update `Dashboard.md` with current stats
7. Append each action to today's log in `/Logs/YYYY-MM-DD.json`
8. Follow all rules in `Company_Handbook.md`

When ALL items are processed output: `<task_complete>TASK_DONE</task_complete>`
