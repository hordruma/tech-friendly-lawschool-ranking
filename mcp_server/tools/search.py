"""
mcp-server/tools/search.py

search_schools MCP tool.
"""

from __future__ import annotations

from mcp.types import TextContent, Tool

from lawschool.data import load_all_schools
from mcp_server._helpers import (
    _VALID_REGIONS,
    _VALID_SORT,
    _VALID_TIERS,
    filter_schools,
    school_summary_text,
    sort_schools,
)

TOOL_DEFINITION = Tool(
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
)


async def handle(args: dict) -> list[TextContent]:
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

    if region and region not in _VALID_REGIONS:
        return [TextContent(type="text", text=f"Invalid region '{region}'. Valid options: {', '.join(sorted(_VALID_REGIONS))}")]
    if tier and tier.upper() not in _VALID_TIERS:
        return [TextContent(type="text", text=f"Invalid tier '{tier}'. Valid options: S, A, B, C, D")]
    if sort_by and sort_by not in _VALID_SORT:
        sort_by = "meta_score"

    all_schools = load_all_schools()
    filtered = filter_schools(
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
    sorted_s = sort_schools(filtered, sort_by=sort_by)
    paginated = sorted_s[:limit]

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
        "Law School Search Results",
        "========================",
        f"Database size: {len(all_schools)} fully researched school(s)",
        f"Filters applied: {filter_str}",
        f"Matching schools: {len(filtered)}",
        f"Showing: top {len(paginated)} sorted by {sort_by}",
        "",
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
            lines.append(school_summary_text(s, rank=rank))
            lines.append("")

        lines.append(
            "Data completeness note: scores marked 'n/a' indicate fields not yet "
            "researched or where data is missing. last_verified=null means no human "
            "reviewer has confirmed this data."
        )

    return [TextContent(type="text", text="\n".join(lines))]
