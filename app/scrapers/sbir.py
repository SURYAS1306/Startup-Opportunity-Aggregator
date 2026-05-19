import re
from typing import Optional
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from app.models import Opportunity
from app.scrapers.base import BaseScraper

SBIR_BASE = "https://www.sbir.gov"


class SbirScraper(BaseScraper):
    source_name = "SBIR.gov"

    def scrape(self, max_pages: int = 5) -> list[Opportunity]:
        opportunities: list[Opportunity] = []
        seen_urls: set[str] = set()
        searches = self._search_terms()

        for search in searches:
            keywords = quote_plus(search)
            for page in range(max_pages):
                url = (
                    f"{SBIR_BASE}/topics?keywords={keywords}&status=open"
                    f"&page={page}"
                )
                try:
                    resp = self.get(url)
                except Exception:
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                links = soup.select('a[href^="/topics/"]')
                topic_map: dict[str, str] = {}
                for link in links:
                    href = link.get("href", "")
                    if re.fullmatch(r"/topics/\d+", href):
                        title_text = link.get_text(strip=True)
                        if href not in topic_map and title_text:
                            topic_map[href] = title_text

                topic_ids = list(topic_map.keys())
                if not topic_ids:
                    break

                for href in topic_ids[:20]:
                    full_url = urljoin(SBIR_BASE, href)
                    if full_url in seen_urls:
                        continue
                    detail = self._parse_topic(
                        full_url,
                        list_title=topic_map.get(href, ""),
                    )
                    if detail and self.matches_keyword(
                        f"{detail.title} {detail.description}"
                    ):
                        if self.matches_region(detail.location):
                            seen_urls.add(full_url)
                            opportunities.append(detail)

                if len(topic_ids) < 10:
                    break

        return opportunities

    def _search_terms(self) -> list[str]:
        if not self.keyword:
            return ["artificial intelligence", "startup"]
        kw = self.keyword.lower()
        terms = [self.keyword]
        if "ai" in kw or "startup" in kw:
            terms.extend(["artificial intelligence", "machine learning", "software"])
        return list(dict.fromkeys(terms))[:3]

    def _parse_topic(self, url: str, list_title: str = "") -> Optional[Opportunity]:
        try:
            resp = self.get(url)
        except Exception:
            return None

        soup = BeautifulSoup(resp.text, "lxml")
        title_el = soup.select_one("h1, .page-title, .field-name-title")
        title = title_el.get_text(strip=True) if title_el else "SBIR Topic"
        if title.lower() == "topic" and list_title:
            title = list_title
        elif title.lower() == "topic":
            breadcrumb = soup.select_one(".breadcrumb li:last-child")
            title = breadcrumb.get_text(strip=True) if breadcrumb else title

        agency = ""
        agency_el = soup.select_one(".field-name-field-agency, h3 + p, .agency-name")
        if agency_el:
            agency = agency_el.get_text(strip=True)
        for h3 in soup.find_all("h3"):
            if "Funding Agency" in h3.get_text():
                p = h3.find_next("p")
                if p:
                    agency = p.get_text(strip=True)
                break

        open_date = self._extract_date(soup, "Open Date")
        close_date = self._extract_date(soup, "Close Date")
        deadline = close_date or open_date

        desc_el = soup.select_one(
            ".field-name-body, .field-name-field-topic-description, article p"
        )
        description = desc_el.get_text(" ", strip=True)[:600] if desc_el else ""

        location = "United States"
        if self.region:
            location = f"United States; filter: {self.region}"

        return Opportunity(
            title=title,
            opp_type="Grant",
            organizer=agency or "U.S. Federal Agency",
            location=location,
            deadline=deadline,
            source_url=url,
            source=self.source_name,
            description=description,
        )

    def _extract_date(self, soup: BeautifulSoup, label: str) -> str:
        for node in soup.find_all(string=re.compile(label, re.I)):
            parent = node.parent
            if parent:
                text = parent.get_text(" ", strip=True)
                match = re.search(
                    r"(January|February|March|April|May|June|July|August|"
                    r"September|October|November|December)\s+\d{1,2},\s+\d{4}",
                    text,
                )
                if match:
                    return match.group(0)
        return ""
