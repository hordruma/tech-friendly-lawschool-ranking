# Meta-Rank Formula

**Formula version:** 1.0  
**Last updated:** 2026-06-04  
**Defined in:** `data/meta-ranking/sources.json`  
**Implemented in:** `agents/scorer.py` (`compute_meta_score`), `web/lib/scoring.ts` (`computeMetaScore`)

---

## Overview

The **meta-rank** is a composite ranking that combines two independent signals:

1. **Tech Score (50%)** — our primary measure of how genuinely tech-friendly a law school is (0–100 scale, see `CRITERIA.md`)
2. **Prestige Score (50%)** — an aggregated, normalized score derived from major external global law school rankings

The meta-rank answers a different question from our primary tech-friendliness ranking: *how does a school's tech engagement relate to its overall global standing?* A school ranked #1 for tech but #50 for prestige tells a different story than a top-prestige school that neglects technology.

---

## Step 1: Normalize Each External Ranking (0–100)

Each external ranking position is converted to a 0–100 score using an **inverse rank, log-scaled** formula:

```
normalized_score = 100 × (1 − log(rank) / log(max_rank + 1))
```

Where:
- `rank` is the school's position in that ranking (1 = best)
- `max_rank` is set to **500** (a conservative ceiling covering all major global law schools)
- `log` is the natural logarithm

**Why log-scaling?** Rankings are not linear. The difference between rank 1 and rank 5 is far more meaningful than the difference between rank 95 and rank 100. Log-scaling compresses the lower end and expands the upper end, better reflecting real-world prestige differentiation.

**Example values (max_rank = 500):**

| Rank | Normalized Score |
|------|-----------------|
| 1    | 100.0           |
| 2    | 89.8            |
| 5    | 74.2            |
| 10   | 62.4            |
| 25   | 47.8            |
| 50   | 36.8            |
| 100  | 25.6            |
| 200  | 14.4            |
| 500  | 0.0             |

---

## Step 2: Average Available Normalized Scores (Prestige Score)

The **prestige score** is the arithmetic mean of all normalized external ranking scores for which data is available:

```
prestige_score = mean(normalized_score_i for all available rankings i)
```

**Missing rankings are excluded — not zeroed.** A school not covered by a ranking (e.g., a non-US school not in US News domestic rankings) is not penalized for that absence. Only rankings where the school appears are included in the average.

**Minimum coverage:** A prestige score is computed as long as at least **1** external ranking is available. Schools with no external ranking data at all receive a prestige score of `null` and are excluded from meta-ranking.

**Source weights:** The six sources are used in the prestige average with equal arithmetic weight (i.e., the weighted average in `sources.json` applies only if a weighted average mode is selected — the default is unweighted). Future formula versions may apply the weights defined in `sources.json`.

---

## Step 3: Compute Meta Score

```
meta_score = (tech_score × 0.50) + (prestige_score × 0.50)
```

Where:
- `tech_score` is the school's tech-friendliness score (0–100), from `scores.total` normalized to 100 (the raw score is already out of 100)
- `prestige_score` is the normalized average from Step 2 (0–100)
- Both weights sum to 1.0

If `prestige_score` is null (no external ranking data), the meta score cannot be computed and is left as null. A future version may allow prestige-less meta-scores using tech score alone, but this would require a schema version bump.

---

## Step 4: Determine Meta Rank

Schools are sorted by `meta_score` in descending order. The school with the highest meta score receives meta rank #1. Ties are broken by `tech_score` (higher is better), then alphabetically by school name.

Schools with `meta_score = null` are excluded from the meta-rank list and displayed as unranked on the meta-rank axis.

---

## Why 50/50?

We weight tech score and prestige equally for two reasons:

1. **Interpretability.** A 50/50 split is easy for users to understand and interrogate. It clearly signals that neither dimension dominates.

2. **Complementarity.** Our primary ranking already answers "which school is most tech-friendly?" The meta-rank adds a different question: "accounting for overall global standing, which schools are punching above or below their prestige weight on tech?" Equal weighting keeps both dimensions visible.

A future formula version may allow users to adjust the weight interactively (e.g., 80% tech / 20% prestige for users who care only about tech, or 30% tech / 70% prestige for users who prioritize traditional markers).

---

## Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-04 | Initial release. Six sources, unweighted average, 50/50 split, log-scaled normalization with max_rank=500. |

Formula changes that would materially alter rank positions trigger a re-computation cycle and are announced with at least 30 days notice before scores are updated.
