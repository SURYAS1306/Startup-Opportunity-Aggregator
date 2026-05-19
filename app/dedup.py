import hashlib
import re
from typing import Iterable

from app.models import Opportunity


def normalize_title(title: str) -> str:
    cleaned = re.sub(r"[^\w\s]", "", title.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def make_fingerprint(opp: Opportunity) -> str:
  """Stable hash for duplicate detection across sources."""
  key = "|".join(
      [
          normalize_title(opp.title),
          opp.opp_type.lower(),
          (opp.organizer or "").lower()[:80],
          (opp.deadline or "")[:10],
      ]
  )
  return hashlib.sha256(key.encode("utf-8")).hexdigest()


def assign_fingerprints(opportunities: Iterable[Opportunity]) -> list[Opportunity]:
    result = []
    for opp in opportunities:
        opp.fingerprint = make_fingerprint(opp)
        result.append(opp)
    return result


def merge_unique(existing_fps: set[str], opportunities: list[Opportunity]) -> list[Opportunity]:
    unique = []
    seen = set(existing_fps)
    for opp in assign_fingerprints(opportunities):
        if opp.fingerprint in seen:
            continue
        seen.add(opp.fingerprint)
        unique.append(opp)
    return unique
