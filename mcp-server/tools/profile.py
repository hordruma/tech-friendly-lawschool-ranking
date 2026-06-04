"""
mcp-server/tools/profile.py

get_school_profile MCP tool.
"""

from __future__ import annotations

from mcp.types import TextContent, Tool

from lawschool.data import get_queue_entry, load_school
from _helpers import infer_region, prg_warning

TOOL_DEFINITION = Tool(
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
)


async def handle(args: dict) -> list[TextContent]:
    school_id = (args.get("school_id") or "").strip()
    if not school_id:
        return [TextContent(type="text", text="school_id is required.")]

    school = load_school(school_id)

    if school is None:
        queue_entry = get_queue_entry(school_id)
        if queue_entry:
            lines = [
                f"School Not Yet Researched: {queue_entry.get('name', school_id)}",
                "==========================================",
                "This school is in the research queue but has not yet been scored.",
                "",
                "Known information from the queue:",
                f"  Country: {queue_entry.get('country', '??')}",
                f"  City: {queue_entry.get('city', 'unknown')}",
                f"  Region: {queue_entry.get('region', 'unknown')}",
                f"  URL: {queue_entry.get('url', 'unknown')}",
                f"  Research status: {queue_entry.get('research_status', 'pending')}",
            ]
            kr = queue_entry.get("known_rankings") or {}
            if kr:
                lines.append("  Known approximate rankings:")
                for k, v in kr.items():
                    if v is not None:
                        lines.append(f"    {k}: ~#{v}")
            lines.append(
                "\nTo prioritise this school for research, open a GitHub issue using "
                "the School Submission template."
            )
        else:
            lines = [
                f"School Not Found: '{school_id}'",
                "This school ID was not found in the database or research queue.",
                "",
                "Tips:",
                "  - School IDs are slugs like 'harvard-law', 'oxford-law', 'nus-law'.",
                "  - Use search_schools to browse what is available.",
            ]
        return [TextContent(type="text", text="\n".join(lines))]

    # Build full profile
    scores = school.scores
    practical = school.practical_skills_score
    practical_bd = school.practical_skills_breakdown
    meta = school.meta_score
    tier = school.ranking_tier or "unranked"
    last_verified = school.last_verified or "never (unverified)"
    last_researched = school.last_researched or "never"
    country = school.country or "??"
    region = infer_region(school) or "unknown region"
    url = school.url or "n/a"

    courses = school.courses or []
    programs = school.programs or []
    faculty = school.faculty or []
    partnerships = school.partnerships or []
    orgs = school.student_orgs or []
    gaps = school.press_release_gap or []
    ext = school.external_rankings

    scores_dict = scores.model_dump() if scores else {}

    lines = [
        f"Full Profile: {school.name or school_id}",
        f"{'=' * (len(school.name or school_id) + 14)}",
        "",
        f"Country: {country}  |  Region: {region}",
        f"URL: {url}",
        f"Last researched: {last_researched}  |  Last verified: {last_verified}",
        "",
        "SCORES",
        "------",
        f"  Tech-Friendliness Score : {scores_dict.get('total', 'n/a')}/100  (Tier: {tier})",
        f"  Practical Skills Score  : {practical if practical is not None else 'n/a'}/100",
        f"  Meta Score              : {meta if meta is not None else 'n/a'}/100",
        "",
        "  Tech Score Breakdown:",
        f"    Curriculum – Courses     : {scores_dict.get('curriculum_courses', 'n/a')}/20",
        f"    Curriculum – Practical   : {scores_dict.get('curriculum_practical', 'n/a')}/10",
        f"    Curriculum – Clinics     : {scores_dict.get('curriculum_clinics', 'n/a')}/10",
        f"    Infrastructure – Center  : {scores_dict.get('infrastructure_center', 'n/a')}/10",
        f"    Infrastructure – Jt Deg  : {scores_dict.get('infrastructure_joint_degrees', 'n/a')}/10",
        f"    Infrastructure – Partners: {scores_dict.get('infrastructure_partnerships', 'n/a')}/10",
        f"    Faculty – Expertise      : {scores_dict.get('faculty_expertise', 'n/a')}/10",
        f"    Faculty – Research       : {scores_dict.get('faculty_research', 'n/a')}/10",
        f"    Community – Orgs         : {scores_dict.get('community_orgs', 'n/a')}/5",
        f"    Community – Careers      : {scores_dict.get('community_careers', 'n/a')}/5",
        f"    PRG Penalty              : {scores_dict.get('press_release_gap_penalty', 0)}  (max -20)",
    ]

    if practical_bd:
        bd = practical_bd.model_dump()
        lines += [
            "",
            "  Practical Skills Breakdown:",
            f"    Clinical Programs      : {bd.get('clinical_programs', 'n/a')}/25",
            f"    Skills Curriculum      : {bd.get('skills_curriculum', 'n/a')}/25",
            f"    Experiential Placements: {bd.get('experiential_placements', 'n/a')}/25",
            f"    Professional Readiness : {bd.get('professional_readiness', 'n/a')}/25",
        ]

    # External rankings
    lines += ["", "EXTERNAL RANKINGS", "-----------------"]
    rank_names = {
        "qs_law": "QS Law",
        "the_law": "Times Higher Education Law",
        "arwu_law": "ARWU Law",
        "usnews_law": "US News Law (domestic)",
        "usnews_global_law": "US News Global Law",
        "vault_law": "Vault Law",
    }
    has_any_rank = False
    if ext:
        ext_dict = ext.model_dump()
        for key, label in rank_names.items():
            entry = ext_dict.get(key)
            if entry and isinstance(entry, dict):
                rank_val = entry.get("rank")
                year = entry.get("year", "?")
                lines.append(f"  {label}: #{rank_val} ({year})")
                has_any_rank = True
    if not has_any_rank:
        lines.append("  No external ranking data available.")

    # Courses
    lines += [f"", f"COURSES ({len(courses)} listed)", "-------"]
    if courses:
        for c in courses:
            verified = f" [verified {c.year_verified}]" if c.year_verified else " [UNVERIFIED]"
            ctype = (c.type or "elective").upper()
            lines.append(f"  [{ctype}] {c.title or 'Untitled'}{verified}")
    else:
        lines.append("  No courses listed.")

    # Programs
    lines += [f"", f"PROGRAMS & CENTRES ({len(programs)} listed)", "------------------"]
    if programs:
        for p in programs:
            ptype = (p.type or "other").replace("_", " ").title()
            status = (p.status or "unknown").upper()
            tech_tag = " [TECH FOCUS]" if p.tech_focus else ""
            lines.append(f"  [{status}] {p.name or 'Unnamed'} ({ptype}){tech_tag}")
            if p.description:
                lines.append(f"           {p.description[:100]}")
    else:
        lines.append("  No programs listed.")

    # Faculty
    lines += [f"", f"FACULTY ({len(faculty)} listed)", "-------"]
    if faculty:
        for f_ in faculty:
            apt = f_.appointment_type or "unknown"
            expertise = ", ".join((f_.tech_expertise or [])[:3])
            lines.append(f"  {f_.name or 'Unknown'} ({apt})")
            if expertise:
                lines.append(f"    Tech expertise: {expertise}")
    else:
        lines.append("  No faculty listed.")

    # Partnerships
    lines += [f"", f"PARTNERSHIPS ({len(partnerships)} listed)", "------------"]
    if partnerships:
        for p in partnerships:
            active_str = "ACTIVE" if p.active else ("?" if p.active is None else "INACTIVE")
            lines.append(f"  [{active_str}] {p.org or 'Unknown'} ({p.type or 'unknown'})")
    else:
        lines.append("  No partnerships listed.")

    # Student orgs
    lines += [f"", f"STUDENT ORGANISATIONS ({len(orgs)} listed)", "---------------------"]
    if orgs:
        for o in orgs:
            active_str = "ACTIVE" if o.active else ("?" if o.active is None else "INACTIVE")
            lines.append(f"  [{active_str}] {o.name or 'Unknown'}")
    else:
        lines.append("  No student organisations listed.")

    # Press release gaps
    if gaps:
        lines += ["", "PRESS RELEASE GAPS — ACCOUNTABILITY SECTION", "-------------------------------------------"]
        lines.append(
            f"  This school has {len(gaps)} documented press release gap(s). "
            "These are programs that were publicly marketed but may no longer exist or function as described."
        )
        for i, g in enumerate(gaps, start=1):
            severity = (g.severity or "unassigned").upper()
            lines += [
                "",
                f"  Gap #{i} (Severity: {severity}, Penalty: {g.penalty_points or 'TBD'} pts)",
                f"  Claimed : {g.claimed or 'N/A'}",
                f"  Reality : {g.reality or 'Not yet documented'}",
                f"  Year claimed: {g.year_claimed or 'unknown'}",
            ]
            if g.evidence_url:
                lines.append(f"  Evidence: {g.evidence_url}")
            if g.current_url:
                lines.append(f"  Current : {g.current_url}")
    else:
        lines += ["", "PRESS RELEASE GAPS", "------------------", "  None documented."]

    if school.notes:
        lines += ["", "NOTES", "-----", f"  {school.notes}"]

    lines += [
        "",
        "DATA FRESHNESS WARNING",
        "----------------------",
        "  All data with year_verified=null has NOT been confirmed by a researcher.",
        f"  last_verified={last_verified} reflects the last human review date.",
        "  Treat unverified data as indicative only.",
    ]

    return [TextContent(type="text", text="\n".join(lines))]
