#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

source .venv/bin/activate

if [ ! -f "data/opportunities.db" ]; then
  echo "Populating database (first run)..."
  python scripts/run_scraper.py --keyword "AI startup"
fi

export PORT="${PORT:-8080}"
export RUN_SCRAPE_ON_START="${RUN_SCRAPE_ON_START:-0}"
echo "Starting dashboard at http://127.0.0.1:$PORT"
python run.py
