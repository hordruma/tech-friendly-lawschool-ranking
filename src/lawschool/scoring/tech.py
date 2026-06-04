"""
src/lawschool/scoring/tech.py

Tech-friendliness scoring functions.

Each scorer takes a school dict and returns (score: float, notes: list[str]).
compute_tech_score() aggregates them using the dispatch table at the bottom.
"""

from __future__ import annotations

from typing import Any


def score_curriculum_courses(school: dict) -> tuple[float, list[str]]:
    """LegalTech / AI Courses (max 20 points). Required=2 pts, elective/certificate=1 pt."""
    notes: list[str] = []
    total = 0.0
    for course in school.get("courses") or []:
        if course.get("year_verified") is None:
            notes.append(f"UNVERIFIED (not counted): {course.get('title', '')}")
            continue
        t = course.get("type")
        title = course.get("title", "")
        if t == "required":
            total += 2
            notes.append(f"+2 required: {title}")
        elif t in ("elective", "certificate"):
            total += 1
            notes.append(f"+1 elective: {title}")
    return min(total, 20.0), notes


def score_practical_requirement(school: dict) -> tuple[float, list[str]]:
    """Practical Skills Requirement (0-10 points)."""
    notes: list[str] = []
    programs = school.get("programs") or []
    courses = school.get("courses") or []

    has_required_tech = any(
        c.get("type") == "required" and c.get("year_verified") is not None
        for c in courses
    )
    has_tech_clinic = any(
        p.get("type") == "clinic" and p.get("tech_focus") and p.get("status") == "active"
        for p in programs
    )
    has_any_clinic = any(
        p.get("type") == "clinic" and p.get("status") == "active"
        for p in programs
    )

    if has_required_tech:
        notes.append("Required tech course in curriculum.")
        return 10.0, notes
    if has_tech_clinic:
        notes.append("Active tech-focused clinic (practical component confirmed).")
        return 7.0, notes
    if has_any_clinic:
        notes.append("Active clinic found, tech focus unconfirmed.")
        return 4.0, notes
    notes.append("No formal practical technology requirement found.")
    return 0.0, notes


def score_tech_clinics(school: dict) -> tuple[float, list[str]]:
    """Tech-Integrated Clinics (0-10 points)."""
    notes: list[str] = []
    programs = school.get("programs") or []

    tech_clinics = [
        p for p in programs
        if p.get("type") == "clinic" and p.get("tech_focus") and p.get("status") == "active"
    ]
    any_clinics = [
        p for p in programs
        if p.get("type") == "clinic" and p.get("status") == "active"
    ]

    if tech_clinics:
        notes.append(f"Dedicated legaltech clinic: {tech_clinics[0].get('name')}")
        return 10.0, notes
    if any_clinics:
        notes.append(f"Active clinic (no confirmed tech focus): {any_clinics[0].get('name')}")
        return 4.0, notes
    notes.append("No active clinics found.")
    return 0.0, notes


def score_legaltech_center(school: dict) -> tuple[float, list[str]]:
    """Dedicated LegalTech Center or Institute (0-10 points)."""
    notes: list[str] = []
    programs = school.get("programs") or []

    centers = [p for p in programs if p.get("type") == "center" and p.get("tech_focus")]
    active = [c for c in centers if c.get("status") == "active"]
    unknown = [c for c in centers if c.get("status") == "unknown"]

    if active:
        c = active[0]
        notes.append(f"Active legaltech center: {c.get('name')}")
        return (10.0 if c.get("source_url") else 7.0), notes
    if unknown:
        notes.append(f"Center status unknown: {unknown[0].get('name')} — 4 pts pending verification.")
        return 4.0, notes
    notes.append("No dedicated legaltech center found.")
    return 0.0, notes


def score_joint_degrees(school: dict) -> tuple[float, list[str]]:
    """Joint Degrees with tech disciplines (0-10 points, 5 pts each)."""
    notes: list[str] = []
    tech_keywords = {
        "computer science", "cs", "data science", "information science",
        "engineering", "software", "machine learning", "ai",
        "artificial intelligence", "data", "technology", "tech",
    }
    qualifying = [
        p for p in (school.get("programs") or [])
        if p.get("type") == "joint_degree"
        and p.get("status") in ("active", None, "unknown")
        and (
            p.get("tech_focus")
            or any(kw in (p.get("name") or "").lower() or kw in (p.get("description") or "").lower()
                   for kw in tech_keywords)
        )
    ]
    for jd in qualifying:
        notes.append(f"+5 qualifying joint degree: {jd.get('name')}")
    if not qualifying:
        notes.append("No qualifying joint degrees found.")
    return float(min(len(qualifying) * 5, 10)), notes


def score_partnerships(school: dict) -> tuple[float, list[str]]:
    """Industry Partnerships (0-10 points)."""
    notes: list[str] = []
    partnerships = school.get("partnerships") or []
    documented = [p for p in partnerships if p.get("source_url") or p.get("active") is not None]
    count = max(len(documented), min(len(partnerships), 3))

    if count >= 3:
        notes.append(f"3+ partnerships documented ({len(partnerships)} total listed).")
        return 10.0, notes
    if count == 2:
        notes.append("2 partnerships documented.")
        return 7.0, notes
    if count == 1:
        notes.append("1 partnership documented.")
        return 4.0, notes
    notes.append("No partnerships documented.")
    return 0.0, notes


def score_faculty_expertise(school: dict) -> tuple[float, list[str]]:
    """Faculty with Technology Expertise (0-10 points)."""
    notes: list[str] = []
    qualifying = [
        f for f in (school.get("faculty") or [])
        if f.get("appointment_type") in {"tenure_track", "clinical", None}
        and (f.get("tech_expertise") or f.get("research_areas"))
    ]
    count = len(qualifying)
    score = 10.0 if count >= 4 else 7.0 if count == 3 else 4.0 if count == 2 else 2.0 if count == 1 else 0.0
    notes.append(f"{count} qualifying tech-expertise faculty (score: {score}).")
    for f in qualifying:
        notes.append(f"  - {f.get('name')} ({f.get('appointment_type', 'unspecified')})")
    return score, notes


def score_research_output(school: dict) -> tuple[float, list[str]]:
    """Active LegalTech Research Output (0-10 points, proxy via faculty count)."""
    notes: list[str] = []
    count = len([
        f for f in (school.get("faculty") or [])
        if f.get("tech_expertise") or f.get("research_areas")
    ])
    if count >= 4:
        notes.append(f"Proxy: {count} tech faculty → estimated 7 pts. Verify publications for final score.")
        return 7.0, notes
    if count >= 2:
        notes.append(f"Proxy: {count} tech faculty → estimated 4 pts.")
        return 4.0, notes
    if count == 1:
        notes.append("Proxy: 1 tech faculty → estimated 2 pts.")
        return 2.0, notes
    notes.append("No tech faculty — assuming 0 research output.")
    return 0.0, notes


def score_student_orgs(school: dict) -> tuple[float, list[str]]:
    """Student LegalTech Organizations (0-5 points)."""
    notes: list[str] = []
    orgs = school.get("student_orgs") or []
    verified_active = [o for o in orgs if o.get("active") is True]

    if len(verified_active) >= 2:
        notes.append(f"{len(verified_active)} verified active student orgs.")
        return 5.0, notes
    if orgs:
        notes.append(f"{len(orgs)} student org(s) listed (activity unverified) → 3 pts pending verification.")
        return 3.0, notes
    notes.append("No student legaltech organizations found.")
    return 0.0, notes


def score_career_placement(school: dict) -> tuple[float, list[str]]:
    """Career Placement in LegalTech (0-5 points)."""
    notes: list[str] = []
    legaltech_partners = [
        p for p in (school.get("partnerships") or [])
        if p.get("type") in ("legaltech_vendor", "industry")
    ]
    if legaltech_partners:
        notes.append(f"{len(legaltech_partners)} legaltech/industry partner(s) → 3 pts. Verify placement data for full score.")
        return 3.0, notes
    notes.append("No documented legaltech career focus.")
    return 0.0, notes


def score_press_release_penalty(school: dict) -> tuple[float, list[str]]:
    """Press Release Gap penalty (0 to -20 points)."""
    gaps = school.get("press_release_gap") or []
    if not gaps:
        return 0.0, ["No press release gaps documented."]

    severity_map = {"minor": -5, "moderate": -10, "major": -15, "egregious": -20}
    notes: list[str] = []
    total = 0.0
    for gap in gaps:
        p = float(
            gap["penalty_points"] if gap.get("penalty_points") is not None
            else severity_map.get(gap.get("severity", ""), -5)
        )
        notes.append(f"Gap (severity={gap.get('severity', 'unassigned')}, {p} pts): {gap.get('claimed', '')[:80]}…")
        total += p
    return max(total, -20.0), notes


_SCORERS: list[tuple[str, Any]] = [
    ("curriculum_courses",          score_curriculum_courses),
    ("curriculum_practical",        score_practical_requirement),
    ("curriculum_clinics",          score_tech_clinics),
    ("infrastructure_center",       score_legaltech_center),
    ("infrastructure_joint_degrees", score_joint_degrees),
    ("infrastructure_partnerships",  score_partnerships),
    ("faculty_expertise",           score_faculty_expertise),
    ("faculty_research",            score_research_output),
    ("community_orgs",              score_student_orgs),
    ("community_careers",           score_career_placement),
    ("press_release_gap_penalty",   score_press_release_penalty),
]


def compute_tech_score(school: dict) -> dict[str, Any]:
    """
    Compute all tech-friendliness scores for a school dict.

    Returns {"scores": {..., "total": float}, "ranking_tier": str, "scoring_notes": {...}}
    """
    scores: dict[str, float] = {}
    scoring_notes: dict[str, list[str]] = {}

    for key, fn in _SCORERS:
        scores[key], scoring_notes[key] = fn(school)

    total = sum(v for k, v in scores.items() if k != "press_release_gap_penalty")
    total += scores["press_release_gap_penalty"]
    scores["total"] = round(total, 1)

    if school.get("last_verified") is None:
        tier = "unranked"
    elif total >= 85:
        tier = "S"
    elif total >= 70:
        tier = "A"
    elif total >= 50:
        tier = "B"
    elif total >= 30:
        tier = "C"
    else:
        tier = "D"

    return {"scores": scores, "ranking_tier": tier, "scoring_notes": scoring_notes}
