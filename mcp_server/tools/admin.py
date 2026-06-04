"""
mcp_server/tools/admin.py

Administrative / accountability MCP tools:
  - explain_ranking
  - flag_press_release_gaps
  - get_research_queue_stats
"""

from __future__ import annotations

from mcp.types import TextContent, Tool

from lawschool.data import get_research_stats, load_all_schools

# ---------------------------------------------------------------------------
# explain_ranking
# ---------------------------------------------------------------------------

EXPLAIN_TOOL_DEFINITION = Tool(
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
)

_EXPLAIN_TEXT = """
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

# ---------------------------------------------------------------------------
# flag_press_release_gaps
# ---------------------------------------------------------------------------

FLAG_TOOL_DEFINITION = Tool(
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
)

# ---------------------------------------------------------------------------
# get_research_queue_stats
# ---------------------------------------------------------------------------

STATS_TOOL_DEFINITION = Tool(
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
)

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

# server.py expects a single TOOL_DEFINITION per module; for admin we have three.
# We expose them all via a list and handle routing in handle().

TOOL_DEFINITIONS = [EXPLAIN_TOOL_DEFINITION, FLAG_TOOL_DEFINITION, STATS_TOOL_DEFINITION]


async def handle_explain(args: dict) -> list[TextContent]:
    return [TextContent(type="text", text=_EXPLAIN_TEXT)]


async def handle_flag(args: dict) -> list[TextContent]:
    schools = load_all_schools()
    gap_schools = [s for s in schools if s.press_release_gap]

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
            gaps = s.press_release_gap or []
            prg_penalty = (s.scores.press_release_gap_penalty if s.scores else 0) or 0
            tech_total = s.scores.total if s.scores else None
            lines += [
                f"SCHOOL: {s.name or s.id} ({s.country or '??'})",
                f"  Tech Score: {tech_total if tech_total is not None else 'n/a'}/100  |  PRG Penalty: {prg_penalty} pts",
                f"  Number of gaps: {len(gaps)}",
            ]
            for i, g in enumerate(gaps, start=1):
                severity = (g.severity or "unassigned").upper()
                year_claimed = g.year_claimed or "unknown"
                lines += [
                    "",
                    f"  Gap #{i} — Severity: {severity}  |  Year claimed: {year_claimed}",
                    f"  Claimed : {g.claimed or 'N/A'}",
                    f"  Reality : {g.reality or 'Not yet documented'}",
                ]
                if g.evidence_url:
                    lines.append(f"  Evidence: {g.evidence_url}")
                if g.current_url:
                    lines.append(f"  Current : {g.current_url}")
                lines.append(
                    f"  Penalty : {f'{g.penalty_points} pts' if g.penalty_points is not None else 'TBD — awaiting severity assignment'}"
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


async def handle_stats(args: dict) -> list[TextContent]:
    stats = get_research_stats()

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
