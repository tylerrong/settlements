import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
EXTRA_WEBHOOK_URLS = [u.strip() for u in os.getenv("EXTRA_WEBHOOK_URLS", "").split(",") if u.strip()]
DB_PATH = os.getenv("DB_PATH", "./settlements.db")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5050"))
CRAWL_INTERVAL_HOURS = int(os.getenv("CRAWL_INTERVAL_HOURS", "24"))

ALL_WEBHOOK_URLS = [u for u in [DISCORD_WEBHOOK_URL] + EXTRA_WEBHOOK_URLS if u]

# Twitter/X API credentials (OAuth 1.0a — required for posting tweets)
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
