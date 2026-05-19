"""
Uses DeepSeek to extract structured settlement data from raw page text.
DeepSeek's API is OpenAI-compatible; we use the openai SDK with a custom base URL.
"""
from __future__ import annotations
import json
import logging
import re
from typing import Optional

from openai import OpenAI

from config import DEEPSEEK_API_KEY

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
        )
    return _client


SYSTEM_PROMPT = (
    "You are a legal data extraction assistant. "
    "You always respond with valid JSON only — no markdown, no explanation, no code fences."
)

EXTRACTION_PROMPT = """\
Extract structured data from this class action settlement webpage.

Respond with a single JSON object using these exact keys (use null for unknown fields):
- title: short descriptive title e.g. "Acme Corp - Data Breach Settlement"
- company: primary company/brand name
- defendant: full legal defendant name
- case_name: official case name
- case_number: court case number
- category: one of data_breach, privacy, insurance, product_liability, wage_theft, antitrust, consumer, financial, employment, other
- eligibility_summary: 2-3 sentence plain English summary of who qualifies
- state_scope: "nationwide" or specific states e.g. "California, Texas"
- proof_required: "yes", "no", or "unknown"
- claim_required: "yes" (must file) or "no" (automatic) or "unknown"
- claim_deadline: YYYY-MM-DD or null
- exclusion_deadline: YYYY-MM-DD or null
- objection_deadline: YYYY-MM-DD or null
- fairness_hearing_date: YYYY-MM-DD or null
- estimated_payout: e.g. "$20-$50 per person" or "varies" or null
- max_payout: e.g. "$5,000" or null
- settlement_fund: total fund size e.g. "$12.5 million" or null
- claim_form_url: direct URL to claim form or null
- official_website_url: primary settlement website URL
- documents_url: URL to settlement documents or null
- administrator: administrator name e.g. "Epiq", "Kroll", "JND" or null
- confidence_score: float 0.0-1.0 confidence this is a real open settlement
- is_settlement_page: true if this is a single settlement page, false if it is a listing/aggregator page or unrelated

Page URL: {url}

Page text:
{text}
"""


def parse_settlement(text: str, url: str, max_chars: int = 12000) -> Optional[dict]:
    """Call DeepSeek to extract settlement fields from page text."""
    truncated = text[:max_chars]
    prompt = EXTRACTION_PROMPT.format(url=url, text=truncated)

    try:
        client = _get_client()
        msg = client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=1500,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        raw = msg.choices[0].message.content.strip()

        # Fallback: strip markdown fences if present despite json_object mode
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if match:
            raw = match.group(1).strip()

        data = json.loads(raw)

        if not data.get("is_settlement_page", True):
            return None

        data.pop("is_settlement_page", None)
        data["source_url"] = url
        data["raw_text"] = text[:3000]

        if not data.get("title"):
            return None

        return data

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error for {url}: {e} | raw={raw[:200] if 'raw' in dir() else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"DeepSeek extraction failed for {url}: {e}")
        return None


def is_likely_settlement_link(url: str, anchor_text: str = "") -> bool:
    """Quick heuristic to skip obviously irrelevant links."""
    skip_patterns = [
        r"/about", r"/contact", r"/privacy", r"/terms", r"/blog(?!/.*settlement)",
        r"/category/", r"/tag/", r"/author/", r"/page/\d+",
        r"\.(jpg|jpeg|png|gif|pdf|zip|doc)$",
        r"facebook\.com", r"twitter\.com", r"linkedin\.com",
        r"youtube\.com", r"instagram\.com",
    ]
    url_lower = url.lower()
    for pat in skip_patterns:
        if re.search(pat, url_lower):
            return False

    keep_patterns = [
        r"settlement", r"claim", r"lawsuit", r"class.?action",
        r"refund", r"compensation",
    ]
    text_lower = anchor_text.lower()
    for pat in keep_patterns:
        if re.search(pat, url_lower) or re.search(pat, text_lower):
            return True

    return True  # Default: try it
