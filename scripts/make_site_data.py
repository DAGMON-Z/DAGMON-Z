"""Write data/site.json: live data for the web terminal at https://dagmon-z.github.io

Usage: python3 make_site_data.py <cache_dir>
The site (separate repo DAGMON-Z/DAGMON-Z.github.io) fetches this file from raw.githubusercontent.com
on every visit, so it is always as fresh as the profile itself.
"""
import json
import sys
import time
from pathlib import Path
import thm_stats

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
def all_time_solved():
    """All-time solved from the Profile Sync extension's file (the Codeforces
    profile page's own count), or the accepted problems the API lists."""
    n = len({(s["problem"].get("contestId"), s["problem"]["index"]) for s in subs if s.get("verdict") == "OK"})
    try:
        cfj = json.loads(Path(f"profile-sync/codeforces-{info.get('handle', '').lower()}.json").read_text())
        v = cfj.get("stats", {}).get("solved")
        return max(n, v) if isinstance(v, int) else n
    except (OSError, ValueError):
        return n


cf = {
    "handle": info.get("handle", "DAGMON"), "rating": info.get("rating"), "rank": info.get("rank"),
    "max": info.get("maxRating"), "contests": len(rating),
    "history": [r["newRating"] for r in rating],
    "solved": all_time_solved(),
}

thm = json.loads(Path("data/thm.json").read_text())
data = {"generated": int(time.time()), "projects": projects, "cf": cf,
        "thm": {"user": thm.get("user"), "path": thm.get("path"), "privilege": thm.get("privilege"), "stats": thm_stats.load(thm.get("user", "DAGMON")) or None,
                "url": "https://tryhackme.com/p/" + thm.get("user", "DAGMON"),
                "badge": "https://raw.githubusercontent.com/DAGMON-Z/DAGMON-Z/main/assets/thm-badge.png"}}
Path("data/site.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("site data:", len(projects), "projects")
