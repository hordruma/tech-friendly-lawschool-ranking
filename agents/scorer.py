#!/usr/bin/env python3
"""
agents/scorer.py — thin CLI wrapper for the scoring library.

Scoring logic lives in src/lawschool/scoring/.

Usage:
    python agents/scorer.py data/schools/harvard-law.json
    python agents/scorer.py data/schools/harvard-law.json --output data/schools/harvard-law.json
    python agents/scorer.py data/schools/harvard-law.json --format json
"""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from lawschool.schema import LawSchool
from lawschool.scoring import compute_tech_score, compute_practical_score

console = Console()


def tier_color(tier: str) -> str:
    return {
        "S": "bold magenta",
        "A": "bold green",
        "B": "bold yellow",
        "C": "bold orange3",
        "D": "bold red",
        "unranked": "dim",
    }.get(tier, "white")


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Write updated JSON to this path")
@click.option("--format", "output_format", type=click.Choice(["human", "json"]), default="human")
@click.option("--write-scores", is_flag=True, default=False,
              help="Write computed scores back into the JSON file")
def main(input_file: str, output: str | None, output_format: str, write_scores: bool):
    """Score a law school JSON file against the ranking criteria."""
    path = Path(input_file)
    school = LawSchool.from_json_file(path).model_dump(mode="json")

    result = compute_tech_score(school)
    scores = result["scores"]
    tier = result["ranking_tier"]
    notes = result["scoring_notes"]

    practical_result = compute_practical_score(school)

    if output_format == "json":
        click.echo(json.dumps({
            "scores": scores,
            "ranking_tier": tier,
            "practical_skills_score": practical_result["practical_skills_score"],
            "practical_skills_breakdown": practical_result["breakdown"],
        }, indent=2))
        return

    # Human-readable table — Tech Score
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
        note_str = " | ".join(note_lines[:2])
        color = "red" if val < 0 else ("green" if val == max_pts and max_pts > 0 else "white")
        table.add_row(label, f"[{color}]{val}[/{color}]", str(max_pts), note_str)

    console.print(table)
    tc = tier_color(tier)
    console.print(f"\n[bold]Tech Score:[/bold] {scores['total']}/100   [bold]Tier:[/bold] [{tc}]{tier}[/{tc}]")

    # Practical Skills table
    console.rule("[bold cyan]Practical Skills Score[/bold cyan]")
    ps_table = Table(show_header=True, header_style="bold cyan")
    ps_table.add_column("Dimension", style="dim", width=35)
    ps_table.add_column("Score", justify="right", width=8)
    ps_table.add_column("Max", justify="right", width=6)
    ps_table.add_column("Notes", overflow="fold")

    ps_criteria = [
        ("Clinical Programs",       "clinical_programs",       25),
        ("Skills Curriculum",       "skills_curriculum",       25),
        ("Experiential Placements", "experiential_placements", 25),
        ("Professional Readiness",  "professional_readiness",  25),
    ]
    ps_breakdown = practical_result["breakdown"]
    ps_notes = practical_result["scoring_notes"]

    for label, key, max_pts in ps_criteria:
        val = ps_breakdown.get(key, 0)
        note_lines = ps_notes.get(key, [])
        note_str = " | ".join(note_lines[:2])
        color = "green" if val == max_pts else "white"
        ps_table.add_row(label, f"[{color}]{val}[/{color}]", str(max_pts), note_str)

    console.print(ps_table)
    ps_total = practical_result["practical_skills_score"]
    console.print(f"\n[bold]Practical Skills Score:[/bold] {ps_total}/100\n")

    if write_scores or output:
        out_path = Path(output) if output else path
        school["scores"] = scores
        school["ranking_tier"] = tier
        school["practical_skills_score"] = practical_result["practical_skills_score"]
        school["practical_skills_breakdown"] = practical_result["breakdown"]
        out_path.write_text(json.dumps(school, indent=2, ensure_ascii=False))
        console.print(f"[green]Scores written to {out_path}[/green]")


if __name__ == "__main__":
    main()
