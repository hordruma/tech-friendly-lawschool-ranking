"""
tests/test_golden.py

Golden-file regression tests.  For each school in tests/golden/scores.json,
load the school from data/schools/ and verify that current Python scoring
matches the stored golden values.

If scoring logic changes intentionally, regenerate with:
    python scripts/regenerate_golden.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lawschool.scoring.practical import compute_practical_score
from lawschool.scoring.tech import compute_tech_score

_GOLDEN_PATH = Path(__file__).parent / "golden" / "scores.json"
_SCHOOLS_DIR = Path(__file__).parent.parent / "data" / "schools"

# Load golden data at module import time so pytest can parametrize from it
_GOLDEN: dict = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("school_id", list(_GOLDEN.keys()))
def test_tech_total_matches_golden(school_id):
    school_path = _SCHOOLS_DIR / f"{school_id}.json"
    assert school_path.exists(), f"School file not found: {school_path}"

    data = json.loads(school_path.read_text(encoding="utf-8"))
    result = compute_tech_score(data)
    actual = result["scores"]["total"]
    expected = _GOLDEN[school_id]["tech_total"]
    assert abs(actual - expected) < 0.01, (
        f"{school_id}: tech_total {actual} != golden {expected}. "
        "If scoring changed intentionally, run: python scripts/regenerate_golden.py"
    )


@pytest.mark.parametrize("school_id", list(_GOLDEN.keys()))
def test_practical_total_matches_golden(school_id):
    school_path = _SCHOOLS_DIR / f"{school_id}.json"
    assert school_path.exists(), f"School file not found: {school_path}"

    data = json.loads(school_path.read_text(encoding="utf-8"))
    result = compute_practical_score(data)
    actual = result["practical_skills_score"]
    expected = _GOLDEN[school_id]["practical_total"]
    assert abs(actual - expected) < 0.01, (
        f"{school_id}: practical_total {actual} != golden {expected}. "
        "If scoring changed intentionally, run: python scripts/regenerate_golden.py"
    )


@pytest.mark.parametrize("school_id", list(_GOLDEN.keys()))
def test_tier_matches_golden(school_id):
    school_path = _SCHOOLS_DIR / f"{school_id}.json"
    assert school_path.exists(), f"School file not found: {school_path}"

    data = json.loads(school_path.read_text(encoding="utf-8"))
    result = compute_tech_score(data)
    actual = result["ranking_tier"]
    expected = _GOLDEN[school_id]["tier"]
    assert actual == expected, (
        f"{school_id}: tier '{actual}' != golden '{expected}'. "
        "If scoring changed intentionally, run: python scripts/regenerate_golden.py"
    )


@pytest.mark.parametrize("school_id", list(_GOLDEN.keys()))
def test_tech_subscores_match_golden(school_id):
    school_path = _SCHOOLS_DIR / f"{school_id}.json"
    data = json.loads(school_path.read_text(encoding="utf-8"))
    result = compute_tech_score(data)

    golden_subscores = _GOLDEN[school_id]["tech_subscores"]
    for key, expected in golden_subscores.items():
        actual = result["scores"][key]
        assert abs(actual - expected) < 0.01, (
            f"{school_id}.tech_subscores.{key}: {actual} != golden {expected}"
        )


@pytest.mark.parametrize("school_id", list(_GOLDEN.keys()))
def test_practical_breakdown_matches_golden(school_id):
    school_path = _SCHOOLS_DIR / f"{school_id}.json"
    data = json.loads(school_path.read_text(encoding="utf-8"))
    result = compute_practical_score(data)

    golden_breakdown = _GOLDEN[school_id]["practical_breakdown"]
    for key, expected in golden_breakdown.items():
        actual = result["breakdown"][key]
        assert abs(actual - expected) < 0.01, (
            f"{school_id}.practical_breakdown.{key}: {actual} != golden {expected}"
        )
