"""
Main crawl pipeline: fetch sources → extract links → parse → store → alert.
"""
import logging
import time
from datetime import datetime, timezone

from crawler.fetcher import fetch_page, extract_links, extract_text
from crawler.parser import parse_settlement, is_likely_settlement_link
from crawler.sources import SOURCES, DIRECT_SITES
from db.repository import upsert_settlement, log_crawl, mark_expired, mark_closing_soon

logger = logging.getLogger(__name__)

# Max links to follow per aggregator page (avoid hammering sites)
MAX_LINKS_PER_SOURCE = 10
# Seconds between individual page fetches
FETCH_DELAY = 2.0


def crawl_source(source: dict) -> list[dict]:
    """Crawl one source. Returns list of new settlement dicts."""
    url = source["url"]
    logger.info(f"Crawling source: {source['name']} ({url})")

    html = fetch_page(url)
    if not html:
        log_crawl(url, 0, error="fetch failed")
        return []

    new_settlements = []

    if source["type"] == "admin":
        # Single settlement site — parse it directly
        text = extract_text(html)
        data = parse_settlement(text, url)
        if data:
            is_new, row_id = upsert_settlement(data)
            if is_new:
                new_settlements.append(data)
        log_crawl(url, len(new_settlements))
        return new_settlements

    # Aggregator: extract child links and parse each
    link_selector = source.get("link_pattern", "a")
    links = extract_links(html, url, link_selector)
    logger.info(f"  Found {len(links)} candidate links")

    processed = 0
    for link in links[:MAX_LINKS_PER_SOURCE]:
        if not is_likely_settlement_link(link):
            continue
        time.sleep(FETCH_DELAY)
        child_html = fetch_page(link, use_playwright=False)  # faster for child pages
        if not child_html:
            child_html = fetch_page(link, use_playwright=True)
        if not child_html:
            continue

        text = extract_text(child_html)
        data = parse_settlement(text, link)
        if not data:
            continue

        is_new, row_id = upsert_settlement(data)
        processed += 1
        if is_new:
            logger.info(f"  NEW: {data.get('title')}")
            new_settlements.append(data)
        else:
            logger.debug(f"  EXISTING: {data.get('title')}")

    log_crawl(url, processed)
    return new_settlements


def run_pipeline(alert_callback=None) -> list[dict]:
    """Run full crawl pipeline. Calls alert_callback(settlement) for each new one."""
    logger.info(f"=== Settlement crawl started at {datetime.now(timezone.utc).isoformat()} ===")

    all_new = []
    all_sources = SOURCES + DIRECT_SITES

    for source in all_sources:
        try:
            new = crawl_source(source)
            all_new.extend(new)
        except Exception as e:
            logger.error(f"Error crawling {source['name']}: {e}")

    # Update statuses
    mark_expired()
    mark_closing_soon(days=7)

    # Fire alerts only for no-proof-required settlements
    alertable = [s for s in all_new if s.get("proof_required", "").lower() == "no"]
    skipped = len(all_new) - len(alertable)
    if skipped:
        logger.info(f"  Filtered out {skipped} settlement(s) requiring proof of purchase")

    if alert_callback and alertable:
        for settlement in alertable:
            try:
                alert_callback(settlement)
            except Exception as e:
                logger.error(f"Alert failed for '{settlement.get('title')}': {e}")

    logger.info(f"=== Crawl complete. {len(all_new)} new settlements found, {len(alertable)} alerted (no proof required). ===")
    return alertable
