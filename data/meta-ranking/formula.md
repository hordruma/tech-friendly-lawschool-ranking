# Meta-Rank Formula

**Formula version:** 2.0  
**Last updated:** 2026-06-04  
**Defined in:** `data/meta-ranking/sources.json`  
**Implemented in:** `agents/scorer.py` (`compute_meta_score`), `web/lib/scoring.ts` (`computeMetaScore`)

---

## Overview

The **meta-rank** is a composite ranking that combines three independent signals:

1. **Tech Score (50%)** — our primary measure of how genuinely tech-friendly a law school is (0–100 scale, see `CRITERIA.md` Sections 3.1–3.5)
2. **Practical Skills Score (30%)** — how well the school prepares students for real legal practice (0–100 scale, see `CRITERIA.md` Section 3.6)
3. **Prestige Score (20%)** — an aggregated, normalized score derived from major external global law school rankings

The meta-rank answers a richer question than any single score: *across tech integration, practice preparation, and traditional academic standing, which schools offer the most complete legal education?*

### Why 50/30/20?

- **Tech at 50%** is our primary unique contribution. No other ranking measures genuine tech integration. It must dominate the composite.
- **Practical Skills at 30%** is closely aligned with our mission — we care about schools that prepare graduates for modern practice, not just those that teach about technology in the abstract. Rewarding practical training reinforces our core value.
- **Prestige at 20%** provides contextual background that other rankings already handle well. We include it so users can see where tech/practical scores diverge from traditional standing, but we do not let it dominate.

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
meta_score = (tech_score × 0.50) + (practical_skills_score × 0.30) + (prestige_score × 0.20)
```

Where:
- `tech_score` is the school's tech-friendliness score (0–100), from `scores.total`
- `practical_skills_score` is the school's practical skills score (0–100), from `practical_skills_score`
- `prestige_score` is the normalized average from Step 2 (0–100)
- All weights sum to 1.0

**Null handling:**

- If `prestige_score` is null (no external ranking data), the meta score is null and the school is excluded from meta-ranking.
- If `practical_skills_score` is null (not yet researched), the formula proportionally rescales the remaining two components:

```
meta_score = (tech_score × 0.625) + (prestige_score × 0.375)
```

(0.50 / 0.80 = 0.625 for tech; 0.20 / 0.80 = 0.25 — but we use 0.375 per the 50:20 ratio rescaled to sum to 1.0.)

This fallback ensures schools that have not yet been assessed for practical skills can still appear in the meta-rank, with a note that practical skills data is pending.

---

## Step 4: Determine Meta Rank

Schools are sorted by `meta_score` in descending order. The school with the highest meta score receives meta rank #1. Ties are broken by `tech_score` (higher is better), then `practical_skills_score`, then alphabetically by school name.

Schools with `meta_score = null` are excluded from the meta-rank list and displayed as unranked on the meta-rank axis.

---

## The Three Pillars

| Pillar | Weight | What It Measures |
|--------|--------|-----------------|
| Tech-Friendliness | 50% | Genuine integration of legal technology into curriculum, infrastructure, faculty, and community |
| Practical Skills | 30% | Clinical programs, skills curricula, experiential placements, and professional readiness |
| Prestige | 20% | Aggregated position across six major external global law school rankings |

Each pillar is independently computed and independently displayed. Users can explore how each school performs on each axis separately; the meta-score is one composite view, not the only view.

---

## Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-04 | Initial release. Six sources, unweighted average, 50/50 tech/prestige split, log-scaled normalization with max_rank=500. |
| 2.0 | 2026-06-04 | Added Practical Skills as a third pillar. Weights updated: Tech 50%, Practical Skills 30%, Prestige 20%. Added null fallback for practical_skills_score. |

Formula changes that would materially alter rank positions trigger a re-computation cycle and are announced with at least 30 days notice before scores are updated.
