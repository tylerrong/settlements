"""
Fetches pages using Playwright (JS-rendered) with a requests fallback.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_with_requests(url: str, timeout: int = 15) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning(f"requests fetch failed for {url}: {e}")
        return None


async def _fetch_playwright(url: str, timeout_ms: int = 30000) -> Optional[str]:
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=HEADERS["User-Agent"],
                locale="en-US",
            )
            page = await ctx.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_timeout(2000)
            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        logger.warning(f"Playwright fetch failed for {url}: {e}")
        return None


def fetch_page(url: str, use_playwright: bool = True) -> Optional[str]:
    """Fetch a page, trying Playwright first then falling back to requests."""
    if use_playwright:
        html = asyncio.run(_fetch_playwright(url))
        if html:
            return html
    return fetch_with_requests(url)


def extract_links(html: str, base_url: str, css_selector: str) -> list[str]:
    """Extract hrefs matching css_selector from html, resolved against base_url."""
    from urllib.parse import urljoin, urlparse
    soup = BeautifulSoup(html, "lxml")
    links = []
    seen = set()
    for tag in soup.select(css_selector):
        href = tag.get("href", "").strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.scheme not in ("http", "https"):
            continue
        if full not in seen:
            seen.add(full)
            links.append(full)
    return links


def extract_text(html: str) -> str:
    """Strip HTML tags, collapse whitespace."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)
