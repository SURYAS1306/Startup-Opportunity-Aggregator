# Startup Opportunity Aggregator (Opportunity Pulse)

[![CI](https://github.com/SURYAS1306/Startup-Opportunity-Aggregator/actions/workflows/ci.yml/badge.svg)](https://github.com/SURYAS1306/Startup-Opportunity-Aggregator/actions)

> **Assignment 3** — Web Scraping + Data Pipeline  
> Collects startup opportunities (grants, hackathons, fellowships, conferences) from multiple public sources, deduplicates them, stores in SQLite, and displays them in a searchable dashboard with analytics.

**Repository:** [github.com/SURYAS1306/Startup-Opportunity-Aggregator](https://github.com/SURYAS1306/Startup-Opportunity-Aggregator)

---

## Live Demo

| Environment | URL |
|-------------|-----|
| **Local** | http://127.0.0.1:8080 (after `./start.sh`) |
| **Render** | Deploy via `render.yaml` — add your URL here after deploy |

> **Note:** macOS uses port 5000 for AirPlay Receiver. This app defaults to **port 8080** to avoid conflicts.

---

## Highlights (Evaluation Criteria)

| Criteria | Implementation |
|----------|----------------|
| **Scraper reliability (35%)** | 3 sources, retries, pagination, Devpost API bypass for WAF, per-source error isolation |
| **Data pipeline (25%)** | SHA-256 dedup, ISO deadline normalization, scrape audit logs, SQLite indexes |
| **Dashboard UI (25%)** | Hero, sidebar filters, grid/table views, analytics charts, email alerts |
| **Code quality (15%)** | Modular scrapers, CI workflow, Docker, `ARCHITECTURE.md`, `SCRAPING_NOTES.md` |

### Bonus features

- Auto-tags: funding range, startup stage, remote/on-site
- Email alert subscriptions (stored in DB; wire SendGrid for production)
- Webhook notifications (`WEBHOOK_URL`)
- Export CSV / JSON
- OpenAI tagging when `OPENAI_API_KEY` is set

---

## Sources

| Source | URL | Types | Method |
|--------|-----|-------|--------|
| **SBIR.gov** | https://www.sbir.gov/topics | Federal grants | HTML + pagination |
| **Devpost** | https://devpost.com/api/hackathons | Hackathons, competitions | Public JSON API |
| **Opportunity Desk** | https://opportunitydesk.org | Grants, fellowships, conferences | RSS feeds |

---

## Quick Start

```bash
git clone https://github.com/SURYAS1306/Startup-Opportunity-Aggregator.git
cd Startup-Opportunity-Aggregator
chmod +x start.sh
./start.sh
```

Open **http://127.0.0.1:8080**

### Manual setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_scraper.py --keyword "AI startup"
python run.py   # → http://127.0.0.1:8080
```

### Docker

```bash
docker compose up --build
# → http://localhost:8080
```

---

## API

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard |
| `GET /analytics` | Charts & scrape logs |
| `GET /health` | Health check JSON |
| `GET /api/opportunities` | Filtered JSON list |
| `POST /api/scrape` | `{"keyword":"AI startup","region":""}` |
| `POST /api/alerts` | Email alert subscription |
| `GET /export/csv` | Download CSV |
| `GET /export/json` | Download JSON |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` (local) | Server port |
| `DATABASE_PATH` | `data/opportunities.db` | SQLite path |
| `SCRAPE_INTERVAL_HOURS` | `6` | Scheduler interval |
| `SCRAPE_KEYWORD` | `AI startup` | Default keyword |
| `WEBHOOK_URL` | — | Slack/Discord webhook |
| `OPENAI_API_KEY` | — | Optional AI tagging |

---

## Deploy to Render

1. Push to GitHub.
2. [Render](https://render.com) → New Web Service → connect repo.
3. Uses `render.yaml` automatically.
4. Set `RUN_SCRAPE_ON_START=1`.

---

## Project Structure

```
├── app/scrapers/          # SBIR, Devpost, Opportunity Desk
├── app/database.py        # SQLite + scrape logs
├── templates/             # Dashboard + analytics
├── scripts/run_scraper.py
├── SCRAPING_NOTES.md      # Challenges & handling
├── ARCHITECTURE.md
├── Dockerfile
└── .github/workflows/ci.yml
```

---

## Author

**Surya S** — Assignment 3 Submission
