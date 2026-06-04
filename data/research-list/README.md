# Research List: Global Law School Coverage

## What This List Is

`top-500.json` is the **input dataset** for the tech-friendliness ranking project. It contains ~500 law schools from around the world, compiled from:

- QS World University Rankings by Subject (Law)
- Times Higher Education World University Rankings (Law)
- ARWU (Shanghai Rankings) subject rankings for Law
- US News & World Report Law School Rankings (US schools)
- Regional prestige and national significance

Each entry is a school **to be researched** by AI agents. The entries do not yet contain tech-friendliness scores — those are populated by the research agent and written to `data/schools/`.

---

## File Format

Each entry in the JSON array follows this schema:

```json
{
  "id": "harvard-law",
  "name": "Harvard Law School",
  "institution": "Harvard University",
  "country": "US",
  "city": "Cambridge, MA",
  "region": "North America",
  "url": "https://hls.harvard.edu",
  "known_rankings": {
    "qs_law_approx": 1,
    "the_law_approx": 1,
    "arwu_law_approx": 1,
    "usnews_law_approx": 3
  },
  "accreditation_body": "ABA",
  "research_status": "pending",
  "notes": ""
}
```

### Field reference

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Unique kebab-case slug. For name collisions across countries, append country code (e.g. `university-of-law-uk`) |
| `name` | string | yes | Official English name of the law school |
| `institution` | string | yes | Parent university name |
| `country` | string | yes | ISO 3166-1 alpha-2 country code |
| `city` | string | yes | City (and state/province where helpful) |
| `region` | string | yes | One of: `North America`, `UK & Ireland`, `Europe`, `Asia-Pacific`, `Latin America`, `Middle East & Africa` |
| `url` | string | yes | Official website URL |
| `known_rankings.qs_law_approx` | int or null | yes | Approximate QS Law rank, or null |
| `known_rankings.the_law_approx` | int or null | yes | Approximate THE Law rank, or null |
| `known_rankings.arwu_law_approx` | int or null | yes | Approximate ARWU Law rank, or null |
| `known_rankings.usnews_law_approx` | int or null | yes | US News rank (US schools only), or null |
| `accreditation_body` | string or null | yes | `ABA` (US), `SRA` (England/Wales), `LSRA` (Ireland), or null |
| `research_status` | string | yes | One of: `pending`, `in-progress`, `complete`, `skipped` |
| `notes` | string | yes | Optional free-text notes; use `"verify name and URL"` for uncertain entries |

---

## How to Add Schools

1. **Check for duplicates** — search `top-500.json` for the institution name or URL before adding.
2. **Assign a unique ID** — use kebab-case of the school name. For institutions with the same common name in different countries, append the ISO country code: e.g. `queens-law-ca` vs `queens-belfast-law`.
3. **Set `research_status` to `"pending"`** — all new entries start as pending.
4. **Flag uncertainty** — if you are not confident about the URL or official name, add `"verify name and URL"` to the `notes` field.
5. **Chinese schools** — include the English name in `name` and add the Chinese name in `notes`.
6. **Maintain sort order** — new entries should be appended; the research agent processes all `pending` entries regardless of order.

### Minimal valid entry

```json
{
  "id": "example-law",
  "name": "Example University School of Law",
  "institution": "Example University",
  "country": "AU",
  "city": "Sydney, NSW",
  "region": "Asia-Pacific",
  "url": "https://law.example.edu.au",
  "known_rankings": {
    "qs_law_approx": null,
    "the_law_approx": null,
    "arwu_law_approx": null,
    "usnews_law_approx": null
  },
  "accreditation_body": null,
  "research_status": "pending",
  "notes": ""
}
```

---

## How the Research Agent Uses This List

1. The agent reads `top-500.json` and filters for entries where `research_status === "pending"`.
2. For each school it visits the `url`, crawls key pages (curriculum, clinics, programs, faculty), and scores the school against the criteria in `CRITERIA.md`.
3. On completion it writes a scored profile to `data/schools/<id>.json` and updates `research_status` to `"complete"` in this file.
4. Failures (unreachable URL, insufficient data) set `research_status` to `"skipped"` with a reason appended to `notes`.

Agents can be run in parallel; each agent locks a school by setting `research_status` to `"in-progress"` before crawling.

```bash
# Research a single school
python agents/researcher.py --school harvard-law --output data/schools/harvard-law.json

# Research all pending schools (rate-limited)
python agents/researcher.py --batch data/research-list/top-500.json --output-dir data/schools/
```

---

## Regional Coverage Breakdown

| Region | Count | Primary countries |
|---|---|---|
| North America | ~177 | US (~154 ABA-accredited), Canada (~23) |
| UK & Ireland | ~45 | England, Scotland, Wales, N. Ireland, Republic of Ireland |
| Europe (non-UK) | ~76 | DE, FR, NL, IT, ES, SE, CH, BE, DK, NO, FI, AT, PL, CZ, HU, PT, GR, TR, RU, EE, LV, LT, HR, SI |
| Asia-Pacific | ~112 | AU, NZ, SG, HK, JP, KR, CN, IN, MY, TW, PH, TH, ID, VN, LK, PK, BD, NP |
| Latin America | ~49 | BR, MX, AR, CL, CO, PE, PR, CR, UY, VE, EC, BO |
| Middle East & Africa | ~42 | ZA, IL, EG, AE, SA, QA, JO, LB, IR, KW, NG, GH, KE, ET, UG, TZ, ZM, ZW, BW, SN, OM, MA, TN |

**Total: ~501 schools**

The list is sorted roughly by global prestige (highest first). Schools without global ranking data are sorted by national significance within their region.

---

## Maintenance Notes

- Entries marked `"verify name and URL"` in `notes` should be manually checked before the research agent crawls them.
- Closed or merged schools are kept in the list with an explanatory note so the agent can skip them cleanly rather than failing on a bad URL.
- US coverage includes all ABA-accredited schools that have appeared in any major ranking plus nationally significant schools (HBCUs, regional flagships).
- Ranking values (`qs_law_approx`, etc.) are approximate as of 2024-2025 and are for ordering purposes only — not authoritative figures.
- Ranks listed as ranges (e.g. `100` in US News) mean the school appeared in that tier, not necessarily at that exact rank.
