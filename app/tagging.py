import re

from app.models import Opportunity


def auto_tag(opp: Opportunity) -> Opportunity:
    """Rule-based auto-tagging (bonus). Uses OpenAI only when API key is set."""
    text = f"{opp.title} {opp.description} {opp.location} {opp.opp_type}".lower()

    if not opp.funding_range:
        if any(w in text for w in ("$1m", "$1 m", "million", "seed fund", "series a")):
            opp.funding_range = "$500K–$5M"
        elif any(w in text for w in ("$50", "$100", "cash prize", "prize")):
            opp.funding_range = "Under $100K"
        elif "sbir" in text or "grant" in text or "funding" in text:
            opp.funding_range = "$50K–$2M (typical grant)"
        elif "fellowship" in text or "stipend" in text:
            opp.funding_range = "Stipend / fellowship"

    if not opp.startup_stage:
        if any(w in text for w in ("pre-seed", "preseed", "idea stage", "student")):
            opp.startup_stage = "Pre-seed / Idea"
        elif any(w in text for w in ("seed", "early stage", "early-stage")):
            opp.startup_stage = "Seed"
        elif any(w in text for w in ("series", "growth", "scale")):
            opp.startup_stage = "Growth"
        elif "phase i" in text or "phase 1" in text:
            opp.startup_stage = "R&D / Phase I"
        else:
            opp.startup_stage = "All stages"

    if not opp.work_mode:
        if any(w in text for w in ("remote", "online", "virtual", "global")):
            opp.work_mode = "Remote"
        elif any(w in text for w in ("on-site", "onsite", "in-person", "hybrid")):
            opp.work_mode = "On-site / Hybrid"
        elif "online" in (opp.location or "").lower():
            opp.work_mode = "Remote"
        else:
            opp.work_mode = "Varies"

    return opp


def enrich_with_ai(opportunities: list[Opportunity], api_key: str) -> list[Opportunity]:
    if not api_key:
        return [auto_tag(o) for o in opportunities]

    try:
        import json
        import urllib.request

        for opp in opportunities:
            auto_tag(opp)
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Return JSON with keys funding_range, startup_stage, work_mode "
                            f"for this startup opportunity:\n{opp.title}\n{opp.description[:500]}"
                        ),
                    }
                ],
                "response_format": {"type": "json_object"},
            }
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            content = json.loads(data["choices"][0]["message"]["content"])
            opp.funding_range = content.get("funding_range") or opp.funding_range
            opp.startup_stage = content.get("startup_stage") or opp.startup_stage
            opp.work_mode = content.get("work_mode") or opp.work_mode
    except Exception:
        return [auto_tag(o) for o in opportunities]

    return opportunities
