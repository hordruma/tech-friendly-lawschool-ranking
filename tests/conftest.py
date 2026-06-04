"""
tests/conftest.py

Shared pytest fixtures for all test files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lawschool.schema import LawSchool


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

_SCHOOLS_DIR = Path(__file__).parent.parent / "data" / "schools"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_school() -> dict:
    """Bare-minimum valid school dict — should score zero on everything."""
    return {
        "id": "test-minimal",
        "name": "Minimal Law School",
        "country": "US",
        "url": "https://example.com",
        "last_verified": None,
        "courses": [],
        "programs": [],
        "faculty": [],
        "partnerships": [],
        "student_orgs": [],
        "press_release_gap": [],
        "external_rankings": None,
        "scores": None,
        "practical_skills_score": None,
        "meta_score": None,
        "notes": None,
    }


@pytest.fixture
def tech_school() -> dict:
    """School with strong tech signals — should score high on tech dimension."""
    return {
        "id": "test-tech",
        "name": "Tech-Heavy Law School",
        "country": "US",
        "url": "https://example-tech.com",
        "last_verified": "2024-01-01",
        "courses": [
            {
                "id": "course-req-ai",
                "title": "Artificial Intelligence and the Law",
                "credits": 3,
                "type": "required",
                "topics": ["artificial_intelligence"],
                "source_url": "https://example.com/ai",
                "year_verified": 2024,
                "notes": None,
            },
            {
                "id": "course-req-data",
                "title": "Data Privacy and Cybersecurity",
                "credits": 3,
                "type": "required",
                "topics": ["data_privacy"],
                "source_url": "https://example.com/data",
                "year_verified": 2024,
                "notes": None,
            },
        ],
        "programs": [
            {
                "id": "prog-tech-clinic",
                "name": "LegalTech Innovation Clinic",
                "type": "clinic",
                "description": "Active tech-focused clinic.",
                "tech_focus": True,
                "practical_focus": True,
                "source_url": "https://example.com/clinic",
                "year_verified": 2024,
                "status": "active",
                "notes": None,
            },
            {
                "id": "prog-lt-center",
                "name": "Center for Legal Technology",
                "type": "center",
                "description": "Dedicated legaltech research center.",
                "tech_focus": True,
                "practical_focus": None,
                "source_url": "https://example.com/center",
                "year_verified": 2024,
                "status": "active",
                "notes": None,
            },
            {
                "id": "prog-jd-cs",
                "name": "JD/MS Computer Science",
                "type": "joint_degree",
                "description": "Joint degree with computer science department.",
                "tech_focus": True,
                "practical_focus": None,
                "source_url": "https://example.com/jdcs",
                "year_verified": 2024,
                "status": "active",
                "notes": None,
            },
        ],
        "faculty": [],
        "partnerships": [
            {
                "org": "TechCorp",
                "type": "industry",
                "description": "Tech industry partnership.",
                "year_start": 2020,
                "source_url": "https://example.com/p1",
                "active": True,
            },
            {
                "org": "LegalAI Inc",
                "type": "legaltech_vendor",
                "description": "LegalTech vendor partnership.",
                "year_start": 2021,
                "source_url": "https://example.com/p2",
                "active": True,
            },
            {
                "org": "DataLaw",
                "type": "industry",
                "description": "Data analytics partnership.",
                "year_start": 2022,
                "source_url": "https://example.com/p3",
                "active": True,
            },
        ],
        "student_orgs": [],
        "press_release_gap": [],
        "external_rankings": None,
        "scores": None,
        "practical_skills_score": None,
        "meta_score": None,
        "notes": None,
    }


@pytest.fixture
def practical_school() -> dict:
    """School with strong practical skills — should score well on practical dimension."""
    return {
        "id": "test-practical",
        "name": "Practical Law School",
        "country": "US",
        "url": "https://example-practical.com",
        "last_verified": "2024-01-01",
        "courses": [
            {
                "id": "course-lawyering",
                "title": "Lawyering Skills and Practice",
                "credits": 3,
                "type": "required",
                "topics": ["lawyering"],
                "source_url": "https://example.com/lawyering",
                "year_verified": 2024,
                "notes": None,
            },
            {
                "id": "course-trial",
                "title": "Trial Advocacy",
                "credits": 2,
                "type": "required",
                "topics": ["advocacy"],
                "source_url": "https://example.com/trial",
                "year_verified": 2024,
                "notes": None,
            },
        ],
        "programs": [
            {
                "id": "prog-clinic-1",
                "name": "Immigration Clinic",
                "type": "clinic",
                "description": "Live-client immigration clinic.",
                "tech_focus": False,
                "practical_focus": True,
                "source_url": "https://example.com/imm-clinic",
                "year_verified": 2024,
                "status": "active",
                "notes": None,
            },
            {
                "id": "prog-clinic-2",
                "name": "Housing Clinic",
                "type": "clinic",
                "description": "Live-client housing clinic.",
                "tech_focus": False,
                "practical_focus": True,
                "source_url": "https://example.com/housing-clinic",
                "year_verified": 2024,
                "status": "active",
                "notes": None,
            },
            {
                "id": "prog-extern",
                "name": "Judicial Externship Program",
                "type": "other",
                "description": "Structured externship placements.",
                "tech_focus": False,
                "practical_focus": True,
                "source_url": "https://example.com/extern",
                "year_verified": 2024,
                "status": "active",
                "notes": None,
            },
        ],
        "faculty": [],
        "partnerships": [],
        "student_orgs": [],
        "press_release_gap": [],
        "external_rankings": None,
        "scores": None,
        "practical_skills_score": None,
        "meta_score": None,
        "notes": "mandatory pro bono requirement for graduation",
    }


@pytest.fixture
def prg_school() -> dict:
    """School with one press-release gap (severity=major, penalty=-15)."""
    return {
        "id": "test-prg",
        "name": "Overpromising Law School",
        "country": "US",
        "url": "https://example-prg.com",
        "last_verified": None,
        "courses": [],
        "programs": [],
        "faculty": [],
        "partnerships": [],
        "student_orgs": [],
        "press_release_gap": [
            {
                "claimed": "World-class AI lab with 50 faculty researchers",
                "reality": "A single part-time instructor teaches one elective",
                "evidence_url": "https://example.com/evidence",
                "current_url": "https://example.com/current",
                "year_claimed": 2023,
                "year_verified": 2024,
                "severity": "major",
                "penalty_points": -15,
            },
        ],
        "external_rankings": None,
        "scores": None,
        "practical_skills_score": None,
        "meta_score": None,
        "notes": None,
    }


@pytest.fixture
def seed_harvard() -> LawSchool:
    """LawSchool model loaded from data/schools/harvard-law.json."""
    return LawSchool.from_json_file(_SCHOOLS_DIR / "harvard-law.json")
