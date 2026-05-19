# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Opportunity Pulse (Flask)                    │
├──────────────┬──────────────────────┬───────────────────────────┤
│  Dashboard   │  Analytics + Health  │  REST API (/api/*)        │
└──────┬───────┴──────────┬───────────┴─────────────┬─────────────┘
       │                  │                         │
       ▼                  ▼                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                     SQLite (opportunities.db)                     │
│  opportunities │ scrape_logs │ alert_subscriptions               │
└──────────────────────────────▲───────────────────────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────┐      ┌─────────────────┐    ┌──────────────────┐
│  SBIR.gov   │      │ Devpost API     │    │ Opportunity Desk │
│  HTML scrape│      │ JSON + paginate │    │ RSS feeds        │
└─────────────┘      └─────────────────┘    └──────────────────┘
```

## Data Pipeline

1. **Extract** — Scrapers fetch raw listings (keyword/region aware).
2. **Transform** — Parse deadlines to ISO, auto-tag funding/stage/work mode.
3. **Deduplicate** — SHA-256 fingerprint on title+type+organizer+deadline.
4. **Load** — Insert into SQLite; skip duplicates via UNIQUE constraint.
5. **Serve** — Dashboard search/filter; export CSV/JSON.

## Scheduler

APScheduler runs `run_all_scrapers()` every 6 hours in-process. Alternative: system cron via `crontab.example`.

## Deployment

- **Render** — `render.yaml` + Gunicorn
- **Docker** — `Dockerfile` + `docker-compose.yml`
- **Local** — `./start.sh` on port **8080** (avoids macOS AirPlay on 5000)
