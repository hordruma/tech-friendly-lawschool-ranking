"""
mcp_server/tools/career.py

find_schools_for_career MCP tool.
"""

from __future__ import annotations

from mcp.types import TextContent, Tool

from lawschool.data import load_all_schools
from lawschool.schema import VALID_REGIONS as _VALID_REGIONS
from mcp_server._helpers import (
    filter_schools,
    school_summary_text,
    sort_schools,
)

TOOL_DEFINITION = Tool(
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
)


async def handle(args: dict) -> list[TextContent]:
    career_goal = (args.get("career_goal") or "").strip()
    region = args.get("region")
    limit = min(int(args.get("limit", 5)), 20)

    if not career_goal:
        return [TextContent(type="text", text="career_goal is required.")]

    goal_lower = career_goal.lower()

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

    all_schools = load_all_schools()
    filtered = filter_schools(
        all_schools,
        region=region,
        min_tech_score=min_tech if min_tech > 0 else None,
        min_practical_score=min_practical if min_practical > 0 else None,
        requires_ai_course=requires_ai,
        has_legaltech_clinic=has_clinic,
        joint_degree_available=joint_deg,
    )
    sorted_s = sort_schools(filtered, sort_by=sort_by)
    recommendations = sorted_s[:limit]

    lines = [
        "Career-Focused Law School Recommendations",
        "=========================================",
        f"Goal: {career_goal}",
        "",
        explanation_prefix,
        "",
        "What to look for:",
    ]
    for note in profile_notes:
        lines.append(f"  - {note}")

    if region:
        lines.append(f"  - Region filtered to: {region}")

    lines += ["", f"Top {len(recommendations)} Recommendations (sorted by {sort_by})", "-" * 40, ""]

    if not recommendations:
        lines.append(
            "No schools currently in the database match all the criteria for this goal. "
            "This may be because only a small number of schools have been fully researched. "
            "Try the search_schools tool with relaxed filters or check get_research_queue_stats "
            "to see how many schools are pending."
        )
    else:
        for rank, s in enumerate(recommendations, start=1):
            lines.append(school_summary_text(s, rank=rank))
            relevant_programs = [
                p.name for p in (s.programs or [])
                if p.tech_focus and p.status in ("active", "unknown")
            ]
            if relevant_programs:
                lines.append(f"  Career-relevant programs: {', '.join(str(p) for p in relevant_programs[:3])}")
            lines.append("")

    lines += [
        "",
        "Tip: Use get_school_profile <school_id> for the full details on any of these schools.",
        "Tip: Use compare_schools to do a head-to-head comparison of your finalists.",
        f"Data note: Only {len(all_schools)} schools fully researched. "
        "Many more are in the queue — use get_research_queue_stats for coverage details.",
    ]

    return [TextContent(type="text", text="\n".join(lines))]
