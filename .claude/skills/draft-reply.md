# Draft Reply

Draft a reply to an email or message and queue it for approval.

## Usage
Provide the file path of the email action file to reply to.

## Steps
1. Read the specified email file from `/Needs_Action/` or `/Done/`
2. Understand the context, sender, and what they need
3. Draft a professional, concise reply
4. Create an approval file in `/Pending_Approval/` with:
   - The drafted reply text
   - Recipient email address
   - Subject line
   - Action: send_email
5. Log the draft to today's log file
6. Never send directly — always go through `/Pending_Approval/`

Follow tone guidelines in `Company_Handbook.md`.
Output: `<task_complete>TASK_DONE</task_complete>` when approval file is created.
