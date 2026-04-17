"""
audit_logic.py - Subscription and transaction analysis for the weekly CEO Briefing.

Used by the orchestrator / Claude Code to identify cost anomalies.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

SUBSCRIPTION_PATTERNS = {
    "netflix.com": "Netflix",
    "spotify.com": "Spotify",
    "adobe.com": "Adobe Creative Cloud",
    "notion.so": "Notion",
    "slack.com": "Slack",
    "github.com": "GitHub",
    "openai.com": "OpenAI",
    "anthropic.com": "Anthropic",
    "figma.com": "Figma",
    "zoom.us": "Zoom",
    "dropbox.com": "Dropbox",
    "aws.amazon.com": "AWS",
    "cloud.google.com": "Google Cloud",
    "azure.microsoft.com": "Azure",
    "digitalocean.com": "DigitalOcean",
    "heroku.com": "Heroku",
    "vercel.com": "Vercel",
    "netlify.com": "Netlify",
}


def analyze_transaction(transaction: dict) -> Optional[dict]:
    """
    Identify if a transaction is a known subscription.

    Args:
        transaction: dict with keys: description, amount, date

    Returns:
        dict with type, name, amount, date or None
    """
    desc = transaction.get("description", "").lower()
    for pattern, name in SUBSCRIPTION_PATTERNS.items():
        if pattern.replace(".", "") in desc.replace(".", "") or pattern in desc:
            return {
                "type": "subscription",
                "name": name,
                "amount": transaction.get("amount", 0),
                "date": transaction.get("date", ""),
            }
    return None


def generate_subscription_report(transactions: list[dict]) -> str:
    """Generate a markdown report of all subscription charges found."""
    found = []
    for t in transactions:
        result = analyze_transaction(t)
        if result:
            found.append(result)

    if not found:
        return "No known subscriptions found in transactions.\n"

    total = sum(s["amount"] for s in found)
    lines = [
        "### Subscription Summary\n",
        f"| Service | Amount | Date |",
        f"|---------|--------|------|",
    ]
    for s in found:
        lines.append(f"| {s['name']} | ${s['amount']:.2f} | {s['date']} |")
    lines.append(f"\n**Total Monthly Subscriptions:** ${total:.2f}")
    return "\n".join(lines)


def load_transactions_from_csv(csv_path: str) -> list[dict]:
    """Load bank transactions from a CSV file. Expected columns: date, description, amount."""
    import csv
    transactions = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                transactions.append({
                    "date": row.get("date", row.get("Date", "")),
                    "description": row.get("description", row.get("Description", "")),
                    "amount": abs(float(row.get("amount", row.get("Amount", 0)) or 0)),
                })
    except FileNotFoundError:
        pass
    return transactions


if __name__ == "__main__":
    # Demo with sample data
    sample = [
        {"date": "2026-04-01", "description": "NETFLIX.COM", "amount": 15.99},
        {"date": "2026-04-02", "description": "Groceries ABC", "amount": 45.00},
        {"date": "2026-04-03", "description": "spotify premium", "amount": 9.99},
        {"date": "2026-04-04", "description": "GITHUB.COM", "amount": 4.00},
    ]
    print(generate_subscription_report(sample))
