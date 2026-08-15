# Methodology

This ranking evaluates law schools worldwide on how well they prepare students for
modern, technology-driven legal practice. It is **indicator-based**: schools are scored
against documented, publicly verifiable evidence (program pages, center websites,
course catalogs), not surveys or reputation polls.

## Pillars & weights

| Pillar | Weight | What it measures |
|---|---|---|
| Tech & AI Curriculum | 25% | Breadth/depth of legal tech and AI-specific courses; specialized degrees or certificates (e.g., LLM in Law & Technology, JD certificates) |
| Hands-On Legal Tech | 25% | Clinics and labs where students *build or deploy* technology (e.g., app-building clinics, document automation for legal aid); hackathons and competitions |
| Practical Preparation | 20% | Strength of the experiential program overall: clinical guarantees, required experiential credits, externships, simulation courses |
| Research & Leadership | 20% | A dedicated legal tech/innovation center or lab; faculty scholarship and field leadership in law + technology/AI |
| Industry Ecosystem | 10% | Partnerships with legal tech companies, firms' innovation arms, incubators, and access to a legal tech job market |

## Scoring

Each pillar is scored **0–5** from the documented evidence:

- **5** — Global leader; the program is a reference point for the field
- **4** — Strong, well-established offering with multiple concrete components
- **3** — Solid offering; clearly institutionalized but narrower
- **2** — Some activity; individual courses or ad hoc initiatives
- **1** — Minimal documented activity
- **0** — Nothing documented

The composite score is the weighted sum, rescaled to 0–100.

## Scope & limitations

- **Coverage is curated, not exhaustive.** The list focuses on schools with documented
  legal tech/AI activity. Absence from the list is not a judgment.
- Scores reflect publicly available information as of **August 2026**; programs change.
  Each school's entry carries source URLs in `data/schools.json`.
- Pillar scores involve editorial judgment in mapping evidence to the 0–5 scale.
  The raw evidence is published alongside the scores so readers can disagree.
- Traditional prestige, bar passage, and employment outcomes are deliberately
  **not** ranked here — this is a lens on tech-forward practical preparation, meant to
  complement (not replace) general rankings.

## Reproducing the ranking

```
python3 scripts/score.py   # reads data/schools.json → writes data/rankings.json
```
