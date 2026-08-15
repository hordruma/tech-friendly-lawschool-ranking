# Tech-Forward Law School Index

A ranking of global law schools based on a mixture of metrics, with a focus on practical
preparation and tech+AI skill development.

**50 schools · 17 countries · August 2026 edition.** Indicator-based and fully open:
every school entry ships with its evidence, pillar scores, and source URLs, so you can
audit or disagree with any placement.

📊 **View the ranking:** open `index.html` (or serve the repo with GitHub Pages).

## How it works

Schools are scored 0–5 per pillar against publicly documented evidence, combined as a
weighted sum rescaled to 0–100:

| Pillar | Weight |
|---|---|
| Tech & AI Curriculum | 25% |
| Hands-On Legal Tech (build clinics, hackathons) | 25% |
| Practical Preparation (experiential program) | 20% |
| Research & Leadership (centers, scholarship) | 20% |
| Industry Ecosystem (partnerships, incubators) | 10% |

Full details and limitations: [METHODOLOGY.md](METHODOLOGY.md).

## Repo layout

```
data/regions/*.json   # school entries: evidence, pillar scores, sources
data/rankings.json    # generated: composite scores + ranks
scripts/score.py      # data/regions/*.json -> data/rankings.json
scripts/build_site.py # data/rankings.json + site/template.html -> index.html
site/template.html    # page template
index.html            # generated ranking page
```

Rebuild everything:

```
python3 scripts/score.py && python3 scripts/build_site.py
```

## Contributing / corrections

Schools change fast — programs launch and labs close. If an entry is out of date or a
school with documented legal-tech activity is missing, open an issue or PR with source
URLs. Coverage is curated, not exhaustive; absence is not a judgment.

## License

MIT. Not affiliated with any listed institution.
