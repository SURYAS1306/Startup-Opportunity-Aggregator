import re
import xml.etree.ElementTree as ET
from html import unescape
from typing import Optional

from app.models import Opportunity
from app.scrapers.base import BaseScraper

FEEDS = [
    ("https://opportunitydesk.org/category/grants/feed/", "Grant"),
    ("https://opportunitydesk.org/category/fellowships/feed/", "Fellowship"),
    (
        "https://opportunitydesk.org/category/training-and-conference/feed/",
        "Conference",
    ),
    (
        "https://opportunitydesk.org/category/competitions/feed/",
        "Competition",
    ),
]


class OpportunityDeskScraper(BaseScraper):
    source_name = "Opportunity Desk"

    def scrape(self) -> list[Opportunity]:
        opportunities: list[Opportunity] = []

        for feed_url, default_type in FEEDS:
            try:
                resp = self.get(feed_url)
                root = ET.fromstring(resp.content)
            except Exception:
                continue

            channel = root.find("channel")
            if channel is None:
                continue

            for item in channel.findall("item")[:40]:
                opp = self._parse_item(item, default_type)
                if not opp:
                    continue
                if self.matches_keyword(f"{opp.title} {opp.description}"):
                    if self.matches_region(opp.location):
                        opportunities.append(opp)

        return opportunities

    def _parse_item(self, item: ET.Element, default_type: str) -> Optional[Opportunity]:
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        creator_el = item.find("{http://purl.org/dc/elements/1.1/}creator")

        title = unescape(title_el.text or "").strip() if title_el is not None else ""
        link = (link_el.text or "").strip() if link_el is not None else ""
        if not title or not link:
            return None

        description = ""
        if desc_el is not None and desc_el.text:
            description = re.sub(r"<[^>]+>", "", unescape(desc_el.text)).strip()

        deadline = self._extract_deadline(description)
        location = self._extract_location(item, description)
        organizer = unescape(creator_el.text or "Opportunity Desk") if creator_el else "Opportunity Desk"

        opp_type = default_type
        title_lower = title.lower()
        if "accelerator" in title_lower:
            opp_type = "Accelerator"
        elif "fellowship" in title_lower:
            opp_type = "Fellowship"
        elif "conference" in title_lower or "summit" in title_lower:
            opp_type = "Conference"

        return Opportunity(
            title=title,
            opp_type=opp_type,
            organizer=organizer,
            location=location,
            deadline=deadline,
            source_url=link,
            source=self.source_name,
            description=description[:600],
        )

    def _extract_deadline(self, text: str) -> str:
        match = re.search(
            r"Deadline:\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
            text,
            re.I,
        )
        return match.group(1) if match else ""

    def _extract_location(self, item: ET.Element, description: str) -> str:
        regions = []
        for cat in item.findall("category"):
            if cat.text and cat.text in (
                "Africa",
                "Europe",
                "Asia",
                "North America",
                "South America",
                "Global",
                "United States",
                "India",
                "Nigeria",
            ):
                regions.append(cat.text)
        if regions:
            return ", ".join(regions[:3])
        if self.region:
            return self.region
        return "Global"
