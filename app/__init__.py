import logging
import os

from flask import Flask

from app.config import SECRET_KEY
from app.database import init_db
from app.routes import bp
from app.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_app(run_scheduler: bool = True) -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = SECRET_KEY
    app.config["JSON_SORT_KEYS"] = False

    init_db()
    app.register_blueprint(bp)

    if run_scheduler and not os.environ.get("DISABLE_SCHEDULER"):
        start_scheduler(
            keyword=os.environ.get("SCRAPE_KEYWORD", "AI startup"),
            region=os.environ.get("SCRAPE_REGION", ""),
        )

    return app
