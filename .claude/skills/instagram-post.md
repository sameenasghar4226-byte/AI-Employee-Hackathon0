# Instagram Post

Create and queue an Instagram post for approval.

## Usage
Describe what to post about (topic, tone, hashtags).

## Steps
1. Read `Business_Goals.md` to understand current business context
2. Draft an engaging Instagram caption (max 2200 chars)
3. Suggest relevant hashtags (5-10)
4. Create an approval file in `/Pending_Approval/INSTAGRAM_POST_TIMESTAMP.md` with:
   - The full caption
   - Hashtags
   - Suggested posting time (peak: 6-9pm)
   - Reason for posting
5. Log the queued post to today's log

Never post directly — always create an approval file first.
Output: `<task_complete>TASK_DONE</task_complete>` when approval file is created.
