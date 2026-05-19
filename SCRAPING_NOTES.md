# Scraping Challenges & Handling

## Overview

This project aggregates opportunities from three sources with different technical profiles: a government HTML portal (SBIR.gov), a JavaScript-heavy site with a hidden JSON API (Devpost), and WordPress RSS feeds (Opportunity Desk).

---

## 1. SBIR.gov — HTML & Pagination

### Challenges

- **No public REST API** for topic search; data is rendered server-side as HTML.
- **Pagination** uses `?page=N` query parameters; empty pages must be detected to stop looping.
- **Detail pages** use inconsistent heading structure (`h1` often reads "Topic" with the real title in breadcrumbs or list links).
- **Rate limiting**: Government sites may throttle aggressive crawlers.

### Handling

- `requests.Session` with a realistic browser `User-Agent`.
- **Exponential backoff** on failures (3 retries in `BaseScraper.get()`).
- Parse listing pages for `/topics/{id}` links, then fetch each detail page for agency, open/close dates, and description.
- **Keyword filter** applied client-side after fetch (`AI`, `startup`, etc.).
- **Pagination cap** (`max_pages=5`) to avoid unbounded crawls.

---

## 2. Devpost — Anti-Bot (WAF) vs JSON API

### Challenges

- The **main website** (`devpost.com/hackathons`) is protected by **AWS WAF** and returns a JavaScript challenge to bare `curl`/scrapers.
- HTML scraping would require headless browsers (Playwright/Selenium), which adds complexity and fragility.

### Handling

- Discovered the **undocumented public API**: `GET https://devpost.com/api/hackathons`
- Returns structured JSON (title, location, dates, prizes, organization, URL) without WAF on the API path.
- **Pagination** via `page` query parameter; stops when `hackathons` array is empty.
- Strip HTML from prize fields; map event types (Hackathon / Conference / Competition) from title keywords.

---

## 3. Opportunity Desk — RSS Feeds

### Challenges

- Listing pages are WordPress blogs with mixed content; scraping HTML is noisy.
- Deadlines appear inside `<description>` CDATA as free text (`Deadline: May 22, 2026`).

### Handling

- Use **official RSS feeds** per category (grants, fellowships, conferences, competitions) — stable, polite, and ToS-friendly.
- Parse XML with `xml.etree.ElementTree` (no extra dependency).
- **Regex extraction** for deadlines from description text.
- **Region** inferred from `<category>` tags (Africa, Europe, Global, etc.).

---

## 4. Cross-Cutting: Deduplication

The same opportunity may appear on multiple feeds or be re-listed after updates.

**Fingerprint** = SHA-256 of normalized `(title, type, organizer, deadline)`.

- Stored as `UNIQUE` in SQLite; duplicates raise `IntegrityError` and are skipped.
- Title normalization: lowercase, strip punctuation, collapse whitespace.

---

## 5. Data Quality Issues

| Issue | Mitigation |
|-------|------------|
| Non-ISO deadline strings (`May 21, 2026`) | Stored as text; dashboard deadline range filter works best on ISO dates; SBIR dates parsed to consistent format where possible |
| Missing organizer on RSS items | Fallback to `dc:creator` or "Opportunity Desk" |
| SBIR topics without keyword match | Default search `artificial intelligence` when keyword is startup-related |

---

## 6. Scheduling & Reliability

- **APScheduler** runs in-process every 6 hours when the Flask app starts.
- **Cron alternative** documented in README for production servers.
- Scraper errors are **per-source isolated** — one failure does not block others.
- Optional **webhook** (`WEBHOOK_URL`) fires on new inserts for alerting.

---

## 7. Ethical & Legal Considerations

- Only **public** pages/APIs/RSS feeds are accessed.
- Respectful rate limiting (sequential requests, retries with backoff).
- `robots.txt` and terms of service should be reviewed before production scale.
- SBIR.gov and Devpost data are used for educational aggregation with attribution and outbound links to source URLs.

---

## Future Improvements

- Headless browser fallback for WAF-protected pages.
- Normalize all deadlines to ISO 8601 for reliable sorting/filtering.
- Persistent scrape logs and diff-based “new since last run” views.
- Email alerts via SendGrid in addition to webhooks.
