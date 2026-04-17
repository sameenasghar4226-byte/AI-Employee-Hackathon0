"""
instagram_watcher.py - Instagram automation via Playwright.

Features:
  - Login and save session (first run opens browser for manual login)
  - Monitor notifications/DMs for urgent keywords
  - Post content (caption + optional image) with human approval
  - Generate activity summary to /Briefings

Usage:
    python instagram_watcher.py --setup        # First time: login and save session
    python instagram_watcher.py --check        # Check notifications/DMs
    python instagram_watcher.py --post         # Process pending post approvals
    python instagram_watcher.py --summary      # Generate activity summary

Session is saved to: scripts/instagram_session/
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: playwright not installed. Run: python -m pip install playwright && python -m playwright install chromium")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [InstagramWatcher] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("InstagramWatcher")

VAULT = Path(os.getenv("VAULT_PATH", "C:/Users/samee/AI_Employee_Vault"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
SESSION_DIR = VAULT / "scripts" / "instagram_session"
NEEDS_ACTION = VAULT / "Needs_Action"
BRIEFINGS = VAULT / "Briefings"
PENDING_APPROVAL = VAULT / "Pending_Approval"
APPROVED = VAULT / "Approved"
LOGS = VAULT / "Logs"

URGENT_KEYWORDS = ["urgent", "asap", "invoice", "payment", "help", "emergency", "call me"]
INSTAGRAM_URL = "https://www.instagram.com"


# ── Session management ───────────────────────────────────────────

def setup_session():
    """Open browser for manual Instagram login and save session."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 55)
    print("  Instagram Session Setup")
    print("=" * 55)
    print("\nA browser will open. Log in to your Instagram account.")
    print("After logging in, press ENTER here to save the session.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            str(SESSION_DIR),
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        page = browser.new_page()
        page.goto(INSTAGRAM_URL)
        input("Press ENTER after you've logged in to Instagram...")
        browser.close()

    print("\nSession saved! Future runs will use this session automatically.")


def get_browser(playwright, headless=True):
    """Launch browser with saved session."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return playwright.chromium.launch_persistent_context(
        str(SESSION_DIR),
        headless=headless,
        viewport={"width": 1280, "height": 800},
    )


def is_logged_in(page) -> bool:
    """Check if the current session is still valid."""
    try:
        page.goto(INSTAGRAM_URL, wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)
        # If we see the login form, session expired
        return page.query_selector('input[name="username"]') is None
    except Exception:
        return False


# ── Check notifications & DMs ────────────────────────────────────

def check_notifications():
    """Check Instagram notifications and DMs for urgent items."""
    if DRY_RUN:
        logger.info("[DRY RUN] Skipping real Instagram check")
        return []

    logger.info("Checking Instagram notifications...")
    found_items = []

    with sync_playwright() as p:
        browser = get_browser(p)
        try:
            page = browser.new_page()

            if not is_logged_in(page):
                logger.error("Instagram session expired. Run with --setup to re-login.")
                _create_alert("Instagram session expired. Run: python instagram_watcher.py --setup")
                return []

            # Check DMs
            page.goto(f"{INSTAGRAM_URL}/direct/inbox/", wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)

            # Find unread conversations
            try:
                unread = page.query_selector_all('[aria-label*="Unread"]')
                for chat in unread[:5]:
                    text = chat.inner_text().lower()
                    if any(kw in text for kw in URGENT_KEYWORDS):
                        found_items.append({
                            "type": "dm",
                            "preview": chat.inner_text()[:200],
                            "urgent": True
                        })
                        logger.info(f"Urgent DM found: {chat.inner_text()[:50]}")
            except Exception as e:
                logger.warning(f"Could not read DMs: {e}")

            # Check notifications
            page.goto(f"{INSTAGRAM_URL}/accounts/activity/", wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)

            try:
                notifs = page.query_selector_all("article, [role='article']")
                for notif in notifs[:10]:
                    text = notif.inner_text()
                    if any(kw in text.lower() for kw in URGENT_KEYWORDS):
                        found_items.append({
                            "type": "notification",
                            "preview": text[:200],
                            "urgent": True
                        })
            except Exception as e:
                logger.warning(f"Could not read notifications: {e}")

        finally:
            browser.close()

    # Create action files for urgent items
    for item in found_items:
        _create_action_file(item)

    logger.info(f"Instagram check complete. {len(found_items)} urgent items found.")
    _log_event("instagram_check", {"urgent_items": len(found_items)})
    return found_items


# ── Post content ─────────────────────────────────────────────────

def post_content(caption: str, image_path: str = None):
    """Post to Instagram (caption only or with image). Requires approval first."""
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would post to Instagram: {caption[:80]}...")
        return False

    logger.info(f"Posting to Instagram: {caption[:60]}...")

    with sync_playwright() as p:
        browser = get_browser(p, headless=False)  # Instagram posting needs visible browser
        try:
            page = browser.new_page()

            if not is_logged_in(page):
                logger.error("Instagram session expired.")
                return False

            page.goto(INSTAGRAM_URL, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)

            # Click the + (create post) button
            try:
                create_btn = page.query_selector('[aria-label="New post"]') or \
                             page.query_selector('svg[aria-label="New post"]')
                if create_btn:
                    create_btn.click()
                    time.sleep(2)
                else:
                    logger.error("Could not find 'New post' button.")
                    return False
            except Exception as e:
                logger.error(f"Could not click create button: {e}")
                return False

            # If image provided, upload it
            if image_path and Path(image_path).exists():
                try:
                    file_input = page.query_selector('input[type="file"]')
                    if file_input:
                        file_input.set_input_files(image_path)
                        time.sleep(3)
                        # Click Next through the steps
                        for _ in range(2):
                            next_btn = page.query_selector('[aria-label="Next"]') or \
                                       page.get_by_role("button", name="Next")
                            if next_btn:
                                next_btn.click()
                                time.sleep(2)
                except Exception as e:
                    logger.warning(f"Could not upload image: {e}")

            # Add caption
            try:
                caption_field = page.query_selector('[aria-label="Write a caption..."]') or \
                                page.query_selector('textarea[aria-label*="caption"]')
                if caption_field:
                    caption_field.click()
                    caption_field.fill(caption)
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Could not fill caption: {e}")
                return False

            # Click Share
            try:
                share_btn = page.get_by_role("button", name="Share") or \
                            page.query_selector('[aria-label="Share"]')
                if share_btn:
                    share_btn.click()
                    time.sleep(5)
                    logger.info("Post shared successfully!")
                    _log_event("instagram_post", {"caption": caption[:100], "result": "success"})
                    return True
            except Exception as e:
                logger.error(f"Could not click Share: {e}")
                return False

        finally:
            browser.close()

    return False


# ── Generate summary ─────────────────────────────────────────────

def generate_summary():
    """Generate an Instagram activity summary and save to /Briefings."""
    logger.info("Generating Instagram activity summary...")

    today = datetime.now().date().isoformat()
    summary_file = BRIEFINGS / f"{today}_Instagram_Summary.md"

    if DRY_RUN:
        content = f"""---
type: instagram_summary
date: {today}
mode: dry_run
---

# Instagram Activity Summary — {today}

> DRY_RUN mode — no real data collected.

## Status
- Instagram watcher is configured and ready
- Session setup required before live monitoring

## To Enable Live Monitoring
1. Run: `python scripts/instagram_watcher.py --setup`
2. Log in to your Instagram account in the browser
3. Set DRY_RUN=false in .env

*Generated by AI Employee Instagram Watcher*
"""
    else:
        # Check for action files created today
        today_actions = [
            f for f in NEEDS_ACTION.glob("INSTAGRAM_*.md")
            if today in f.read_text()
        ]

        content = f"""---
type: instagram_summary
date: {today}
generated: {datetime.now().isoformat()}
---

# Instagram Activity Summary — {today}

## Overview
- Items detected today: {len(today_actions)}
- Monitoring: Active

## Urgent Items
{chr(10).join(f'- {f.name}' for f in today_actions) if today_actions else '- None'}

## Posts Queued
Check /Pending_Approval for any Instagram posts awaiting your approval.

## Recommendations
- Review any flagged DMs or mentions
- Schedule posts for peak engagement (6-9pm local time)

*Generated by AI Employee Instagram Watcher*
"""

    BRIEFINGS.mkdir(exist_ok=True)
    summary_file.write_text(content, encoding="utf-8")
    logger.info(f"Summary saved: {summary_file.name}")
    return summary_file


# ── Create approval request for a post ──────────────────────────

def queue_post_for_approval(caption: str, image_path: str = None, reason: str = "Scheduled post"):
    """Create an approval file for a planned Instagram post."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    approval_file = PENDING_APPROVAL / f"INSTAGRAM_POST_{ts}.md"
    PENDING_APPROVAL.mkdir(exist_ok=True)

    content = f"""---
type: approval_request
action: instagram_post
created: {datetime.now().isoformat()}
expires: {datetime.now().date().isoformat()}T23:59:00
status: pending
---

## Instagram Post Request

**Reason:** {reason}

### Caption
{caption}

### Image
{image_path if image_path else "No image — text post only"}

## To Approve
Move this file to /Approved

## To Reject
Move this file to /Rejected
"""
    approval_file.write_text(content, encoding="utf-8")
    logger.info(f"Post queued for approval: {approval_file.name}")
    return approval_file


# ── Process approved posts ───────────────────────────────────────

def process_approved_posts():
    """Execute any approved Instagram posts from /Approved folder."""
    approved_posts = list(APPROVED.glob("INSTAGRAM_POST_*.md"))
    if not approved_posts:
        return

    for f in approved_posts:
        content = f.read_text(encoding="utf-8")
        logger.info(f"Processing approved Instagram post: {f.name}")

        # Extract caption from the approval file
        lines = content.split("\n")
        caption_start = False
        caption_lines = []
        for line in lines:
            if line.strip() == "### Caption":
                caption_start = True
                continue
            if caption_start and line.startswith("###"):
                break
            if caption_start:
                caption_lines.append(line)

        caption = "\n".join(caption_lines).strip()
        if caption:
            success = post_content(caption)
            if success:
                # Move to Done
                done_file = VAULT / "Done" / f.name
                f.rename(done_file)
                logger.info(f"Post completed, moved to /Done: {f.name}")


# ── Helpers ──────────────────────────────────────────────────────

def _create_action_file(item: dict):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    action_file = NEEDS_ACTION / f"INSTAGRAM_{item['type'].upper()}_{ts}.md"
    NEEDS_ACTION.mkdir(exist_ok=True)

    content = f"""---
type: instagram_{item['type']}
received: {datetime.now().isoformat()}
urgent: {item.get('urgent', False)}
status: pending
---

## Instagram {item['type'].upper()} Alert

**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

### Preview
{item.get('preview', 'No preview available')}

## Suggested Actions
- [ ] Review full message on Instagram
- [ ] Draft reply if needed
- [ ] Archive after processing
"""
    action_file.write_text(content, encoding="utf-8")
    logger.info(f"Action file created: {action_file.name}")


def _create_alert(message: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    alert = NEEDS_ACTION / f"SYSTEM_{ts}_instagram_alert.md"
    NEEDS_ACTION.mkdir(exist_ok=True)
    alert.write_text(f"""---
type: system_alert
created: {datetime.now().isoformat()}
---

## Instagram Alert

{message}
""", encoding="utf-8")


def _log_event(action_type: str, details: dict):
    log_file = LOGS / f"{datetime.now().date().isoformat()}.json"
    LOGS.mkdir(exist_ok=True)
    try:
        entries = json.loads(log_file.read_text()) if log_file.exists() else []
        entries.append({
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": "InstagramWatcher",
            **details
        })
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Could not write log: {e}")


# ── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Employee Instagram Watcher")
    parser.add_argument("--setup", action="store_true", help="First-time login setup")
    parser.add_argument("--check", action="store_true", help="Check notifications and DMs")
    parser.add_argument("--post", action="store_true", help="Process approved posts")
    parser.add_argument("--summary", action="store_true", help="Generate activity summary")
    parser.add_argument("--queue-post", metavar="CAPTION", help="Queue a post for approval")
    parser.add_argument("--image", metavar="PATH", help="Image path for --queue-post")
    args = parser.parse_args()

    print("=" * 55)
    print("  AI Employee — Instagram Watcher")
    print("=" * 55)

    if DRY_RUN:
        print(f"\n[DRY_RUN=true] Safe mode — no real Instagram actions.\n")

    if args.setup:
        setup_session()
    elif args.check:
        items = check_notifications()
        print(f"\nFound {len(items)} urgent items.")
    elif args.post:
        process_approved_posts()
    elif args.summary:
        f = generate_summary()
        print(f"\nSummary saved: {f}")
    elif args.queue_post:
        f = queue_post_for_approval(args.queue_post, args.image)
        print(f"\nPost queued for approval: {f}")
    else:
        parser.print_help()
