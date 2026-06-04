"""
src/lawschool/schema.py

Pydantic v2 models for all school data structures, mirroring data/schema/school.schema.json.

All fields are Optional where the JSON schema allows null.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Country → Region mapping (single canonical location)
# ---------------------------------------------------------------------------

COUNTRY_TO_REGION: dict[str, str] = {
    "US": "North America",
    "CA": "North America",
    "MX": "Latin America",
    "BR": "Latin America",
    "AR": "Latin America",
    "CL": "Latin America",
    "CO": "Latin America",
    "PE": "Latin America",
    "VE": "Latin America",
    "GB": "UK & Ireland",
    "IE": "UK & Ireland",
    "DE": "Europe",
    "FR": "Europe",
    "NL": "Europe",
    "BE": "Europe",
    "IT": "Europe",
    "ES": "Europe",
    "PT": "Europe",
    "CH": "Europe",
    "AT": "Europe",
    "SE": "Europe",
    "NO": "Europe",
    "DK": "Europe",
    "FI": "Europe",
    "PL": "Europe",
    "CZ": "Europe",
    "HU": "Europe",
    "RO": "Europe",
    "GR": "Europe",
    "AU": "Asia-Pacific",
    "NZ": "Asia-Pacific",
    "SG": "Asia-Pacific",
    "HK": "Asia-Pacific",
    "JP": "Asia-Pacific",
    "KR": "Asia-Pacific",
    "CN": "Asia-Pacific",
    "IN": "Asia-Pacific",
    "MY": "Asia-Pacific",
    "TH": "Asia-Pacific",
    "PH": "Asia-Pacific",
    "ID": "Asia-Pacific",
    "ZA": "Middle East & Africa",
    "NG": "Middle East & Africa",
    "KE": "Middle East & Africa",
    "EG": "Middle East & Africa",
    "AE": "Middle East & Africa",
    "SA": "Middle East & Africa",
    "IL": "Middle East & Africa",
    "QA": "Middle East & Africa",
    "KW": "Middle East & Africa",
}


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class ExternalRankingEntry(BaseModel):
    rank: int | None = None
    year: int | None = None
    url: str | None = None


class ExternalRankings(BaseModel):
    qs_law: ExternalRankingEntry | None = None
    the_law: ExternalRankingEntry | None = None
    arwu_law: ExternalRankingEntry | None = None
    usnews_law: ExternalRankingEntry | None = None
    usnews_global_law: ExternalRankingEntry | None = None
    vault_law: ExternalRankingEntry | None = None


class Course(BaseModel):
    id: str
    title: str
    credits: float | None = None
    type: Literal["required", "elective", "certificate"]
    topics: list[str] = Field(default_factory=list)
    source_url: str | None = None
    year_verified: int | None = None
    notes: str | None = None


class Program(BaseModel):
    id: str
    name: str
    type: Literal["clinic", "joint_degree", "certificate", "center", "incubator", "competition", "other"]
    description: str | None = None
    tech_focus: bool = False
    practical_focus: bool | None = None
    source_url: str | None = None
    year_verified: int | None = None
    status: str = "unknown"
    notes: str | None = None


class Faculty(BaseModel):
    name: str
    title: str | None = None
    appointment_type: str | None = None
    tech_expertise: list[str] = Field(default_factory=list)
    research_areas: list[str] = Field(default_factory=list)
    profile_url: str | None = None


class Partnership(BaseModel):
    org: str
    type: str | None = None
    description: str | None = None
    year_start: int | None = None
    source_url: str | None = None
    active: bool | None = None


class StudentOrg(BaseModel):
    name: str
    focus: str | None = None
    url: str | None = None
    active: bool | None = None
    year_verified: int | None = None


class PressReleaseGap(BaseModel):
    claimed: str
    reality: str
    evidence_url: str | None = None
    current_url: str | None = None
    year_claimed: int | None = None
    year_verified: int | None = None
    severity: str | None = None
    penalty_points: float | None = None


class Accreditation(BaseModel):
    body: str
    jurisdiction: str
    status: str


class ScoreBreakdown(BaseModel):
    """Result of computing all three score families for a school."""
    tech: float
    practical: float
    prestige: float | None
    meta: float | None
    tier: str


class TechScores(BaseModel):
    """Raw sub-scores for the tech-friendliness dimension."""
    curriculum_courses: float | None = None
    curriculum_practical: float | None = None
    curriculum_clinics: float | None = None
    infrastructure_center: float | None = None
    infrastructure_joint_degrees: float | None = None
    infrastructure_partnerships: float | None = None
    faculty_expertise: float | None = None
    faculty_research: float | None = None
    community_orgs: float | None = None
    community_careers: float | None = None
    press_release_gap_penalty: float | None = None
    total: float | None = None


class PracticalSkillsBreakdown(BaseModel):
    clinical_programs: float | None = None
    skills_curriculum: float | None = None
    experiential_placements: float | None = None
    professional_readiness: float | None = None


# ---------------------------------------------------------------------------
# Root model
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Controlled vocabulary sets (used for validation in MCP tools and the web app)
# ---------------------------------------------------------------------------

VALID_REGIONS: frozenset[str] = frozenset({
    "North America",
    "UK & Ireland",
    "Europe",
    "Asia-Pacific",
    "Latin America",
    "Middle East & Africa",
})

VALID_TIERS: frozenset[str] = frozenset({"S", "A", "B", "C", "D"})

VALID_SORT_KEYS: frozenset[str] = frozenset(
    {"meta_score", "tech_score", "practical_score", "prestige_score"}
)


class LawSchool(BaseModel):
    id: str
    name: str
    country: str
    jurisdiction: str | None = None
    url: str
    last_researched: str | None = None
    last_verified: str | None = None
    accreditation: list[Accreditation] = Field(default_factory=list)
    courses: list[Course] = Field(default_factory=list)
    programs: list[Program] = Field(default_factory=list)
    faculty: list[Faculty] = Field(default_factory=list)
    partnerships: list[Partnership] = Field(default_factory=list)
    student_orgs: list[StudentOrg] = Field(default_factory=list)
    press_release_gap: list[PressReleaseGap] = Field(default_factory=list)
    external_rankings: ExternalRankings | None = None
    practical_skills_score: float | None = None
    practical_skills_breakdown: PracticalSkillsBreakdown | None = None
    meta_score: float | None = None
    meta_rank: int | None = None
    scores: TechScores | None = None
    ranking_tier: str | None = None
    notes: str | None = None

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_json_file(cls, path: str | Path) -> "LawSchool":
        """Load and validate a school JSON file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)

    @property
    def region(self) -> str | None:
        """Infer geographic region from the country code."""
        return COUNTRY_TO_REGION.get(self.country or "", None)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict (suitable for JSON output)."""
        return self.model_dump(mode="json")
