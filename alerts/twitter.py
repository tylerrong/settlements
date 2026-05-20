"""
Posts class action settlement alerts to Twitter/X via the Twitter API v2.
Requires OAuth 1.0a credentials in .env (API key/secret + access token/secret).
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

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


def _build_tweet(settlement: dict) -> str:
    title = settlement.get("title", "Class Action Settlement")
    category = settlement.get("category", "other")
    deadline = settlement.get("claim_deadline", "")
    payout = settlement.get("estimated_payout") or settlement.get("max_payout", "")
    proof = settlement.get("proof_required", "")
    url = settlement.get("official_website_url") or settlement.get("source_url", "")

    emoji = CATEGORY_EMOJI.get(category, "📋")

    lines = [f"⚖️ NEW SETTLEMENT: {title}"]
    if payout:
        lines.append(f"{emoji} Payout: {payout}")
    if proof:
        no_proof = proof.lower() in ("no", "not required", "none")
        lines.append(f"{'✅ No proof needed!' if no_proof else f'📄 Proof required: {proof}'}")
    if deadline:
        lines.append(f"⏰ Deadline: {deadline}")
    if url:
        lines.append(f"\n🔗 {url}")
    lines.append("\n#ClassAction #Settlement #FreeM oney #PriceErrors")

    tweet = "\n".join(lines)
    return tweet[:280]


def post_settlement_tweet(settlement: dict) -> bool:
    """Post a settlement alert to Twitter. Returns True on success."""
    try:
        import tweepy
        from config import (
            TWITTER_API_KEY,
            TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN,
            TWITTER_ACCESS_TOKEN_SECRET,
        )

        if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
            logger.warning("Twitter credentials not fully configured — skipping tweet")
            return False

        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        )

        tweet_text = _build_tweet(settlement)
        response = client.create_tweet(text=tweet_text)
        tweet_id = response.data["id"]
        logger.info(f"Tweet posted successfully (ID: {tweet_id}): {settlement.get('title')}")
        return True

    except ImportError:
        logger.error("tweepy not installed — run: pip install tweepy")
        return False
    except Exception as e:
        logger.error(f"Failed to post tweet: {e}")
        return False
