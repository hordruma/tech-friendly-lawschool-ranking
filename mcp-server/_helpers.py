"""
mcp-server/_helpers.py

Shared helpers used by tool modules: filtering, sorting, and text-rendering
of school data.  Not part of the public MCP API.
"""

from __future__ import annotations

from lawschool.schema import COUNTRY_TO_REGION, LawSchool

_VALID_REGIONS = frozenset(
    {
        "North America",
        "UK & Ireland",
        "Europe",
        "Asia-Pacific",
        "Latin America",
        "Middle East & Africa",
    }
)

_VALID_TIERS = frozenset({"S", "A", "B", "C", "D"})

_VALID_SORT = frozenset(
    {"meta_score", "tech_score", "practical_score", "prestige_score"}
)


def infer_region(school: LawSchool) -> str | None:
    """Infer region from country code via the canonical mapping."""
    return COUNTRY_TO_REGION.get(school.country or "", None)


def _infer_region_dict(school: dict) -> str | None:
    return COUNTRY_TO_REGION.get(school.get("country", ""), None)


def prg_warning(school: LawSchool) -> str:
    """Return a formatted press-release-gap warning block, or empty string."""
    gaps = school.press_release_gap or []
    if not gaps:
        return ""
    lines = ["\n  *** PRESS RELEASE GAP WARNING ***"]
    for g in gaps:
        severity = (g.severity or "unassigned").upper()
        claimed = (g.claimed or "")[:120]
        reality = (g.reality or "Not yet documented")[:120]
        lines.append(f"  Severity: {severity}")
        lines.append(f"  Claimed:  {claimed}")
        lines.append(f"  Reality:  {reality}")
        if g.penalty_points is not None:
            lines.append(f"  Penalty:  {g.penalty_points} points")
    lines.append("  *** END WARNING ***")
    return "\n".join(lines)


def school_summary_text(school: LawSchool, rank: int | None = None) -> str:
    """One-paragraph summary of a school suitable for list display."""
    tech = school.scores.total if school.scores else None
    practical = school.practical_skills_score
    meta = school.meta_score
    tier = school.ranking_tier or "unranked"
    last_verified = school.last_verified or "never verified"
    country = school.country or "??"
    region = infer_region(school) or "unknown region"

    ai_courses = [
        c for c in (school.courses or [])
        if any(
            t in (c.topics or [])
            for t in ("artificial_intelligence", "machine_learning", "legal_technology")
        )
        and c.year_verified is not None
    ]
    tech_clinics = [
        p for p in (school.programs or [])
        if p.type == "clinic" and p.tech_focus and p.status == "active"
    ]
    joint_degrees = [
        p for p in (school.programs or [])
        if p.type == "joint_degree" and p.status in ("active", None)
    ]

    rank_str = f"#{rank}  " if rank is not None else ""
    lines = [
        f"{rank_str}{school.name or school.id} ({country}, {region})",
        f"  Tier: {tier}  |  Tech Score: {tech if tech is not None else 'n/a'}/100"
        f"  |  Practical: {practical if practical is not None else 'n/a'}/100"
        f"  |  Meta Score: {meta if meta is not None else 'n/a'}/100",
        f"  Data status: last verified {last_verified}",
    ]
    if ai_courses:
        lines.append(f"  Verified AI/tech courses: {len(ai_courses)}")
    if tech_clinics:
        lines.append(f"  Tech clinic(s): {', '.join(c.name or '' for c in tech_clinics[:2])}")
    if joint_degrees:
        lines.append(f"  Joint degrees: {len(joint_degrees)} available")
    prg = prg_warning(school)
    if prg:
        lines.append(prg)
    return "\n".join(lines)


def filter_schools(
    schools: list[LawSchool],
    region: str | None = None,
    country: str | None = None,
    min_tech_score: int | None = None,
    min_practical_score: int | None = None,
    requires_ai_course: bool | None = None,
    has_legaltech_clinic: bool | None = None,
    joint_degree_available: bool | None = None,
    tier: str | None = None,
) -> list[LawSchool]:
    """Apply filter parameters and return matching schools."""
    result = []
    for s in schools:
        tech = s.scores.total if s.scores else None
        practical = s.practical_skills_score

        if region is not None:
            if infer_region(s) != region:
                continue

        if country is not None:
            if (s.country or "").upper() != country.upper():
                continue

        if min_tech_score is not None:
            if tech is None or tech < min_tech_score:
                continue

        if min_practical_score is not None:
            if practical is None or practical < min_practical_score:
                continue

        if requires_ai_course is True:
            ai_topics = {"artificial_intelligence", "machine_learning", "legal_technology"}
            has_ai = any(
                any(t in (c.topics or []) for t in ai_topics)
                and c.year_verified is not None
                for c in (s.courses or [])
            )
            if not has_ai:
                continue

        if has_legaltech_clinic is True:
            has_clinic = any(
                p.type == "clinic" and p.tech_focus and p.status == "active"
                for p in (s.programs or [])
            )
            if not has_clinic:
                continue

        if joint_degree_available is True:
            has_jd = any(
                p.type == "joint_degree" and p.status in ("active", None)
                for p in (s.programs or [])
            )
            if not has_jd:
                continue

        if tier is not None:
            if (s.ranking_tier or "").upper() != tier.upper():
                continue

        result.append(s)

    return result


def sort_schools(schools: list[LawSchool], sort_by: str = "meta_score") -> list[LawSchool]:
    """Sort schools by the requested score dimension."""

    def key_fn(s: LawSchool) -> tuple:
        tech = s.scores.total if s.scores else None
        if sort_by == "tech_score":
            v = tech
        elif sort_by == "practical_score":
            v = s.practical_skills_score
        elif sort_by == "prestige_score":
            v = getattr(s, "prestige_score", None)
        else:  # meta_score (default)
            v = s.meta_score
            if v is None:
                return (1, -(tech or 0))
        return (0 if v is not None else 1, -(v or 0))

    return sorted(schools, key=key_fn)
