"""
src/lawschool/data.py

Clean data access layer for the Tech-Friendly Law School Ranking.

Paths are resolved via the env var LAWSCHOOL_DATA_DIR with fallback to
<repo-root>/data, so alternative deployments can point at their own data
directory without touching source code.

Public API
----------
load_school(school_id)   -> LawSchool | None
load_all_schools()       -> list[LawSchool]   (sorted by meta_score desc)
get_research_stats()     -> dict
load_criteria_text()     -> str
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from lawschool.schema import LawSchool
from lawschool.scoring import compute_tech_score, compute_practical_score, compute_meta_score

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _data_dir() -> Path:
    """Return the root data directory, honouring LAWSCHOOL_DATA_DIR if set."""
    env = os.getenv("LAWSCHOOL_DATA_DIR")
    if env:
        return Path(env)
    # Default: <repo-root>/data, where repo root = three levels above this file
    # (src/lawschool/data.py → src/lawschool/ → src/ → repo-root/)
    return Path(__file__).parent.parent.parent / "data"


def _schools_dir() -> Path:
    return _data_dir() / "schools"


def _research_list_path() -> Path:
    return _data_dir() / "research-list" / "top-500.json"


def _criteria_path() -> Path:
    # CRITERIA.md lives at repo root, one level above data/
    return _data_dir().parent / "CRITERIA.md"


# ---------------------------------------------------------------------------
# School loaders
# ---------------------------------------------------------------------------

def _ensure_scores(school: LawSchool) -> LawSchool:
    """Compute and attach any missing score fields, returning the updated model."""
    data = school.model_dump(mode="json")

    # Tech score
    if (school.scores is None) or (school.scores.total is None):
        result = compute_tech_score(data)
        data["scores"] = result["scores"]
        data["ranking_tier"] = result["ranking_tier"]

    # Practical skills score
    if school.practical_skills_score is None:
        ps = compute_practical_score(data)
        data["practical_skills_score"] = ps["practical_skills_score"]
        data["practical_skills_breakdown"] = ps["breakdown"]

    # Meta score
    if school.meta_score is None:
        meta = compute_meta_score(data)
        data["meta_score"] = meta["meta_score"]
        data["prestige_score"] = meta.get("prestige_score")

    return LawSchool.model_validate(data)


def load_school(school_id: str) -> LawSchool | None:
    """Load a single school by its slug.  Returns None if not found."""
    path = _schools_dir() / f"{school_id}.json"
    if not path.exists():
        return None
    try:
        school = LawSchool.from_json_file(path)
        return _ensure_scores(school)
    except Exception as exc:
        logger.warning("Failed to load %s: %s", path, exc)
        return None


def load_all_schools() -> list[LawSchool]:
    """
    Load every *.json file under data/schools/, compute missing scores,
    and return the list sorted by meta_score descending (None last).
    """
    schools: list[LawSchool] = []
    for path in sorted(_schools_dir().glob("*.json")):
        try:
            school = LawSchool.from_json_file(path)
            school = _ensure_scores(school)
            schools.append(school)
        except Exception as exc:
            logger.warning("Skipping %s: %s", path, exc)

    def sort_key(s: LawSchool) -> tuple:
        if s.meta_score is not None:
            return (0, -s.meta_score)
        tech = (s.scores.total if s.scores else None) or 0.0
        return (1, -tech)

    schools.sort(key=sort_key)
    return schools


# ---------------------------------------------------------------------------
# Research queue stats
# ---------------------------------------------------------------------------

def get_research_stats() -> dict:
    """
    Parse data/research-list/top-500.json and data/schools/*.json to produce
    coverage statistics.
    """
    rp = _research_list_path()
    try:
        queue: list[dict] = json.loads(rp.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": f"Could not load research list: {exc}"}

    researched_ids: set[str] = {p.stem for p in _schools_dir().glob("*.json")}

    total = len(queue)
    researched = sum(1 for s in queue if s["id"] in researched_ids)
    pending = total - researched

    by_region: dict[str, dict[str, int]] = {}
    by_country: dict[str, int] = {}
    for entry in queue:
        region = entry.get("region", "Unknown")
        by_region.setdefault(region, {"total": 0, "researched": 0, "pending": 0})
        by_region[region]["total"] += 1
        if entry["id"] in researched_ids:
            by_region[region]["researched"] += 1
        else:
            by_region[region]["pending"] += 1

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


def get_queue_entry(school_id: str) -> dict | None:
    """Return the top-500 queue entry for a school, if present."""
    try:
        queue: list[dict] = json.loads(_research_list_path().read_text(encoding="utf-8"))
        for entry in queue:
            if entry.get("id") == school_id:
                return entry
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

def load_criteria_text() -> str:
    """Return the full text of CRITERIA.md."""
    try:
        return _criteria_path().read_text(encoding="utf-8")
    except Exception as exc:
        return f"[Could not load CRITERIA.md: {exc}]"


def schools_summary_list() -> list[dict]:
    """
    Return lightweight summary dicts for all researched schools — suitable for
    the law-schools://schools MCP resource.
    """
    summaries = []
    for school in load_all_schools():
        summaries.append({
            "id": school.id,
            "name": school.name,
            "country": school.country,
            "region": school.region,
            "tech_score": school.scores.total if school.scores else None,
            "practical_skills_score": school.practical_skills_score,
            "meta_score": school.meta_score,
            "ranking_tier": school.ranking_tier,
            "last_verified": school.last_verified,
            "has_press_release_gaps": bool(school.press_release_gap),
        })
    return summaries
