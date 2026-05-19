# Settlement Monitor

Crawls class action settlement aggregators and administrator sites daily, parses them with Claude, stores them in SQLite, sends Discord alerts for new settlements, and shows them in a filterable dashboard.

## Setup (one-time)

```bash
# 1. Install dependencies + Chromium
bash scripts/setup.sh

# 2. Add your API keys
cp .env.example .env
#    → set ANTHROPIC_API_KEY and DISCORD_WEBHOOK_URL

# 3. Install as a background service (auto-starts at login, restarts on crash)
bash scripts/install_service.sh
```

That's it. The monitor runs silently in the background and pushes new settlements to your webhook.

## Logs

```bash
tail -f logs/monitor.log   # live output
```

## Service management

```bash
# Stop
launchctl unload ~/Library/LaunchAgents/com.settlements.monitor.plist

# Start
launchctl load ~/Library/LaunchAgents/com.settlements.monitor.plist

# Uninstall completely
bash scripts/uninstall_service.sh
```

## Other commands

```bash
source venv/bin/activate

# One-off crawl (sends alerts)
python main.py crawl

# Crawl without alerts
python main.py crawl --no-alert

# Add a specific settlement site to monitor directly
python main.py add-site https://somesettlement.com

# Browse settlements in a local UI (optional)
python main.py serve   # → http://localhost:5050
```

## Architecture

```
Sources (aggregators + admin sites)
  └─ crawler/fetcher.py   — Playwright + requests
  └─ crawler/parser.py    — Claude extracts structured fields
  └─ crawler/pipeline.py  — orchestrates crawl loop
db/repository.py          — SQLite upsert + status management
alerts/webhook.py         — Discord embeds (pluggable to any webhook)
dashboard/app.py          — Flask UI with filters
main.py                   — CLI entry point + APScheduler
```

## Adding sources

Edit `crawler/sources.py` to add aggregator or admin pages, or use:
```bash
python main.py add-site https://example-settlement.com
```

## Dashboard filters

- Status: new / open / closing soon / expired / payment pending  
- Category: data breach, privacy, insurance, product liability, etc.  
- Proof required: yes / no  
- Deadline: next 7 / 14 / 30 days  
