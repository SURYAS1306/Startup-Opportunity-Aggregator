import html
import re
from typing import Optional

from app.models import Opportunity
from app.scrapers.base import BaseScraper

DEVPOST_API = "https://devpost.com/api/hackathons"


class DevpostScraper(BaseScraper):
    source_name = "Devpost"

    def scrape(self, max_pages: int = 12) -> list[Opportunity]:
        opportunities: list[Opportunity] = []
        search_q = "startup"
        if self.keyword:
            if "ai" in self.keyword.lower():
                search_q = "AI"
            else:
                search_q = self.keyword.split()[0]

        for page in range(1, max_pages + 1):
            params = {
                "page": page,
                "status[]": "open",
                "search": search_q,
            }
            try:
                resp = self.get(DEVPOST_API, params=params)
            except Exception:
                break

            data = resp.json()
            hackathons = data.get("hackathons") or data.get("challenges") or []
            if not hackathons:
                break

            for item in hackathons:
                opp = self._parse_item(item)
                if not opp:
                    continue
                if self.matches_region(opp.location):
                    if not self.keyword or self.matches_keyword(
                        f"{opp.title} {opp.description}"
                    ):
                        opportunities.append(opp)

        return opportunities

    def _parse_item(self, item: dict) -> Optional[Opportunity]:
        title = html.unescape(item.get("title") or "").strip()
        if not title:
            return None

        loc_data = item.get("displayed_location") or {}
        location = loc_data.get("location") or "Online"
        if self.region and self.region.lower() not in location.lower():
            if location.lower() != "online" and "global" not in location.lower():
                pass  # still include; region filter applied upstream

        organizer = item.get("organization_name") or "Devpost Community"
        url = item.get("url") or ""
        if url and not url.startswith("http"):
            url = f"https://devpost.com{url}"

        dates = item.get("submission_period_dates") or ""
        deadline = self._extract_end_date(dates)

        prize = item.get("prize_amount") or ""
        prize_clean = re.sub(r"<[^>]+>", "", str(prize))
        description = (
            f"Submission period: {dates}. "
            f"Prizes: {prize_clean}. "
            f"State: {item.get('open_state', 'open')}."
        )

        themes = ", ".join(t.get("name", "") for t in item.get("themes", [])[:4])
        if themes:
            description += f" Themes: {themes}."

        opp_type = "Hackathon"
        title_lower = title.lower()
        if "summit" in title_lower or "conference" in title_lower:
            opp_type = "Conference"
        elif "competition" in title_lower or "challenge" in title_lower:
            opp_type = "Competition"

        return Opportunity(
            title=title,
            opp_type=opp_type,
            organizer=organizer,
            location=location,
            deadline=deadline,
            source_url=url,
            source=self.source_name,
            description=description,
        )

    def _extract_end_date(self, period: str) -> str:
        if not period:
            return ""
        parts = period.split("-")
        if len(parts) >= 2:
            return parts[-1].strip()
        return period.strip()
