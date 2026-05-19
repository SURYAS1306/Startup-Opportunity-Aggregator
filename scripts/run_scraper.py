#!/usr/bin/env python3
"""CLI entry point for manual or cron-triggered scraping."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db
from app.scraper_runner import run_all_scrapers


def main():
    parser = argparse.ArgumentParser(description="Run startup opportunity scrapers")
    parser.add_argument("--keyword", default="AI startup", help="Search keyword")
    parser.add_argument("--region", default="", help="Optional region filter")
    parser.add_argument("--ai", action="store_true", help="Use OpenAI tagging if key set")
    args = parser.parse_args()

    init_db()
    result = run_all_scrapers(
        keyword=args.keyword, region=args.region, use_ai=args.ai
    )
    print(result)


if __name__ == "__main__":
    main()
