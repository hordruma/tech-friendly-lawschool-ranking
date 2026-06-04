"""
src/lawschool/scoring/meta.py

Meta-rank computation: combines tech score, practical skills score, and
prestige score into a single meta_score, and normalises external rankings.
"""

from __future__ import annotations

import math
from typing import Any

from lawschool.scoring.tech import compute_tech_score

MAX_RANK = 500
LOG_MAX = math.log(MAX_RANK + 1)

RANKING_KEYS = [
    "qs_law",
    "the_law",
    "arwu_law",
    "usnews_law",
    "usnews_global_law",
    "vault_law",
]


def normalize_rank(rank: int) -> float:
    """
    Convert an ordinal rank to a 0-100 score using a log scale.

    rank 1   → ~100
    rank 500 → 0
    rank > 500 → 0 (clamped)
    """
    if rank > MAX_RANK:
        return 0.0
    norm = 100.0 * (1.0 - math.log(rank) / LOG_MAX)
    return max(0.0, min(100.0, norm))


def compute_prestige_score(school: dict) -> tuple[float | None, dict[str, float | None], list[str]]:
    """
    Compute the prestige score from external rankings.

    Returns:
        prestige_score              float | None  (None if no valid ranks found)
        external_scores_normalized  dict[str, float | None]
        rankings_used               list[str]
    """
    external_rankings = school.get("external_rankings") or {}
    external_scores_normalized: dict[str, float | None] = {}
    rankings_used: list[str] = []
    normalized_values: list[float] = []

    for key in RANKING_KEYS:
        entry = external_rankings.get(key)
        if entry is None:
            external_scores_normalized[key] = None
            continue

        rank = entry.get("rank")
        if rank is None or not isinstance(rank, (int, float)) or rank <= 0:
            external_scores_normalized[key] = None
            continue

        norm = normalize_rank(int(rank))
        external_scores_normalized[key] = round(norm, 2)
        rankings_used.append(key)
        normalized_values.append(norm)

    if not normalized_values:
        prestige_score = None
    else:
        prestige_score = round(sum(normalized_values) / len(normalized_values), 2)

    return prestige_score, external_scores_normalized, rankings_used


def compute_meta_score(school_data: dict) -> dict[str, Any]:
    """
    Compute the meta-score combining tech, practical skills, and prestige scores.

    Weights: tech 50%, practical_skills 30%, prestige 20%.

    Normalisation formula per external ranking:
        normalized = 100 * (1 - log(rank) / log(max_rank + 1))
    where max_rank = 500.

    Missing rankings are excluded from the prestige average (not zeroed).

    Null fallback when practical_skills_score is None:
        meta_score = (tech_score * 0.625) + (prestige_score * 0.375)

    Returns a dict with:
        meta_score                  float | None
        prestige_score              float | None
        practical_skills_score      float | None
        external_scores_normalized  dict[str, float | None]
        rankings_used               list[str]
    """
    prestige_score, external_scores_normalized, rankings_used = compute_prestige_score(school_data)

    # Tech score: use stored scores.total if available, else compute now
    stored_scores = school_data.get("scores")
    if stored_scores and stored_scores.get("total") is not None:
        tech_score = float(stored_scores["total"])
    else:
        computed = compute_tech_score(school_data)
        tech_score = float(computed["scores"]["total"])

    practical_skills_score = school_data.get("practical_skills_score")

    if prestige_score is None:
        meta_score = None
    elif practical_skills_score is not None:
        meta_score = round(
            (tech_score * 0.50) + (float(practical_skills_score) * 0.30) + (prestige_score * 0.20),
            2,
        )
    else:
        meta_score = round((tech_score * 0.625) + (prestige_score * 0.375), 2)

    return {
        "meta_score": meta_score,
        "prestige_score": prestige_score,
        "practical_skills_score": practical_skills_score,
        "external_scores_normalized": external_scores_normalized,
        "rankings_used": rankings_used,
    }
