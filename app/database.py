import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional

from app.config import DATABASE_PATH
from app.dedup import make_fingerprint
from app.models import Opportunity
from app.tagging import auto_tag
from app.date_utils import parse_deadline


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                organizer TEXT,
                location TEXT,
                deadline TEXT,
                deadline_iso TEXT,
                source_url TEXT NOT NULL,
                source TEXT NOT NULL,
                description TEXT,
                funding_range TEXT,
                startup_stage TEXT,
                work_mode TEXT,
                fingerprint TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scrape_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ran_at TEXT NOT NULL,
                keyword TEXT,
                region TEXT,
                scraped INTEGER,
                inserted INTEGER,
                duplicates INTEGER,
                errors TEXT,
                duration_ms INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                keyword TEXT NOT NULL,
                region TEXT,
                created_at TEXT NOT NULL,
                active INTEGER DEFAULT 1
            )
            """
        )
        _migrate_columns(conn)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_opp_type ON opportunities(type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_opp_source ON opportunities(source)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_opp_deadline_iso ON opportunities(deadline_iso)")
        conn.commit()


def _migrate_columns(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(opportunities)").fetchall()}
    if "deadline_iso" not in cols:
        conn.execute("ALTER TABLE opportunities ADD COLUMN deadline_iso TEXT")
        rows = conn.execute("SELECT id, deadline FROM opportunities").fetchall()
        for row in rows:
            iso = parse_deadline(row["deadline"])
            if iso:
                conn.execute(
                    "UPDATE opportunities SET deadline_iso = ? WHERE id = ?",
                    (iso, row["id"]),
                )


@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_existing_fingerprints() -> set[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT fingerprint FROM opportunities").fetchall()
    return {row["fingerprint"] for row in rows}


def upsert_opportunities(opportunities: list[Opportunity]) -> tuple[int, int]:
    now = datetime.utcnow().isoformat()
    inserted = 0
    skipped = 0

    with get_connection() as conn:
        for opp in opportunities:
            opp = auto_tag(opp)
            if not opp.fingerprint:
                opp.fingerprint = make_fingerprint(opp)
            deadline_iso = parse_deadline(opp.deadline)

            try:
                conn.execute(
                    """
                    INSERT INTO opportunities (
                        title, type, organizer, location, deadline, deadline_iso,
                        source_url, source, description,
                        funding_range, startup_stage, work_mode,
                        fingerprint, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        opp.title,
                        opp.opp_type,
                        opp.organizer,
                        opp.location,
                        opp.deadline,
                        deadline_iso,
                        opp.source_url,
                        opp.source,
                        opp.description,
                        opp.funding_range,
                        opp.startup_stage,
                        opp.work_mode,
                        opp.fingerprint,
                        now,
                        now,
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
        conn.commit()

    return inserted, skipped


def log_scrape(
    keyword: str,
    region: str,
    scraped: int,
    inserted: int,
    duplicates: int,
    errors: str,
    duration_ms: int,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO scrape_logs
            (ran_at, keyword, region, scraped, inserted, duplicates, errors, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                keyword,
                region,
                scraped,
                inserted,
                duplicates,
                errors,
                duration_ms,
            ),
        )
        conn.commit()


def search_opportunities(
    keyword: str = "",
    opp_type: str = "",
    source: str = "",
    deadline_from: str = "",
    deadline_to: str = "",
    work_mode: str = "",
    startup_stage: str = "",
    sort: str = "deadline",
) -> list[dict[str, Any]]:
    query = "SELECT * FROM opportunities WHERE 1=1"
    params: list[Any] = []

    if keyword:
        query += (
            " AND (title LIKE ? OR description LIKE ? OR organizer LIKE ?"
            " OR location LIKE ? OR funding_range LIKE ?)"
        )
        like = f"%{keyword}%"
        params.extend([like, like, like, like, like])

    if opp_type:
        query += " AND type = ?"
        params.append(opp_type)

    if source:
        query += " AND source = ?"
        params.append(source)

    if work_mode:
        query += " AND work_mode = ?"
        params.append(work_mode)

    if startup_stage:
        query += " AND startup_stage = ?"
        params.append(startup_stage)

    if deadline_from:
        query += " AND (deadline_iso >= ? OR deadline >= ?)"
        params.extend([deadline_from, deadline_from])

    if deadline_to:
        query += " AND (deadline_iso <= ? OR deadline <= ?)"
        params.extend([deadline_to, deadline_to])

    order_map = {
        "deadline": "deadline_iso ASC NULLS LAST, updated_at DESC",
        "newest": "created_at DESC",
        "title": "title ASC",
        "source": "source ASC, title ASC",
    }
    query += f" ORDER BY {order_map.get(sort, order_map['deadline'])}"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def get_stats() -> dict[str, Any]:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM opportunities").fetchone()["c"]
        by_source = conn.execute(
            "SELECT source, COUNT(*) AS c FROM opportunities GROUP BY source"
        ).fetchall()
        by_type = conn.execute(
            "SELECT type, COUNT(*) AS c FROM opportunities GROUP BY type ORDER BY c DESC"
        ).fetchall()
        by_work_mode = conn.execute(
            "SELECT work_mode, COUNT(*) AS c FROM opportunities "
            "WHERE work_mode != '' GROUP BY work_mode"
        ).fetchall()
        last_scrape = conn.execute(
            "SELECT MAX(updated_at) AS last FROM opportunities"
        ).fetchone()["last"]
        upcoming = conn.execute(
            """
            SELECT COUNT(*) AS c FROM opportunities
            WHERE deadline_iso >= date('now')
            """
        ).fetchone()["c"]
        recent_logs = conn.execute(
            "SELECT * FROM scrape_logs ORDER BY ran_at DESC LIMIT 5"
        ).fetchall()

    return {
        "total": total,
        "upcoming_deadlines": upcoming,
        "by_source": {row["source"]: row["c"] for row in by_source},
        "by_type": {row["type"]: row["c"] for row in by_type},
        "by_work_mode": {row["work_mode"]: row["c"] for row in by_work_mode},
        "last_updated": last_scrape,
        "recent_scrapes": [dict(r) for r in recent_logs],
    }


def get_filter_options() -> dict[str, list[str]]:
    with get_connection() as conn:
        types = [
            row["type"]
            for row in conn.execute(
                "SELECT DISTINCT type FROM opportunities ORDER BY type"
            ).fetchall()
        ]
        sources = [
            row["source"]
            for row in conn.execute(
                "SELECT DISTINCT source FROM opportunities ORDER BY source"
            ).fetchall()
        ]
        work_modes = [
            row["work_mode"]
            for row in conn.execute(
                "SELECT DISTINCT work_mode FROM opportunities "
                "WHERE work_mode != '' ORDER BY work_mode"
            ).fetchall()
        ]
        stages = [
            row["startup_stage"]
            for row in conn.execute(
                "SELECT DISTINCT startup_stage FROM opportunities "
                "WHERE startup_stage != '' ORDER BY startup_stage"
            ).fetchall()
        ]
    return {
        "types": types,
        "sources": sources,
        "work_modes": work_modes,
        "stages": stages,
    }


def add_alert_subscription(email: str, keyword: str, region: str = "") -> bool:
    with get_connection() as conn:
        try:
            conn.execute(
                """
                INSERT INTO alert_subscriptions (email, keyword, region, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (email, keyword, region, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False


def get_alert_subscriptions() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM alert_subscriptions WHERE active = 1 ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]
