"""
gmail_watcher.py - Monitors Gmail for important unread emails and creates action files.

Prerequisites:
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

Setup:
    1. Go to https://console.cloud.google.com/
    2. Create a project, enable Gmail API
    3. Create OAuth2 credentials (Desktop app) -> download as credentials.json
    4. Place credentials.json in the vault root or specify via --credentials
    5. Run once interactively to authorize; token.json is saved for future runs

Usage:
    python gmail_watcher.py [--vault PATH] [--credentials PATH] [--interval SECONDS]
"""
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: Google API packages not installed.")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailWatcher(BaseWatcher):
    """Monitors Gmail inbox for important unread messages."""

    def __init__(self, vault_path: str, credentials_path: str, interval: int = 120):
        super().__init__(vault_path, check_interval=interval)
        self.credentials_path = Path(credentials_path)
        self.token_path = self.vault_path / "scripts" / "token.json"
        self.processed_ids: set = set()
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    self.logger.error(f"credentials.json not found at {self.credentials_path}")
                    sys.exit(1)
                flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(creds.to_json())
        return build("gmail", "v1", credentials=creds)

    def check_for_updates(self) -> list:
        if DRY_RUN:
            self.logger.info("[DRY RUN] Skipping real Gmail API call")
            return []
        results = self.service.users().messages().list(
            userId="me", q="is:unread", maxResults=10
        ).execute()
        messages = results.get("messages", [])
        return [m for m in messages if m["id"] not in self.processed_ids]

    def create_action_file(self, message: dict) -> Path:
        if DRY_RUN:
            return self.needs_action / "DRY_RUN.md"

        msg = self.service.users().messages().get(
            userId="me", id=message["id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        sender = headers.get("From", "Unknown")
        subject = headers.get("Subject", "No Subject")
        snippet = msg.get("snippet", "")

        safe_id = message["id"][:12]
        filepath = self.needs_action / f"EMAIL_{safe_id}.md"

        content = f"""---
type: email
message_id: {message['id']}
from: {sender}
subject: {subject}
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## Email: {subject}

**From:** {sender}
**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

### Preview
{snippet}

## Suggested Actions
- [ ] Review full email
- [ ] Draft reply
- [ ] Forward to relevant party
- [ ] Archive after processing
"""
        filepath.write_text(content, encoding="utf-8")
        self.processed_ids.add(message["id"])
        self.log_event("email_detected", {"from": sender, "subject": subject})
        return filepath


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Employee Gmail Watcher")
    parser.add_argument("--vault", default="C:/Users/samee/AI_Employee_Vault")
    parser.add_argument("--credentials", default="C:/Users/samee/AI_Employee_Vault/credentials.json")
    parser.add_argument("--interval", type=int, default=120, help="Check interval in seconds")
    args = parser.parse_args()

    # Pre-flight checks
    print("=" * 55)
    print("  AI Employee — Gmail Watcher")
    print("=" * 55)

    creds_path = Path(args.credentials)
    if not creds_path.exists():
        print(f"\n[ERROR] credentials.json not found at:\n  {creds_path}")
        print("\nSetup steps:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create project -> Enable Gmail API")
        print("  3. Credentials -> OAuth client ID (Desktop app)")
        print(f"  4. Download JSON -> save as:\n     {creds_path}")
        sys.exit(1)

    if DRY_RUN:
        print(f"\n[DRY_RUN=true] Safe mode — no real Gmail calls.")
        print("  Set DRY_RUN=false in .env to enable live monitoring.\n")
    else:
        print(f"\n[LIVE MODE] Monitoring Gmail every {args.interval}s")
        print(f"  Credentials: {args.credentials}")
        print(f"  Action files -> {args.vault}/Needs_Action/\n")

    watcher = GmailWatcher(
        vault_path=args.vault,
        credentials_path=args.credentials,
        interval=args.interval,
    )
    watcher.run()
