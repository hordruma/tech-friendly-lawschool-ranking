"""
tests/test_scoring_practical.py

Tests for src/lawschool/scoring/practical.py
"""

from __future__ import annotations

import pytest

from lawschool.scoring.practical import (
    compute_practical_score,
    score_clinical,
    score_placements,
    score_professional_readiness,
    score_skills_curriculum,
)


# ---------------------------------------------------------------------------
# score_clinical
# ---------------------------------------------------------------------------


def test_clinical_empty_gives_0(minimal_school):
    score, _ = score_clinical(minimal_school)
    assert score == 0


def test_clinical_4pts_per_active_clinic():
    school = {
        "programs": [
            {"id": "p1", "name": "Clinic A", "type": "clinic", "status": "active", "practical_focus": True, "notes": None},
        ]
    }
    score, _ = score_clinical(school)
    assert score == 4


def test_clinical_two_clinics_gives_8():
    school = {
        "programs": [
            {"id": "p1", "name": "Clinic A", "type": "clinic", "status": "active", "practical_focus": True, "notes": None},
            {"id": "p2", "name": "Clinic B", "type": "clinic", "status": "active", "practical_focus": True, "notes": None},
        ]
    }
    score, _ = score_clinical(school)
    assert score == 8


def test_clinical_required_bonus_5pts():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "Clinic A",
                "type": "clinic",
                "status": "active",
                "practical_focus": True,
                "notes": "Attendance is required for all 2L students",
            },
        ]
    }
    score, notes = score_clinical(school)
    assert score == 9  # 4 + 5 bonus
    assert any("+5" in n for n in notes)


def test_clinical_capped_at_25():
    # 7 clinics × 4pts = 28, but cap is 25
    school = {
        "programs": [
            {
                "id": f"p{i}",
                "name": f"Clinic {i}",
                "type": "clinic",
                "status": "active",
                "practical_focus": True,
                "notes": None,
            }
            for i in range(7)
        ]
    }
    score, _ = score_clinical(school)
    # 7 * 4 = 28 > 20 cap → clinic_pts = 20, no bonus → 20 total
    assert score == 20


def test_clinical_with_required_note_capped_at_25():
    # 7 clinics with required note: clinic_pts=20 + 5 bonus = 25
    school = {
        "programs": [
            {
                "id": f"p{i}",
                "name": f"Clinic {i}",
                "type": "clinic",
                "status": "active",
                "practical_focus": True,
                "notes": "required participation" if i == 0 else None,
            }
            for i in range(7)
        ]
    }
    score, _ = score_clinical(school)
    assert score == 25


def test_clinical_inactive_clinics_not_counted():
    school = {
        "programs": [
            {"id": "p1", "name": "Clinic A", "type": "clinic", "status": "inactive", "practical_focus": True, "notes": None},
            {"id": "p2", "name": "Clinic B", "type": "clinic", "status": "active", "practical_focus": True, "notes": None},
        ]
    }
    score, _ = score_clinical(school)
    assert score == 4  # only the active one counts


# ---------------------------------------------------------------------------
# score_skills_curriculum
# ---------------------------------------------------------------------------


def test_skills_curriculum_empty_gives_0(minimal_school):
    score, _ = score_skills_curriculum(minimal_school)
    assert score == 0


def test_skills_curriculum_3pts_per_required_skills_course():
    school = {
        "courses": [
            {
                "id": "c1",
                "title": "Lawyering Skills",
                "type": "required",
                "year_verified": 2024,
                "notes": None,
            },
        ],
        "programs": [],
    }
    score, notes = score_skills_curriculum(school)
    assert score == 3
    assert any("+3" in n for n in notes)


def test_skills_curriculum_keyword_negotiat():
    school = {
        "courses": [
            {
                "id": "c1",
                "title": "Negotiation and Dispute Resolution",
                "type": "required",
                "year_verified": 2024,
                "notes": None,
            },
        ],
        "programs": [],
    }
    score, _ = score_skills_curriculum(school)
    assert score == 3


def test_skills_curriculum_2pts_per_advocacy_program():
    school = {
        "courses": [],
        "programs": [
            {
                "id": "p1",
                "name": "Moot Court Program",
                "type": "competition",
                "description": None,
                "status": "active",
            },
        ],
    }
    score, notes = score_skills_curriculum(school)
    assert score == 2
    assert any("+2" in n for n in notes)


def test_skills_curriculum_unverified_course_not_counted():
    school = {
        "courses": [
            {
                "id": "c1",
                "title": "Trial Advocacy",
                "type": "required",
                "year_verified": None,  # not verified
                "notes": None,
            },
        ],
        "programs": [],
    }
    score, _ = score_skills_curriculum(school)
    assert score == 0


# ---------------------------------------------------------------------------
# score_placements
# ---------------------------------------------------------------------------


def test_placements_empty_gives_0(minimal_school):
    score, _ = score_placements(minimal_school)
    assert score == 0


def test_placements_single_externship_gives_10():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "Judicial Externship",
                "type": "other",
                "description": "Structured externship placement.",
                "source_url": None,
                "status": "active",
            },
        ]
    }
    score, _ = score_placements(school)
    assert score == 10


def test_placements_comprehensive_externship_gives_15():
    # Two externships → "comprehensive" → 15 pts
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "Judicial Externship",
                "type": "other",
                "description": "Structured externship placement.",
                "source_url": None,
                "status": "active",
            },
            {
                "id": "p2",
                "name": "Government Externship",
                "type": "other",
                "description": "Government agency externship.",
                "source_url": None,
                "status": "active",
            },
        ]
    }
    score, notes = score_placements(school)
    assert score == 15
    assert any("15" in n for n in notes)


def test_placements_coop_with_source_url_gives_10():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "Field Placement Program",
                "type": "other",
                "description": "Co-op field placements.",
                "source_url": "https://example.com/coop",
                "status": "active",
            },
        ]
    }
    score, _ = score_placements(school)
    assert score == 10


def test_placements_capped_at_25():
    # externship (15) + coop with url (10) = 25
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "Externship A",
                "type": "other",
                "description": "Structured externship.",
                "source_url": None,
                "status": "active",
            },
            {
                "id": "p2",
                "name": "Externship B",
                "type": "other",
                "description": "Another externship.",
                "source_url": None,
                "status": "active",
            },
            {
                "id": "p3",
                "name": "Field Placement",
                "type": "other",
                "description": "Field placement co-op.",
                "source_url": "https://example.com",
                "status": "active",
            },
        ]
    }
    score, _ = score_placements(school)
    assert score == 25


# ---------------------------------------------------------------------------
# score_professional_readiness
# ---------------------------------------------------------------------------


def test_professional_readiness_empty_gives_0(minimal_school):
    score, _ = score_professional_readiness(minimal_school)
    assert score == 0


def test_professional_readiness_mandatory_probono_gives_10():
    school = {
        "programs": [],
        "partnerships": [],
        "notes": "mandatory pro bono requirement for graduation",
    }
    score, notes = score_professional_readiness(school)
    assert score == 10
    assert any("+10" in n for n in notes)


def test_professional_readiness_encouraged_probono_gives_5():
    school = {
        "programs": [],
        "partnerships": [],
        "notes": "Students are encouraged to complete pro bono hours",
    }
    score, notes = score_professional_readiness(school)
    assert score == 5
    assert any("+5" in n for n in notes)


def test_professional_readiness_mandatory_takes_priority_over_encouraged():
    school = {
        "programs": [],
        "partnerships": [],
        "notes": "pro bono requirement is mandatory for all students",
    }
    score, _ = score_professional_readiness(school)
    assert score == 10  # mandatory (10), not encouraged (5)


# ---------------------------------------------------------------------------
# compute_practical_score
# ---------------------------------------------------------------------------


def test_compute_practical_score_is_sum_of_four_subscores():
    school = {
        "programs": [
            {"id": "p1", "name": "Clinic A", "type": "clinic", "status": "active", "practical_focus": True, "notes": None},
        ],
        "courses": [],
        "partnerships": [],
        "notes": None,
    }
    result = compute_practical_score(school)
    bd = result["breakdown"]
    expected = bd["clinical_programs"] + bd["skills_curriculum"] + bd["experiential_placements"] + bd["professional_readiness"]
    assert abs(result["practical_skills_score"] - round(expected, 1)) < 0.01


def test_compute_practical_score_minimal_is_0(minimal_school):
    result = compute_practical_score(minimal_school)
    assert result["practical_skills_score"] == 0


def test_compute_practical_score_breakdown_keys(minimal_school):
    result = compute_practical_score(minimal_school)
    assert set(result["breakdown"].keys()) == {
        "clinical_programs", "skills_curriculum", "experiential_placements", "professional_readiness"
    }


def test_compute_practical_score_practical_school(practical_school):
    result = compute_practical_score(practical_school)
    # 2 active clinics = 8 pts clinical
    # 2 required skills courses (lawyering + trial) = 6 pts
    # mandatory pro bono = 10 pts
    # No externships in practical_school fixture (the externship program name doesn't match keywords)
    assert result["breakdown"]["clinical_programs"] == 8
    assert result["breakdown"]["skills_curriculum"] == 6
    assert result["breakdown"]["professional_readiness"] == 10
    assert result["practical_skills_score"] > 0
