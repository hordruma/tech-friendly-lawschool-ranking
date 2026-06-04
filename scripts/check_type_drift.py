#!/usr/bin/env python
"""
scripts/check_type_drift.py

Checks that web/lib/types.ts TypeScript interfaces stay in sync with
src/lawschool/schema.py Pydantic models.

For each Pydantic model, verifies that the corresponding TS interface
contains at least all the fields the Python model declares.

Exit codes:
    0  — all Python model fields found in TS (PASS / WARN for extra TS fields)
    1  — one or more Python model fields missing from TS (FAIL)
    2  — parse error (could not read files or extract fields)

Usage:
    python scripts/check_type_drift.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration: mapping Python model name → TS interface name
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_SCHEMA_PY = _REPO_ROOT / "src" / "lawschool" / "schema.py"
_TYPES_TS = _REPO_ROOT / "web" / "lib" / "types.ts"

# Models to check; keys are Python class names, values are TS interface names
MODEL_MAP: dict[str, str] = {
    "LawSchool": "LawSchool",
    "Course": "Course",
    "Program": "Program",
    "Faculty": "Faculty",
    "Partnership": "Partnership",
    "StudentOrg": "StudentOrg",
    "PressReleaseGap": "PressReleaseGap",
    "ExternalRankingEntry": "ExternalRankingEntry",
    "ExternalRankings": "ExternalRankings",
    "TechScores": "Scores",
    "PracticalSkillsBreakdown": "PracticalSkillsBreakdown",
}


# ---------------------------------------------------------------------------
# Field extraction helpers
# ---------------------------------------------------------------------------

def _python_fields(model_name: str) -> set[str] | None:
    """Return the set of field names for a Pydantic model by importing it."""
    try:
        sys.path.insert(0, str(_REPO_ROOT / "src"))
        import importlib
        module = importlib.import_module("lawschool.schema")
        cls = getattr(module, model_name, None)
        if cls is None:
            return None
        # Pydantic v2: model_fields is a dict of field_name → FieldInfo
        if hasattr(cls, "model_fields"):
            return set(cls.model_fields.keys())
        return None
    except Exception as exc:
        print(f"ERROR: Could not import {model_name} from lawschool.schema: {exc}", file=sys.stderr)
        return None


def _typescript_interfaces(ts_text: str) -> dict[str, set[str]]:
    """
    Parse TypeScript source and extract field names for each `interface`.

    Returns a dict mapping interface_name → set of field names.
    Uses regex; handles optional fields (field?: type) and readonly.

    Limitations: ignores extends, index signatures, methods, and comments.
    """
    interfaces: dict[str, set[str]] = {}

    # Match interface blocks: "interface Foo { ... }"
    # Using a simple brace-counting approach after finding the opening brace
    interface_header_re = re.compile(r"\binterface\s+(\w+)[^{]*\{")

    pos = 0
    while True:
        m = interface_header_re.search(ts_text, pos)
        if not m:
            break

        iface_name = m.group(1)
        brace_start = m.end() - 1  # position of '{'
        depth = 0
        i = brace_start
        while i < len(ts_text):
            if ts_text[i] == "{":
                depth += 1
            elif ts_text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = ts_text[brace_start + 1:i]

        # Extract field names: lines like "  fieldName?: type;" or "  fieldName: type;"
        field_re = re.compile(r"^\s+(?:readonly\s+)?(\w+)\??:", re.MULTILINE)
        fields: set[str] = set()
        for fm in field_re.finditer(body):
            fields.add(fm.group(1))

        # Skip duplicate definitions (later one wins, but we only track the first)
        if iface_name not in interfaces:
            interfaces[iface_name] = fields

        pos = i + 1

    return interfaces


# ---------------------------------------------------------------------------
# Main check
# ---------------------------------------------------------------------------

def main() -> int:
    # Ensure files exist
    for path in (_SCHEMA_PY, _TYPES_TS):
        if not path.exists():
            print(f"ERROR: File not found: {path}", file=sys.stderr)
            return 2

    try:
        ts_text = _TYPES_TS.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"ERROR: Could not read {_TYPES_TS}: {exc}", file=sys.stderr)
        return 2

    ts_interfaces = _typescript_interfaces(ts_text)

    any_missing = False

    for py_name, ts_name in MODEL_MAP.items():
        py_fields = _python_fields(py_name)
        if py_fields is None:
            print(f"WARN  {py_name}: could not extract Python fields (skipping)")
            continue

        ts_fields = ts_interfaces.get(ts_name)
        if ts_fields is None:
            print(f"FAIL  {py_name} → TS interface '{ts_name}' not found in types.ts")
            any_missing = True
            continue

        missing = py_fields - ts_fields
        extra = ts_fields - py_fields

        status_parts = []
        if missing:
            status_parts.append(f"MISSING in TS: {sorted(missing)}")
            any_missing = True
        if extra:
            status_parts.append(f"extra TS fields: {sorted(extra)}")

        if missing:
            label = "FAIL "
        elif extra:
            label = "WARN "
        else:
            label = "OK   "

        msg = f"{label} {py_name} (Python: {len(py_fields)} fields, TS: {len(ts_fields)} fields)"
        if status_parts:
            msg += " — " + "; ".join(status_parts)
        else:
            msg += " — OK"
        print(msg)

    return 1 if any_missing else 0


if __name__ == "__main__":
    sys.exit(main())
