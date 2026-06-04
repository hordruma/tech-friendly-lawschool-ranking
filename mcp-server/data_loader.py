"""
mcp-server/data_loader.py

Data loading helpers for the MCP server.  All paths are resolved relative to
the project root (the parent directory of mcp-server/).

Public API
----------
load_all_schools()    -> list[dict]
    Load every JSON file under data/schools/, compute scores if missing,
    return a list sorted by meta_score (descending, None last).

load_school(id)       -> dict | None
    Load a single school by slug.  Returns None if not found.

get_research_stats()  -> dict
    Parse data/research-list/top-500.json and return coverage statistics.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from scoring import ensure_scores

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).parent.parent
_SCHOOLS_DIR = _PROJECT_ROOT / "data" / "schools"
_RESEARCH_LIST = _PROJECT_ROOT / "data" / "research-list" / "top-500.json"
_CRITERIA_PATH = _PROJECT_ROOT / "CRITERIA.md"


def _schools_dir() -> Path:
    return _SCHOOLS_DIR


def _load_json(path: Path) -> Any:
    """Load and return JSON from a path."""
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# School loaders
# ---------------------------------------------------------------------------

def load_school(school_id: str) -> dict | None:
    """
    Load a single school by its slug.  Returns None if the file doesn't exist.
    Scores are computed on-the-fly if not already stored.
    """
    path = _schools_dir() / f"{school_id}.json"
    if not path.exists():
        return None
    try:
        school = _load_json(path)
        return ensure_scores(school)
    except Exception as exc:
        logger.warning("Failed to load %s: %s", path, exc)
        return None


def load_all_schools() -> list[dict]:
    """
    Load every *.json file under data/schools/, compute missing scores,
    and return the list sorted by meta_score descending (None last).
    """
    schools: list[dict] = []
    for path in sorted(_schools_dir().glob("*.json")):
        try:
            school = _load_json(path)
            school = ensure_scores(school)
            schools.append(school)
        except Exception as exc:
            logger.warning("Skipping %s due to error: %s", path, exc)

    def sort_key(s: dict) -> tuple:
        score = s.get("meta_score")
        if score is None:
            # Fall back to tech score so unranked schools still sort reasonably
            tech = (s.get("scores") or {}).get("total") or 0
            return (1, -tech)
        return (0, -score)

    schools.sort(key=sort_key)
    return schools


# ---------------------------------------------------------------------------
# Research queue stats
# ---------------------------------------------------------------------------

def get_research_stats() -> dict:
    """
    Parse data/research-list/top-500.json and data/schools/*.json to produce
    coverage statistics useful for the ``get_research_queue_stats`` MCP tool
    and the ``law-schools://research-queue`` resource.
    """
    try:
        queue: list[dict] = _load_json(_RESEARCH_LIST)
    except Exception as exc:
        return {"error": f"Could not load research list: {exc}"}

    # IDs of schools that already have a data file
    researched_ids: set[str] = {
        p.stem for p in _schools_dir().glob("*.json")
    }

    total = len(queue)
    researched = sum(1 for s in queue if s["id"] in researched_ids)
    pending = total - researched

    by_region: dict[str, dict[str, int]] = {}
    for entry in queue:
        region = entry.get("region", "Unknown")
        if region not in by_region:
            by_region[region] = {"total": 0, "researched": 0, "pending": 0}
        by_region[region]["total"] += 1
        if entry["id"] in researched_ids:
            by_region[region]["researched"] += 1
        else:
            by_region[region]["pending"] += 1

    by_country: dict[str, int] = {}
    for entry in queue:
        c = entry.get("country", "??")
        by_country[c] = by_country.get(c, 0) + 1

    return {
        "total_in_queue": total,
        "researched": researched,
        "pending": pending,
        "coverage_pct": round(100 * researched / total, 1) if total else 0,
        "by_region": by_region,
        "countries_represented": len(by_country),
    }


# ---------------------------------------------------------------------------
# Supplemental helpers
# ---------------------------------------------------------------------------

def load_criteria_text() -> str:
    """Return the full text of CRITERIA.md."""
    try:
        return _CRITERIA_PATH.read_text(encoding="utf-8")
    except Exception as exc:
        return f"[Could not load CRITERIA.md: {exc}]"


def schools_summary_list() -> list[dict]:
    """
    Return a lightweight summary of all researched schools — suitable for the
    ``law-schools://schools`` MCP resource.
    """
    schools = load_all_schools()
    summaries = []
    for s in schools:
        scores = s.get("scores") or {}
        summaries.append({
            "id": s.get("id"),
            "name": s.get("name"),
            "country": s.get("country"),
            "region": _infer_region(s),
            "tech_score": scores.get("total"),
            "practical_skills_score": s.get("practical_skills_score"),
            "meta_score": s.get("meta_score"),
            "ranking_tier": s.get("ranking_tier"),
            "last_verified": s.get("last_verified"),
            "has_press_release_gaps": bool(s.get("press_release_gap")),
        })
    return summaries


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_COUNTRY_TO_REGION: dict[str, str] = {
    "US": "North America",
    "CA": "North America",
    "MX": "Latin America",
    "BR": "Latin America",
    "AR": "Latin America",
    "CL": "Latin America",
    "CO": "Latin America",
    "PE": "Latin America",
    "VE": "Latin America",
    "GB": "UK & Ireland",
    "IE": "UK & Ireland",
    "DE": "Europe",
    "FR": "Europe",
    "NL": "Europe",
    "BE": "Europe",
    "IT": "Europe",
    "ES": "Europe",
    "PT": "Europe",
    "CH": "Europe",
    "AT": "Europe",
    "SE": "Europe",
    "NO": "Europe",
    "DK": "Europe",
    "FI": "Europe",
    "PL": "Europe",
    "CZ": "Europe",
    "HU": "Europe",
    "RO": "Europe",
    "GR": "Europe",
    "AU": "Asia-Pacific",
    "NZ": "Asia-Pacific",
    "SG": "Asia-Pacific",
    "HK": "Asia-Pacific",
    "JP": "Asia-Pacific",
    "KR": "Asia-Pacific",
    "CN": "Asia-Pacific",
    "IN": "Asia-Pacific",
    "MY": "Asia-Pacific",
    "TH": "Asia-Pacific",
    "PH": "Asia-Pacific",
    "ID": "Asia-Pacific",
    "ZA": "Middle East & Africa",
    "NG": "Middle East & Africa",
    "KE": "Middle East & Africa",
    "EG": "Middle East & Africa",
    "AE": "Middle East & Africa",
    "SA": "Middle East & Africa",
    "IL": "Middle East & Africa",
    "QA": "Middle East & Africa",
    "KW": "Middle East & Africa",
}


def _infer_region(school: dict) -> str | None:
    """Best-effort region inference from country code."""
    return _COUNTRY_TO_REGION.get(school.get("country", ""), None)


def get_queue_entry(school_id: str) -> dict | None:
    """Return the top-500 queue entry for a school, if present."""
    try:
        queue: list[dict] = _load_json(_RESEARCH_LIST)
        for entry in queue:
            if entry.get("id") == school_id:
                return entry
    except Exception:
        pass
    return None
