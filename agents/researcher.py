#!/usr/bin/env python3
"""
agents/researcher.py — thin CLI wrapper for the research agent.

Agent logic lives in src/lawschool/research/agent.py.

Usage:
    python researcher.py --school "Harvard Law School" --output data/schools/harvard-law.json
    python researcher.py --school "NUS Faculty of Law" --url https://law.nus.edu.sg
    python researcher.py --school "College of Law Australia" --dry-run

Environment variables (required):
    ANTHROPIC_API_KEY
    TAVILY_API_KEY

Optional:
    OPENAI_API_KEY           (for OpenAI fallback)
    TYPEDB_HOST / TYPEDB_PORT / TYPEDB_DATABASE  (for ingest after research)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from lawschool.research.agent import research_school

load_dotenv()

console = Console()


@click.command()
@click.option("--school", required=True, help='Full name of the law school, e.g. "Harvard Law School"')
@click.option("--url", default=None, help="Official website URL of the school")
@click.option("--output", "-o", default=None, help="Output path for the school JSON")
@click.option("--merge", is_flag=True, default=False,
              help="Merge with existing file at output path rather than overwrite")
@click.option("--dry-run", is_flag=True, default=False,
              help="Print extracted JSON without writing to file")
@click.option("--skip-gap-analysis", is_flag=True, default=False,
              help="Skip the second press release gap analysis pass")
def main(school: str, url: str | None, output: str | None, merge: bool,
         dry_run: bool, skip_gap_analysis: bool):
    """Research a law school and produce a structured JSON record."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY not set.[/red]")
        sys.exit(1)

    if not os.getenv("TAVILY_API_KEY"):
        console.print("[yellow]Warning: TAVILY_API_KEY not set. Research will be limited.[/yellow]")

    console.rule(f"[bold]Researching: {school}[/bold]")

    merge_path = Path(output) if (merge and output) else None

    try:
        school_data = asyncio.run(
            research_school(
                school_name=school,
                school_url=url,
                skip_gap_analysis=skip_gap_analysis,
                merge_path=merge_path,
            )
        )
    except Exception as e:
        console.print(f"[red]Research failed: {e}[/red]")
        sys.exit(1)

    output_json = json.dumps(school_data, indent=2, ensure_ascii=False)

    if dry_run:
        console.print(Markdown("```json\n" + output_json + "\n```"))
        return

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json)
        console.print(f"\n[green]Wrote {out_path}[/green]")
    else:
        click.echo(output_json)


if __name__ == "__main__":
    main()
