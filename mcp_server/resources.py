"""
mcp-server/resources.py

All three MCP resources for the law school ranking server.

Resources
---------
law-schools://methodology      Full CRITERIA.md text
law-schools://schools          JSON summaries of all researched schools
law-schools://research-queue   Coverage stats from top-500.json
"""

from __future__ import annotations

import json

from mcp.types import Resource

from lawschool.data import get_research_stats, load_criteria_text, schools_summary_list

RESOURCE_DEFINITIONS = [
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


async def read_resource(uri_str: str) -> str:
    """Dispatch a resource read by URI string."""
    if uri_str == "law-schools://methodology":
        return load_criteria_text()

    elif uri_str == "law-schools://schools":
        summaries = schools_summary_list()
        return json.dumps(summaries, indent=2, ensure_ascii=False)

    elif uri_str == "law-schools://research-queue":
        stats = get_research_stats()
        return json.dumps(stats, indent=2, ensure_ascii=False)

    else:
        raise ValueError(f"Unknown resource URI: {uri_str}")
