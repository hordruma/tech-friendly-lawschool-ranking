#!/usr/bin/env python3
"""
typedb/ingest.py

Reads all school JSON files from data/schools/ and ingests them into a TypeDB
database. The script is idempotent: existing entities are matched before
insertion (upsert pattern) so re-running does not create duplicates.

Usage:
    uv run python typedb/ingest.py [--host localhost] [--port 1729] [--database lawschools]
    python typedb/ingest.py --schema   # also define the schema before ingesting
    python typedb/ingest.py --reset    # drop and recreate the database, then ingest

Environment variables (fallback):
    TYPEDB_HOST       default: localhost
    TYPEDB_PORT       default: 1729
    TYPEDB_DATABASE   default: lawschools
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

load_dotenv()

console = Console()

# Resolve project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
SCHOOLS_DIR = PROJECT_ROOT / "data" / "schools"
SCHEMA_FILE = PROJECT_ROOT / "typedb" / "schema.tql"


# ──────────────────────────────────────────────
# TypeDB helpers
# ──────────────────────────────────────────────

def get_driver(host: str, port: int):
    """Return a TypeDB driver instance."""
    try:
        from typedb.driver import TypeDB, TypeDBDriver
        return TypeDB.core_driver(f"{host}:{port}")
    except ImportError as e:
        console.print(f"[red]typedb-driver package not installed: {e}[/red]")
        console.print("Run: uv add typedb-driver")
        sys.exit(1)


def ensure_database(driver, db_name: str, reset: bool = False) -> None:
    """Create or reset the target database."""
    databases = driver.databases
    if databases.contains(db_name):
        if reset:
            console.print(f"[yellow]Dropping database '{db_name}' for reset…[/yellow]")
            databases.get(db_name).delete()
        else:
            console.print(f"[green]Database '{db_name}' already exists.[/green]")
            return
    console.print(f"[blue]Creating database '{db_name}'…[/blue]")
    databases.create(db_name)


def define_schema(driver, db_name: str) -> None:
    """Run the schema .tql file against the database."""
    schema_text = SCHEMA_FILE.read_text()
    with driver.session(db_name, driver.SessionType.SCHEMA) as session:
        with session.transaction(driver.TransactionType.WRITE) as tx:
            tx.query.define(schema_text)
            tx.commit()
    console.print("[green]Schema defined.[/green]")


# ──────────────────────────────────────────────
# Ingest helpers — upsert patterns
# ──────────────────────────────────────────────

def _str(v) -> str:
    """Escape a string for TypeQL."""
    if v is None:
        return '""'
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _bool(v) -> str:
    return "true" if v else "false"


def ingest_school(tx, school: dict) -> None:
    """Upsert a single school and all related entities."""
    slug = school["id"]

    # ── Upsert LawSchool entity ──────────────────────────────────────────
    _upsert_school(tx, school)

    # ── Accreditations ──────────────────────────────────────────────────
    for acc in school.get("accreditation") or []:
        _upsert_accreditation(tx, slug, acc)

    # ── Courses ─────────────────────────────────────────────────────────
    for course in school.get("courses") or []:
        _upsert_course(tx, slug, course)

    # ── Programs ────────────────────────────────────────────────────────
    for program in school.get("programs") or []:
        _upsert_program(tx, slug, program)

    # ── Faculty ─────────────────────────────────────────────────────────
    for i, fac in enumerate(school.get("faculty") or []):
        _upsert_faculty(tx, slug, fac, index=i)

    # ── Partnerships ────────────────────────────────────────────────────
    for partnership in school.get("partnerships") or []:
        _upsert_partnership(tx, slug, partnership)

    # ── Student orgs ────────────────────────────────────────────────────
    for i, org in enumerate(school.get("student_orgs") or []):
        _upsert_student_org(tx, slug, org, index=i)

    # ── Press Release Gaps ──────────────────────────────────────────────
    for i, gap in enumerate(school.get("press_release_gap") or []):
        _upsert_prg(tx, slug, gap, index=i)

    # ── External Rankings ───────────────────────────────────────────────
    ext_rankings = school.get("external_rankings") or {}
    for source_id, entry in ext_rankings.items():
        if entry is not None:
            _upsert_external_ranking(tx, slug, source_id, entry)

    # ── Meta scores (prestige-score, meta-score, meta-rank) ─────────────
    _update_meta_scores(tx, school)


def _upsert_school(tx, school: dict) -> None:
    slug = school["id"]
    query = f"""
    match
        $school isa LawSchool, has slug {_str(slug)};
    """
    result = list(tx.query.get(query))
    if result:
        return  # already exists; attributes updated separately

    attrs = [f'has slug {_str(slug)}']
    if school.get("name"):
        attrs.append(f'has full-name {_str(school["name"])}')
    if school.get("country"):
        attrs.append(f'has country-code {_str(school["country"])}')
    if school.get("jurisdiction"):
        attrs.append(f'has jurisdiction {_str(school["jurisdiction"])}')
    if school.get("url"):
        attrs.append(f'has website-url {_str(school["url"])}')
    if school.get("last_researched"):
        attrs.append(f'has last-researched {_str(school["last_researched"])}')
    if school.get("last_verified"):
        attrs.append(f'has last-verified {_str(school["last_verified"])}')
    if school.get("notes"):
        attrs.append(f'has notes {_str(school["notes"])}')

    scores = school.get("scores") or {}
    score_map = {
        "curriculum_courses": "score-curriculum-courses",
        "curriculum_practical": "score-curriculum-practical",
        "curriculum_clinics": "score-curriculum-clinics",
        "infrastructure_center": "score-infra-center",
        "infrastructure_joint_degrees": "score-infra-joint-degrees",
        "infrastructure_partnerships": "score-infra-partnerships",
        "faculty_expertise": "score-faculty-expertise",
        "faculty_research": "score-faculty-research",
        "community_orgs": "score-community-orgs",
        "community_careers": "score-community-careers",
        "press_release_gap_penalty": "score-prg-penalty",
        "total": "score-total",
    }
    for json_key, tql_attr in score_map.items():
        val = scores.get(json_key)
        if val is not None:
            attrs.append(f"has {tql_attr} {float(val)}")

    if school.get("ranking_tier"):
        attrs.append(f'has ranking-tier {_str(school["ranking_tier"])}')

    attr_str = ", ".join(attrs)
    tx.query.insert(f"insert $school isa LawSchool, {attr_str};")


def _upsert_accreditation(tx, school_slug: str, acc: dict) -> None:
    body = acc.get("body", "")
    jur = acc.get("jurisdiction", "")
    status = acc.get("status", "")

    # Check if relation already exists
    check = f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
        $acc isa Accreditation, has accred-body {_str(body)}, has jurisdiction {_str(jur)};
        (school: $school, accreditation: $acc) isa accreditation-holding;
    """
    if list(tx.query.get(check)):
        return

    # Insert accreditation entity and relation
    tx.query.insert(f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
    insert
        $acc isa Accreditation,
            has accred-body {_str(body)},
            has jurisdiction {_str(jur)},
            has accred-status {_str(status)};
        (school: $school, accreditation: $acc) isa accreditation-holding;
    """)


def _upsert_course(tx, school_slug: str, course: dict) -> None:
    cid = f"{school_slug}-{course['id']}"
    # Deduplicate on composite key
    check = f"""
    match
        $c isa Course, has course-id {_str(cid)};
    """
    if list(tx.query.get(check)):
        return

    attrs = [f'has course-id {_str(cid)}']
    if course.get("title"):
        attrs.append(f'has course-title {_str(course["title"])}')
    if course.get("credits") is not None:
        attrs.append(f'has credit-hours {float(course["credits"])}')
    if course.get("type"):
        attrs.append(f'has course-type {_str(course["type"])}')
    if course.get("source_url"):
        attrs.append(f'has source-url {_str(course["source_url"])}')
    if course.get("year_verified") is not None:
        attrs.append(f'has year-verified {int(course["year_verified"])}')
    if course.get("notes"):
        attrs.append(f'has notes {_str(course["notes"])}')

    attr_str = ", ".join(attrs)
    yv = course.get("year_verified")
    yv_str = f", has year-verified {int(yv)}" if yv else ""

    tx.query.insert(f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
    insert
        $course isa Course, {attr_str};
        (school: $school, course: $course) isa course-offering{yv_str};
    """)

    # Link topics
    for topic_name in course.get("topics") or []:
        _upsert_topic_link(tx, cid, topic_name)


def _upsert_topic_link(tx, course_id: str, topic_name: str) -> None:
    # Ensure topic entity exists
    check_topic = f"""
    match $t isa Topic, has topic-name {_str(topic_name)};
    """
    if not list(tx.query.get(check_topic)):
        tx.query.insert(f'insert $t isa Topic, has topic-name {_str(topic_name)};')

    # Link course to topic
    check_rel = f"""
    match
        $c isa Course, has course-id {_str(course_id)};
        $t isa Topic, has topic-name {_str(topic_name)};
        (course: $c, topic: $t) isa course-topic;
    """
    if list(tx.query.get(check_rel)):
        return

    tx.query.insert(f"""
    match
        $c isa Course, has course-id {_str(course_id)};
        $t isa Topic, has topic-name {_str(topic_name)};
    insert
        (course: $c, topic: $t) isa course-topic;
    """)


def _upsert_program(tx, school_slug: str, program: dict) -> None:
    pid = f"{school_slug}-{program['id']}"
    check = f"match $p isa Program, has program-id {_str(pid)};"
    if list(tx.query.get(check)):
        return

    attrs = [f'has program-id {_str(pid)}']
    if program.get("name"):
        attrs.append(f'has program-name {_str(program["name"])}')
    if program.get("type"):
        attrs.append(f'has program-type {_str(program["type"])}')
    if program.get("description"):
        attrs.append(f'has description {_str(program["description"])}')
    if program.get("tech_focus") is not None:
        attrs.append(f'has tech-focus {_bool(program["tech_focus"])}')
    if program.get("source_url"):
        attrs.append(f'has source-url {_str(program["source_url"])}')
    if program.get("year_verified") is not None:
        attrs.append(f'has year-verified {int(program["year_verified"])}')
    status = program.get("status", "unknown")
    attrs.append(f'has program-status {_str(status)}')
    if program.get("notes"):
        attrs.append(f'has notes {_str(program["notes"])}')

    attr_str = ", ".join(attrs)
    tx.query.insert(f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
    insert
        $prog isa Program, {attr_str};
        (school: $school, program: $prog) isa program-affiliation;
    """)


def _upsert_faculty(tx, school_slug: str, fac: dict, index: int) -> None:
    # Faculty doesn't have a natural key; use school_slug + index as a synthetic key
    fac_key = f"{school_slug}-fac-{index}"
    name = fac.get("name", "")

    # Skip if faculty already linked by checking name + school combo
    check = f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
        $f isa Faculty, has full-name {_str(name)};
        (faculty-member: $f, school: $school) isa faculty-appointment;
    """
    if list(tx.query.get(check)):
        return

    attrs = [f'has full-name {_str(name)}']
    if fac.get("title"):
        attrs.append(f'has faculty-title {_str(fac["title"])}')
    if fac.get("appointment_type"):
        attrs.append(f'has appointment-type {_str(fac["appointment_type"])}')
    if fac.get("profile_url"):
        attrs.append(f'has profile-url {_str(fac["profile_url"])}')

    attr_str = ", ".join(attrs)
    rel_attrs = []
    if fac.get("title"):
        rel_attrs.append(f'has faculty-title {_str(fac["title"])}')
    if fac.get("appointment_type"):
        rel_attrs.append(f'has appointment-type {_str(fac["appointment_type"])}')
    rel_attr_str = (", " + ", ".join(rel_attrs)) if rel_attrs else ""

    tx.query.insert(f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
    insert
        $f isa Faculty, {attr_str};
        (faculty-member: $f, school: $school) isa faculty-appointment{rel_attr_str};
    """)

    # Expertise topics
    for expertise in fac.get("tech_expertise") or []:
        _upsert_faculty_expertise(tx, name, school_slug, expertise)

    for area in fac.get("research_areas") or []:
        _upsert_faculty_expertise(tx, name, school_slug, area)


def _upsert_faculty_expertise(tx, faculty_name: str, school_slug: str, topic_name: str) -> None:
    # Ensure topic exists
    check_topic = f"match $t isa Topic, has topic-name {_str(topic_name)};"
    if not list(tx.query.get(check_topic)):
        tx.query.insert(f'insert $t isa Topic, has topic-name {_str(topic_name)};')

    check = f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
        $f isa Faculty, has full-name {_str(faculty_name)};
        (faculty-member: $f, school: $school) isa faculty-appointment;
        $t isa Topic, has topic-name {_str(topic_name)};
        (faculty-member: $f, topic: $t) isa faculty-expertise;
    """
    if list(tx.query.get(check)):
        return

    tx.query.insert(f"""
    match
        $f isa Faculty, has full-name {_str(faculty_name)};
        $t isa Topic, has topic-name {_str(topic_name)};
    insert
        (faculty-member: $f, topic: $t) isa faculty-expertise;
    """)


def _upsert_partnership(tx, school_slug: str, partnership: dict) -> None:
    org = partnership.get("org", "")
    check = f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
        $p isa Partnership, has org-name {_str(org)};
        (school: $school, partner: $p) isa institutional-partnership;
    """
    if list(tx.query.get(check)):
        return

    attrs = [f'has org-name {_str(org)}']
    if partnership.get("type"):
        attrs.append(f'has partnership-type {_str(partnership["type"])}')
    if partnership.get("description"):
        attrs.append(f'has description {_str(partnership["description"])}')
    if partnership.get("year_start") is not None:
        attrs.append(f'has year-start {int(partnership["year_start"])}')
    if partnership.get("source_url"):
        attrs.append(f'has source-url {_str(partnership["source_url"])}')
    if partnership.get("active") is not None:
        attrs.append(f'has is-active {_bool(partnership["active"])}')

    attr_str = ", ".join(attrs)
    tx.query.insert(f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
    insert
        $p isa Partnership, {attr_str};
        (school: $school, partner: $p) isa institutional-partnership;
    """)


def _upsert_student_org(tx, school_slug: str, org: dict, index: int) -> None:
    name = org.get("name", "")
    check = f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
        $o isa StudentOrg, has full-name {_str(name)};
        (school: $school, org: $o) isa student-org-affiliation;
    """
    if list(tx.query.get(check)):
        return

    attrs = [f'has full-name {_str(name)}']
    if org.get("focus"):
        attrs.append(f'has description {_str(org["focus"])}')
    if org.get("url"):
        attrs.append(f'has org-url {_str(org["url"])}')
    if org.get("active") is not None:
        attrs.append(f'has is-active {_bool(org["active"])}')
    if org.get("year_verified") is not None:
        attrs.append(f'has year-verified {int(org["year_verified"])}')

    attr_str = ", ".join(attrs)
    tx.query.insert(f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
    insert
        $o isa StudentOrg, {attr_str};
        (school: $school, org: $o) isa student-org-affiliation;
    """)


def _upsert_prg(tx, school_slug: str, gap: dict, index: int) -> None:
    claimed = gap.get("claimed", "")
    # Use claimed text as quasi-key within this school
    check = f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
        $g isa PressReleaseGap, has claimed-text {_str(claimed)};
        (school: $school, gap: $g) isa school-press-release-gap;
    """
    if list(tx.query.get(check)):
        return

    attrs = [f'has claimed-text {_str(claimed)}']
    if gap.get("reality"):
        attrs.append(f'has reality-text {_str(gap["reality"])}')
    if gap.get("evidence_url"):
        attrs.append(f'has evidence-url {_str(gap["evidence_url"])}')
    if gap.get("current_url"):
        attrs.append(f'has source-url {_str(gap["current_url"])}')
    if gap.get("year_claimed") is not None:
        attrs.append(f'has year-claimed {int(gap["year_claimed"])}')
    if gap.get("year_verified") is not None:
        attrs.append(f'has year-verified {int(gap["year_verified"])}')
    if gap.get("severity"):
        attrs.append(f'has gap-severity {_str(gap["severity"])}')
    if gap.get("penalty_points") is not None:
        attrs.append(f'has penalty-points {float(gap["penalty_points"])}')

    attr_str = ", ".join(attrs)
    tx.query.insert(f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
    insert
        $g isa PressReleaseGap, {attr_str};
        (school: $school, gap: $g) isa school-press-release-gap;
    """)


def _upsert_external_ranking(tx, school_slug: str, source_id: str, entry: dict) -> None:
    """Upsert a single external ranking entry and link it to the school."""
    rank = entry.get("rank")
    year = entry.get("year")
    url = entry.get("url")

    # Deduplicate on school + source_id
    check = f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
        $er isa ExternalRanking, has source-id {_str(source_id)};
        (school: $school, ranking: $er) isa external-ranking-position;
    """
    if list(tx.query.get(check)):
        return

    attrs = [f'has source-id {_str(source_id)}']
    if rank is not None:
        attrs.append(f'has ext-rank {int(rank)}')
    if year is not None:
        attrs.append(f'has ext-year {int(year)}')
    if url:
        attrs.append(f'has ext-source-url {_str(url)}')

    attr_str = ", ".join(attrs)
    tx.query.insert(f"""
    match
        $school isa LawSchool, has slug {_str(school_slug)};
    insert
        $er isa ExternalRanking, {attr_str};
        (school: $school, ranking: $er) isa external-ranking-position;
    """)


def _update_meta_scores(tx, school: dict) -> None:
    """Write prestige-score, meta-score, and meta-rank attributes onto the LawSchool entity."""
    slug = school["id"]

    prestige = school.get("prestige_score")
    meta = school.get("meta_score")
    meta_rank = school.get("meta_rank")

    # Only attempt to set values that are present and non-null
    attrs_to_set = []
    if prestige is not None:
        attrs_to_set.append(f'has prestige-score {float(prestige)}')
    if meta is not None:
        attrs_to_set.append(f'has meta-score {float(meta)}')
    if meta_rank is not None:
        attrs_to_set.append(f'has meta-rank {int(meta_rank)}')

    if not attrs_to_set:
        return

    for attr_clause in attrs_to_set:
        tx.query.insert(f"""
        match
            $school isa LawSchool, has slug {_str(slug)};
        insert
            $school {attr_clause};
        """)


# ──────────────────────────────────────────────
# CLI entrypoint
# ──────────────────────────────────────────────

@click.command()
@click.option("--host", default=lambda: os.getenv("TYPEDB_HOST", "localhost"), show_default=True)
@click.option("--port", default=lambda: int(os.getenv("TYPEDB_PORT", "1729")), show_default=True)
@click.option("--database", default=lambda: os.getenv("TYPEDB_DATABASE", "lawschools"), show_default=True)
@click.option("--schema", "define_schema_flag", is_flag=True, default=False,
              help="Define/redefine schema before ingesting data")
@click.option("--reset", is_flag=True, default=False,
              help="Drop and recreate the database before ingesting")
@click.option("--school", default=None,
              help="Ingest only this school slug (e.g. harvard-law). Omit for all.")
def main(host: str, port: int, database: str, define_schema_flag: bool, reset: bool, school: str | None):
    """Ingest law school JSON data into TypeDB."""
    console.rule("[bold]TypeDB Law School Ingest[/bold]")

    driver = get_driver(host, port)

    ensure_database(driver, database, reset=reset)

    if define_schema_flag or reset:
        define_schema(driver, database)

    # Load school files
    if school:
        files = [SCHOOLS_DIR / f"{school}.json"]
        if not files[0].exists():
            console.print(f"[red]File not found: {files[0]}[/red]")
            sys.exit(1)
    else:
        files = sorted(SCHOOLS_DIR.glob("*.json"))

    if not files:
        console.print("[yellow]No school JSON files found.[/yellow]")
        return

    with driver.session(database, driver.SessionType.DATA) as session:
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task("Ingesting schools…", total=len(files))
            for path in files:
                progress.update(task, description=f"Ingesting {path.stem}…")
                try:
                    data = json.loads(path.read_text())
                    with session.transaction(driver.TransactionType.WRITE) as tx:
                        ingest_school(tx, data)
                        tx.commit()
                    console.print(f"  [green]✓[/green] {path.stem}")
                except Exception as e:
                    console.print(f"  [red]✗[/red] {path.stem}: {e}")
                progress.advance(task)

    console.print("\n[bold green]Ingest complete.[/bold green]")
    driver.close()


if __name__ == "__main__":
    main()
