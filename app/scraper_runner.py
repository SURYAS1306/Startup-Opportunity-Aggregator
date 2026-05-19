import json
import logging
import time
import urllib.request
from typing import Optional

from app.config import OPENAI_API_KEY, WEBHOOK_URL
from app.database import (
    get_existing_fingerprints,
    log_scrape,
    upsert_opportunities,
)
from app.dedup import merge_unique
from app.scrapers import ALL_SCRAPERS
from app.tagging import enrich_with_ai

logger = logging.getLogger(__name__)


def run_all_scrapers(
    keyword: str = "AI startup",
    region: str = "",
    use_ai: bool = False,
) -> dict:
    start = time.time()
    all_opportunities = []
    errors = []

    for scraper_cls in ALL_SCRAPERS:
        name = scraper_cls.source_name
        try:
            scraper = scraper_cls(keyword=keyword, region=region)
            found = scraper.scrape()
            logger.info("%s returned %d items", name, len(found))
            all_opportunities.extend(found)
        except Exception as exc:
            logger.exception("Scraper %s failed: %s", name, exc)
            errors.append({"source": name, "error": str(exc)})

    existing = get_existing_fingerprints()
    unique = merge_unique(existing, all_opportunities)

    if use_ai and OPENAI_API_KEY:
        unique = enrich_with_ai(unique, OPENAI_API_KEY)
    else:
        from app.tagging import auto_tag

        unique = [auto_tag(o) for o in unique]

    inserted, skipped = upsert_opportunities(unique)
    duration_ms = int((time.time() - start) * 1000)

    log_scrape(
        keyword=keyword,
        region=region,
        scraped=len(all_opportunities),
        inserted=inserted,
        duplicates=skipped + (len(unique) - inserted),
        errors=json.dumps(errors) if errors else "",
        duration_ms=duration_ms,
    )

    if WEBHOOK_URL and inserted > 0:
        _send_webhook(inserted, keyword, [o.source_url for o in unique[:5]])

    return {
        "scraped": len(all_opportunities),
        "unique_new": inserted,
        "duplicates_skipped": skipped,
        "errors": errors,
        "keyword": keyword,
        "region": region,
        "duration_ms": duration_ms,
    }


def _send_webhook(count: int, keyword: str, sample_urls: list[str]) -> None:
    payload = {
        "event": "new_opportunities",
        "count": count,
        "keyword": keyword,
        "sample_urls": sample_urls,
    }
    try:
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as exc:
        logger.warning("Webhook failed: %s", exc)
