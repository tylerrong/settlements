"""
Settlement source registry.

Each source has:
  - url:         page to crawl
  - type:        "aggregator" (lists many settlements) or "admin" (single settlement site)
  - name:        human-readable label
  - link_pattern: optional CSS selector to find individual settlement links on aggregator pages
  - notes:       optional
"""

SOURCES = [
    # ── Aggregators ───────────────────────────────────────────────────────────
    {
        "name": "Top Class Actions",
        "url": "https://topclassactions.com/lawsuit-settlements/open-lawsuit-settlements/",
        "type": "aggregator",
        "link_pattern": "h3.entry-title a, article a.entry-title-link",
    },
    {
        "name": "Top Class Actions - Data Breach",
        "url": "https://topclassactions.com/lawsuit-settlements/open-lawsuit-settlements/?settlement_category=data-breach-privacy",
        "type": "aggregator",
        "link_pattern": "h3.entry-title a, article a.entry-title-link",
    },
    {
        "name": "OpenClassActions",
        "url": "https://openclassactions.com/",
        "type": "aggregator",
        "link_pattern": "a",
    },
    {
        "name": "ClassAction.org Settlements",
        "url": "https://www.classaction.org/settlements",
        "type": "aggregator",
        "link_pattern": "a[href*='/settlements/'], a[href*='/lawsuit/'], a[href*='/class-action/']",
    },
    {
        "name": "Claim Depot",
        "url": "https://www.claimdepot.com/",
        "type": "aggregator",
        "link_pattern": "a[href*='settlement'], a[href*='claim'], h2 a, h3 a, .entry-title a",
    },

    # ── Administrator index pages ─────────────────────────────────────────────
    {
        "name": "Epiq Active Cases",
        "url": "https://www.epiqglobal.com/en-us/cases",
        "type": "aggregator",
        "link_pattern": "a[href*='settlement'], a[href*='claims'], a[href*='case'], td a, li a",
    },
    {
        "name": "Kroll Settlement Administration",
        "url": "https://www.kroll.com/en/services/legal-business-services/claims-noticing-settlement-administration",
        "type": "aggregator",
        "link_pattern": "a[href*='settlement'], a[href*='claim'], td a, li a",
    },
    {
        "name": "JND Legal Administration",
        "url": "https://www.jndla.com/cases",
        "type": "aggregator",
        "link_pattern": "a",
    },
    {
        "name": "Angeion Group",
        "url": "https://www.angeiongroup.com/cases/",
        "type": "aggregator",
        "link_pattern": "a",
    },
    {
        "name": "Simpluris",
        "url": "https://simpluris.com/cases/",
        "type": "aggregator",
        "link_pattern": "a",
    },
]

# Individual settlement admin sites can be added here for direct monitoring
DIRECT_SITES: list[dict] = [
    # Example:
    # {"name": "Whitehead v. Amica", "url": "https://azuminsuranceclaims6.com", "type": "admin"},
]
