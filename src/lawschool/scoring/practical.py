"""
src/lawschool/scoring/practical.py

Practical skills scoring functions.

Each sub-scorer returns (score: float, notes: list[str]).
compute_practical_score() aggregates all four sub-scores.
"""

from __future__ import annotations

from typing import Any


def score_clinical(school: dict) -> tuple[float, list[str]]:
    """
    Clinical Programs sub-score (0-25 points).

    Each distinct live-client clinic: 4 pts (max 20).
    Required clinical participation: +5 bonus.
    """
    notes: list[str] = []
    programs = school.get("programs") or []

    clinics = [
        p for p in programs
        if p.get("type") == "clinic" and p.get("status") == "active"
        and p.get("practical_focus") is not False
    ]

    clinic_pts = min(len(clinics) * 4, 20)
    for c in clinics:
        notes.append(f"+4 live-client clinic: {c.get('name')}")

    required_bonus = 0
    if any(
        p.get("type") == "clinic" and p.get("status") == "active"
        and "required" in (p.get("notes") or "").lower()
        for p in programs
    ):
        required_bonus = 5
        notes.append("+5 bonus: required clinical participation")

    total = min(clinic_pts + required_bonus, 25)
    if not clinics:
        notes.append("No active live-client clinics found.")

    return total, notes


def score_skills_curriculum(school: dict) -> tuple[float, list[str]]:
    """
    Skills Curriculum sub-score (0-25 points).

    Required skills/simulation courses: 3 pts each (max 15).
    Moot court / negotiation / advocacy programs: 2 pts each (max 10).
    """
    notes: list[str] = []
    programs = school.get("programs") or []
    courses = school.get("courses") or []

    skills_keywords = [
        "negotiat", "advocacy", "lawyering", "simulation", "drafting",
        "writing", "counseling", "trial", "moot", "practical",
    ]

    required_skills = [
        c for c in courses
        if c.get("type") == "required"
        and c.get("year_verified") is not None
        and any(kw in (c.get("title") or "").lower() for kw in skills_keywords)
    ]
    skills_pts = min(len(required_skills) * 3, 15)
    for c in required_skills:
        notes.append(f"+3 required skills course: {c.get('title')}")

    advocacy_keywords = ["moot", "negotiat", "advocacy", "competition", "trial team"]
    advocacy_programs = [
        p for p in programs
        if p.get("type") in ("competition", "other")
        and any(
            kw in (p.get("name") or "").lower() or kw in (p.get("description") or "").lower()
            for kw in advocacy_keywords
        )
        and p.get("status") in ("active", "unknown")
    ]
    advocacy_pts = min(len(advocacy_programs) * 2, 10)
    for p in advocacy_programs:
        notes.append(f"+2 advocacy/moot program: {p.get('name')}")

    total = min(skills_pts + advocacy_pts, 25)

    if not required_skills and not advocacy_programs:
        notes.append("No required skills courses or advocacy programs found.")

    return total, notes


def score_placements(school: dict) -> tuple[float, list[str]]:
    """
    Experiential Placements sub-score (0-25 points).

    Structured externship program: up to 15 pts.
    Field placement / co-op programs: up to 10 pts.
    """
    notes: list[str] = []
    programs = school.get("programs") or []

    externship_keywords = ["externship", "extern", "practicum"]
    coop_keywords = ["co-op", "coop", "field placement", "field work", "residency"]

    externships = [
        p for p in programs
        if any(
            kw in (p.get("name") or "").lower() or kw in (p.get("description") or "").lower()
            for kw in externship_keywords
        )
        and p.get("status") in ("active", "unknown")
    ]
    coops = [
        p for p in programs
        if any(
            kw in (p.get("name") or "").lower() or kw in (p.get("description") or "").lower()
            for kw in coop_keywords
        )
        and p.get("status") in ("active", "unknown")
    ]

    ext_pts = 0
    if externships:
        if len(externships) >= 2 or all(p.get("source_url") for p in externships):
            ext_pts = 15
            notes.append(f"Comprehensive externship program ({len(externships)} track(s)) → 15 pts.")
        else:
            ext_pts = 10
            notes.append("Structured externship (limited evidence) → 10 pts.")

    coop_pts = 0
    if coops:
        if any(p.get("source_url") for p in coops):
            coop_pts = 10
            notes.append("Dedicated field placement/co-op program → 10 pts.")
        else:
            coop_pts = 5
            notes.append("Field placement opportunities (limited documentation) → 5 pts.")

    total = min(ext_pts + coop_pts, 25)

    if not externships and not coops:
        notes.append("No externship or field placement programs found.")

    return total, notes


def score_professional_readiness(school: dict) -> tuple[float, list[str]]:
    """
    Professional Readiness sub-score (0-25 points).

    Pro bono requirement: mandatory 10 pts; encouraged 5 pts.
    Bar passage support / skills bridge: up to 8 pts.
    Career integration (employer partnerships for practical skills): up to 7 pts.
    """
    notes: list[str] = []
    programs = school.get("programs") or []
    partnerships = school.get("partnerships") or []
    school_notes_lower = (school.get("notes") or "").lower()

    probono_pts = 0
    mandatory_kw = ["pro bono requirement", "mandatory pro bono", "required pro bono"]
    encouraged_kw = ["pro bono", "public service"]
    if any(kw in school_notes_lower for kw in mandatory_kw):
        probono_pts = 10
        notes.append("+10: mandatory pro bono requirement (verify with source).")
    elif any(kw in school_notes_lower for kw in encouraged_kw):
        probono_pts = 5
        notes.append("+5: pro bono program encouraged (verify mandatory status).")

    bar_pts = 0
    bar_kw = ["bar prep", "bar bridge", "bar passage", "bar exam", "skills bridge"]
    has_bar = any(
        any(kw in (p.get("name") or "").lower() or kw in (p.get("description") or "").lower()
            for kw in bar_kw)
        for p in programs
    )
    if has_bar:
        bar_pts = 8
        notes.append("+8: bar passage support / skills bridge program found.")

    career_pts = 0
    practical_types = {"legaltech_vendor", "industry", "government"}
    practical_partners = [p for p in partnerships if p.get("type") in practical_types]
    if len(practical_partners) >= 2:
        career_pts = 7
        notes.append(f"+7: {len(practical_partners)} employer partnerships for practical skills.")
    elif len(practical_partners) == 1:
        career_pts = 3
        notes.append("+3: 1 employer partnership (limited career integration).")

    total = min(probono_pts + bar_pts + career_pts, 25)
    if not probono_pts and not bar_pts and not career_pts:
        notes.append("No pro bono requirement, bar support, or employer partnerships found.")

    return total, notes


def compute_practical_score(school: dict) -> dict[str, Any]:
    """
    Compute the full practical skills score (0-100) with sub-score breakdown.

    Returns a dict with:
        practical_skills_score  float
        breakdown               dict[str, float]
        scoring_notes           dict[str, list[str]]
    """
    clinical, clinical_notes = score_clinical(school)
    curriculum, curriculum_notes = score_skills_curriculum(school)
    placements, placements_notes = score_placements(school)
    readiness, readiness_notes = score_professional_readiness(school)

    total = round(clinical + curriculum + placements + readiness, 1)

    return {
        "practical_skills_score": total,
        "breakdown": {
            "clinical_programs": clinical,
            "skills_curriculum": curriculum,
            "experiential_placements": placements,
            "professional_readiness": readiness,
        },
        "scoring_notes": {
            "clinical_programs": clinical_notes,
            "skills_curriculum": curriculum_notes,
            "experiential_placements": placements_notes,
            "professional_readiness": readiness_notes,
        },
    }
