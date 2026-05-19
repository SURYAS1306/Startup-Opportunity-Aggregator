from app.scrapers.devpost import DevpostScraper
from app.scrapers.opportunity_desk import OpportunityDeskScraper
from app.scrapers.sbir import SbirScraper

ALL_SCRAPERS = [SbirScraper, DevpostScraper, OpportunityDeskScraper]
