"""
src/lawschool/scoring/__init__.py

Public exports for the scoring subpackage.

Exported names
--------------
compute_tech_score(school: dict) -> dict
    Full tech-friendliness score with sub-scores, tier, and notes.

compute_practical_score(school: dict) -> dict
    Full practical skills score (0-100) with sub-score breakdown.

compute_meta_score(school: dict) -> dict
    Meta-score combining tech, practical, and prestige.

score_school(school: dict) -> ScoreBreakdown
    Convenience wrapper: computes all three and returns a ScoreBreakdown.
"""

from lawschool.scoring.meta import compute_meta_score
from lawschool.scoring.practical import compute_practical_score
from lawschool.scoring.tech import compute_tech_score
from lawschool.schema import ScoreBreakdown


def score_school(school) -> ScoreBreakdown:
    """
    Compute all three score dimensions and return a ScoreBreakdown.

    Accepts either a LawSchool Pydantic model or a plain dict.
    Respects already-stored scores (does not recompute if 'scores.total' is set).
    """
    # Normalise to dict so all sub-scorers can use .get() uniformly
    if hasattr(school, "model_dump"):
        school = school.model_dump(mode="json")

    # Tech
    stored = school.get("scores") or {}
    if stored.get("total") is not None:
        tech = float(stored["total"])
        tier = school.get("ranking_tier") or "unranked"
    else:
        tech_result = compute_tech_score(school)
        tech = float(tech_result["scores"]["total"])
        tier = tech_result["ranking_tier"]

    # Practical
    if school.get("practical_skills_score") is not None:
        practical = float(school["practical_skills_score"])
    else:
        ps_result = compute_practical_score(school)
        practical = float(ps_result["practical_skills_score"])

    # Meta (includes prestige)
    enriched = dict(school)
    if enriched.get("scores") is None or enriched["scores"].get("total") is None:
        enriched["scores"] = {"total": tech}
    if enriched.get("practical_skills_score") is None:
        enriched["practical_skills_score"] = practical

    meta_result = compute_meta_score(enriched)

    return ScoreBreakdown(
        tech=tech,
        practical=practical,
        prestige=meta_result.get("prestige_score"),
        meta=meta_result.get("meta_score"),
        tier=tier,
    )


__all__ = [
    "compute_tech_score",
    "compute_practical_score",
    "compute_meta_score",
    "score_school",
]
