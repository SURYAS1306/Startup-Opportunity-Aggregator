from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Opportunity:
    title: str
    opp_type: str
    organizer: str
    location: str
    deadline: Optional[str]
    source_url: str
    source: str
    description: str = ""
    funding_range: str = ""
    startup_stage: str = ""
    work_mode: str = ""
    fingerprint: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "type": self.opp_type,
            "organizer": self.organizer,
            "location": self.location,
            "deadline": self.deadline or "",
            "source_url": self.source_url,
            "source": self.source,
            "description": self.description,
            "funding_range": self.funding_range,
            "startup_stage": self.startup_stage,
            "work_mode": self.work_mode,
            "fingerprint": self.fingerprint,
        }
