"""
tests/test_scoring_meta.py

Tests for src/lawschool/scoring/meta.py
"""

from __future__ import annotations

import math

import pytest

from lawschool.scoring.meta import (
    MAX_RANK,
    compute_meta_score,
    compute_prestige_score,
    normalize_rank,
)


# ---------------------------------------------------------------------------
# normalize_rank
# ---------------------------------------------------------------------------


def test_normalize_rank_1_near_100():
    score = normalize_rank(1)
    assert score > 95.0  # rank 1 should be close to 100


def test_normalize_rank_500_near_0():
    score = normalize_rank(500)
    # rank 500 is near 0 (log-scale formula gives ~0.03, bounded close to 0)
    assert score < 1.0


def test_normalize_rank_above_500_gives_0():
    assert normalize_rank(501) == 0.0
    assert normalize_rank(1000) == 0.0


def test_normalize_rank_monotonically_decreasing():
    scores = [normalize_rank(r) for r in [1, 5, 10, 50, 100, 250, 499, 500]]
    for i in range(len(scores) - 1):
        assert scores[i] > scores[i + 1], f"Expected decreasing at index {i}"


def test_normalize_rank_bounded_0_to_100():
    for rank in [1, 2, 50, 100, 499, 500]:
        score = normalize_rank(rank)
        assert 0.0 <= score <= 100.0


# ---------------------------------------------------------------------------
# compute_prestige_score
# ---------------------------------------------------------------------------


def test_compute_prestige_score_none_when_no_rankings():
    school = {"external_rankings": None}
    prestige, ext_scores, used = compute_prestige_score(school)
    assert prestige is None
    assert used == []


def test_compute_prestige_score_average_of_available():
    # Two rankings present
    school = {
        "external_rankings": {
            "qs_law": {"rank": 1, "year": 2024, "url": None},
            "the_law": {"rank": 2, "year": 2024, "url": None},
            "arwu_law": None,
            "usnews_law": None,
            "usnews_global_law": None,
            "vault_law": None,
        }
    }
    prestige, ext_scores, used = compute_prestige_score(school)
    assert prestige is not None
    assert len(used) == 2
    # prestige should be average of normalized(1) and normalized(2)
    expected = round((normalize_rank(1) + normalize_rank(2)) / 2, 2)
    assert abs(prestige - expected) < 0.01


def test_compute_prestige_score_excludes_none_ranks():
    # Entry present but rank is None → should be excluded
    school = {
        "external_rankings": {
            "qs_law": {"rank": None, "year": 2024, "url": None},
            "the_law": {"rank": 5, "year": 2024, "url": None},
            "arwu_law": None,
            "usnews_law": None,
            "usnews_global_law": None,
            "vault_law": None,
        }
    }
    prestige, _, used = compute_prestige_score(school)
    assert "qs_law" not in used
    assert "the_law" in used
    assert prestige is not None


def test_compute_prestige_score_single_ranking():
    school = {
        "external_rankings": {
            "qs_law": {"rank": 10, "year": 2024, "url": None},
            "the_law": None,
            "arwu_law": None,
            "usnews_law": None,
            "usnews_global_law": None,
            "vault_law": None,
        }
    }
    prestige, _, used = compute_prestige_score(school)
    assert prestige == round(normalize_rank(10), 2)
    assert used == ["qs_law"]


# ---------------------------------------------------------------------------
# compute_meta_score
# ---------------------------------------------------------------------------


def test_compute_meta_score_full_formula():
    """50/30/20 formula when all scores present."""
    school = {
        "scores": {"total": 60.0},
        "practical_skills_score": 40.0,
        "external_rankings": {
            "qs_law": {"rank": 1, "year": 2024, "url": None},
            "the_law": None,
            "arwu_law": None,
            "usnews_law": None,
            "usnews_global_law": None,
            "vault_law": None,
        },
        "courses": [],
        "programs": [],
        "faculty": [],
        "partnerships": [],
        "student_orgs": [],
        "press_release_gap": [],
        "last_verified": "2024-01-01",
    }
    result = compute_meta_score(school)
    prestige = normalize_rank(1)
    expected = round(60.0 * 0.50 + 40.0 * 0.30 + prestige * 0.20, 2)
    assert abs(result["meta_score"] - expected) < 0.1


def test_compute_meta_score_null_fallback_when_no_practical():
    """62.5/37.5 formula when practical_skills_score is None."""
    school = {
        "scores": {"total": 50.0},
        "practical_skills_score": None,
        "external_rankings": {
            "qs_law": {"rank": 10, "year": 2024, "url": None},
            "the_law": None,
            "arwu_law": None,
            "usnews_law": None,
            "usnews_global_law": None,
            "vault_law": None,
        },
        "courses": [],
        "programs": [],
        "faculty": [],
        "partnerships": [],
        "student_orgs": [],
        "press_release_gap": [],
        "last_verified": "2024-01-01",
    }
    result = compute_meta_score(school)
    prestige = normalize_rank(10)
    expected = round(50.0 * 0.625 + prestige * 0.375, 2)
    assert abs(result["meta_score"] - expected) < 0.1


def test_compute_meta_score_none_when_no_prestige():
    """Meta score is None when no external rankings available."""
    school = {
        "scores": {"total": 50.0},
        "practical_skills_score": 30.0,
        "external_rankings": None,
        "courses": [],
        "programs": [],
        "faculty": [],
        "partnerships": [],
        "student_orgs": [],
        "press_release_gap": [],
        "last_verified": "2024-01-01",
    }
    result = compute_meta_score(school)
    assert result["meta_score"] is None
    assert result["prestige_score"] is None


def test_compute_meta_score_result_keys():
    school = {
        "scores": {"total": 40.0},
        "practical_skills_score": None,
        "external_rankings": None,
        "courses": [],
        "programs": [],
        "faculty": [],
        "partnerships": [],
        "student_orgs": [],
        "press_release_gap": [],
        "last_verified": None,
    }
    result = compute_meta_score(school)
    assert set(result.keys()) == {
        "meta_score", "prestige_score", "practical_skills_score",
        "external_scores_normalized", "rankings_used",
    }
