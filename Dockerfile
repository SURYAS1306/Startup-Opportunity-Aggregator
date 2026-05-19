FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libxml2-dev libxslt1-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data

ENV PORT=8080
ENV RUN_SCRAPE_ON_START=1
ENV SCRAPE_KEYWORD="AI startup"

EXPOSE 8080
CMD ["sh", "-c", "python scripts/run_scraper.py --keyword \"$SCRAPE_KEYWORD\" && gunicorn run:app --bind 0.0.0.0:${PORT} --workers 2 --timeout 120"]
