#!/usr/bin/env python3
"""Compute the tech-friendly law school ranking from data/schools.json.

Each school entry carries pillar scores (0-5) under "scores". The composite is a
weighted sum rescaled to 0-100. Output: data/rankings.json, sorted descending.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

WEIGHTS = {
    "curriculum": 0.25,
    "hands_on": 0.25,
    "practical": 0.20,
    "research": 0.20,
    "ecosystem": 0.10,
}

PILLAR_LABELS = {
    "curriculum": "Tech & AI Curriculum",
    "hands_on": "Hands-On Legal Tech",
    "practical": "Practical Preparation",
    "research": "Research & Leadership",
    "ecosystem": "Industry Ecosystem",
}


def composite(scores: dict) -> float:
    missing = set(WEIGHTS) - set(scores)
    if missing:
        raise ValueError(f"missing pillar scores: {missing}")
    return round(sum(scores[p] * w for p, w in WEIGHTS.items()) / 5 * 100, 1)


def main() -> None:
    schools = []
    for f in sorted((ROOT / "data" / "regions").glob("*.json")):
        schools.extend(json.loads(f.read_text()))
    for s in schools:
        s["composite"] = composite(s["scores"])
    schools.sort(key=lambda s: (-s["composite"], s["name"]))
    rank = 0
    prev = None
    for i, s in enumerate(schools, 1):
        if s["composite"] != prev:
            rank = i
            prev = s["composite"]
        s["rank"] = rank  # ties share a rank
    out = {"weights": WEIGHTS, "pillar_labels": PILLAR_LABELS, "schools": schools}
    (ROOT / "data" / "rankings.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"Ranked {len(schools)} schools -> data/rankings.json")
    for s in schools[:10]:
        print(f"{s['rank']:>3}. {s['name']:<45} {s['composite']}")


if __name__ == "__main__":
    main()
