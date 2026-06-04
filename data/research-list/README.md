# Research List

This directory contains the queue of law schools to be researched by the AI agents.

## `top-500.json`

A list of ~500 law schools globally, ordered roughly by prestige, for use as input to `agents/researcher.py`.

**Current status:** Partial — US/Canada complete, international schools being added.

### Schema

```json
{
  "id": "harvard-law",           // unique kebab-case slug
  "name": "Harvard Law School",  // official name
  "institution": "Harvard University",
  "country": "US",               // ISO 3166-1 alpha-2
  "city": "Cambridge, MA",
  "region": "North America",     // North America | UK & Ireland | Europe | Asia-Pacific | Latin America | Middle East & Africa
  "url": "https://hls.harvard.edu",
  "known_rankings": {
    "qs_law_approx": 1,          // approximate rank from public sources, or null
    "the_law_approx": null,
    "arwu_law_approx": null,
    "usnews_law_approx": 3       // US schools only
  },
  "accreditation_body": "ABA",   // ABA | SRA | LSRA | etc.
  "research_status": "pending",  // pending | in_progress | complete | skipped
  "notes": ""
}
```

## Running the research agent

```bash
# Research a single school from the list
python agents/researcher.py --school "Harvard Law School" --output data/schools/harvard-law.json

# Research all pending schools (rate-limited)
python agents/researcher.py --batch data/research-list/top-500.json --output-dir data/schools/
```

## Adding schools

Submit a PR editing `top-500.json`, or open an issue using the school submission template. Required fields: `id`, `name`, `country`, `url`, `region`, `research_status: "pending"`.
