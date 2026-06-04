# Law School Ranking MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that lets AI assistants
help prospective law students explore, search, and compare schools from the
Tech-Friendly Law School Ranking database.

---

## What this server provides

### Tools

| Tool | Description |
|------|-------------|
| `search_schools` | Filter and rank schools by region, country, scores, programs, and tier |
| `get_school_profile` | Full profile of a single school — all courses, programs, faculty, scores |
| `compare_schools` | Side-by-side comparison of 2–5 schools |
| `find_schools_for_career` | Advisor-style recommendations based on a career goal |
| `explain_ranking` | Plain-English methodology overview |
| `flag_press_release_gaps` | Accountability: schools that marketed programs they no longer offer |
| `get_research_queue_stats` | Research coverage: how many schools scored vs pending |

### Resources

| URI | Description |
|-----|-------------|
| `law-schools://methodology` | Full CRITERIA.md text |
| `law-schools://schools` | JSON summaries of all researched schools |
| `law-schools://research-queue` | Coverage stats from top-500.json |

---

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Install with uv

```bash
# From the project root
uv pip install -e mcp-server/
```

### Install with pip

```bash
pip install -e mcp-server/
```

### Verify the install

```bash
lawschool-mcp --help
# or
python mcp-server/server.py
```

The server communicates over stdio (standard MCP transport). It will start and
wait for MCP messages — you'll typically not run it directly, but through your
AI assistant's MCP integration.

---

## Add to Claude Desktop

1. Open your Claude Desktop config file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the server under `mcpServers`:

```json
{
  "mcpServers": {
    "lawschool-ranking": {
      "command": "python",
      "args": ["/absolute/path/to/tech-friendly-lawschool-ranking/mcp-server/server.py"],
      "env": {}
    }
  }
}
```

Or if you've installed the package with uv/pip:

```json
{
  "mcpServers": {
    "lawschool-ranking": {
      "command": "lawschool-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

3. Restart Claude Desktop. You should see the law school tools available in the
   tool picker (hammer icon).

---

## Add to Cursor

In Cursor, open **Settings → Features → MCP Servers** and add:

```json
{
  "lawschool-ranking": {
    "command": "python",
    "args": ["/absolute/path/to/tech-friendly-lawschool-ranking/mcp-server/server.py"]
  }
}
```

Or via the Cursor `mcp.json` config file (usually at `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "lawschool-ranking": {
      "command": "python",
      "args": ["/absolute/path/to/tech-friendly-lawschool-ranking/mcp-server/server.py"]
    }
  }
}
```

---

## Add to VS Code (Copilot / Continue)

For [Continue](https://continue.dev), add to `.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "lawschool-ranking",
      "command": "python",
      "args": ["/absolute/path/to/tech-friendly-lawschool-ranking/mcp-server/server.py"]
    }
  ]
}
```

For GitHub Copilot's MCP support (VS Code extension settings):

```json
{
  "github.copilot.mcp.servers": {
    "lawschool-ranking": {
      "command": "python",
      "args": ["/absolute/path/to/tech-friendly-lawschool-ranking/mcp-server/server.py"]
    }
  }
}
```

---

## Example prompts for students

Once the server is connected to your AI assistant, try these prompts:

**Finding schools by criteria:**
- "Which law schools in Europe have required AI courses?"
- "Show me all Tier A or S law schools with a legaltech clinic"
- "Which law schools offer a JD/CS joint degree?"
- "Find law schools in Asia with a tech score above 50"

**Career-based recommendations:**
- "I want to be a legal engineer — where should I study?"
- "Recommend law schools for someone who wants to work in AI policy"
- "I'm interested in legal operations at a tech company. Which schools prepare students for that?"
- "I want to code as well as practise law — what are my options?"
- "Best schools for access-to-justice technology work?"

**Comparing schools:**
- "Compare Oxford, UCL and Edinburgh for tech-focused law"
- "Compare Harvard, Stanford and NYU on practical skills training"
- "Head-to-head: NUS Law vs Oxford Law for an AI policy career"

**Regional searches:**
- "Show me schools with the highest practical training scores in Asia"
- "Best tech-friendly law schools in the UK?"
- "Which Latin American law schools are doing interesting legaltech work?"

**Accountability and transparency:**
- "Are there any schools that marketed legaltech programs they no longer offer?"
- "Which schools have press release gaps that affect their score?"
- "How does the ranking methodology work? Can I trust it?"

**Data coverage:**
- "How many law schools have been fully researched so far?"
- "What percentage of the research queue is complete?"
- "What is the methodology for the prestige score?"

---

## Data freshness and re-running agents

The MCP server reads directly from the JSON files in `data/schools/`. It does
**not** require TypeDB or any database — the JSON files are the source of truth
for the MCP layer.

### Scores are computed on-the-fly

If a school JSON file does not have pre-computed scores (i.e., `scores.total`
is null), the server computes them at request time using the same logic as
`agents/scorer.py`. This means you always get the latest scores as long as the
JSON data is up to date.

### To update school data

Re-run the research agent (see `agents/researcher.py`) and scorer:

```bash
# Research a specific school
python agents/researcher.py data/schools/harvard-law.json

# Re-score after updating data
python agents/scorer.py data/schools/harvard-law.json --write-scores

# Re-score all schools
for f in data/schools/*.json; do
  python agents/scorer.py "$f" --write-scores --output "$f"
done
```

### Data freshness rules

- Scores are **current** if all sources verified within 18 months
- `last_verified: null` means no human reviewer has confirmed the data
- Courses with `year_verified: null` are **not counted** in tech scores
- Treat any field without a verification date as indicative only

### To add a new school to the queue

Edit `data/research-list/top-500.json` or open a GitHub issue.

---

## Architecture notes

```
mcp-server/
├── server.py        Main MCP server (tools + resources)
├── data_loader.py   Loads JSON files, computes missing scores, returns stats
├── scoring.py       Thin adapter re-exporting agents/scorer.py logic
├── pyproject.toml   Package metadata + entry point
└── README.md        This file
```

The server has no database dependency. It reads JSON files at request time and
caches nothing (intentional — keeps it stateless and easy to reason about).

The scoring logic lives in `agents/scorer.py`. `scoring.py` in this directory
is a thin adapter that adds the project root to sys.path and re-exports the
functions the server needs, so there is a single source of truth for scoring.

---

## Troubleshooting

**"Module not found: scorer" or similar import error**

Make sure you are running the server from within the project or have installed
the package with `uv pip install -e mcp-server/`. The scoring adapter uses
`Path(__file__).parent.parent` to locate `agents/scorer.py` — this requires
the directory structure to be intact.

**"No schools found" in search results**

Only schools with JSON files in `data/schools/` are searched. Use
`get_research_queue_stats` to see how many schools are pending research.

**Scores all show as n/a**

School profiles with all `year_verified: null` fields will compute low or zero
tech scores. This is correct — unverified courses don't count. The school needs
to be researched and verified before meaningful scores appear.

**Server crashes on startup**

Check that `mcp>=1.0.0` is installed in the Python environment the server uses.
Run `pip show mcp` to confirm.
