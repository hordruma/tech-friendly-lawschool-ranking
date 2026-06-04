"""
src/lawschool/scoring/tech.py

Tech-friendliness scoring functions.

Each function takes a school dict and returns (score: float, notes: list[str]).
compute_tech_score() aggregates them into the full tech score result dict.
"""

from __future__ import annotations

from typing import Any


def score_curriculum(school: dict) -> tuple[float, list[str]]:
    """
    LegalTech / AI Courses (max 20 points).
    Required course = 2 pts, elective/certificate = 1 pt.
    Unverified courses (year_verified=None) are skipped.
    """
    notes: list[str] = []
    total = 0.0
    courses = school.get("courses") or []

    for course in courses:
        course_type = course.get("type")
        title = course.get("title", "")
        year = course.get("year_verified")

        if year is None:
            notes.append(f"UNVERIFIED (not counted): {title}")
            continue

        if course_type == "required":
            total += 2
            notes.append(f"+2 required: {title}")
        elif course_type in ("elective", "certificate"):
            total += 1
            notes.append(f"+1 elective: {title}")

    total = min(total, 20.0)
    return total, notes


def score_infrastructure(school: dict) -> tuple[float, list[str]]:
    """
    Practical Skills Requirement (0-10 points).
    10 pts: formal required practical tech component
    7 pts: strongly encouraged with dedicated tech content
    4 pts: practical requirement exists but tech content is incidental
    0 pts: no formal practical tech requirement
    """
    notes: list[str] = []
    programs = school.get("programs") or []
    courses = school.get("courses") or []

    has_required_tech_course = any(
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

    if has_required_tech_course:
        notes.append("Required tech course found in curriculum.")
        return 10.0, notes

    if has_tech_clinic:
        notes.append("Active tech-focused clinic found (counts as 7 pts, practical component exists).")
        return 7.0, notes

    if has_any_clinic:
        notes.append("Active clinic found but tech focus not confirmed (4 pts).")
        return 4.0, notes

    notes.append("No formal practical technology requirement found.")
    return 0.0, notes


def score_faculty_research(school: dict) -> tuple[float, list[str]]:
    """
    Tech-Integrated Clinics (0-10 points).
    10 pts: dedicated legaltech clinic with verified enrollment
    7 pts: established clinic with technology as primary component
    4 pts: traditional clinic with documented tech integration
    0 pts: none
    """
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

    if len(tech_clinics) >= 1:
        notes.append(f"Dedicated legaltech clinic: {tech_clinics[0].get('name')}")
        return 10.0, notes

    if len(any_clinics) >= 1:
        notes.append(f"Active clinic (no confirmed tech focus): {any_clinics[0].get('name')}")
        return 4.0, notes

    notes.append("No active clinics found.")
    return 0.0, notes


def score_community(school: dict) -> tuple[float, list[str]]:
    """
    Dedicated LegalTech Center or Institute (0-10 points).
    10 pts: active center with staff, space, programming, web presence
    7 pts: active center with partial evidence
    4 pts: named center with limited activity
    0 pts: none
    """
    notes: list[str] = []
    programs = school.get("programs") or []

    centers = [
        p for p in programs
        if p.get("type") == "center" and p.get("tech_focus")
    ]

    active_centers = [c for c in centers if c.get("status") == "active"]
    unknown_centers = [c for c in centers if c.get("status") == "unknown"]

    if active_centers:
        c = active_centers[0]
        notes.append(f"Active legaltech center: {c.get('name')}")
        if c.get("source_url"):
            return 10.0, notes
        notes.append("Center active but source URL missing — awarding 7 pts.")
        return 7.0, notes

    if unknown_centers:
        c = unknown_centers[0]
        notes.append(f"Center status unknown: {c.get('name')} — awarding 4 pts pending verification.")
        return 4.0, notes

    notes.append("No dedicated legaltech center found.")
    return 0.0, notes


def _score_infrastructure_joint_degrees(school: dict) -> tuple[float, list[str]]:
    """Joint Degrees (0-10 points, 5 pts each). Internal helper."""
    notes: list[str] = []
    programs = school.get("programs") or []

    qualifying_keywords = [
        "computer science", "cs", "data science", "information science",
        "engineering", "software", "machine learning", "ai", "artificial intelligence",
        "data", "technology", "tech"
    ]

    joint_degrees = [
        p for p in programs
        if p.get("type") == "joint_degree" and p.get("status") in ("active", None, "unknown")
    ]

    qualifying = []
    for jd in joint_degrees:
        name_lower = (jd.get("name") or "").lower()
        desc_lower = (jd.get("description") or "").lower()
        if any(kw in name_lower or kw in desc_lower for kw in qualifying_keywords) or jd.get("tech_focus"):
            qualifying.append(jd)

    score = min(len(qualifying) * 5, 10)
    for jd in qualifying:
        notes.append(f"+5 qualifying joint degree: {jd.get('name')}")

    if not qualifying:
        notes.append("No qualifying joint degrees found.")

    return float(score), notes


def _score_infrastructure_partnerships(school: dict) -> tuple[float, list[str]]:
    """Industry Partnerships (0-10 points). Internal helper."""
    notes: list[str] = []
    partnerships = school.get("partnerships") or []

    documented = [p for p in partnerships if p.get("source_url") or p.get("active") is not None]
    any_listed = len(partnerships)

    count = max(len(documented), min(any_listed, 3))

    if count >= 3:
        notes.append(f"3+ partnerships documented ({any_listed} total listed).")
        return 10.0, notes
    elif count == 2:
        notes.append("2 partnerships documented.")
        return 7.0, notes
    elif count == 1:
        notes.append("1 partnership documented.")
        return 4.0, notes
    else:
        notes.append("No partnerships documented.")
        return 0.0, notes


def _score_faculty_expertise(school: dict) -> tuple[float, list[str]]:
    """Faculty with Technology Expertise (0-10 points). Internal helper."""
    notes: list[str] = []
    faculty = school.get("faculty") or []

    qualifying_types = {"tenure_track", "clinical", None}

    qualifying = [
        f for f in faculty
        if f.get("appointment_type") in qualifying_types
        and (f.get("tech_expertise") or f.get("research_areas"))
    ]

    count = len(qualifying)
    if count >= 4:
        score = 10.0
    elif count == 3:
        score = 7.0
    elif count == 2:
        score = 4.0
    elif count == 1:
        score = 2.0
    else:
        score = 0.0

    notes.append(f"{count} qualifying tech-expertise faculty found (score: {score}).")
    for f in qualifying:
        notes.append(f"  - {f.get('name')} ({f.get('appointment_type', 'unspecified')})")

    return score, notes


def _score_faculty_research_output(school: dict) -> tuple[float, list[str]]:
    """Active LegalTech Research Output (0-10 points). Proxy scoring. Internal helper."""
    notes: list[str] = []
    faculty = school.get("faculty") or []

    tech_faculty_count = len([
        f for f in faculty
        if (f.get("tech_expertise") or f.get("research_areas"))
    ])

    if tech_faculty_count >= 4:
        score = 7.0
        notes.append(f"Proxy: {tech_faculty_count} tech faculty → estimated 7 pts. Verify publication count for final score.")
    elif tech_faculty_count >= 2:
        score = 4.0
        notes.append(f"Proxy: {tech_faculty_count} tech faculty → estimated 4 pts. Verify publication count.")
    elif tech_faculty_count == 1:
        score = 2.0
        notes.append("Proxy: 1 tech faculty → estimated 2 pts. Verify publication count.")
    else:
        score = 0.0
        notes.append("No tech faculty found — assuming 0 research output.")

    return score, notes


def _score_community_orgs(school: dict) -> tuple[float, list[str]]:
    """Student LegalTech Organizations (0-5 points). Internal helper."""
    notes: list[str] = []
    orgs = school.get("student_orgs") or []

    verified_active = [o for o in orgs if o.get("active") is True]

    if len(verified_active) >= 2:
        notes.append(f"{len(verified_active)} verified active student orgs.")
        return 5.0, notes
    elif len(orgs) >= 2:
        notes.append(f"{len(orgs)} student orgs listed (activity unverified) → 3 pts pending verification.")
        return 3.0, notes
    elif len(orgs) == 1:
        notes.append("1 student org listed → 3 pts pending verification.")
        return 3.0, notes
    else:
        notes.append("No student legaltech organizations found.")
        return 0.0, notes


def _score_community_careers(school: dict) -> tuple[float, list[str]]:
    """Career Placement in LegalTech (0-5 points). Internal helper."""
    notes: list[str] = []
    partnerships = school.get("partnerships") or []

    legaltech_partners = [
        p for p in partnerships
        if p.get("type") in ("legaltech_vendor", "industry")
    ]

    if len(legaltech_partners) >= 2:
        notes.append("Multiple legaltech/industry partners suggest career placement → 3 pts. Verify placement data for full score.")
        return 3.0, notes
    elif len(legaltech_partners) == 1:
        notes.append("One legaltech/industry partner → 3 pts (anecdotal, pending verification).")
        return 3.0, notes
    else:
        notes.append("No documented legaltech career focus. Needs agent verification.")
        return 0.0, notes


def _score_press_release_gap_penalty(school: dict) -> tuple[float, list[str]]:
    """Press Release Gap penalty (0 to -20 points)."""
    notes: list[str] = []
    gaps = school.get("press_release_gap") or []

    if not gaps:
        return 0.0, ["No press release gaps documented."]

    total_penalty = 0.0
    severity_map = {
        "minor": -5,
        "moderate": -10,
        "major": -15,
        "egregious": -20,
    }

    for gap in gaps:
        if gap.get("penalty_points") is not None:
            p = float(gap["penalty_points"])
        elif gap.get("severity"):
            p = float(severity_map.get(gap["severity"], -5))
        else:
            p = -5.0
            notes.append(f"Unscored gap: {gap.get('claimed', '')[:80]}… → applying provisional -5 pts.")
            total_penalty += p
            continue

        notes.append(f"Gap (severity={gap.get('severity', 'unassigned')}, {p} pts): {gap.get('claimed', '')[:80]}…")
        total_penalty += p

    total_penalty = max(total_penalty, -20.0)
    return total_penalty, notes


def compute_tech_score(school: dict) -> dict[str, Any]:
    """
    Compute all tech-friendliness scores for a school dict.

    Returns a dict with:
        scores          dict of sub-scores including 'total'
        ranking_tier    str
        scoring_notes   dict of note lists per dimension
    """
    funcs = [
        ("curriculum_courses",          score_curriculum),
        ("curriculum_practical",         score_infrastructure),
        ("curriculum_clinics",           score_faculty_research),
        ("infrastructure_center",        score_community),
        ("infrastructure_joint_degrees", _score_infrastructure_joint_degrees),
        ("infrastructure_partnerships",  _score_infrastructure_partnerships),
        ("faculty_expertise",            _score_faculty_expertise),
        ("faculty_research",             _score_faculty_research_output),
        ("community_orgs",               _score_community_orgs),
        ("community_careers",            _score_community_careers),
        ("press_release_gap_penalty",    _score_press_release_gap_penalty),
    ]

    scoring_notes: dict[str, list[str]] = {}
    scores: dict[str, float] = {}

    for key, fn in funcs:
        score, notes = fn(school)
        scores[key] = score
        scoring_notes[key] = notes

    total = sum(
        v for k, v in scores.items()
        if k != "press_release_gap_penalty"
    ) + scores["press_release_gap_penalty"]

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

    return {
        "scores": scores,
        "ranking_tier": tier,
        "scoring_notes": scoring_notes,
    }
