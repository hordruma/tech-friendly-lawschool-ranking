#!/usr/bin/env python
"""
scripts/regenerate_golden.py

Regenerate tests/golden/scores.json by running the Python scorers on all
seed schools in data/schools/.

Run after intentional scoring changes:
    python scripts/regenerate_golden.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the src/ package is importable when run from repo root
_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from lawschool.scoring.practical import compute_practical_score  # noqa: E402
from lawschool.scoring.tech import compute_tech_score  # noqa: E402

_SCHOOLS_DIR = _REPO_ROOT / "data" / "schools"
_GOLDEN_PATH = _REPO_ROOT / "tests" / "golden" / "scores.json"


def main() -> None:
    results: dict = {}

    school_files = sorted(_SCHOOLS_DIR.glob("*.json"))
    if not school_files:
        print(f"ERROR: No school JSON files found in {_SCHOOLS_DIR}", file=sys.stderr)
        sys.exit(1)

    for path in school_files:
        school_id = path.stem
        data = json.loads(path.read_text(encoding="utf-8"))

        tech_result = compute_tech_score(data)
        practical_result = compute_practical_score(data)

        # Normalise all subscore values to float for consistent JSON output
        tech_subscores = {
            k: float(v)
            for k, v in tech_result["scores"].items()
            if k != "total"
        }
        practical_breakdown = {
            k: float(v)
            for k, v in practical_result["breakdown"].items()
        }

        results[school_id] = {
            "tech_total": float(tech_result["scores"]["total"]),
            "practical_total": float(practical_result["practical_skills_score"]),
            "tier": tech_result["ranking_tier"],
            "tech_subscores": tech_subscores,
            "practical_breakdown": practical_breakdown,
        }

        print(f"  {school_id}: tech={results[school_id]['tech_total']}, "
              f"practical={results[school_id]['practical_total']}, "
              f"tier={results[school_id]['tier']}")

    _GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    _GOLDEN_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {len(results)} schools to {_GOLDEN_PATH}")


if __name__ == "__main__":
    main()
