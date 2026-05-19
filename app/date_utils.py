import re
from datetime import datetime
from typing import Optional

from dateutil import parser as date_parser

MONTH_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},?\s+\d{4}",
    re.I,
)


def parse_deadline(text: Optional[str]) -> str:
    """Normalize deadline text to ISO date (YYYY-MM-DD) when possible."""
    if not text or not str(text).strip():
        return ""
    raw = str(text).strip()
    match = MONTH_PATTERN.search(raw)
    if match:
        raw = match.group(0)
    try:
        dt = date_parser.parse(raw, fuzzy=True, dayfirst=False)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError, OverflowError):
        return ""
