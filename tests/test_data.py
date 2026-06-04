"""
tests/test_data.py

Tests for src/lawschool/data.py
"""

from __future__ import annotations

import pytest

from lawschool.data import _ensure_scores, get_research_stats, load_all_schools, load_school
from lawschool.schema import LawSchool, TechScores


# ---------------------------------------------------------------------------
# load_school
# ---------------------------------------------------------------------------


def test_load_school_harvard_returns_lawschool():
    school = load_school("harvard-law")
    assert school is not None
    assert isinstance(school, LawSchool)


def test_load_school_harvard_name():
    school = load_school("harvard-law")
    assert school is not None
    assert school.name == "Harvard Law School"


def test_load_school_nonexistent_returns_none():
    school = load_school("nonexistent-school-xyz-abc")
    assert school is None


def test_load_school_fills_in_scores():
    school = load_school("harvard-law")
    assert school is not None
    assert school.scores is not None
    assert school.scores.total is not None


def test_load_school_fills_in_practical_score():
    school = load_school("harvard-law")
    assert school is not None
    assert school.practical_skills_score is not None


# ---------------------------------------------------------------------------
# load_all_schools
# ---------------------------------------------------------------------------


def test_load_all_schools_returns_list():
    schools = load_all_schools()
    assert isinstance(schools, list)
    assert len(schools) > 0


def test_load_all_schools_returns_lawschool_instances():
    schools = load_all_schools()
    for school in schools:
        assert isinstance(school, LawSchool)


def test_load_all_schools_sorted_by_meta_score_desc():
    schools = load_all_schools()
    meta_scores = [s.meta_score for s in schools]
    # Schools with meta_score should come before None
    non_none = [m for m in meta_scores if m is not None]
    none_vals = [m for m in meta_scores if m is None]
    # Verify non-None scores are sorted descending
    assert non_none == sorted(non_none, reverse=True)
    # Verify None values come at the end
    if non_none and none_vals:
        last_non_none_idx = max(i for i, m in enumerate(meta_scores) if m is not None)
        first_none_idx = min(i for i, m in enumerate(meta_scores) if m is None)
        assert last_non_none_idx < first_none_idx


# ---------------------------------------------------------------------------
# get_research_stats
# ---------------------------------------------------------------------------


def test_get_research_stats_returns_dict():
    stats = get_research_stats()
    assert isinstance(stats, dict)


def test_get_research_stats_has_required_keys():
    stats = get_research_stats()
    assert "total_in_queue" in stats
    assert "researched" in stats
    assert "pending" in stats


def test_get_research_stats_counts_consistent():
    stats = get_research_stats()
    if "error" not in stats:
        assert stats["total_in_queue"] == stats["researched"] + stats["pending"]


# ---------------------------------------------------------------------------
# _ensure_scores
# ---------------------------------------------------------------------------


def test_ensure_scores_fills_none_scores():
    """_ensure_scores should compute scores when school.scores is None."""
    school = LawSchool(
        id="test-ensure",
        name="Test School",
        country="US",
        url="https://example.com",
        scores=None,
        practical_skills_score=None,
        meta_score=None,
    )
    result = _ensure_scores(school)
    assert result.scores is not None
    assert result.scores.total is not None
    assert result.practical_skills_score is not None


def test_ensure_scores_does_not_overwrite_existing_scores():
    """_ensure_scores should not recompute if scores.total is already set."""
    existing_scores = TechScores(
        curriculum_courses=10.0,
        curriculum_practical=5.0,
        curriculum_clinics=3.0,
        infrastructure_center=7.0,
        infrastructure_joint_degrees=5.0,
        infrastructure_partnerships=4.0,
        faculty_expertise=6.0,
        faculty_research=3.0,
        community_orgs=2.0,
        community_careers=1.0,
        press_release_gap_penalty=0.0,
        total=46.0,
    )
    school = LawSchool(
        id="test-existing",
        name="Test School",
        country="US",
        url="https://example.com",
        scores=existing_scores,
        practical_skills_score=None,
        meta_score=None,
    )
    result = _ensure_scores(school)
    # Tech scores should remain unchanged
    assert result.scores.total == 46.0


def test_ensure_scores_returns_lawschool_instance():
    school = LawSchool(
        id="test-type",
        name="Test",
        country="US",
        url="https://x.com",
        scores=None,
    )
    result = _ensure_scores(school)
    assert isinstance(result, LawSchool)
