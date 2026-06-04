# Contributing to Tech-Friendly Law School Ranking

Thank you for wanting to improve the project. This guide covers the three most
common contribution types.

---

## How to add a new scoring dimension

Scoring dimensions are functions in `src/lawschool/scoring/`.  Pick the right
file for the domain or create a new one.

### Step-by-step

1. **Write the scorer function** in the appropriate module
   (`tech.py`, `practical.py`, or a new file):

   ```python
   def score_my_dimension(school: dict) -> tuple[float, list[str]]:
       """Short description (0–N points). Document the scale."""
       notes: list[str] = []
       # ... logic ...
       return score, notes
   ```

   Follow the existing pattern:
   - Return `(float, list[str])` — the score and human-readable notes.
   - Use `school.get("field") or []` / `or {}` for safe access.
   - Cap scores explicitly: `min(total, MAX)`.

2. **Register the function** in `compute_tech_score()` (in `tech.py`) or
   `compute_practical_score()` (in `practical.py`) by adding it to the
   `funcs` list with a key name:

   ```python
   ("my_dimension_key", score_my_dimension),
   ```

3. **Add the key to the schema** — update `data/schema/school.schema.json` if
   the new sub-score needs to be stored, and add the corresponding field to
   `TechScores` or `PracticalSkillsBreakdown` in `src/lawschool/schema.py`.

4. **Update the CLI display** in `agents/scorer.py`:
   add a row to the `criteria` or `ps_criteria` list.

5. **Update the MCP profile view** in `mcp-server/tools/profile.py`:
   add a line in the "Tech Score Breakdown" or "Practical Skills Breakdown"
   section.

6. **Update `CRITERIA.md`** to document the new dimension publicly.

7. **Re-score all schools** after the change:
   ```bash
   for f in data/schools/*.json; do
     python agents/scorer.py "$f" --write-scores --output "$f"
   done
   ```

---

## How to add a new MCP tool

MCP tools live in `mcp-server/tools/`.  Each tool is a self-contained module.

### Step-by-step

1. **Create a new file** in `mcp-server/tools/`, e.g. `tools/compare_regions.py`.

2. **Define `TOOL_DEFINITION`** — a `mcp.types.Tool` instance:

   ```python
   from mcp.types import TextContent, Tool

   TOOL_DEFINITION = Tool(
       name="compare_regions",          # must be unique, snake_case
       description="...",
       inputSchema={
           "type": "object",
           "properties": {
               "region_a": {"type": "string", "description": "..."},
               "region_b": {"type": "string", "description": "..."},
           },
           "required": ["region_a", "region_b"],
       },
   )
   ```

3. **Define `async def handle(args: dict) -> list[TextContent]`**:

   ```python
   async def handle(args: dict) -> list[TextContent]:
       region_a = args.get("region_a", "")
       # ... logic using lawschool.data and lawschool.scoring ...
       return [TextContent(type="text", text="\n".join(lines))]
   ```

4. **Register the module** in `mcp-server/tools/__init__.py`:
   add it to `ALL_TOOLS` and the imports.

5. **Register in `server.py`**: import the module and add it to
   `_SIMPLE_TOOL_MODULES` (or the admin dispatch dict if it doesn't follow
   the simple one-tool-per-module pattern).

6. **Test the tool** by running the MCP server and calling the tool via an
   MCP client, or write a short async test script.

7. **Document the tool** in the `## Tools` table in `mcp-server/README.md`.

### Naming conventions

- Tool names: `snake_case`, verb-first where possible (`search_`, `get_`,
  `compare_`, `find_`, `explain_`, `flag_`).
- File names: match the tool name without the verb prefix where appropriate
  (`search.py`, `profile.py`, `compare.py`, `career.py`, `admin.py`).
- Argument names: `snake_case`, consistent with existing tools.

---

## How to add schools to the research queue

The research queue lives in `data/research-list/top-500.json`.

### Quickest route: open a GitHub issue

Use the **School Submission** issue template. A maintainer will review and
merge the addition.

### Editing the queue directly

Add an entry to `data/research-list/top-500.json`:

```json
{
    "id": "my-law-school",
    "name": "My Law School",
    "country": "GB",
    "city": "London",
    "region": "UK & Ireland",
    "url": "https://www.mylaw.ac.uk",
    "research_status": "pending",
    "known_rankings": {
        "qs_law": null,
        "the_law": null
    }
}
```

Field requirements:
- `id`: URL-safe slug (`lowercase-hyphenated`, matching the future JSON filename).
- `country`: ISO 3166-1 alpha-2 code.
- `region`: one of `North America`, `UK & Ireland`, `Europe`, `Asia-Pacific`,
  `Latin America`, `Middle East & Africa`.
- `research_status`: always `"pending"` for new additions.

### Running the research agent

Once the school is in the queue, run the research agent:

```bash
python agents/researcher.py \
    --school "My Law School" \
    --url https://www.mylaw.ac.uk \
    --output data/schools/my-law-school.json
```

Then score:

```bash
python agents/scorer.py data/schools/my-law-school.json --write-scores --output data/schools/my-law-school.json
```

Human verification is required before a school's data is considered final
(`last_verified` must be set by a reviewer).

---

## Project structure quick reference

```
src/lawschool/           Shared library (install with: pip install -e ".[mcp,agents]")
  schema.py              Pydantic v2 models
  data.py                load_school(), load_all_schools(), etc.
  scoring/               All scoring logic — edit here, nowhere else
  research/agent.py      Research agent — edit here, nowhere else

agents/
  scorer.py              Thin CLI — imports from lawschool.scoring
  researcher.py          Thin CLI — imports from lawschool.research.agent

mcp-server/
  server.py              ~50-line entry point
  tools/                 One file per tool
  resources.py           All three MCP resources
  _helpers.py            Shared filter/sort/render helpers

typedb/ingest.py         Imports from lawschool.schema + lawschool.data

data/schools/            JSON source-of-truth for all schools
data/schema/             JSON Schema (school.schema.json)
CRITERIA.md              Public methodology document
```
