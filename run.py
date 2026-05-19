import os
import sys

from app import create_app
from app.scraper_runner import run_all_scrapers

app = create_app()

# macOS Monterey+ uses port 5000 for AirPlay Receiver — default to 8080 locally
DEFAULT_PORT = 8080


@app.cli.command("scrape")
def scrape_cli():
    """Run all scrapers once from the command line."""
    result = run_all_scrapers(
        keyword=os.environ.get("SCRAPE_KEYWORD", "AI startup"),
        region=os.environ.get("SCRAPE_REGION", ""),
    )
    print(result)


def _resolve_port() -> int:
    env_port = os.environ.get("PORT")
    if env_port:
        return int(env_port)
    port = DEFAULT_PORT
    import socket

    for candidate in (8080, 8081, 3000, 5001):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", candidate)) != 0:
                return candidate
    return port


if __name__ == "__main__":
    if os.environ.get("RUN_SCRAPE_ON_START"):
        run_all_scrapers(
            keyword=os.environ.get("SCRAPE_KEYWORD", "AI startup"),
            region=os.environ.get("SCRAPE_REGION", ""),
        )

    port = _resolve_port()
    print(f"\n  Opportunity Pulse running at http://127.0.0.1:{port}\n", flush=True)
    if port != 5000:
        print(
            "  (Using port %d — port 5000 is often taken by macOS AirPlay Receiver)\n"
            % port,
            flush=True,
        )
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
