import time
from abc import ABC, abstractmethod
from typing import Optional

import requests

from app.config import DEFAULT_USER_AGENT, REQUEST_TIMEOUT
from app.models import Opportunity


class BaseScraper(ABC):
    source_name: str = "unknown"

    def __init__(self, keyword: str = "", region: str = ""):
        self.keyword = keyword.strip()
        self.region = region.strip()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

    def get(self, url: str, **kwargs) -> requests.Response:
        for attempt in range(3):
            try:
                resp = self.session.get(url, timeout=REQUEST_TIMEOUT, **kwargs)
                if resp.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                return resp
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"Failed to fetch {url}")

    @abstractmethod
    def scrape(self) -> list[Opportunity]:
        pass

    def matches_region(self, location: str) -> bool:
        if not self.region:
            return True
        return self.region.lower() in (location or "").lower()

    def matches_keyword(self, text: str) -> bool:
        if not self.keyword:
            return True
        haystack = text.lower()
        terms = self._expanded_terms()
        return any(term in haystack for term in terms)

    def _expanded_terms(self) -> list[str]:
        raw = self.keyword.lower().split()
        extras = []
        joined = " ".join(raw)
        if "ai" in joined or "artificial" in joined:
            extras.extend(["ai", "artificial", "intelligence", "machine learning", "ml"])
        if "startup" in joined:
            extras.extend(["startup", "founder", "entrepreneur", "small business", "innovation"])
        return list(dict.fromkeys(raw + extras))
