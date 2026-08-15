#!/usr/bin/env python3
"""Generate index.html from data/rankings.json."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "rankings.json").read_text())

PILLARS = ["curriculum", "hands_on", "practical", "research", "ecosystem"]
LABELS = DATA["pillar_labels"]
WEIGHTS = DATA["weights"]

e = html.escape


def school_row(s: dict) -> str:
    segs = []
    for p in PILLARS:
        contrib = s["scores"][p] / 5 * WEIGHTS[p] * 100
        if contrib > 0:
            segs.append(
                f'<span class="seg seg-{p}" style="width:{contrib:.1f}%" '
                f'title="{e(LABELS[p])}: {s["scores"][p]}/5"></span>'
            )
    bar = "".join(segs)
    pillar_rows = "".join(
        f'<tr><td><span class="dot seg-{p}"></span>{e(LABELS[p])}'
        f'<span class="wt">{int(WEIGHTS[p]*100)}%</span></td>'
        f'<td class="num">{s["scores"][p]}<span class="of5">/5</span></td></tr>'
        for p in PILLARS
    )
    hl = "".join(f"<li>{e(h)}</li>" for h in s.get("highlights", []))
    caveat = (
        f'<p class="caveat"><strong>Caveat:</strong> {e(s["caveats"])}</p>'
        if s.get("caveats") else ""
    )
    srcs = "".join(
        f'<li><a href="{e(u)}" rel="noopener">{e(u.split("//", 1)[-1].rstrip("/"))}</a></li>'
        for u in s.get("sources", [])
    )
    center = f'<p class="center-line">{e(s["tech_center"])}</p>' if s.get("tech_center") else ""
    return f'''<details class="row" data-region="{e(s["region"])}">
<summary>
  <span class="rank">{s["rank"]}</span>
  <span class="who"><span class="school">{e(s["name"])}</span>
  <span class="where">{e(s["city"])} · {e(s["country"])}</span></span>
  <span class="bar" role="img" aria-label="Composite score {s["composite"]} of 100">{bar}</span>
  <span class="score">{s["composite"]}</span>
</summary>
<div class="detail">
  {center}
  <div class="detail-cols">
    <div>
      <h3>Why it ranks here</h3>
      <ul class="evidence">{hl}</ul>
      {caveat}
    </div>
    <div>
      <h3>Pillar scores</h3>
      <table class="pillars">{pillar_rows}</table>
      <h3>Sources</h3>
      <ul class="sources">{srcs}</ul>
    </div>
  </div>
</div>
</details>'''


def main() -> None:
    schools = DATA["schools"]
    regions = sorted({s["region"] for s in schools})
    chips = '<button class="chip active" data-filter="all">All regions</button>' + "".join(
        f'<button class="chip" data-filter="{e(r)}">{e(r)}</button>' for r in regions
    )
    legend = "".join(
        f'<span class="lg"><span class="dot seg-{p}"></span>{e(LABELS[p])} '
        f'<span class="wt">{int(WEIGHTS[p]*100)}%</span></span>'
        for p in PILLARS
    )
    rows = "\n".join(school_row(s) for s in schools)
    n = len(schools)
    countries = len({s["country"] for s in schools})

    tpl = (ROOT / "site" / "template.html").read_text()
    page = (
        tpl.replace("{{ROWS}}", rows)
        .replace("{{CHIPS}}", chips)
        .replace("{{LEGEND}}", legend)
        .replace("{{N}}", str(n))
        .replace("{{COUNTRIES}}", str(countries))
    )
    (ROOT / "site" / "artifact.html").write_text(page)
    # For the standalone repo page, split so markup lands in <body>.
    style_end = page.index("</style>") + len("</style>")
    head_part, body_part = page[:style_end], page[style_end:]
    full = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        + head_part
        + "\n</head>\n<body>"
        + body_part
        + "\n</body>\n</html>\n"
    )
    (ROOT / "index.html").write_text(full)
    print(f"Wrote index.html + site/artifact.html ({n} schools, {countries} countries)")


if __name__ == "__main__":
    main()
