"""
mcp-server/tools/compare.py

compare_schools MCP tool.
"""

from __future__ import annotations

from mcp.types import TextContent, Tool

from lawschool.data import load_school
from _helpers import infer_region, prg_warning

TOOL_DEFINITION = Tool(
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
)


async def handle(args: dict) -> list[TextContent]:
    school_ids: list[str] = args.get("school_ids") or []

    if len(school_ids) < 2:
        return [TextContent(type="text", text="Please provide at least 2 school IDs to compare.")]
    if len(school_ids) > 5:
        school_ids = school_ids[:5]

    loaded = []
    not_found: list[str] = []
    for sid in school_ids:
        s = load_school(sid)
        if s is None:
            not_found.append(sid)
            loaded.append(None)
        else:
            loaded.append(s)

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
        f"{(s.name if s else sid)[:20]:^20}"
        for s, sid in zip(loaded, school_ids)
    )

    lines = [
        "Side-by-Side School Comparison",
        "==============================",
        "",
        col_header,
        header_row(),
        row("Country", lambda s: s.country),
        row("Region", lambda s: infer_region(s) or "unknown"),
        row("Tier", lambda s: s.ranking_tier or "unranked"),
        row("Tech Score (/100)", lambda s: s.scores.total if s.scores else None),
        row("Practical Score (/100)", lambda s: s.practical_skills_score),
        row("Meta Score (/100)", lambda s: s.meta_score),
        header_row(),
        row("  Courses (total)", lambda s: len(s.courses or [])),
        row("  AI/ML courses (verified)", lambda s: sum(
            1 for c in (s.courses or [])
            if c.year_verified is not None
            and any(t in (c.topics or []) for t in
                    ("artificial_intelligence", "machine_learning", "legal_technology"))
        )),
        row("  Required tech courses", lambda s: sum(
            1 for c in (s.courses or [])
            if c.type == "required" and c.year_verified is not None
        )),
        header_row(),
        row("  Tech clinics (active)", lambda s: sum(
            1 for p in (s.programs or [])
            if p.type == "clinic" and p.tech_focus and p.status == "active"
        )),
        row("  All clinics (active)", lambda s: sum(
            1 for p in (s.programs or [])
            if p.type == "clinic" and p.status == "active"
        )),
        row("  Joint degrees", lambda s: sum(
            1 for p in (s.programs or [])
            if p.type == "joint_degree" and p.status in ("active", None)
        )),
        row("  LegalTech centre", lambda s: "YES" if any(
            p.type == "center" and p.tech_focus and p.status == "active"
            for p in (s.programs or [])
        ) else "no"),
        header_row(),
        row("  Faculty (total)", lambda s: len(s.faculty or [])),
        row("  Tech faculty", lambda s: sum(
            1 for f in (s.faculty or [])
            if f.tech_expertise or f.research_areas
        )),
        row("  Industry partnerships", lambda s: len(s.partnerships or [])),
        row("  Student orgs", lambda s: len(s.student_orgs or [])),
        header_row(),
        row("  QS Law rank", lambda s: (
            (s.external_rankings.qs_law.rank if s.external_rankings and s.external_rankings.qs_law else None)
        )),
        row("  THE Law rank", lambda s: (
            (s.external_rankings.the_law.rank if s.external_rankings and s.external_rankings.the_law else None)
        )),
        header_row(),
        row("  PRG warnings", lambda s: len(s.press_release_gap or [])),
        row("  Last verified", lambda s: s.last_verified or "never"),
    ]

    # Surface any PRG warnings prominently
    prg_lines = []
    for s, sid in zip(loaded, school_ids):
        if s is not None:
            prg = prg_warning(s)
            if prg:
                prg_lines.append(f"\n{s.name or sid}:{prg}")
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
