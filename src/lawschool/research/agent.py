"""
src/lawschool/research/agent.py

Research agent logic for the Tech-Friendly Law School Ranking.

Given a school name (and optional URL), this module:
1. Uses Tavily search to find: current course catalog, legaltech programs,
   faculty pages, and recent press releases.
2. Uses Claude (Anthropic SDK) to extract structured data matching the JSON schema.
3. Identifies press release gaps by comparing dated claims vs current catalog.

This module contains only reusable logic — no CLI.
The CLI wrapper lives in agents/researcher.py.

Environment variables (required):
    ANTHROPIC_API_KEY
    TAVILY_API_KEY
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import date
from pathlib import Path

import anthropic
import httpx
from pydantic import BaseModel, Field
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Rate limiting
TAVILY_RATE_LIMIT = 1.0   # seconds between requests
ANTHROPIC_RATE_LIMIT = 0.5

# Model configuration
CLAUDE_MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 8192

# Schema file (resolved relative to repo root so it works from any CWD)
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
SCHEMA_FILE = _REPO_ROOT / "data" / "schema" / "school.schema.json"


# ──────────────────────────────────────────────
# Pydantic models for structured extraction
# ──────────────────────────────────────────────

class CourseExtract(BaseModel):
    id: str
    title: str
    credits: float | None = None
    type: str  # required | elective | certificate
    topics: list[str] = Field(default_factory=list)
    source_url: str | None = None
    year_verified: int | None = None
    notes: str | None = None


class ProgramExtract(BaseModel):
    id: str
    name: str
    type: str  # clinic | joint_degree | certificate | center | incubator | other
    description: str | None = None
    tech_focus: bool = False
    source_url: str | None = None
    year_verified: int | None = None
    status: str = "unknown"
    notes: str | None = None


class FacultyExtract(BaseModel):
    name: str
    title: str | None = None
    appointment_type: str | None = None
    tech_expertise: list[str] = Field(default_factory=list)
    research_areas: list[str] = Field(default_factory=list)
    profile_url: str | None = None


class PartnershipExtract(BaseModel):
    org: str
    type: str | None = None
    description: str | None = None
    year_start: int | None = None
    source_url: str | None = None
    active: bool | None = None


class StudentOrgExtract(BaseModel):
    name: str
    focus: str | None = None
    url: str | None = None
    active: bool | None = None
    year_verified: int | None = None


class PressReleaseGapExtract(BaseModel):
    claimed: str
    reality: str
    evidence_url: str | None = None
    current_url: str | None = None
    year_claimed: int | None = None
    year_verified: int | None = None
    severity: str | None = None
    penalty_points: float | None = None


class SchoolExtract(BaseModel):
    id: str
    name: str
    country: str
    jurisdiction: str | None = None
    url: str
    last_researched: str | None = None
    last_verified: None = None  # always null from agent
    accreditation: list[dict] = Field(default_factory=list)
    courses: list[CourseExtract] = Field(default_factory=list)
    programs: list[ProgramExtract] = Field(default_factory=list)
    faculty: list[FacultyExtract] = Field(default_factory=list)
    partnerships: list[PartnershipExtract] = Field(default_factory=list)
    student_orgs: list[StudentOrgExtract] = Field(default_factory=list)
    press_release_gap: list[PressReleaseGapExtract] = Field(default_factory=list)
    scores: None = None  # always null from agent — scorer handles this
    ranking_tier: None = None
    notes: str | None = None


# ──────────────────────────────────────────────
# Tavily search
# ──────────────────────────────────────────────

async def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """Perform a Tavily search and return results."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        console.print("[yellow]TAVILY_API_KEY not set — skipping search.[/yellow]")
        return []

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": True,
                "include_raw_content": False,
                "max_results": max_results,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])


async def gather_research(school_name: str, school_url: str | None) -> dict[str, list[dict]]:
    """Run multiple Tavily searches to gather research data."""
    queries = {
        "courses": f'"{school_name}" legaltech AI law courses curriculum 2024 2025',
        "programs": f'"{school_name}" legaltech center institute joint degree clinic technology',
        "faculty": f'"{school_name}" faculty professor artificial intelligence technology law expertise',
        "press_releases": f'"{school_name}" legaltech program launch announcement 2020 2021 2022 2023 2024',
        "press_current": f'site:{school_url or school_name} legaltech OR "legal technology" OR AI OR "artificial intelligence"',
    }

    results = {}
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        for key, query in queries.items():
            task = progress.add_task(f"Searching: {key}…", total=None)
            try:
                await asyncio.sleep(TAVILY_RATE_LIMIT)
                results[key] = await tavily_search(query, max_results=5)
                progress.update(task, description=f"[green]✓[/green] {key}: {len(results[key])} results")
            except Exception as e:
                console.print(f"[red]Search failed for '{key}': {e}[/red]")
                results[key] = []
            progress.remove_task(task)

    return results


# ──────────────────────────────────────────────
# Claude extraction
# ──────────────────────────────────────────────

def format_search_results(results: dict[str, list[dict]]) -> str:
    """Format search results into a string for Claude."""
    sections = []
    for category, items in results.items():
        if not items:
            continue
        section = f"## Search results: {category}\n\n"
        for r in items:
            section += f"### {r.get('title', 'Untitled')}\n"
            section += f"URL: {r.get('url', 'N/A')}\n"
            section += f"Content: {r.get('content', '')[:800]}\n\n"
        sections.append(section)
    return "\n".join(sections)


def build_extraction_prompt(school_name: str, school_url: str, search_content: str, schema: dict) -> str:
    """Build the Claude extraction prompt."""
    today = date.today().isoformat()
    schema_str = json.dumps(schema, indent=2)

    return f"""You are a legal education researcher extracting structured data for the Tech-Friendly Law School Ranking.

Today's date: {today}

## Task

Extract structured data about **{school_name}** from the search results below and output a JSON object matching the schema exactly.

## School URL
{school_url}

## Schema
```json
{schema_str}
```

## Key instructions

1. **Courses**: Only include courses with substantial technology content. Include `year_verified` only if you found solid evidence the course is in the *current* catalog (within 18 months). Topics must be from the `enum` in the schema.

2. **Programs**: Include centers, joint degrees, clinics, incubators. Set `status` to "active" only if you have current evidence. Set "unknown" if you found it but cannot confirm current status.

3. **Faculty**: Only include faculty with genuine tech/AI/legaltech expertise. Identify whether they are tenure-track, clinical, visiting, or adjunct. Don't include adjuncts for unverified minor mentions.

4. **Press Release Gaps**: Look carefully for programs, centers, or initiatives that were announced but may no longer exist. Compare press releases from 2019–2023 against current catalog/website evidence. If a center was announced but there's no current web evidence, flag it.

5. **ID field**: Create a URL-safe slug from the school name (lowercase, hyphens, no special chars).

6. **Country**: Use ISO 3166-1 alpha-2 code (US, GB, AU, SG, DE, etc.).

7. **Set `last_researched`** to today's date: {today}

8. **Set `last_verified`** to null — human review is required before setting this.

9. **Set `scores`** to null — the scorer script handles this.

10. Be conservative: if you're not sure a program is active, set status "unknown" rather than "active".

## Search Results

{search_content}

## Output

Respond with ONLY a valid JSON object matching the schema. No markdown fences, no explanation text, just the raw JSON.
"""


async def extract_with_claude(school_name: str, school_url: str, search_results: dict) -> dict:
    """Use Claude to extract structured school data from search results."""
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    schema = json.loads(SCHEMA_FILE.read_text())
    search_content = format_search_results(search_results)
    prompt = build_extraction_prompt(school_name, school_url, search_content, schema)

    console.print(f"[blue]Extracting structured data with {CLAUDE_MODEL}…[/blue]")

    await asyncio.sleep(ANTHROPIC_RATE_LIMIT)

    message = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system="""You are a meticulous legal education researcher who extracts structured data
from web sources. You always output valid JSON that exactly matches the provided schema.
You flag uncertainty rather than inventing data. You are particularly alert to 'press release gaps' —
cases where schools announce programs that later disappear.""",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        console.print(f"[red]JSON parse error: {e}[/red]")
        console.print("[yellow]Raw output:[/yellow]")
        console.print(raw[:500])
        raise


async def run_gap_analysis(school_name: str, school_data: dict, search_results: dict) -> list[dict]:
    """Second Claude pass: specifically look for press release gaps."""
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    press_releases = search_results.get("press_releases", [])
    current_content = search_results.get("press_current", [])

    if not press_releases:
        return []

    pr_text = format_search_results({"press_releases": press_releases, "current": current_content})
    existing_programs = school_data.get("programs", [])

    prompt = f"""You are auditing a law school's marketing claims against current reality, specifically looking for "Press Release Gaps" — programs, centers, or initiatives that were publicly announced but may no longer exist.

School: {school_name}

## Existing programs found (currently active/unknown):
{json.dumps([p.get('name') for p in existing_programs], indent=2)}

## Press releases and historical announcements:
{pr_text}

## Task:
1. Identify any announced programs, centers, courses, or initiatives from the press release content that do NOT appear in the current active programs list.
2. For each identified gap, provide structured evidence.
3. Be conservative — only flag something as a gap if you have clear evidence of an announcement AND clear evidence (or absence of evidence) that it no longer exists.

For each gap, output a JSON array item with:
{{
    "claimed": "What was publicly claimed (quote or close paraphrase of the claim)",
    "reality": "What appears to be currently true based on search evidence",
    "evidence_url": "URL of the original claim if available",
    "current_url": null,
    "year_claimed": <year of claim or null>,
    "year_verified": null,
    "severity": null,
    "penalty_points": null
}}

Respond with ONLY a JSON array (can be empty []).
"""

    await asyncio.sleep(ANTHROPIC_RATE_LIMIT)

    message = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        gaps = json.loads(raw)
        return gaps if isinstance(gaps, list) else []
    except json.JSONDecodeError:
        return []


# ──────────────────────────────────────────────
# Merge with existing file
# ──────────────────────────────────────────────

def merge_with_existing(new_data: dict, existing_path: Path) -> dict:
    """
    Merge agent-researched data with an existing school JSON.
    Existing human-verified data takes precedence. Agent data fills gaps.
    """
    if not existing_path.exists():
        return new_data

    existing = json.loads(existing_path.read_text())

    # Fields where existing (human-verified) data always wins
    protected = ["last_verified", "scores", "ranking_tier"]
    for field in protected:
        if existing.get(field) is not None:
            new_data[field] = existing[field]

    # Merge courses: keep existing verified courses, add new ones
    existing_course_ids = {c["id"] for c in (existing.get("courses") or [])}
    for course in (new_data.get("courses") or []):
        if course["id"] not in existing_course_ids:
            existing.setdefault("courses", []).append(course)
    new_data["courses"] = existing.get("courses", [])

    # Merge programs similarly
    existing_program_ids = {p["id"] for p in (existing.get("programs") or [])}
    for prog in (new_data.get("programs") or []):
        if prog["id"] not in existing_program_ids:
            existing.setdefault("programs", []).append(prog)
    new_data["programs"] = existing.get("programs", [])

    # Faculty: keep existing, add new by name
    existing_faculty_names = {f["name"] for f in (existing.get("faculty") or [])}
    for fac in (new_data.get("faculty") or []):
        if fac["name"] not in existing_faculty_names:
            existing.setdefault("faculty", []).append(fac)
    new_data["faculty"] = existing.get("faculty", [])

    # PRG: merge by claimed text
    existing_claims = {g["claimed"] for g in (existing.get("press_release_gap") or [])}
    for gap in (new_data.get("press_release_gap") or []):
        if gap["claimed"] not in existing_claims:
            existing.setdefault("press_release_gap", []).append(gap)
    new_data["press_release_gap"] = existing.get("press_release_gap", [])

    return new_data


# ──────────────────────────────────────────────
# High-level entry point
# ──────────────────────────────────────────────

async def research_school(
    school_name: str,
    school_url: str | None,
    skip_gap_analysis: bool = False,
    merge_path: Path | None = None,
) -> dict:
    """
    Full research pipeline for a single school.

    Returns the extracted school dict (not yet written to disk).
    """
    search_results = await gather_research(school_name, school_url)

    school_data = await extract_with_claude(school_name, school_url or school_name, search_results)

    if not skip_gap_analysis:
        console.print("[blue]Running press release gap analysis…[/blue]")
        try:
            new_gaps = await run_gap_analysis(school_name, school_data, search_results)
            if new_gaps:
                existing_claims = {g.get("claimed") for g in school_data.get("press_release_gap", [])}
                for gap in new_gaps:
                    if gap.get("claimed") not in existing_claims:
                        school_data.setdefault("press_release_gap", []).append(gap)
                console.print(f"[yellow]Gap analysis found {len(new_gaps)} potential gaps.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Gap analysis failed: {e}[/yellow]")

    if merge_path is not None:
        school_data = merge_with_existing(school_data, merge_path)

    return school_data
