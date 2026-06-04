"""
tests/test_type_drift.py

Pytest wrapper around scripts/check_type_drift.py.

Fails if any Python model field is absent from the corresponding TypeScript
interface in web/lib/types.ts.  This catches schema drift early.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).parent.parent / "scripts" / "check_type_drift.py"


def test_no_missing_fields_in_typescript():
    """
    Run check_type_drift.py and assert exit code 0.

    Exit code 0 = all Python fields present in TS (may have extra TS fields — WARN is OK).
    Exit code 1 = missing fields (FAIL).
    Exit code 2 = parse error.
    """
    result = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        capture_output=True,
        text=True,
    )

    # Print output so it's visible in pytest -v output
    if result.stdout:
        print("\n--- check_type_drift.py output ---")
        print(result.stdout)
    if result.stderr:
        print("\n--- check_type_drift.py stderr ---")
        print(result.stderr)

    assert result.returncode != 2, (
        "check_type_drift.py returned exit code 2 (parse error).\n"
        f"stderr: {result.stderr}"
    )

    assert result.returncode == 0, (
        "TypeScript types.ts is missing fields that exist in the Python schema.\n"
        "Fix web/lib/types.ts or run: python scripts/check_type_drift.py for details.\n"
        f"Output:\n{result.stdout}"
    )
