# Tech-Friendly Law School Ranking

A global, evidence-based ranking of law schools by their genuine commitment to legal technology, artificial intelligence, and technology-integrated legal practice.

**Website:** coming soon  
**Methodology:** [CRITERIA.md](./CRITERIA.md)  
**Data:** [data/schools/](./data/schools/)

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

- Node.js 18+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- TypeDB 2.28+ (optional, for graph database features)

### 1. Clone and install

```bash
git clone https://github.com/your-org/tech-friendly-lawschool-ranking
cd tech-friendly-lawschool-ranking

# Install Python dependencies (agents)
cd agents
uv sync
cd ..

# Install Node.js dependencies (web app)
cd web
npm install
cd ..
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 3. Run the web app

```bash
cd web
npm run dev
# Open http://localhost:3000
```

The web app reads directly from the JSON files in `data/schools/` — no database required for basic operation.

### 4. Run the research agent

```bash
cd agents
python researcher.py --school "Harvard Law School" \
  --url https://hls.harvard.edu \
  --output ../data/schools/harvard-law.json \
  --merge
```

This will:
1. Search the web for Harvard Law's current legaltech offerings (requires `TAVILY_API_KEY`)
2. Use Claude to extract structured data (requires `ANTHROPIC_API_KEY`)
3. Run a second pass to identify press release gaps
4. Merge results with the existing file

### 5. Score a school

```bash
cd agents
python scorer.py ../data/schools/harvard-law.json
```

To write scores back into the file:

```bash
python scorer.py ../data/schools/harvard-law.json --write-scores
```

### 6. Ingest into TypeDB (optional)

TypeDB enables complex graph queries that flat JSON files can't efficiently answer (e.g., "find all schools in Asia with a legaltech center AND a JD/CS joint degree AND at least 3 active partnerships").

```bash
# Start TypeDB (Docker)
docker run -d --name typedb -p 1729:1729 vaticle/typedb:latest

# Define schema and ingest all schools
python typedb/ingest.py --schema
```

---

## Project structure

```
/
├── CRITERIA.md                  # Public methodology document
├── README.md                    # This file
├── .env.example                 # Environment variable template
│
├── data/
│   ├── schema/
│   │   └── school.schema.json   # JSON Schema for school data files
│   └── schools/                 # One JSON file per school (source of truth)
│       ├── harvard-law.json
│       ├── stanford-law.json
│       ├── oxford-law.json
│       ├── nus-law.json
│       └── college-of-law-australia.json
│
├── typedb/
│   ├── schema.tql               # TypeDB schema (TypeQL)
│   └── ingest.py                # Script to load JSON → TypeDB
│
├── agents/
│   ├── researcher.py            # Research agent (Tavily + Claude)
│   ├── scorer.py                # Scoring logic
│   ├── pyproject.toml           # Python dependencies (uv)
│   └── requirements.txt         # Python dependencies (pip)
│
├── web/                         # Next.js 14 frontend
│   ├── app/
│   │   ├── page.tsx             # Homepage
│   │   ├── rankings/page.tsx    # Full rankings table
│   │   ├── schools/[id]/page.tsx # School profile
│   │   ├── methodology/page.tsx # CRITERIA.md rendered
│   │   └── submit/page.tsx      # Contribution guide
│   ├── components/
│   │   ├── RankingTable.tsx
│   │   ├── SchoolCard.tsx
│   │   ├── ScoreBadge.tsx
│   │   └── PressReleaseGapAlert.tsx
│   └── lib/
│       ├── data.ts              # Read school JSONs
│       └── scoring.ts           # TypeScript port of scoring logic
│
└── .github/
    └── ISSUE_TEMPLATE/
        ├── school-submission.md
        └── press-release-gap.md
```

---

## Data format

Each school is a JSON file at `data/schools/<id>.json` conforming to `data/schema/school.schema.json`.

Key fields:
- `last_researched`: date when an automated agent last gathered data
- `last_verified`: date when a human reviewer last verified data (**null = unverified**)
- `scores`: computed scores per criterion (**null = not yet scored**)
- `press_release_gap`: array of documented gaps between marketing and reality

Schools with `last_verified: null` are displayed with reduced confidence in the UI.

---

## License

Data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)  
Code: MIT  
Methodology (CRITERIA.md): CC BY 4.0
