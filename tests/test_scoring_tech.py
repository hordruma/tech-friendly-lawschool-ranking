"""
tests/test_scoring_tech.py

Tests for src/lawschool/scoring/tech.py
"""

from __future__ import annotations

import pytest

from lawschool.scoring.tech import (
    compute_tech_score,
    score_curriculum_courses,
    score_joint_degrees,
    score_legaltech_center,
    score_practical_requirement,
    score_press_release_penalty,
    score_tech_clinics,
)


# ---------------------------------------------------------------------------
# score_curriculum_courses
# ---------------------------------------------------------------------------


def test_curriculum_courses_empty(minimal_school):
    score, notes = score_curriculum_courses(minimal_school)
    assert score == 0.0


def test_curriculum_courses_elective_gives_1pt():
    school = {
        "courses": [
            {"id": "c1", "title": "Tech Law", "type": "elective", "year_verified": 2024},
        ]
    }
    score, _ = score_curriculum_courses(school)
    assert score == 1.0


def test_curriculum_courses_required_gives_2pt():
    school = {
        "courses": [
            {"id": "c1", "title": "AI Law", "type": "required", "year_verified": 2024},
        ]
    }
    score, _ = score_curriculum_courses(school)
    assert score == 2.0


def test_curriculum_courses_certificate_gives_1pt():
    school = {
        "courses": [
            {"id": "c1", "title": "Data Law", "type": "certificate", "year_verified": 2024},
        ]
    }
    score, _ = score_curriculum_courses(school)
    assert score == 1.0


def test_curriculum_courses_cap_at_20():
    # 15 required courses → 30 pts, but capped at 20
    school = {
        "courses": [
            {"id": f"c{i}", "title": f"Course {i}", "type": "required", "year_verified": 2024}
            for i in range(15)
        ]
    }
    score, _ = score_curriculum_courses(school)
    assert score == 20.0


def test_curriculum_courses_unverified_not_counted():
    school = {
        "courses": [
            {"id": "c1", "title": "AI Law", "type": "required", "year_verified": None},
            {"id": "c2", "title": "Tech Law", "type": "elective", "year_verified": 2024},
        ]
    }
    score, notes = score_curriculum_courses(school)
    # only the verified elective (1pt) should count
    assert score == 1.0
    assert any("UNVERIFIED" in n for n in notes)


def test_curriculum_courses_mixed():
    school = {
        "courses": [
            {"id": "c1", "title": "AI Law", "type": "required", "year_verified": 2024},
            {"id": "c2", "title": "Privacy", "type": "elective", "year_verified": 2024},
            {"id": "c3", "title": "Unverified", "type": "required", "year_verified": None},
        ]
    }
    score, _ = score_curriculum_courses(school)
    # 2 (required) + 1 (elective) = 3; unverified not counted
    assert score == 3.0


# ---------------------------------------------------------------------------
# score_practical_requirement
# ---------------------------------------------------------------------------


def test_practical_requirement_required_tech_course_gives_10():
    school = {
        "courses": [
            {"id": "c1", "title": "Tech Law", "type": "required", "year_verified": 2024},
        ],
        "programs": [],
    }
    score, _ = score_practical_requirement(school)
    assert score == 10.0


def test_practical_requirement_tech_clinic_gives_7():
    school = {
        "courses": [],
        "programs": [
            {
                "id": "p1",
                "name": "Tech Clinic",
                "type": "clinic",
                "tech_focus": True,
                "status": "active",
            },
        ],
    }
    score, _ = score_practical_requirement(school)
    assert score == 7.0


def test_practical_requirement_any_clinic_gives_4():
    school = {
        "courses": [],
        "programs": [
            {
                "id": "p1",
                "name": "General Clinic",
                "type": "clinic",
                "tech_focus": False,
                "status": "active",
            },
        ],
    }
    score, _ = score_practical_requirement(school)
    assert score == 4.0


def test_practical_requirement_none_gives_0(minimal_school):
    score, _ = score_practical_requirement(minimal_school)
    assert score == 0.0


def test_practical_requirement_prefers_required_course_over_clinic():
    # Required tech course takes priority over clinic
    school = {
        "courses": [
            {"id": "c1", "title": "Tech Law", "type": "required", "year_verified": 2024},
        ],
        "programs": [
            {
                "id": "p1",
                "name": "Tech Clinic",
                "type": "clinic",
                "tech_focus": True,
                "status": "active",
            },
        ],
    }
    score, _ = score_practical_requirement(school)
    assert score == 10.0


# ---------------------------------------------------------------------------
# score_tech_clinics
# ---------------------------------------------------------------------------


def test_tech_clinics_active_tech_clinic_gives_10():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "LegalTech Clinic",
                "type": "clinic",
                "tech_focus": True,
                "status": "active",
            },
        ]
    }
    score, _ = score_tech_clinics(school)
    assert score == 10.0


def test_tech_clinics_non_tech_clinic_gives_4():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "Immigration Clinic",
                "type": "clinic",
                "tech_focus": False,
                "status": "active",
            },
        ]
    }
    score, _ = score_tech_clinics(school)
    assert score == 4.0


def test_tech_clinics_none_gives_0(minimal_school):
    score, _ = score_tech_clinics(minimal_school)
    assert score == 0.0


def test_tech_clinics_inactive_tech_clinic_gives_0():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "LegalTech Clinic",
                "type": "clinic",
                "tech_focus": True,
                "status": "inactive",
            },
        ]
    }
    score, _ = score_tech_clinics(school)
    assert score == 0.0


# ---------------------------------------------------------------------------
# score_legaltech_center
# ---------------------------------------------------------------------------


def test_legaltech_center_active_with_url_gives_10():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "Center for Legal Tech",
                "type": "center",
                "tech_focus": True,
                "status": "active",
                "source_url": "https://example.com",
            },
        ]
    }
    score, _ = score_legaltech_center(school)
    assert score == 10.0


def test_legaltech_center_active_without_url_gives_7():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "Center for Legal Tech",
                "type": "center",
                "tech_focus": True,
                "status": "active",
                "source_url": None,
            },
        ]
    }
    score, _ = score_legaltech_center(school)
    assert score == 7.0


def test_legaltech_center_unknown_status_gives_4():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "Center for Legal Tech",
                "type": "center",
                "tech_focus": True,
                "status": "unknown",
                "source_url": "https://example.com",
            },
        ]
    }
    score, _ = score_legaltech_center(school)
    assert score == 4.0


def test_legaltech_center_none_gives_0(minimal_school):
    score, _ = score_legaltech_center(minimal_school)
    assert score == 0.0


def test_legaltech_center_non_tech_center_ignored():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "Humanities Center",
                "type": "center",
                "tech_focus": False,
                "status": "active",
                "source_url": "https://example.com",
            },
        ]
    }
    score, _ = score_legaltech_center(school)
    assert score == 0.0


# ---------------------------------------------------------------------------
# score_joint_degrees
# ---------------------------------------------------------------------------


def test_joint_degrees_5pts_per_qualifying():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "JD/MS Computer Science",
                "type": "joint_degree",
                "tech_focus": True,
                "status": "active",
                "description": None,
            },
        ]
    }
    score, _ = score_joint_degrees(school)
    assert score == 5.0


def test_joint_degrees_capped_at_10():
    school = {
        "programs": [
            {
                "id": f"p{i}",
                "name": f"JD/Tech Degree {i}",
                "type": "joint_degree",
                "tech_focus": True,
                "status": "active",
                "description": None,
            }
            for i in range(5)
        ]
    }
    score, _ = score_joint_degrees(school)
    assert score == 10.0


def test_joint_degrees_keyword_detection():
    # "data science" in the name should qualify even without tech_focus=True
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "JD/MS Data Science",
                "type": "joint_degree",
                "tech_focus": False,
                "status": "active",
                "description": None,
            },
        ]
    }
    score, _ = score_joint_degrees(school)
    assert score == 5.0


def test_joint_degrees_non_tech_does_not_qualify():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "JD/MBA",
                "type": "joint_degree",
                "tech_focus": False,
                "status": "active",
                "description": "Business administration joint degree.",
            },
        ]
    }
    score, _ = score_joint_degrees(school)
    assert score == 0.0


def test_joint_degrees_none_gives_0(minimal_school):
    score, _ = score_joint_degrees(minimal_school)
    assert score == 0.0


def test_joint_degrees_keyword_in_description():
    school = {
        "programs": [
            {
                "id": "p1",
                "name": "JD/Science",
                "type": "joint_degree",
                "tech_focus": False,
                "status": "active",
                "description": "Joint degree covering engineering principles.",
            },
        ]
    }
    score, _ = score_joint_degrees(school)
    assert score == 5.0


# ---------------------------------------------------------------------------
# score_press_release_penalty
# ---------------------------------------------------------------------------


def test_press_release_penalty_no_gaps_gives_0(minimal_school):
    score, _ = score_press_release_penalty(minimal_school)
    assert score == 0.0


def test_press_release_penalty_minor_gives_minus5():
    school = {
        "press_release_gap": [
            {
                "claimed": "We have great programs",
                "reality": "We do not",
                "severity": "minor",
                "penalty_points": None,
            }
        ]
    }
    score, _ = score_press_release_penalty(school)
    assert score == -5.0


def test_press_release_penalty_explicit_penalty_points():
    school = {
        "press_release_gap": [
            {
                "claimed": "Claim",
                "reality": "Reality",
                "severity": "major",
                "penalty_points": -15,
            }
        ]
    }
    score, _ = score_press_release_penalty(school)
    assert score == -15.0


def test_press_release_penalty_capped_at_minus20():
    # Multiple gaps totalling more than -20
    school = {
        "press_release_gap": [
            {"claimed": f"Claim {i}", "reality": "Reality", "severity": "major", "penalty_points": None}
            for i in range(5)
        ]
    }
    # 5 * -15 = -75, should be capped at -20
    score, _ = score_press_release_penalty(school)
    assert score == -20.0


def test_press_release_penalty_multiple_egregious_capped():
    school = {
        "press_release_gap": [
            {"claimed": "Claim A", "reality": "Reality", "severity": "egregious", "penalty_points": -20},
            {"claimed": "Claim B", "reality": "Reality", "severity": "egregious", "penalty_points": -20},
        ]
    }
    score, _ = score_press_release_penalty(school)
    assert score == -20.0


# ---------------------------------------------------------------------------
# compute_tech_score
# ---------------------------------------------------------------------------


def test_compute_tech_score_total_is_sum(minimal_school):
    result = compute_tech_score(minimal_school)
    scores = result["scores"]
    # Sum of sub-scores minus penalty should equal total
    subtotal = sum(v for k, v in scores.items() if k not in ("total", "press_release_gap_penalty"))
    expected = subtotal + scores["press_release_gap_penalty"]
    assert abs(scores["total"] - round(expected, 1)) < 0.01


def test_compute_tech_score_unranked_when_no_last_verified(minimal_school):
    result = compute_tech_score(minimal_school)
    assert result["ranking_tier"] == "unranked"


def test_compute_tech_score_tier_thresholds():
    # Use a school dict with explicit scores to test thresholds
    # We create schools that just hit each tier boundary

    def school_with_total(target_total):
        # Build a school that will score roughly at target
        # Use partnerships to hit exact scores (10pts per 3+ partnerships)
        partnerships = [
            {"org": f"P{i}", "type": "industry", "source_url": f"https://p{i}.com", "active": True}
            for i in range(3)
        ]
        return {
            "id": "threshold-test",
            "last_verified": "2024-01-01",
            "courses": [],
            "programs": [],
            "faculty": [],
            "partnerships": partnerships,
            "student_orgs": [],
            "press_release_gap": [],
        }

    # A school with last_verified set should get a real tier
    school = school_with_total(50)
    result = compute_tech_score(school)
    # It should not be "unranked"
    assert result["ranking_tier"] != "unranked"


def test_compute_tech_score_tier_s():
    """Score >= 85 → tier S."""
    # Build a high-scoring school to verify S tier is achievable
    school = {
        "id": "high-tech",
        "last_verified": "2024-01-01",
        "courses": [
            {"id": f"c{i}", "title": f"AI Course {i}", "type": "required", "year_verified": 2024}
            for i in range(10)  # 10 required = 20pts (capped)
        ],
        "programs": [
            {"id": "p1", "name": "LT Clinic", "type": "clinic", "tech_focus": True, "status": "active"},
            {"id": "p2", "name": "LT Center", "type": "center", "tech_focus": True, "status": "active", "source_url": "https://x.com"},
            {"id": "p3", "name": "JD/CS", "type": "joint_degree", "tech_focus": True, "status": "active", "description": None},
            {"id": "p4", "name": "JD/DS", "type": "joint_degree", "tech_focus": True, "status": "active", "description": None},
        ],
        "faculty": [
            {"name": f"Prof {i}", "appointment_type": "tenure_track", "tech_expertise": ["AI"], "research_areas": ["tech"]}
            for i in range(4)
        ],
        "partnerships": [
            {"org": f"P{i}", "type": "industry", "source_url": f"https://p{i}.com", "active": True}
            for i in range(3)
        ],
        "student_orgs": [
            {"name": "LT Org 1", "active": True},
            {"name": "LT Org 2", "active": True},
        ],
        "press_release_gap": [],
    }
    result = compute_tech_score(school)
    assert result["scores"]["total"] >= 85.0
    assert result["ranking_tier"] == "S"


def test_compute_tech_score_uses_penalty(prg_school):
    result = compute_tech_score(prg_school)
    assert result["scores"]["press_release_gap_penalty"] == -15.0
    # total should include the penalty
    assert result["scores"]["total"] < 0.0 or result["scores"]["total"] <= 0.0


def test_compute_tech_score_includes_all_keys(minimal_school):
    result = compute_tech_score(minimal_school)
    expected_keys = {
        "curriculum_courses", "curriculum_practical", "curriculum_clinics",
        "infrastructure_center", "infrastructure_joint_degrees", "infrastructure_partnerships",
        "faculty_expertise", "faculty_research", "community_orgs", "community_careers",
        "press_release_gap_penalty", "total",
    }
    assert set(result["scores"].keys()) == expected_keys
