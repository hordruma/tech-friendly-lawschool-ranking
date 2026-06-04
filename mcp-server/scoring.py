"""
mcp-server/scoring.py

Thin adapter that re-exports the scoring logic from agents/scorer.py so the
MCP server has no dependency on the agents package's CLI infrastructure.

All heavy lifting lives in agents/scorer.py.  This module just exposes the
functions the server needs by adding the project root to sys.path once and
importing them cleanly.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Resolve the project root (parent of this file's parent directory)
_PROJECT_ROOT = Path(__file__).parent.parent
_AGENTS_DIR = _PROJECT_ROOT / "agents"

if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Re-export everything the MCP server needs from scorer.py
from scorer import (  # noqa: E402  (import not at top of file is intentional here)
    compute_scores,
    compute_practical_skills_score,
    compute_meta_score,
)

__all__ = [
    "compute_scores",
    "compute_practical_skills_score",
    "compute_meta_score",
]


def ensure_scores(school: dict) -> dict:
    """
    Return a copy of the school dict with all score fields populated.

    If ``scores`` is already present and ``scores.total`` is set, the stored
    scores are used as-is.  Otherwise all three score families are computed on
    the fly and merged into the copy.

    The returned dict is always a shallow copy — the original is never mutated.
    """
    school = dict(school)

    stored = school.get("scores") or {}
    if stored.get("total") is None:
        result = compute_scores(school)
        school["scores"] = result["scores"]
        school["ranking_tier"] = result["ranking_tier"]

    if school.get("practical_skills_score") is None:
        ps = compute_practical_skills_score(school)
        school["practical_skills_score"] = ps["practical_skills_score"]
        school["practical_skills_breakdown"] = ps["breakdown"]

    if school.get("meta_score") is None:
        meta = compute_meta_score(school)
        school["meta_score"] = meta["meta_score"]
        school["prestige_score"] = meta["prestige_score"]

    return school
