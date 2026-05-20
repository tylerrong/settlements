"""
Sends settlement alerts to webhook endpoints (Discord, Slack, generic).
Designed to be pluggable — just add URLs to ALL_WEBHOOK_URLS in config.
"""
from __future__ import annotations
import logging
from typing import Optional

import requests

from config import ALL_WEBHOOK_URLS

logger = logging.getLogger(__name__)

STATUS_EMOJI = {
    "new": "🆕",
    "open": "✅",
    "closing_soon": "⚠️",
    "expired": "❌",
    "payment_pending": "💰",
}

CATEGORY_EMOJI = {
    "data_breach": "🔓",
    "privacy": "🔒",
    "insurance": "🛡️",
    "product_liability": "⚠️",
    "wage_theft": "💼",
    "antitrust": "⚖️",
    "consumer": "🛍️",
    "financial": "💵",
    "employment": "👔",
    "other": "📋",
}


def _build_discord_embed(settlement: dict) -> dict:
    title = settlement.get("title", "Unknown Settlement")
    category = settlement.get("category", "other")
    status = settlement.get("status", "new")
    deadline = settlement.get("claim_deadline", "Unknown")
    payout = settlement.get("estimated_payout") or settlement.get("max_payout") or "Varies"
    eligibility = settlement.get("eligibility_summary", "")
    proof = settlement.get("proof_required", "unknown")
    url = settlement.get("official_website_url") or settlement.get("source_url", "")
    fund = settlement.get("settlement_fund")
    administrator = settlement.get("administrator", "")

    cat_emoji = CATEGORY_EMOJI.get(category, "📋")
    status_emoji = STATUS_EMOJI.get(status, "🆕")

    fields = [
        {"name": "Proof of Purchase", "value": proof.title() if proof else "Unknown", "inline": True},
        {"name": "Deadline", "value": deadline or "TBD", "inline": True},
        {"name": "Typical Settlement", "value": payout, "inline": True},
    ]
    if fund:
        fields.append({"name": "Settlement Fund", "value": fund, "inline": True})
    if administrator:
        fields.append({"name": "Administrator", "value": administrator, "inline": True})

    color = 0x5865F2  # Discord blurple for new
    if status == "closing_soon":
        color = 0xFFA500
    elif status == "expired":
        color = 0xFF0000

    return {
        "title": f"{cat_emoji} {title}",
        "description": eligibility[:300] if eligibility else "",
        "url": url,
        "color": color,
        "fields": fields,
        "footer": {"text": f"{status_emoji} {status.replace('_', ' ').title()} • Settlement Monitor"},
    }


def send_settlement_alert(
    settlement: dict,
    webhook_urls: Optional[list[str]] = None,
):
    """Send a settlement alert to all configured webhooks."""
    targets = webhook_urls or ALL_WEBHOOK_URLS
    if not targets:
        logger.warning("No webhook URLs configured — skipping alert")
        return

    embed = _build_discord_embed(settlement)

    # Discord-format payload (also works with most Discord-compatible webhooks)
    payload = {
        "username": "Settlement Monitor",
        "avatar_url": "https://i.imgur.com/wBmpHJc.png",
        "embeds": [embed],
    }

    for url in targets:
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info(f"Alert sent to webhook ({resp.status_code})")
        except Exception as e:
            logger.error(f"Webhook POST failed to {url[:50]}...: {e}")

    # Post to Twitter/X
    try:
        from alerts.twitter import post_settlement_tweet
        post_settlement_tweet(settlement)
    except Exception as e:
        logger.error(f"Twitter post failed: {e}")


def send_digest(settlements: list[dict], webhook_urls: Optional[list[str]] = None):
    """Send a digest of multiple settlements as a single message."""
    if not settlements:
        return
    targets = webhook_urls or ALL_WEBHOOK_URLS
    if not targets:
        return

    embeds = [_build_discord_embed(s) for s in settlements[:10]]  # Discord max 10 embeds

    payload = {
        "username": "Settlement Monitor",
        "content": f"**{len(settlements)} new settlement(s) found**",
        "embeds": embeds,
    }

    for url in targets:
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Digest webhook failed: {e}")
