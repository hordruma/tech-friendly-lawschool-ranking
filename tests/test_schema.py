"""
tests/test_schema.py

Tests for src/lawschool/schema.py
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lawschool.schema import COUNTRY_TO_REGION, ExternalRankingEntry, LawSchool


# ---------------------------------------------------------------------------
# LawSchool.from_json_file
# ---------------------------------------------------------------------------


def test_from_json_file_loads_harvard(seed_harvard):
    assert seed_harvard.name == "Harvard Law School"


def test_from_json_file_returns_lawschool_instance(seed_harvard):
    assert isinstance(seed_harvard, LawSchool)


def test_from_json_file_harvard_id(seed_harvard):
    assert seed_harvard.id == "harvard-law"


def test_from_json_file_harvard_country(seed_harvard):
    assert seed_harvard.country == "US"


# ---------------------------------------------------------------------------
# ExternalRankingEntry.year accepts None
# ---------------------------------------------------------------------------


def test_external_ranking_entry_year_none():
    entry = ExternalRankingEntry(rank=5, year=None, url=None)
    assert entry.year is None


def test_external_ranking_entry_year_int():
    entry = ExternalRankingEntry(rank=5, year=2024, url="https://example.com")
    assert entry.year == 2024


def test_external_ranking_entry_rank_none():
    entry = ExternalRankingEntry(rank=None, year=2024, url=None)
    assert entry.rank is None


# ---------------------------------------------------------------------------
# Pydantic validation
# ---------------------------------------------------------------------------


def test_lawschool_missing_required_id_raises():
    with pytest.raises(ValidationError):
        LawSchool(
            # id is missing
            name="Test",
            country="US",
            url="https://example.com",
        )


def test_lawschool_missing_required_name_raises():
    with pytest.raises(ValidationError):
        LawSchool(
            id="test",
            # name is missing
            country="US",
            url="https://example.com",
        )


def test_lawschool_missing_required_url_raises():
    with pytest.raises(ValidationError):
        LawSchool(
            id="test",
            name="Test",
            country="US",
            # url is missing
        )


def test_lawschool_minimal_valid():
    school = LawSchool(
        id="test",
        name="Test School",
        country="US",
        url="https://example.com",
    )
    assert school.id == "test"
    assert school.courses == []
    assert school.programs == []


# ---------------------------------------------------------------------------
# LawSchool.region property
# ---------------------------------------------------------------------------


def test_region_us():
    school = LawSchool(id="t", name="T", country="US", url="https://x.com")
    assert school.region == "North America"


def test_region_gb():
    school = LawSchool(id="t", name="T", country="GB", url="https://x.com")
    assert school.region == "UK & Ireland"


def test_region_sg():
    school = LawSchool(id="t", name="T", country="SG", url="https://x.com")
    assert school.region == "Asia-Pacific"


def test_region_unknown_returns_none():
    school = LawSchool(id="t", name="T", country="XX", url="https://x.com")
    assert school.region is None


def test_region_de():
    school = LawSchool(id="t", name="T", country="DE", url="https://x.com")
    assert school.region == "Europe"


def test_region_au():
    school = LawSchool(id="t", name="T", country="AU", url="https://x.com")
    assert school.region == "Asia-Pacific"


def test_region_br():
    school = LawSchool(id="t", name="T", country="BR", url="https://x.com")
    assert school.region == "Latin America"


# ---------------------------------------------------------------------------
# COUNTRY_TO_REGION coverage
# ---------------------------------------------------------------------------


def test_country_to_region_covers_at_least_40_entries():
    assert len(COUNTRY_TO_REGION) >= 40


def test_country_to_region_has_expected_regions():
    regions = set(COUNTRY_TO_REGION.values())
    assert "North America" in regions
    assert "UK & Ireland" in regions
    assert "Europe" in regions
    assert "Asia-Pacific" in regions
    assert "Latin America" in regions
    assert "Middle East & Africa" in regions
