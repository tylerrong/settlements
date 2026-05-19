"""
Settlement Monitor — entry point.

Usage:
  python main.py daemon         # Headless scheduler only (for production / LaunchAgent)
  python main.py serve          # Dashboard + scheduler (for local browsing)
  python main.py crawl          # Run one crawl immediately
  python main.py crawl --no-alert  # Crawl without sending alerts
  python main.py add-site URL   # Add a direct settlement site to monitor
"""
import argparse
import logging
import sys

from db.models import init_db
from config import FLASK_PORT, CRAWL_INTERVAL_HOURS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def cmd_crawl(send_alerts: bool = True):
    from crawler.pipeline import run_pipeline
    from alerts.webhook import send_settlement_alert
    callback = send_settlement_alert if send_alerts else None
    new = run_pipeline(alert_callback=callback)
    logger.info(f"Done. {len(new)} new settlement(s).")
    return new


def cmd_daemon():
    """Headless mode: run one crawl immediately, then on interval. No Flask."""
    import signal
    import time
    from apscheduler.schedulers.blocking import BlockingScheduler

    logger.info("Settlement Monitor daemon starting")
    logger.info(f"Crawl interval: every {CRAWL_INTERVAL_HOURS}h")

    # Run one crawl right now so we don't wait a full interval on first start
    cmd_crawl(send_alerts=True)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        cmd_crawl,
        "interval",
        hours=CRAWL_INTERVAL_HOURS,
        id="crawl_job",
        replace_existing=True,
    )

    def _shutdown(sig, frame):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown(wait=False)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info("Scheduler running — Ctrl-C or SIGTERM to stop")
    scheduler.start()


def cmd_serve():
    from apscheduler.schedulers.background import BackgroundScheduler
    from dashboard.app import run_dashboard

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cmd_crawl,
        "interval",
        hours=CRAWL_INTERVAL_HOURS,
        id="crawl_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — crawling every {CRAWL_INTERVAL_HOURS}h")
    logger.info(f"Dashboard at http://localhost:{FLASK_PORT}")

    try:
        run_dashboard(port=FLASK_PORT)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("Shutdown.")


def cmd_add_site(url: str):
    from crawler.sources import DIRECT_SITES
    # Persist to a local JSON file for simplicity
    import json, os
    path = "./custom_sites.json"
    sites = []
    if os.path.exists(path):
        with open(path) as f:
            sites = json.load(f)
    entry = {"name": url, "url": url, "type": "admin"}
    if entry not in sites:
        sites.append(entry)
        with open(path, "w") as f:
            json.dump(sites, f, indent=2)
        logger.info(f"Added: {url}")
    else:
        logger.info("Already in list.")


def main():
    init_db()

    # Load any custom sites added via CLI
    import json, os
    path = "./custom_sites.json"
    if os.path.exists(path):
        with open(path) as f:
            custom = json.load(f)
        from crawler import sources
        for s in custom:
            if s not in sources.DIRECT_SITES:
                sources.DIRECT_SITES.append(s)

    parser = argparse.ArgumentParser(description="Settlement Monitor")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("daemon", help="Headless scheduler — no dashboard (use for LaunchAgent)")
    sub.add_parser("serve", help="Start dashboard + scheduler")
    crawl_p = sub.add_parser("crawl", help="Run one crawl now")
    crawl_p.add_argument("--no-alert", action="store_true", help="Skip alerts")
    add_p = sub.add_parser("add-site", help="Add a settlement site URL to monitor")
    add_p.add_argument("url", help="URL of the settlement site")

    args = parser.parse_args()

    if args.command == "daemon":
        cmd_daemon()
    elif args.command == "serve":
        cmd_serve()
    elif args.command == "crawl":
        cmd_crawl(send_alerts=not args.no_alert)
    elif args.command == "add-site":
        cmd_add_site(args.url)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
