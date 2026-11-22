"""Build project cards + README snippet from the GitHub repos API.

Usage: python3 make_projects.py <gh_json_dir> <out_dir>
  <gh_json_dir>/repos.json      = GET /users/<user>/repos?per_page=100&sort=pushed
  <gh_json_dir>/lang-<repo>.json = GET /repos/<user>/<repo>/languages
Writes <out_dir>/proj-<repo>.svg for each repo and <out_dir>/projects.md (the README block).

Rules: public, not a fork, not archived, not the profile repo itself, and no `hide-from-profile` topic.
Order: most recently pushed first. A new repo shows up on the next run automatically.
"""
import json
import sys
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

src, out = Path(sys.argv[1]), Path(sys.argv[2])
USER = "DAGMON-Z"
FONT = "'JetBrains Mono','Fira Code',ui-monospace,Menlo,Consolas,monospace"
ACCENTS = ["#7aa2f7", "#bb9af7", "#9ece6a", "#7dcfff", "#e0af68", "#f7768e"]

repos = json.loads((src / "repos.json").read_text())
repos = [r for r in repos if not r["fork"] and not r["archived"] and not r.get("private")
         and r["name"].lower() != USER.lower() and "hide-from-profile" not in r.get("topics", [])]
repos.sort(key=lambda r: r["pushed_at"], reverse=True)


def card(r, accent):
    w, h = 420, 230
    name = r["name"]
    langs_path = src / f"lang-{name}.json"
    langs = list(json.loads(langs_path.read_text()).keys())[:3] if langs_path.exists() else []
    tags = langs or ([r["language"]] if r.get("language") else [])
    desc = textwrap.wrap(r.get("description") or "No description yet.", 44)[:3]
    if len(textwrap.wrap(r.get("description") or "", 44)) > 3:
        desc[-1] = desc[-1][:41].rstrip() + "…"
    text = "".join(f'<text x="22" y="{96 + i * 22}" class="t" style="font-size:13px">{escape(s)}</text>'
                   for i, s in enumerate(desc))
    x, pills = 22, ""
    for tg in tags:
        tw = 8 * len(tg) + 16
        pills += (f'<rect x="{x}" y="166" width="{tw}" height="22" rx="11" fill="none" stroke="{accent}" stroke-opacity=".5"/>'
                  f'<text x="{x + tw / 2}" y="181" text-anchor="middle" class="t" style="font-size:12px;fill:{accent}">{escape(tg)}</text>')
        x += tw + 8
    foot = ["→ open repo"]
    if r.get("homepage"):
        foot.append("live demo")
    if r["stargazers_count"]:
        foot.append(f"★ {r['stargazers_count']}")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>.t {{ font:14px {FONT}; fill:#c0caf5; white-space:pre; }}</style>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="#1a1b26" stroke="#292e42"/>
<rect x="0" y="0" width="5" height="{h}" rx="2" fill="{accent}"/>
<text x="22" y="34" class="t" style="font-size:12px;fill:#565f89">❯ cat ~/projects/{escape(name)}/README.md</text>
<text x="22" y="66" class="t" style="font-size:20px;font-weight:bold;fill:{accent}">{escape(name)}</text>
{text}{pills}
<text x="22" y="214" class="t" style="font-size:12px;fill:#565f89">{escape("  ·  ".join(foot))}</text>
</svg>'''
    (out / f"proj-{name}.svg").write_text(svg, encoding="utf-8")


md = []
for i, r in enumerate(repos):
    card(r, ACCENTS[i % len(ACCENTS)])
    md.append(f'<a href="{r["html_url"]}"><img src="assets/proj-{r["name"]}.svg" width="49%" alt="{escape(r["name"])}"></a>')
(out / "projects.md").write_text("<p align=\"center\">\n" + "\n".join(md) + "\n</p>\n", encoding="utf-8")
print("projects:", [r["name"] for r in repos])
