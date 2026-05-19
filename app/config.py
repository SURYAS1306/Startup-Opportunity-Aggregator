import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = os.environ.get("DATABASE_PATH", str(DATA_DIR / "opportunities.db"))
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
SCRAPE_INTERVAL_HOURS = int(os.environ.get("SCRAPE_INTERVAL_HOURS", "6"))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30
