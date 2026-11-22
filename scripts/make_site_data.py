"""Write data/site.json: live data for the web terminal at https://dagmon-z.github.io

Usage: python3 make_site_data.py <cache_dir>
The site (separate repo DAGMON-Z/DAGMON-Z.github.io) fetches this file from raw.githubusercontent.com
on every visit, so it is always as fresh as the profile itself.
"""
import json
import sys
import time
from pathlib import Path

src = Path(sys.argv[1])


def load(name, default):
    p = src / name
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


USER = "DAGMON-Z"
repos = [r for r in load("repos.json", []) if not r["fork"] and not r["archived"]
         and r["name"].lower() != USER.lower() and "hide-from-profile" not in r.get("topics", [])]
repos.sort(key=lambda r: r["pushed_at"], reverse=True)
projects = []
for r in repos:
    langs = list(load(f"lang-{r['name']}.json", {}).keys())[:3]
    projects.append({"name": r["name"], "desc": r.get("description") or "", "url": r["html_url"],
                     "homepage": r.get("homepage") or "", "stars": r["stargazers_count"], "langs": langs})

info = (load("info.json", {}).get("result") or [{}])[0]
rating = load("rating.json", {}).get("result", [])
subs = load("status.json", {}).get("result", [])
contests = [c for c in load("contests.json", {}).get("result", []) if c.get("phase") == "BEFORE"]
contests.sort(key=lambda c: c["startTimeSeconds"])
cf = {
    "handle": info.get("handle", "DAGMON"), "rating": info.get("rating"), "rank": info.get("rank"),
    "max": info.get("maxRating"), "contests": len(rating),
    "history": [r["newRating"] for r in rating],
    "solved": len({(s["problem"].get("contestId"), s["problem"]["index"]) for s in subs if s.get("verdict") == "OK"}),
    "next": {"name": contests[0]["name"], "start": contests[0]["startTimeSeconds"]} if contests else None,
}

htb_cfg = json.loads(Path("data/htb.json").read_text())
pub = Path("data/htb-public.json")
badges = json.loads(pub.read_text())["badges"] if pub.exists() else []
data = {"generated": int(time.time()), "projects": projects, "cf": cf,
        "htb": {"user": htb_cfg.get("user"), "path": htb_cfg.get("path"), "privilege": htb_cfg.get("privilege"),
                "badges": [{"name": b["name"], "desc": b.get("description") or "", "date": str(b.get("awarded_at", ""))[:10]}
                           for b in badges]}}
Path("data/site.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("site data:", len(projects), "projects,", len(badges), "badges")
