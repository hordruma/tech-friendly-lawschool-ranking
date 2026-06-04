#!/usr/bin/env python3
"""
agents/scorer.py

Scoring logic: takes a school JSON file and computes scores per criteria
defined in CRITERIA.md.

Usage:
    python scorer.py data/schools/harvard-law.json
    python scorer.py data/schools/harvard-law.json --output data/schools/harvard-law.json
    python scorer.py data/schools/harvard-law.json --format json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent


# ──────────────────────────────────────────────
# Scoring functions
# ──────────────────────────────────────────────

def score_curriculum_courses(school: dict) -> tuple[float, list[str]]:
    """
    LegalTech / AI Courses (max 20 points)
    Required course = 2 pts, elective/certificate = 1 pt
    """
    notes = []
    total = 0.0
    courses = school.get("courses") or []

    for course in courses:
        course_type = course.get("type")
        title = course.get("title", "")
        year = course.get("year_verified")

        # Skip courses with no year_verified — flag them
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


def score_curriculum_practical(school: dict) -> tuple[float, list[str]]:
    """
    Practical Skills Requirement (0–10 points)
    10 pts: formal required practical tech component
    7 pts: strongly encouraged with dedicated tech content
    4 pts: practical requirement exists but tech content is incidental
    0 pts: no formal practical tech requirement
    """
    notes = []

    programs = school.get("programs") or []
    courses = school.get("courses") or []

    # Look for clinics or programs that are required
    has_required_tech_course = any(
        c.get("type") == "required" and c.get("year_verified") is not None
        for c in courses
    )

    has_tech_clinic = any(
        p.get("type") == "clinic" and p.get("tech_focus") and p.get("status") == "active"
        for p in programs
    )

    has_any_clinic = any(p.get("type") == "clinic" and p.get("status") == "active" for p in programs)

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


def score_curriculum_clinics(school: dict) -> tuple[float, list[str]]:
    """
    Tech-Integrated Clinics (0–10 points)
    10 pts: dedicated legaltech clinic with verified enrollment
    7 pts: established clinic with technology as primary component
    4 pts: traditional clinic with documented tech integration
    0 pts: none
    """
    notes = []
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


def score_infrastructure_center(school: dict) -> tuple[float, list[str]]:
    """
    Dedicated LegalTech Center or Institute (0–10 points)
    10 pts: active center with staff, space, programming, web presence
    7 pts: active center with partial evidence
    4 pts: named center with limited activity
    0 pts: none
    """
    notes = []
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
        # Full 10 pts if has source URL (evidence of web presence)
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


def score_infrastructure_joint_degrees(school: dict) -> tuple[float, list[str]]:
    """
    Joint Degrees (0–10 points, 5 pts each)
    Qualifying: JD/CS, JD/Data Science, JD/InfoSci, JD/Engineering, JD/MBA+tech
    """
    notes = []
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


def score_infrastructure_partnerships(school: dict) -> tuple[float, list[str]]:
    """
    Industry Partnerships (0–10 points)
    10 pts: 3+ documented active partnerships
    7 pts: 2 documented partnerships
    4 pts: 1 documented partnership
    0 pts: none
    """
    notes = []
    partnerships = school.get("partnerships") or []

    # Count partnerships with source URLs as more credible
    documented = [p for p in partnerships if p.get("source_url") or p.get("active") is not None]
    any_listed = len(partnerships)

    count = max(len(documented), min(any_listed, 3))  # use documented count, cap any_listed at 3

    if count >= 3:
        notes.append(f"3+ partnerships documented ({any_listed} total listed).")
        return 10.0, notes
    elif count == 2:
        notes.append(f"2 partnerships documented.")
        return 7.0, notes
    elif count == 1:
        notes.append(f"1 partnership documented.")
        return 4.0, notes
    else:
        notes.append("No partnerships documented.")
        return 0.0, notes


def score_faculty_expertise(school: dict) -> tuple[float, list[str]]:
    """
    Faculty with Technology Expertise (0–10 points)
    10 pts: 4+ faculty; 7 pts: 3; 4 pts: 2; 2 pts: 1; 0 pts: none
    Adjunct/practitioner faculty excluded (unless substantial appointment)
    """
    notes = []
    faculty = school.get("faculty") or []

    qualifying_types = {"tenure_track", "clinical", None}  # visiting can count with caveats

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


def score_faculty_research(school: dict) -> tuple[float, list[str]]:
    """
    Active LegalTech Research Output (0–10 points)
    Inferred from faculty count and programs — a full score requires
    agent-researched publication data. Without it, we estimate conservatively.

    10 pts: 5+ verified outputs (needs agent data)
    7 pts: 3–4 verified outputs
    4 pts: 1–2 verified outputs
    0 pts: none

    Without agent-verified publication data, this scores based on faculty count
    as a proxy (conservative estimate).
    """
    notes = []
    faculty = school.get("faculty") or []

    tech_faculty_count = len([
        f for f in faculty
        if (f.get("tech_expertise") or f.get("research_areas"))
    ])

    # Conservative proxy scoring without publication data
    if tech_faculty_count >= 4:
        score = 7.0
        notes.append(f"Proxy: {tech_faculty_count} tech faculty → estimated 7 pts. Verify publication count for final score.")
    elif tech_faculty_count >= 2:
        score = 4.0
        notes.append(f"Proxy: {tech_faculty_count} tech faculty → estimated 4 pts. Verify publication count.")
    elif tech_faculty_count == 1:
        score = 2.0
        notes.append(f"Proxy: 1 tech faculty → estimated 2 pts. Verify publication count.")
    else:
        score = 0.0
        notes.append("No tech faculty found — assuming 0 research output.")

    return score, notes


def score_community_orgs(school: dict) -> tuple[float, list[str]]:
    """
    Student LegalTech Organizations (0–5 points)
    5 pts: 2+ active orgs; 3 pts: 1 active org; 0 pts: none
    """
    notes = []
    orgs = school.get("student_orgs") or []

    active_orgs = [o for o in orgs if o.get("active") or o.get("active") is None]  # treat unknown as potentially active
    verified_active = [o for o in orgs if o.get("active") is True]

    if len(verified_active) >= 2:
        notes.append(f"{len(verified_active)} verified active student orgs.")
        return 5.0, notes
    elif len(orgs) >= 2:
        notes.append(f"{len(orgs)} student orgs listed (activity unverified) → 3 pts pending verification.")
        return 3.0, notes
    elif len(orgs) == 1:
        notes.append(f"1 student org listed → 3 pts pending verification.")
        return 3.0, notes
    else:
        notes.append("No student legaltech organizations found.")
        return 0.0, notes


def score_community_careers(school: dict) -> tuple[float, list[str]]:
    """
    Career Placement in LegalTech (0–5 points)
    Inferred from partnerships with legaltech companies; needs agent data for full scoring.
    """
    notes = []
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


def score_press_release_gap(school: dict) -> tuple[float, list[str]]:
    """
    Press Release Gap penalty (0 to -20 points)
    Based on documented gaps in press_release_gap array.
    """
    notes = []
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
        # If a specific penalty is set, use it
        if gap.get("penalty_points") is not None:
            p = float(gap["penalty_points"])
        elif gap.get("severity"):
            p = float(severity_map.get(gap["severity"], -5))
        else:
            # Unscored gap — flag but apply minimal penalty
            p = -5.0
            notes.append(f"Unscored gap: {gap.get('claimed', '')[:80]}… → applying provisional -5 pts.")
            total_penalty += p
            continue

        notes.append(f"Gap (severity={gap.get('severity', 'unassigned')}, {p} pts): {gap.get('claimed', '')[:80]}…")
        total_penalty += p

    total_penalty = max(total_penalty, -20.0)  # floor at -20
    return total_penalty, notes


def compute_scores(school: dict) -> dict[str, Any]:
    """Compute all scores for a school dict. Returns a scores dict with breakdown and notes."""
    results = {}

    funcs = [
        ("curriculum_courses",         score_curriculum_courses),
        ("curriculum_practical",        score_curriculum_practical),
        ("curriculum_clinics",          score_curriculum_clinics),
        ("infrastructure_center",       score_infrastructure_center),
        ("infrastructure_joint_degrees",score_infrastructure_joint_degrees),
        ("infrastructure_partnerships", score_infrastructure_partnerships),
        ("faculty_expertise",           score_faculty_expertise),
        ("faculty_research",            score_faculty_research),
        ("community_orgs",              score_community_orgs),
        ("community_careers",           score_community_careers),
        ("press_release_gap_penalty",   score_press_release_gap),
    ]

    scoring_notes = {}
    scores = {}

    for key, fn in funcs:
        score, notes = fn(school)
        scores[key] = score
        scoring_notes[key] = notes

    total = sum(
        v for k, v in scores.items()
        if k != "press_release_gap_penalty"
    ) + scores["press_release_gap_penalty"]

    scores["total"] = round(total, 1)

    # Determine tier
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


def compute_meta_score(school_data: dict) -> dict[str, Any]:
    """
    Compute the meta-score combining tech score and prestige score from external rankings.

    Normalization formula per external ranking:
        normalized = 100 * (1 - log(rank) / log(max_rank + 1))
    where max_rank = 500.

    Missing rankings are excluded from the prestige average (not zeroed).
    Meta score = (tech_score * 0.5) + (prestige_score * 0.5).

    Returns a dict with:
        meta_score               float | None
        prestige_score           float | None
        external_scores_normalized  dict[str, float | None]
        rankings_used            list[str]
    """
    MAX_RANK = 500
    LOG_MAX = math.log(MAX_RANK + 1)

    RANKING_KEYS = ["qs_law", "the_law", "arwu_law", "usnews_law", "usnews_global_law", "vault_law"]

    external_rankings = school_data.get("external_rankings") or {}

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

        rank = int(rank)
        if rank > MAX_RANK:
            # Rank beyond ceiling → score = 0
            norm = 0.0
        else:
            norm = 100.0 * (1.0 - math.log(rank) / LOG_MAX)
            norm = max(0.0, min(100.0, norm))

        external_scores_normalized[key] = round(norm, 2)
        rankings_used.append(key)
        normalized_values.append(norm)

    if not normalized_values:
        prestige_score = None
    else:
        prestige_score = round(sum(normalized_values) / len(normalized_values), 2)

    # Tech score: use stored scores.total if available, else compute now
    stored_scores = school_data.get("scores")
    if stored_scores and stored_scores.get("total") is not None:
        tech_score = float(stored_scores["total"])
    else:
        computed = compute_scores(school_data)
        tech_score = float(computed["scores"]["total"])

    if prestige_score is None:
        meta_score = None
    else:
        meta_score = round((tech_score * 0.5) + (prestige_score * 0.5), 2)

    return {
        "meta_score": meta_score,
        "prestige_score": prestige_score,
        "external_scores_normalized": external_scores_normalized,
        "rankings_used": rankings_used,
    }


def tier_color(tier: str) -> str:
    return {
        "S": "bold magenta",
        "A": "bold green",
        "B": "bold yellow",
        "C": "bold orange3",
        "D": "bold red",
        "unranked": "dim",
    }.get(tier, "white")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Write updated JSON to this path (overwrites in-place if same as input)")
@click.option("--format", "output_format", type=click.Choice(["human", "json"]), default="human")
@click.option("--write-scores", is_flag=True, default=False,
              help="Write computed scores back into the JSON file (requires --output or overwrites input)")
def main(input_file: str, output: str | None, output_format: str, write_scores: bool):
    """Score a law school JSON file against the ranking criteria."""
    path = Path(input_file)
    school = json.loads(path.read_text())

    result = compute_scores(school)
    scores = result["scores"]
    tier = result["ranking_tier"]
    notes = result["scoring_notes"]

    if output_format == "json":
        click.echo(json.dumps({"scores": scores, "ranking_tier": tier}, indent=2))
        return

    # Human-readable table
    console.rule(f"[bold]{school.get('name', school.get('id'))}[/bold]")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Criterion", style="dim", width=35)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Max", justify="right", width=6)
    table.add_column("Notes", overflow="fold")

    criteria = [
        ("Curriculum: Courses",       "curriculum_courses",          20),
        ("Curriculum: Practical",      "curriculum_practical",         10),
        ("Curriculum: Clinics",        "curriculum_clinics",           10),
        ("Infrastructure: Center",     "infrastructure_center",        10),
        ("Infrastructure: Joint Deg.", "infrastructure_joint_degrees", 10),
        ("Infrastructure: Partners",   "infrastructure_partnerships",  10),
        ("Faculty: Expertise",         "faculty_expertise",            10),
        ("Faculty: Research",          "faculty_research",             10),
        ("Community: Orgs",            "community_orgs",                5),
        ("Community: Careers",         "community_careers",             5),
        ("PRG Penalty",                "press_release_gap_penalty",    -20),
    ]

    for label, key, max_pts in criteria:
        val = scores.get(key, 0)
        note_lines = notes.get(key, [])
        note_str = " | ".join(note_lines[:2])  # truncate for display
        color = "red" if val < 0 else ("green" if val == max_pts and max_pts > 0 else "white")
        table.add_row(label, f"[{color}]{val}[/{color}]", str(max_pts), note_str)

    console.print(table)
    tc = tier_color(tier)
    console.print(f"\n[bold]Total:[/bold] {scores['total']}/100   [bold]Tier:[/bold] [{tc}]{tier}[/{tc}]\n")

    if write_scores or output:
        out_path = Path(output) if output else path
        school["scores"] = scores
        school["ranking_tier"] = tier
        out_path.write_text(json.dumps(school, indent=2, ensure_ascii=False))
        console.print(f"[green]Scores written to {out_path}[/green]")


if __name__ == "__main__":
    main()
