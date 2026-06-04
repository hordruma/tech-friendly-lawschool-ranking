# Tech-Friendly Law School Ranking

A global, evidence-based ranking of law schools by their genuine commitment to legal technology, artificial intelligence, and technology-integrated legal practice.

**Website:** coming soon  
**Methodology:** [CRITERIA.md](./CRITERIA.md)  
**Data:** [data/schools/](./data/schools/)  
**Formula version:** 2.0 (last updated 2026-06-04)

---

## What this is

Most law school rankings measure reputation, selectivity, or bar passage rates. This ranking measures something different: does this law school actually prepare students for technology-integrated legal practice?

We measure curriculum depth, institutional infrastructure, faculty expertise, and community outcomes — and we apply a **Press Release Gap penalty** to schools that market programs they no longer run.

The data is public, auditable, and community-maintained. All sources are cited. All scores are computed by open-source code.

---

## Methodology

See [CRITERIA.md](./CRITERIA.md) for the full public methodology, including:

- What we measure and why
- The full scoring rubric (100-point scale)
- How data is collected and verified
- The Press Release Gap accountability mechanism
- How to submit corrections

---

## Contributing

### Reporting corrections or new schools

Open a GitHub Issue using one of the templates:

- **[School Submission / Correction](.github/ISSUE_TEMPLATE/school-submission.md)** — add a new school or correct existing data
- **[Press Release Gap Report](.github/ISSUE_TEMPLATE/press-release-gap.md)** — report a gap between marketing and reality

All accepted corrections are merged via pull request. Contributors are credited in git history.

### Submitting a pull request

1. Fork the repository
2. Edit or add JSON files in `data/schools/`
3. Ensure your JSON validates against `data/schema/school.schema.json`
4. Add source URLs and `year_verified` for every new field you add
5. Open a pull request with a description of what you changed and why

JSON files are the canonical source of truth. If you add data without source URLs, it will not be merged.

---

## Running locally

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+ (web app only)
- TypeDB 2.28+ (optional — graph database features only)

### 1. Clone and install

```bash
git clone https://github.com/your-org/tech-friendly-lawschool-ranking
cd tech-friendly-lawschool-ranking

# Install Python package (scoring library + MCP server + agents)
uv sync --extra mcp --extra agents

# Install Node.js dependencies (web app)
cd web && npm install && cd ..
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys:
#   ANTHROPIC_API_KEY   — required for research agent
#   TAVILY_API_KEY      — required for web search in research agent
```

### 3. Run the web app

```bash
cd web && npm run dev
# Open http://localhost:3000
```

The web app reads directly from the JSON files in `data/schools/` — no database required.

### 4. Run the research agent

```bash
python agents/researcher.py \
  --school "Harvard Law School" \
  --url https://hls.harvard.edu \
  --output data/schools/harvard-law.json \
  --merge
```

This will:
1. Search the web for the school's current legaltech offerings (requires `TAVILY_API_KEY`)
2. Use Claude to extract structured data (requires `ANTHROPIC_API_KEY`)
3. Run a second pass to identify press release gaps
4. Merge results with the existing file

### 5. Score a school

```bash
# Human-readable output
python agents/scorer.py data/schools/harvard-law.json

# Write scores back into the file
python agents/scorer.py data/schools/harvard-law.json --write-scores

# JSON output (for scripting)
python agents/scorer.py data/schools/harvard-law.json --format json
```

### 6. Run the MCP server

The MCP server exposes the ranking data to AI assistants (Claude Desktop, Claude.ai, any MCP client).

```bash
# Start the server
lawschool-mcp
# or: python -m mcp_server.server
```

To add it to Claude Desktop, add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lawschool-ranking": {
      "command": "uv",
      "args": ["run", "lawschool-mcp"],
      "cwd": "/path/to/tech-friendly-lawschool-ranking"
    }
  }
}
```

Available MCP tools: `search_schools`, `get_school_profile`, `compare_schools`, `get_career_paths`, `explain_ranking`, `flag_press_release_gaps`, `get_research_queue_stats`.  
Available resources: `lawschool://rankings/all`, `lawschool://methodology`, `lawschool://research-queue`.

### 7. Ingest into TypeDB (optional)

TypeDB enables complex graph queries that flat JSON files can't efficiently answer.

```bash
# Start TypeDB
docker run -d --name typedb -p 1729:1729 vaticle/typedb:latest

# Define schema and ingest all schools
python typedb/ingest.py --schema
```

---

## Testing

```bash
# Python test suite (136 tests)
python -m pytest

# TypeScript test suite (51 tests — unit + Python parity)
cd web && npm test

# Type drift check (Pydantic schema vs TypeScript interfaces)
python scripts/check_type_drift.py

# Regenerate golden scores after changing scoring logic
python scripts/regenerate_golden.py
```

The test suite includes regression tests (`tests/test_golden.py`) that lock the scorer output for the 5 seed schools. If you change scoring logic, regenerate the golden file and commit it alongside your change.

---

## Project structure

```
/
├── CRITERIA.md                      # Public methodology
├── CONTRIBUTING.md                  # Detailed contributor guide
├── pyproject.toml                   # Single root Python package (uv)
├── .env.example                     # Environment variable template
│
├── src/lawschool/                   # Python library (installed as 'lawschool')
│   ├── schema.py                    # Pydantic models (source of truth for data shape)
│   ├── data.py                      # load_school / load_all_schools / get_research_stats
│   ├── scoring/
│   │   ├── tech.py                  # Tech-friendliness scorer (0–100)
│   │   ├── practical.py             # Practical skills scorer (0–100)
│   │   └── meta.py                  # Meta-rank formula (50/30/20 weighted)
│   └── research/
│       └── agent.py                 # Claude + Tavily research agent
│
├── mcp_server/                      # MCP server (exposes data to AI assistants)
│   ├── server.py                    # Entry point (lawschool-mcp console script)
│   ├── resources.py                 # MCP resources
│   └── tools/
│       ├── search.py                # search_schools
│       ├── profile.py               # get_school_profile
│       ├── compare.py               # compare_schools
│       ├── career.py                # get_career_paths
│       └── admin.py                 # explain_ranking, flag_press_release_gaps, stats
│
├── agents/                          # CLI tools
│   ├── researcher.py                # Research agent wrapper
│   └── scorer.py                    # Score a single school JSON
│
├── web/                             # Next.js 14 frontend
│   ├── app/
│   │   ├── page.tsx                 # Homepage
│   │   ├── rankings/page.tsx        # Full rankings table
│   │   ├── schools/[id]/page.tsx    # School profile
│   │   ├── methodology/page.tsx     # CRITERIA.md rendered
│   │   └── submit/page.tsx          # Contribution guide
│   ├── components/
│   │   ├── RankingTable.tsx
│   │   ├── SchoolCard.tsx
│   │   ├── ScoreBadge.tsx
│   │   └── PressReleaseGapAlert.tsx
│   ├── lib/
│   │   ├── types.ts                 # TypeScript types (mirrors schema.py)
│   │   ├── data.ts                  # Read school JSONs
│   │   └── scoring.ts               # TS port of scoring logic (parity with Python)
│   └── __tests__/
│       ├── scoring.unit.test.ts     # Unit tests for TS scoring functions
│       └── scoring.parity.test.ts   # Cross-language parity vs Python golden
│
├── tests/                           # Python test suite (pytest)
│   ├── conftest.py                  # Shared fixtures
│   ├── golden/scores.json           # Locked scorer output for 5 seed schools
│   ├── test_scoring_tech.py
│   ├── test_scoring_practical.py
│   ├── test_scoring_meta.py
│   ├── test_schema.py
│   ├── test_data.py
│   ├── test_golden.py
│   └── test_type_drift.py
│
├── scripts/
│   ├── check_type_drift.py          # Detect Pydantic ↔ TypeScript schema divergence
│   └── regenerate_golden.py         # Regenerate tests/golden/scores.json
│
├── data/
│   ├── schema/school.schema.json    # JSON Schema for school data files
│   ├── meta-ranking/sources.json    # External ranking sources and weights
│   ├── research-list/top-500.json   # 501 schools queued for research
│   └── schools/                     # One JSON file per researched school
│       ├── harvard-law.json
│       ├── stanford-law.json
│       ├── oxford-law.json
│       ├── nus-law.json
│       └── college-of-law-australia.json
│
├── typedb/
│   ├── schema.tql                   # TypeDB schema (TypeQL)
│   └── ingest.py                    # Load JSON → TypeDB
│
└── .github/
    ├── workflows/ci.yml             # CI: pytest + type-drift check + vitest
    └── ISSUE_TEMPLATE/
        ├── school-submission.md
        └── press-release-gap.md
```

---

## Data format

Each school is a JSON file at `data/schools/<id>.json` conforming to `data/schema/school.schema.json`.

Key fields:
- `last_researched` — date when an automated agent last gathered data
- `last_verified` — date when a human reviewer last confirmed data (**null = unverified**)
- `scores` — computed tech scores per criterion (**null = not yet scored**)
- `practical_skills_score` — practical skills score (0–100)
- `meta_score` — combined meta-rank score (0–100)
- `press_release_gap` — documented gaps between marketing claims and reality

Schools with `last_verified: null` are displayed with reduced confidence in the UI and are excluded from tier assignments.

---

## License

Data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)  
Code: MIT  
Methodology (CRITERIA.md): CC BY 4.0
