import csv
import io
import json
import re

from flask import (
    Blueprint,
    Response,
    jsonify,
    render_template,
    request,
)

from app.database import (
    add_alert_subscription,
    get_filter_options,
    get_stats,
    search_opportunities,
)
from app.scraper_runner import run_all_scrapers

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return _render_dashboard("index.html")


@bp.route("/analytics")
def analytics():
    stats = get_stats()
    return render_template("analytics.html", stats=stats)


@bp.route("/health")
def health():
    stats = get_stats()
    return jsonify(
        {
            "status": "ok",
            "opportunities": stats["total"],
            "last_updated": stats.get("last_updated"),
        }
    )


def _render_dashboard(template: str):
    keyword = request.args.get("q", "").strip()
    opp_type = request.args.get("type", "").strip()
    source = request.args.get("source", "").strip()
    deadline_from = request.args.get("deadline_from", "").strip()
    deadline_to = request.args.get("deadline_to", "").strip()
    work_mode = request.args.get("work_mode", "").strip()
    startup_stage = request.args.get("stage", "").strip()
    sort = request.args.get("sort", "deadline").strip()
    view = request.args.get("view", "grid").strip()

    opportunities = search_opportunities(
        keyword=keyword,
        opp_type=opp_type,
        source=source,
        deadline_from=deadline_from,
        deadline_to=deadline_to,
        work_mode=work_mode,
        startup_stage=startup_stage,
        sort=sort,
    )
    filters = get_filter_options()
    stats = get_stats()

    return render_template(
        template,
        opportunities=opportunities,
        filters=filters,
        stats=stats,
        query={
            "q": keyword,
            "type": opp_type,
            "source": source,
            "deadline_from": deadline_from,
            "deadline_to": deadline_to,
            "work_mode": work_mode,
            "stage": startup_stage,
            "sort": sort,
            "view": view,
        },
    )


@bp.route("/api/opportunities")
def api_opportunities():
    return jsonify(
        search_opportunities(
            keyword=request.args.get("q", "").strip(),
            opp_type=request.args.get("type", ""),
            source=request.args.get("source", ""),
            deadline_from=request.args.get("deadline_from", ""),
            deadline_to=request.args.get("deadline_to", ""),
            work_mode=request.args.get("work_mode", ""),
            startup_stage=request.args.get("stage", ""),
            sort=request.args.get("sort", "deadline"),
        )
    )


@bp.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


@bp.route("/api/scrape", methods=["POST"])
def api_scrape():
    data = request.get_json(silent=True) or {}
    keyword = data.get("keyword") or request.args.get("keyword", "AI startup")
    region = data.get("region") or request.args.get("region", "")
    result = run_all_scrapers(keyword=keyword, region=region)
    return jsonify(result)


@bp.route("/api/alerts", methods=["POST"])
def api_alerts():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip()
    keyword = (data.get("keyword") or "AI startup").strip()
    region = (data.get("region") or "").strip()

    if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return jsonify({"ok": False, "error": "Valid email required"}), 400

    ok = add_alert_subscription(email, keyword, region)
    return jsonify({"ok": ok, "message": "Alert saved. New matches will be emailed when configured."})


@bp.route("/export/<fmt>")
def export_data(fmt: str):
    rows = search_opportunities()
    if fmt == "json":
        return Response(
            json.dumps(rows, indent=2, default=str),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=opportunities.json"},
        )

    output = io.StringIO()
    fieldnames = [
        "title",
        "type",
        "organizer",
        "location",
        "deadline",
        "deadline_iso",
        "source",
        "source_url",
        "funding_range",
        "startup_stage",
        "work_mode",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fieldnames})

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=opportunities.csv"},
    )
