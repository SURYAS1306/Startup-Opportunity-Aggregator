import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import SCRAPE_INTERVAL_HOURS
from app.scraper_runner import run_all_scrapers

logger = logging.getLogger(__name__)
_scheduler = None  # type: Optional[BackgroundScheduler]


def start_scheduler(keyword: str = "AI startup", region: str = "") -> BackgroundScheduler:
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        func=lambda: run_all_scrapers(keyword=keyword, region=region),
        trigger="interval",
        hours=SCRAPE_INTERVAL_HOURS,
        id="scrape_job",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started (every %s hours)", SCRAPE_INTERVAL_HOURS)
    return _scheduler
