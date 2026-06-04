"""
mcp-server/server.py

MCP server for the Tech-Friendly Law School Ranking project.

Exposes tools and resources that allow AI assistants (Claude Desktop, Cursor,
etc.) to help prospective law students explore and compare schools.

Tools
-----
search_schools          – filter/rank researched schools
get_school_profile      – full profile for one school
compare_schools         – side-by-side comparison of 2-5 schools
find_schools_for_career – advisor-style career-goal matching
explain_ranking         – plain-English methodology overview
flag_press_release_gaps – accountability: schools that marketed ghost programs
get_research_queue_stats – research coverage overview

Resources
---------
law-schools://methodology      – full CRITERIA.md text
law-schools://schools          – JSON summaries of all researched schools
law-schools://research-queue   – coverage stats from top-500.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure the mcp-server directory itself is on the path so local modules work
# when the server is launched as ``python server.py`` or via the project script.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    TextContent,
    Tool,
)

import data_loader as _dl

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

app = Server("lawschool-ranking-mcp")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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


def _prg_warning(school: dict) -> str:
    """Return a formatted press-release-gap warning block, or empty string."""
    gaps = school.get("press_release_gap") or []
    if not gaps:
        return ""
    lines = ["\n  *** PRESS RELEASE GAP WARNING ***"]
    for g in gaps:
        severity = (g.get("severity") or "unassigned").upper()
        claimed = (g.get("claimed") or "")[:120]
        reality = (g.get("reality") or "Not yet documented")[:120]
        lines.append(f"  Severity: {severity}")
        lines.append(f"  Claimed:  {claimed}")
        lines.append(f"  Reality:  {reality}")
        if g.get("penalty_points") is not None:
            lines.append(f"  Penalty:  {g['penalty_points']} points")
    lines.append("  *** END WARNING ***")
    return "\n".join(lines)


def _school_summary_text(school: dict, rank: int | None = None) -> str:
    """One-paragraph summary of a school suitable for list display."""
    scores = school.get("scores") or {}
    tech = scores.get("total")
    practical = school.get("practical_skills_score")
    meta = school.get("meta_score")
    tier = school.get("ranking_tier") or "unranked"
    last_verified = school.get("last_verified") or "never verified"
    country = school.get("country") or "??"
    region = _dl._infer_region(school) or "unknown region"

    courses = school.get("courses") or []
    ai_courses = [
        c for c in courses
        if any(
            t in (c.get("topics") or [])
            for t in ("artificial_intelligence", "machine_learning", "legal_technology")
        )
        and c.get("year_verified") is not None
    ]
    programs = school.get("programs") or []
    tech_clinics = [
        p for p in programs
        if p.get("type") == "clinic" and p.get("tech_focus") and p.get("status") == "active"
    ]
    joint_degrees = [
        p for p in programs
        if p.get("type") == "joint_degree" and p.get("status") in ("active", None)
    ]

    rank_str = f"#{rank}  " if rank is not None else ""
    lines = [
        f"{rank_str}{school.get('name', school.get('id'))} ({country}, {region})",
        f"  Tier: {tier}  |  Tech Score: {tech if tech is not None else 'n/a'}/100"
        f"  |  Practical: {practical if practical is not None else 'n/a'}/100"
        f"  |  Meta Score: {meta if meta is not None else 'n/a'}/100",
        f"  Data status: last verified {last_verified}",
    ]
    if ai_courses:
        lines.append(f"  Verified AI/tech courses: {len(ai_courses)}")
    if tech_clinics:
        lines.append(f"  Tech clinic(s): {', '.join(c.get('name', '') for c in tech_clinics[:2])}")
    if joint_degrees:
        lines.append(f"  Joint degrees: {len(joint_degrees)} available")
    prg = _prg_warning(school)
    if prg:
        lines.append(prg)
    return "\n".join(lines)


def _filter_schools(
    schools: list[dict],
    region: str | None = None,
    country: str | None = None,
    min_tech_score: int | None = None,
    min_practical_score: int | None = None,
    requires_ai_course: bool | None = None,
    has_legaltech_clinic: bool | None = None,
    joint_degree_available: bool | None = None,
    tier: str | None = None,
) -> list[dict]:
    """Apply filter parameters and return matching schools."""
    result = []
    for s in schools:
        scores = s.get("scores") or {}
        tech = scores.get("total")
        practical = s.get("practical_skills_score")
        programs = s.get("programs") or []
        courses = s.get("courses") or []

        if region is not None:
            inferred = _dl._infer_region(s)
            if inferred != region:
                continue

        if country is not None:
            if (s.get("country") or "").upper() != country.upper():
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
                any(t in (c.get("topics") or []) for t in ai_topics)
                and c.get("year_verified") is not None
                for c in courses
            )
            if not has_ai:
                continue

        if has_legaltech_clinic is True:
            has_clinic = any(
                p.get("type") == "clinic"
                and p.get("tech_focus")
                and p.get("status") == "active"
                for p in programs
            )
            if not has_clinic:
                continue

        if joint_degree_available is True:
            has_jd = any(
                p.get("type") == "joint_degree"
                and p.get("status") in ("active", None)
                for p in programs
            )
            if not has_jd:
                continue

        if tier is not None:
            if (s.get("ranking_tier") or "").upper() != tier.upper():
                continue

        result.append(s)

    return result


def _sort_schools(
    schools: list[dict], sort_by: str = "meta_score"
) -> list[dict]:
    """Sort schools by the requested score dimension."""

    def key_fn(s: dict) -> tuple:
        scores = s.get("scores") or {}
        if sort_by == "tech_score":
            v = scores.get("total")
        elif sort_by == "practical_score":
            v = s.get("practical_skills_score")
        elif sort_by == "prestige_score":
            v = s.get("prestige_score")
        else:  # meta_score (default)
            v = s.get("meta_score")
            if v is None:
                # Fall back to tech score so schools still get a reasonable order
                v = scores.get("total")
                return (1, -(v or 0))
        return (0 if v is not None else 1, -(v or 0))

    return sorted(schools, key=key_fn)


# ---------------------------------------------------------------------------
# Tool: list_tools
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_schools",
            description=(
                "Filter and rank law schools from the database. "
                "Returns school summaries with scores and key highlights. "
                "Use this to find schools matching specific criteria such as region, "
                "score thresholds, program types, or tier."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Geographic region filter.",
                        "enum": sorted(_VALID_REGIONS),
                    },
                    "country": {
                        "type": "string",
                        "description": "ISO 2-letter country code (e.g. US, GB, SG).",
                    },
                    "min_tech_score": {
                        "type": "integer",
                        "description": "Minimum tech-friendliness score (0–100).",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "min_practical_score": {
                        "type": "integer",
                        "description": "Minimum practical skills score (0–100).",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "requires_ai_course": {
                        "type": "boolean",
                        "description": "If true, only return schools with at least one verified AI/ML course.",
                    },
                    "has_legaltech_clinic": {
                        "type": "boolean",
                        "description": "If true, only return schools with an active legaltech clinic.",
                    },
                    "joint_degree_available": {
                        "type": "boolean",
                        "description": "If true, only return schools offering JD/CS or similar joint degrees.",
                    },
                    "tier": {
                        "type": "string",
                        "description": "Tech-friendliness tier (S=85+, A=70-84, B=50-69, C=30-49, D=<30).",
                        "enum": ["S", "A", "B", "C", "D"],
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "Sort order for results.",
                        "enum": ["meta_score", "tech_score", "practical_score", "prestige_score"],
                        "default": "meta_score",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 10, max 50).",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="get_school_profile",
            description=(
                "Get the full detailed profile of a single law school, including all courses, "
                "programs, faculty, partnerships, student organisations, score breakdowns, "
                "external rankings, and any press release gaps. "
                "Use the school slug as the id (e.g. 'harvard-law', 'oxford-law', 'nus-law')."
            ),
            inputSchema={
                "type": "object",
                "required": ["school_id"],
                "properties": {
                    "school_id": {
                        "type": "string",
                        "description": "School slug / id (e.g. 'harvard-law').",
                    },
                },
            },
        ),
        Tool(
            name="compare_schools",
            description=(
                "Compare 2 to 5 law schools side-by-side. "
                "Returns a structured comparison covering tech score, practical score, meta score, "
                "course counts, clinic counts, joint degrees, and press release gap warnings. "
                "Ideal for head-to-head decision-making."
            ),
            inputSchema={
                "type": "object",
                "required": ["school_ids"],
                "properties": {
                    "school_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "maxItems": 5,
                        "description": "List of 2–5 school slugs to compare (e.g. ['oxford-law', 'nus-law']).",
                    },
                },
            },
        ),
        Tool(
            name="find_schools_for_career",
            description=(
                "Recommend law schools based on a described career goal. "
                "Interprets the goal to set smart filter defaults, then searches and returns "
                "results with an explanation of why each school matches. "
                "Examples: 'legal engineer', 'AI policy lawyer', 'legal ops at a tech company', "
                "'startup lawyer with coding skills', 'litigation tech specialist'."
            ),
            inputSchema={
                "type": "object",
                "required": ["career_goal"],
                "properties": {
                    "career_goal": {
                        "type": "string",
                        "description": "Free-text description of the career you want to pursue.",
                    },
                    "region": {
                        "type": "string",
                        "description": "Preferred geographic region (optional).",
                        "enum": sorted(_VALID_REGIONS),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of recommendations to return (default 5).",
                        "minimum": 1,
                        "maximum": 20,
                        "default": 5,
                    },
                },
            },
        ),
        Tool(
            name="explain_ranking",
            description=(
                "Return a plain-English explanation of how the ranking methodology works: "
                "what is measured, why, and how the meta-rank is computed. "
                "Suitable for a student who wants to understand whether to trust the rankings."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="flag_press_release_gaps",
            description=(
                "Return all schools that have documented press-release-gap entries — "
                "schools that publicly marketed programs, centres, or initiatives "
                "that no longer exist or no longer function as described. "
                "This is the ranking's most important accountability feature."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_research_queue_stats",
            description=(
                "Return statistics on research coverage: how many schools have been "
                "fully researched versus still pending, broken down by region. "
                "Useful for understanding the completeness of the dataset."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool: call_tool
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> list[TextContent]:  # type: ignore[return]
    args = arguments or {}
    if name == "search_schools":
        return await _tool_search_schools(args)
    elif name == "get_school_profile":
        return await _tool_get_school_profile(args)
    elif name == "compare_schools":
        return await _tool_compare_schools(args)
    elif name == "find_schools_for_career":
        return await _tool_find_schools_for_career(args)
    elif name == "explain_ranking":
        return await _tool_explain_ranking(args)
    elif name == "flag_press_release_gaps":
        return await _tool_flag_press_release_gaps(args)
    elif name == "get_research_queue_stats":
        return await _tool_get_research_queue_stats(args)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def _tool_search_schools(args: dict) -> list[TextContent]:
    region = args.get("region")
    country = args.get("country")
    min_tech = args.get("min_tech_score")
    min_practical = args.get("min_practical_score")
    requires_ai = args.get("requires_ai_course")
    has_clinic = args.get("has_legaltech_clinic")
    joint_deg = args.get("joint_degree_available")
    tier = args.get("tier")
    sort_by = args.get("sort_by", "meta_score")
    limit = min(int(args.get("limit", 10)), 50)

    # Validation
    if region and region not in _VALID_REGIONS:
        return [TextContent(type="text", text=f"Invalid region '{region}'. Valid options: {', '.join(sorted(_VALID_REGIONS))}")]
    if tier and tier.upper() not in _VALID_TIERS:
        return [TextContent(type="text", text=f"Invalid tier '{tier}'. Valid options: S, A, B, C, D")]
    if sort_by and sort_by not in _VALID_SORT:
        sort_by = "meta_score"

    all_schools = _dl.load_all_schools()
    filtered = _filter_schools(
        all_schools,
        region=region,
        country=country,
        min_tech_score=min_tech,
        min_practical_score=min_practical,
        requires_ai_course=requires_ai,
        has_legaltech_clinic=has_clinic,
        joint_degree_available=joint_deg,
        tier=tier,
    )
    sorted_schools = _sort_schools(filtered, sort_by=sort_by)
    paginated = sorted_schools[:limit]

    # Build response
    filter_desc_parts: list[str] = []
    if region:
        filter_desc_parts.append(f"region={region}")
    if country:
        filter_desc_parts.append(f"country={country.upper()}")
    if min_tech:
        filter_desc_parts.append(f"min_tech_score={min_tech}")
    if min_practical:
        filter_desc_parts.append(f"min_practical_score={min_practical}")
    if requires_ai:
        filter_desc_parts.append("requires_ai_course=true")
    if has_clinic:
        filter_desc_parts.append("has_legaltech_clinic=true")
    if joint_deg:
        filter_desc_parts.append("joint_degree_available=true")
    if tier:
        filter_desc_parts.append(f"tier={tier}")
    filter_str = ", ".join(filter_desc_parts) if filter_desc_parts else "none (showing all)"

    lines = [
        f"Law School Search Results",
        f"========================",
        f"Database size: {len(all_schools)} fully researched school(s)",
        f"Filters applied: {filter_str}",
        f"Matching schools: {len(filtered)}",
        f"Showing: top {len(paginated)} sorted by {sort_by}",
        f"",
    ]

    if not paginated:
        lines.append(
            "No schools matched your filters. "
            "Try relaxing the criteria (e.g. lower min scores, remove region filter)."
        )
        lines.append(
            f"\nNote: Only {len(all_schools)} schools have been fully researched so far. "
            f"Use get_research_queue_stats to see how many are pending."
        )
    else:
        for rank, s in enumerate(paginated, start=1):
            lines.append(_school_summary_text(s, rank=rank))
            lines.append("")

        lines.append(
            f"Data completeness note: scores marked 'n/a' indicate fields not yet "
            f"researched or where data is missing. last_verified=null means no human "
            f"reviewer has confirmed this data."
        )

    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_school_profile(args: dict) -> list[TextContent]:
    school_id = (args.get("school_id") or "").strip()
    if not school_id:
        return [TextContent(type="text", text="school_id is required.")]

    school = _dl.load_school(school_id)

    if school is None:
        # Check if it's in the research queue
        queue_entry = _dl.get_queue_entry(school_id)
        if queue_entry:
            lines = [
                f"School Not Yet Researched: {queue_entry.get('name', school_id)}",
                f"==========================================",
                f"This school is in the research queue but has not yet been scored.",
                f"",
                f"Known information from the queue:",
                f"  Country: {queue_entry.get('country', '??')}",
                f"  City: {queue_entry.get('city', 'unknown')}",
                f"  Region: {queue_entry.get('region', 'unknown')}",
                f"  URL: {queue_entry.get('url', 'unknown')}",
                f"  Research status: {queue_entry.get('research_status', 'pending')}",
            ]
            kr = queue_entry.get("known_rankings") or {}
            if kr:
                lines.append(f"  Known approximate rankings:")
                for k, v in kr.items():
                    if v is not None:
                        lines.append(f"    {k}: ~#{v}")
            lines.append(
                f"\nTo prioritise this school for research, open a GitHub issue using "
                f"the School Submission template."
            )
        else:
            lines = [
                f"School Not Found: '{school_id}'",
                f"This school ID was not found in the database or research queue.",
                f"",
                f"Tips:",
                f"  - School IDs are slugs like 'harvard-law', 'oxford-law', 'nus-law'.",
                f"  - Use search_schools to browse what is available.",
            ]
        return [TextContent(type="text", text="\n".join(lines))]

    # Build full profile
    scores = school.get("scores") or {}
    practical = school.get("practical_skills_score")
    practical_bd = school.get("practical_skills_breakdown") or {}
    meta = school.get("meta_score")
    tier = school.get("ranking_tier") or "unranked"
    last_verified = school.get("last_verified") or "never (unverified)"
    last_researched = school.get("last_researched") or "never"
    country = school.get("country") or "??"
    region = _dl._infer_region(school) or "unknown region"
    url = school.get("url") or "n/a"

    courses = school.get("courses") or []
    programs = school.get("programs") or []
    faculty = school.get("faculty") or []
    partnerships = school.get("partnerships") or []
    orgs = school.get("student_orgs") or []
    gaps = school.get("press_release_gap") or []
    ext = school.get("external_rankings") or {}

    lines = [
        f"Full Profile: {school.get('name', school_id)}",
        f"{'=' * (len(school.get('name', school_id)) + 14)}",
        f"",
        f"Country: {country}  |  Region: {region}",
        f"URL: {url}",
        f"Last researched: {last_researched}  |  Last verified: {last_verified}",
        f"",
        f"SCORES",
        f"------",
        f"  Tech-Friendliness Score : {scores.get('total', 'n/a')}/100  (Tier: {tier})",
        f"  Practical Skills Score  : {practical if practical is not None else 'n/a'}/100",
        f"  Meta Score              : {meta if meta is not None else 'n/a'}/100",
        f"",
        f"  Tech Score Breakdown:",
        f"    Curriculum – Courses     : {scores.get('curriculum_courses', 'n/a')}/20",
        f"    Curriculum – Practical   : {scores.get('curriculum_practical', 'n/a')}/10",
        f"    Curriculum – Clinics     : {scores.get('curriculum_clinics', 'n/a')}/10",
        f"    Infrastructure – Center  : {scores.get('infrastructure_center', 'n/a')}/10",
        f"    Infrastructure – Jt Deg  : {scores.get('infrastructure_joint_degrees', 'n/a')}/10",
        f"    Infrastructure – Partners: {scores.get('infrastructure_partnerships', 'n/a')}/10",
        f"    Faculty – Expertise      : {scores.get('faculty_expertise', 'n/a')}/10",
        f"    Faculty – Research       : {scores.get('faculty_research', 'n/a')}/10",
        f"    Community – Orgs         : {scores.get('community_orgs', 'n/a')}/5",
        f"    Community – Careers      : {scores.get('community_careers', 'n/a')}/5",
        f"    PRG Penalty              : {scores.get('press_release_gap_penalty', 0)}  (max -20)",
    ]

    if practical_bd:
        lines += [
            f"",
            f"  Practical Skills Breakdown:",
            f"    Clinical Programs      : {practical_bd.get('clinical_programs', 'n/a')}/25",
            f"    Skills Curriculum      : {practical_bd.get('skills_curriculum', 'n/a')}/25",
            f"    Experiential Placements: {practical_bd.get('experiential_placements', 'n/a')}/25",
            f"    Professional Readiness : {practical_bd.get('professional_readiness', 'n/a')}/25",
        ]

    # External rankings
    lines += [f"", f"EXTERNAL RANKINGS", f"-----------------"]
    rank_names = {
        "qs_law": "QS Law",
        "the_law": "Times Higher Education Law",
        "arwu_law": "ARWU Law",
        "usnews_law": "US News Law (domestic)",
        "usnews_global_law": "US News Global Law",
        "vault_law": "Vault Law",
    }
    has_any_rank = False
    for key, label in rank_names.items():
        entry = ext.get(key)
        if entry and isinstance(entry, dict):
            rank_val = entry.get("rank")
            year = entry.get("year", "?")
            lines.append(f"  {label}: #{rank_val} ({year})")
            has_any_rank = True
    if not has_any_rank:
        lines.append("  No external ranking data available.")

    # Courses
    lines += [f"", f"COURSES ({len(courses)} listed)", f"-------"]
    if courses:
        for c in courses:
            verified = f" [verified {c.get('year_verified')}]" if c.get("year_verified") else " [UNVERIFIED]"
            ctype = c.get("type", "elective").upper()
            lines.append(f"  [{ctype}] {c.get('title', 'Untitled')}{verified}")
    else:
        lines.append("  No courses listed.")

    # Programs
    lines += [f"", f"PROGRAMS & CENTRES ({len(programs)} listed)", f"------------------"]
    if programs:
        for p in programs:
            ptype = p.get("type", "other").replace("_", " ").title()
            status = p.get("status", "unknown").upper()
            tech_tag = " [TECH FOCUS]" if p.get("tech_focus") else ""
            lines.append(f"  [{status}] {p.get('name', 'Unnamed')} ({ptype}){tech_tag}")
            if p.get("description"):
                lines.append(f"           {p['description'][:100]}")
    else:
        lines.append("  No programs listed.")

    # Faculty
    lines += [f"", f"FACULTY ({len(faculty)} listed)", f"-------"]
    if faculty:
        for f_ in faculty:
            apt = f_.get("appointment_type", "unknown")
            expertise = ", ".join((f_.get("tech_expertise") or [])[:3])
            lines.append(f"  {f_.get('name', 'Unknown')} ({apt})")
            if expertise:
                lines.append(f"    Tech expertise: {expertise}")
    else:
        lines.append("  No faculty listed.")

    # Partnerships
    lines += [f"", f"PARTNERSHIPS ({len(partnerships)} listed)", f"------------"]
    if partnerships:
        for p in partnerships:
            active = "ACTIVE" if p.get("active") else ("?" if p.get("active") is None else "INACTIVE")
            lines.append(f"  [{active}] {p.get('org', 'Unknown')} ({p.get('type', 'unknown')})")
    else:
        lines.append("  No partnerships listed.")

    # Student orgs
    lines += [f"", f"STUDENT ORGANISATIONS ({len(orgs)} listed)", f"---------------------"]
    if orgs:
        for o in orgs:
            active = "ACTIVE" if o.get("active") else ("?" if o.get("active") is None else "INACTIVE")
            lines.append(f"  [{active}] {o.get('name', 'Unknown')}")
    else:
        lines.append("  No student organisations listed.")

    # Press release gaps
    if gaps:
        lines += [f"", f"PRESS RELEASE GAPS — ACCOUNTABILITY SECTION", f"-------------------------------------------"]
        lines.append(
            f"  This school has {len(gaps)} documented press release gap(s). "
            f"These are programs that were publicly marketed but may no longer exist or function as described."
        )
        for i, g in enumerate(gaps, start=1):
            severity = (g.get("severity") or "unassigned").upper()
            lines += [
                f"",
                f"  Gap #{i} (Severity: {severity}, Penalty: {g.get('penalty_points', 'TBD')} pts)",
                f"  Claimed : {g.get('claimed', 'N/A')}",
                f"  Reality : {g.get('reality', 'Not yet documented')}",
                f"  Year claimed: {g.get('year_claimed', 'unknown')}",
            ]
            if g.get("evidence_url"):
                lines.append(f"  Evidence: {g['evidence_url']}")
            if g.get("current_url"):
                lines.append(f"  Current : {g['current_url']}")
    else:
        lines += [f"", f"PRESS RELEASE GAPS", f"------------------", f"  None documented."]

    # General notes
    if school.get("notes"):
        lines += [f"", f"NOTES", f"-----", f"  {school['notes']}"]

    lines += [
        f"",
        f"DATA FRESHNESS WARNING",
        f"----------------------",
        f"  All data with year_verified=null has NOT been confirmed by a researcher.",
        f"  last_verified={last_verified} reflects the last human review date.",
        f"  Treat unverified data as indicative only.",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_compare_schools(args: dict) -> list[TextContent]:
    school_ids: list[str] = args.get("school_ids") or []

    if len(school_ids) < 2:
        return [TextContent(type="text", text="Please provide at least 2 school IDs to compare.")]
    if len(school_ids) > 5:
        school_ids = school_ids[:5]

    loaded: list[dict | None] = []
    not_found: list[str] = []
    for sid in school_ids:
        s = _dl.load_school(sid)
        if s is None:
            not_found.append(sid)
            loaded.append(None)
        else:
            loaded.append(s)

    # Build header row
    headers = ["Dimension"] + [
        (s.get("name", sid) if s else f"[NOT FOUND: {sid}]")
        for s, sid in zip(loaded, school_ids)
    ]

    def row(label: str, extractor) -> str:
        vals = []
        for s in loaded:
            if s is None:
                vals.append("N/A")
            else:
                try:
                    v = extractor(s)
                    vals.append(str(v) if v is not None else "n/a")
                except Exception:
                    vals.append("err")
        return f"  {label:<30} | " + " | ".join(f"{v:^20}" for v in vals)

    def header_row() -> str:
        sep_label = "-" * 30
        sep_cols = " | ".join("-" * 20 for _ in loaded)
        return f"  {sep_label}-+-{sep_cols}"

    col_header = "  " + f"{'Dimension':<30}" + " | " + " | ".join(
        f"{(s.get('name', sid) if s else sid)[:20]:^20}"
        for s, sid in zip(loaded, school_ids)
    )

    lines = [
        f"Side-by-Side School Comparison",
        f"==============================",
        f"",
        col_header,
        header_row(),
        row("Country", lambda s: s.get("country")),
        row("Region", lambda s: _dl._infer_region(s) or "unknown"),
        row("Tier", lambda s: s.get("ranking_tier") or "unranked"),
        row("Tech Score (/100)", lambda s: (s.get("scores") or {}).get("total")),
        row("Practical Score (/100)", lambda s: s.get("practical_skills_score")),
        row("Meta Score (/100)", lambda s: s.get("meta_score")),
        header_row(),
        row("  Courses (total)", lambda s: len(s.get("courses") or [])),
        row("  AI/ML courses (verified)", lambda s: sum(
            1 for c in (s.get("courses") or [])
            if c.get("year_verified") is not None
            and any(t in (c.get("topics") or []) for t in
                    ("artificial_intelligence", "machine_learning", "legal_technology"))
        )),
        row("  Required tech courses", lambda s: sum(
            1 for c in (s.get("courses") or [])
            if c.get("type") == "required" and c.get("year_verified") is not None
        )),
        header_row(),
        row("  Tech clinics (active)", lambda s: sum(
            1 for p in (s.get("programs") or [])
            if p.get("type") == "clinic" and p.get("tech_focus") and p.get("status") == "active"
        )),
        row("  All clinics (active)", lambda s: sum(
            1 for p in (s.get("programs") or [])
            if p.get("type") == "clinic" and p.get("status") == "active"
        )),
        row("  Joint degrees", lambda s: sum(
            1 for p in (s.get("programs") or [])
            if p.get("type") == "joint_degree" and p.get("status") in ("active", None)
        )),
        row("  LegalTech centre", lambda s: "YES" if any(
            p.get("type") == "center" and p.get("tech_focus") and p.get("status") == "active"
            for p in (s.get("programs") or [])
        ) else "no"),
        header_row(),
        row("  Faculty (total)", lambda s: len(s.get("faculty") or [])),
        row("  Tech faculty", lambda s: sum(
            1 for f in (s.get("faculty") or [])
            if f.get("tech_expertise") or f.get("research_areas")
        )),
        row("  Industry partnerships", lambda s: len(s.get("partnerships") or [])),
        row("  Student orgs", lambda s: len(s.get("student_orgs") or [])),
        header_row(),
        row("  QS Law rank", lambda s: (s.get("external_rankings") or {}).get("qs_law", {}).get("rank") if isinstance((s.get("external_rankings") or {}).get("qs_law"), dict) else "n/a"),
        row("  THE Law rank", lambda s: (s.get("external_rankings") or {}).get("the_law", {}).get("rank") if isinstance((s.get("external_rankings") or {}).get("the_law"), dict) else "n/a"),
        header_row(),
        row("  PRG warnings", lambda s: len(s.get("press_release_gap") or [])),
        row("  Last verified", lambda s: s.get("last_verified") or "never"),
    ]

    # Surface any PRG warnings prominently
    prg_lines = []
    for s, sid in zip(loaded, school_ids):
        if s is not None:
            prg = _prg_warning(s)
            if prg:
                prg_lines.append(f"\n{s.get('name', sid)}:{prg}")
    if prg_lines:
        lines += [
            "",
            "PRESS RELEASE GAP WARNINGS",
            "==========================",
        ]
        lines.extend(prg_lines)

    if not_found:
        lines += [
            "",
            f"NOTE: The following school IDs were not found in the database: {', '.join(not_found)}",
            "Use search_schools to browse available schools.",
        ]

    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_find_schools_for_career(args: dict) -> list[TextContent]:
    career_goal = (args.get("career_goal") or "").strip()
    region = args.get("region")
    limit = min(int(args.get("limit", 5)), 20)

    if not career_goal:
        return [TextContent(type="text", text="career_goal is required.")]

    goal_lower = career_goal.lower()

    # Map career goals to filter weights and search criteria
    # We derive filter defaults from the goal text

    # Determine primary filter strategy
    min_tech = 0
    min_practical = 0
    requires_ai = None
    has_clinic = None
    joint_deg = None
    sort_by = "meta_score"
    explanation_prefix = ""
    profile_notes: list[str] = []

    if any(kw in goal_lower for kw in ("legal engineer", "legal technology", "legaltech", "legal tech")):
        min_tech = 30
        requires_ai = True
        joint_deg = True
        sort_by = "tech_score"
        explanation_prefix = (
            "For a legal engineer career, you need a school with deep tech integration: "
            "verified AI/ML courses, joint degree options (JD/CS is the gold standard), "
            "and a strong tech score. Practical skills are secondary to technical curriculum."
        )
        profile_notes = [
            "Look for joint degrees (JD/CS or equivalent)",
            "Required tech courses beat electives",
            "Check for industry partnerships with tech companies",
        ]

    elif any(kw in goal_lower for kw in ("ai policy", "artificial intelligence policy", "ai regulation", "tech policy")):
        min_tech = 20
        requires_ai = True
        sort_by = "tech_score"
        explanation_prefix = (
            "AI policy roles sit at the intersection of technical understanding and regulatory expertise. "
            "You need a school with serious AI course offerings and strong research output on tech policy, "
            "ideally with faculty who engage with government or standards bodies."
        )
        profile_notes = [
            "Prioritise AI/ML course depth over pure tech score",
            "Look for faculty with AI governance research",
            "Strong prestige helps in policy careers (government / think tanks recognise brand)",
        ]

    elif any(kw in goal_lower for kw in ("legal ops", "legal operations", "process", "clm", "contract management")):
        min_tech = 20
        min_practical = 30
        sort_by = "meta_score"
        explanation_prefix = (
            "Legal operations is where tech meets process efficiency. "
            "You want a school that combines strong practical training (clinics, externships) "
            "with technology courses focused on document automation, e-discovery, and workflow tools."
        )
        profile_notes = [
            "Practical score matters as much as tech score here",
            "Look for document automation and e-discovery courses",
            "Industry partnerships with LegalTech vendors are a plus",
        ]

    elif any(kw in goal_lower for kw in ("startup", "entrepreneur", "venture", "founder")):
        min_tech = 20
        joint_deg = True
        sort_by = "meta_score"
        explanation_prefix = (
            "Startup and entrepreneurship-focused lawyers benefit from schools with joint degree options "
            "(especially JD/MBA), strong industry networks, and tech integration that makes you credible "
            "in tech-company boardrooms. Practical training in deal-making contexts is valuable."
        )
        profile_notes = [
            "JD/MBA with tech track is ideal",
            "Industry partnerships signal employer-facing relationships",
            "Clinics focused on business/startup law are a plus",
        ]

    elif any(kw in goal_lower for kw in ("litigation tech", "ediscovery", "e-discovery", "trial tech")):
        min_tech = 15
        min_practical = 40
        sort_by = "practical_score"
        explanation_prefix = (
            "Litigation technology specialists need deep practical training — trial advocacy programs, "
            "externships with litigation firms or courts — combined with e-discovery and digital evidence courses. "
            "Practical score is the primary filter here."
        )
        profile_notes = [
            "Prioritise high practical score (externships, moot court)",
            "Look for e-discovery courses specifically",
            "Trial advocacy programs are a strong signal",
        ]

    elif any(kw in goal_lower for kw in ("access to justice", "a2j", "public interest", "legal aid")):
        min_tech = 15
        has_clinic = True
        sort_by = "meta_score"
        explanation_prefix = (
            "Access-to-justice tech roles require schools with active legaltech clinics and "
            "practical training focused on underserved populations. Look for schools with "
            "technology delivery components in their clinical programs and faculty engaged in A2J research."
        )
        profile_notes = [
            "Active legaltech clinic is the most important signal",
            "Look for Access to Justice Lab or similar research programs",
            "Pro bono requirements signal commitment to public service",
        ]

    elif any(kw in goal_lower for kw in ("coding", "software", "developer", "programmer", "engineer")):
        min_tech = 30
        joint_deg = True
        sort_by = "tech_score"
        explanation_prefix = (
            "If you want to code as a lawyer, you need a school that takes technical education seriously. "
            "Joint JD/CS degrees are rare but transformative. Look for schools with coding-for-lawyers "
            "courses, strong tech faculties, and industry partnerships with software companies."
        )
        profile_notes = [
            "JD/CS joint degree is the highest signal",
            "Required tech practicum or coding module is next best",
            "Check faculty for CS or engineering backgrounds",
        ]

    else:
        # Generic: balanced search
        sort_by = "meta_score"
        explanation_prefix = (
            f"Based on your goal '{career_goal}', here are the most tech-forward law schools "
            f"with strong overall profiles. The meta score combines tech (50%), practical skills (30%), "
            f"and prestige (20%)."
        )
        profile_notes = [
            "Consider how heavily you weight tech vs. prestige in your decision",
            "Use compare_schools to do a head-to-head comparison of finalists",
        ]

    all_schools = _dl.load_all_schools()
    filtered = _filter_schools(
        all_schools,
        region=region,
        min_tech_score=min_tech if min_tech > 0 else None,
        min_practical_score=min_practical if min_practical > 0 else None,
        requires_ai_course=requires_ai,
        has_legaltech_clinic=has_clinic,
        joint_degree_available=joint_deg,
    )
    sorted_schools = _sort_schools(filtered, sort_by=sort_by)
    recommendations = sorted_schools[:limit]

    lines = [
        f"Career-Focused Law School Recommendations",
        f"=========================================",
        f"Goal: {career_goal}",
        f"",
        explanation_prefix,
        f"",
        f"What to look for:",
    ]
    for note in profile_notes:
        lines.append(f"  - {note}")

    if region:
        lines.append(f"  - Region filtered to: {region}")

    lines += [f"", f"Top {len(recommendations)} Recommendations (sorted by {sort_by})", f"-" * 40, f""]

    if not recommendations:
        lines.append(
            "No schools currently in the database match all the criteria for this goal. "
            "This may be because only a small number of schools have been fully researched. "
            "Try the search_schools tool with relaxed filters or check get_research_queue_stats "
            "to see how many schools are pending."
        )
    else:
        for rank, s in enumerate(recommendations, start=1):
            lines.append(_school_summary_text(s, rank=rank))
            # Add career-specific contextual note
            programs = s.get("programs") or []
            courses = s.get("courses") or []
            relevant_programs = [
                p.get("name") for p in programs
                if p.get("tech_focus") and p.get("status") in ("active", "unknown")
            ]
            if relevant_programs:
                lines.append(f"  Career-relevant programs: {', '.join(str(p) for p in relevant_programs[:3])}")
            lines.append("")

    lines += [
        f"",
        f"Tip: Use get_school_profile <school_id> for the full details on any of these schools.",
        f"Tip: Use compare_schools to do a head-to-head comparison of your finalists.",
        f"Data note: Only {len(all_schools)} schools fully researched. "
        f"Many more are in the queue — use get_research_queue_stats for coverage details.",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_explain_ranking(args: dict) -> list[TextContent]:
    text = """
Tech-Friendly Law School Ranking — Methodology Explained
=========================================================

Who is this ranking for?
-------------------------
This ranking is for prospective law students who want to find schools where
technology is genuinely integrated into legal education — not just mentioned
in a brochure. It is also useful for legal employers evaluating graduates'
tech-readiness, and for researchers studying legal education reform.

What makes this ranking different?
------------------------------------
Most law school rankings focus on academic reputation, bar passage rates, and
employment outcomes. We focus on one specific question: how seriously does this
school treat the technological transformation of legal practice?

We rank law schools globally using the same criteria regardless of country.
A school in Singapore, Germany, or Brazil is assessed the same way as one in
the United States.

What we measure
---------------
We compute THREE independent scores, then combine them into a Meta Score.

1. TECH-FRIENDLINESS SCORE (0–100) — our unique contribution
   This is the primary signal. It measures:

   a) CURRICULUM (max 40 points)
      - AI/LegalTech courses: 2 pts each for required, 1 pt for elective (max 20)
      - Practical tech requirement: 0–10 pts (10 = formal required tech practicum)
      - Tech-integrated clinics: 0–10 pts (10 = dedicated legaltech clinic)

   b) INFRASTRUCTURE (max 30 points)
      - Dedicated legaltech centre: 0–10 pts (10 = active centre with staff/web presence)
      - Joint degrees (JD/CS etc): 5 pts each, up to 10 pts total
      - Industry partnerships: 0–10 pts (10 = 3+ documented active partnerships)

   c) FACULTY & RESEARCH (max 20 points)
      - Faculty with tech expertise: 0–10 pts (10 = 4+ qualifying faculty)
      - Active legaltech research: 0–10 pts (10 = 5+ verified publications in 3 years)

   d) COMMUNITY & CAREER (max 10 points)
      - Student legaltech organisations: 0–5 pts
      - Career placement in legaltech: 0–5 pts

   e) PRESS RELEASE GAP PENALTY (−5 to −20 points)
      This is the most important accountability mechanism. A school loses points
      when it has publicly marketed programs, centres, or initiatives that no
      longer exist or no longer function as described. Penalties range from
      −5 (minor, single small program) to −20 (egregious, systematic pattern).

2. PRACTICAL SKILLS SCORE (0–100) — independent dimension
   Measures how well the school prepares students for real legal practice:
   - Clinical programs (max 25 pts): live-client clinics, 4 pts each
   - Skills curriculum (max 25 pts): required skills courses, advocacy programs
   - Experiential placements (max 25 pts): externships, co-op, field placements
   - Professional readiness (max 25 pts): pro bono requirements, bar support,
     employer partnerships for skills development

3. PRESTIGE SCORE (0–100) — derived from external rankings
   Aggregated and normalised from up to 6 major global law school rankings:
   QS Law, Times Higher Education Law, ARWU Law, US News Law (domestic),
   US News Global Law, and Vault Law. Each rank is normalised on a log scale
   (rank 1 → ~100 points; rank 500 → 0 points). Missing rankings are excluded
   from the average (not zeroed).

Meta Score formula
------------------
  meta_score = (tech_score × 0.50) + (practical_score × 0.30) + (prestige × 0.20)

  If practical_score is not yet researched:
  meta_score = (tech_score × 0.625) + (prestige × 0.375)   [proportional rescale]

  If prestige_score is null (no ranking data), the school has no meta score.

Tiers
-----
  S  (85–100)   Exemplary: genuine leader in legal technology education
  A  (70–84)    Strong: substantial and well-integrated technology focus
  B  (50–69)    Developing: meaningful commitment with room for growth
  C  (30–49)    Limited: minimal integration despite some presence
  D  (< 30)     Absent or declining: little to no genuine engagement
  Unranked      Insufficient verified data

How to trust the data
----------------------
- Every claim must have a source URL and a verification date.
- Courses with year_verified=null are NOT counted in scoring.
- Human reviewers confirm all scores before publication.
- Schools are given 30 days to respond to draft scores before publication.
- Press release gaps require: (1) a documented public claim, (2) current evidence
  the program no longer exists, and (3) a temporal gap between claim and reality.

What this ranking does NOT measure
------------------------------------
- General law school quality, bar passage, or employment rates
- Whether a school is "good" in the traditional sense
- US-specific metrics that disadvantage international schools

Limitations
-----------
- Smaller schools with excellent tech integration may be disadvantaged by
  criteria that reward institutional size (more faculty, more courses).
- Only schools that have been fully researched appear in search results.
  Many schools are in the queue but not yet scored.
- Data with year_verified=null should be treated as indicative only.

Want to submit a correction?
------------------------------
Open a GitHub issue using the School Submission / Correction template.
For press release gap reports, use the Press Release Gap Report template.
All accepted corrections are merged via pull request and credited.

Version: 1.0  |  Formula version: 2.0  |  Last updated: 2026-06-04
""".strip()
    return [TextContent(type="text", text=text)]


async def _tool_flag_press_release_gaps(args: dict) -> list[TextContent]:
    schools = _dl.load_all_schools()
    gap_schools = [s for s in schools if s.get("press_release_gap")]

    lines = [
        "Press Release Gap Report",
        "========================",
        "",
        "This report lists schools with documented press release gaps — programs,",
        "centres, or initiatives that were publicly marketed but no longer exist",
        "or no longer function as described.",
        "",
        "A press release gap requires:",
        "  1. A documented public claim (press release, website, admissions material)",
        "  2. Current evidence that the program no longer exists or is substantially different",
        "  3. A temporal gap — the claim was made, then quietly removed or abandoned",
        "",
        "Penalty scale: Minor = −5 pts, Moderate = −10, Major = −15, Egregious = −20",
        "",
        f"Schools with documented gaps: {len(gap_schools)} of {len(schools)} researched",
        "",
    ]

    if not gap_schools:
        lines.append(
            "No press release gaps are currently documented. "
            "This will be updated as more schools are researched."
        )
    else:
        for s in gap_schools:
            gaps = s.get("press_release_gap") or []
            scores = s.get("scores") or {}
            prg_penalty = scores.get("press_release_gap_penalty", 0)
            lines += [
                f"SCHOOL: {s.get('name', s.get('id'))} ({s.get('country', '??')})",
                f"  Tech Score: {scores.get('total', 'n/a')}/100  |  PRG Penalty: {prg_penalty} pts",
                f"  Number of gaps: {len(gaps)}",
            ]
            for i, g in enumerate(gaps, start=1):
                severity = (g.get("severity") or "unassigned").upper()
                year_claimed = g.get("year_claimed", "unknown")
                lines += [
                    f"",
                    f"  Gap #{i} — Severity: {severity}  |  Year claimed: {year_claimed}",
                    f"  Claimed : {g.get('claimed', 'N/A')}",
                    f"  Reality : {g.get('reality', 'Not yet documented')}",
                ]
                if g.get("evidence_url"):
                    lines.append(f"  Evidence: {g['evidence_url']}")
                if g.get("current_url"):
                    lines.append(f"  Current : {g['current_url']}")
                penalty = g.get("penalty_points")
                lines.append(
                    f"  Penalty : {f'{penalty} pts' if penalty is not None else 'TBD — awaiting severity assignment'}"
                )
            lines.append("")

    lines += [
        "---",
        "To report a new press release gap, open a GitHub issue using the",
        "'Press Release Gap Report' template.",
        "",
        "Note: Gaps marked severity=null or penalty_points=null have been flagged",
        "but not yet fully verified. A provisional −5 pt penalty applies until",
        "a human reviewer completes verification.",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_research_queue_stats(args: dict) -> list[TextContent]:
    stats = _dl.get_research_stats()

    if "error" in stats:
        return [TextContent(type="text", text=f"Error loading research stats: {stats['error']}")]

    total = stats.get("total_in_queue", 0)
    researched = stats.get("researched", 0)
    pending = stats.get("pending", 0)
    pct = stats.get("coverage_pct", 0)
    countries = stats.get("countries_represented", 0)
    by_region = stats.get("by_region", {})

    lines = [
        "Research Coverage Statistics",
        "============================",
        "",
        f"Total schools in research queue : {total}",
        f"Fully researched (scored)        : {researched}",
        f"Pending research                 : {pending}",
        f"Coverage                         : {pct}%",
        f"Countries represented in queue   : {countries}",
        "",
        "Breakdown by Region",
        "-------------------",
    ]

    for region in sorted(by_region.keys()):
        data = by_region[region]
        r_total = data.get("total", 0)
        r_done = data.get("researched", 0)
        r_pend = data.get("pending", 0)
        pct_done = round(100 * r_done / r_total, 1) if r_total else 0
        bar_fill = int(pct_done / 5)
        bar = "#" * bar_fill + "." * (20 - bar_fill)
        lines.append(
            f"  {region:<28} {r_done:>3}/{r_total:<3} [{bar}] {pct_done}%"
        )

    lines += [
        "",
        "What 'researched' means",
        "-----------------------",
        "A school is 'researched' if a JSON profile exists in data/schools/.",
        "This does NOT mean all data has been human-verified — many profiles",
        "contain fields with year_verified=null that still need confirmation.",
        "",
        "last_verified=null on a school profile means no human reviewer has",
        "confirmed the data. Treat those scores as provisional estimates.",
        "",
        "To prioritise a school for research, open a GitHub issue using the",
        "'School Submission / Correction' template.",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@app.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="law-schools://methodology",
            name="Ranking Methodology",
            description=(
                "Full text of CRITERIA.md — the complete public methodology explaining "
                "what we measure, why, and how the meta-rank is computed."
            ),
            mimeType="text/markdown",
        ),
        Resource(
            uri="law-schools://schools",
            name="All Researched Schools",
            description=(
                "JSON list of summary objects for all schools that have been fully "
                "researched and scored. Includes tech score, practical score, meta score, "
                "tier, and whether any press release gaps have been documented."
            ),
            mimeType="application/json",
        ),
        Resource(
            uri="law-schools://research-queue",
            name="Research Queue Stats",
            description=(
                "Coverage statistics from top-500.json: how many schools have been "
                "researched vs. pending, broken down by region."
            ),
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def read_resource(uri) -> str:
    # uri may be a pydantic AnyUrl object or a plain string depending on MCP version
    uri_str = str(uri)

    if uri_str == "law-schools://methodology":
        return _dl.load_criteria_text()

    elif uri_str == "law-schools://schools":
        summaries = _dl.schools_summary_list()
        return json.dumps(summaries, indent=2, ensure_ascii=False)

    elif uri_str == "law-schools://research-queue":
        stats = _dl.get_research_stats()
        return json.dumps(stats, indent=2, ensure_ascii=False)

    else:
        raise ValueError(f"Unknown resource URI: {uri_str}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def main():
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()
