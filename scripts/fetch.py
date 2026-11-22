"""Fetch everything the profile needs into .cache/ (Codeforces + GitHub public APIs).

Each source is fetched independently; if one fails, its old cache (if any) is kept and the
build carries on, so a flaky API never breaks the profile.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

GH_USER = "DAGMON-Z"
CF_HANDLE = "DAGMON"
CACHE = Path(sys.argv[1] if len(sys.argv) > 1 else ".cache")
CACHE.mkdir(exist_ok=True)
TOKEN = os.environ.get("GITHUB_TOKEN")


def get(url, gh=False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-builder"})
    if gh:
        req.add_header("Accept", "application/vnd.github+json")
        if TOKEN:
            req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def save(name, fn):
    try:
        data = fn()
        (CACHE / name).write_text(json.dumps(data), encoding="utf-8")
        return data
    except Exception as e:  # keep the previous cache, report, continue
        print(f"warn: {name}: {e}", file=sys.stderr)
        return None


def cf(method):
    d = get(f"https://codeforces.com/api/{method}")
    if d.get("status") != "OK":
        raise RuntimeError(d.get("comment"))
    time.sleep(2.1)  # Codeforces allows 1 call / 2 s
    return d


save("info.json", lambda: cf(f"user.info?handles={CF_HANDLE}"))
save("rating.json", lambda: cf(f"user.rating?handle={CF_HANDLE}"))
save("status.json", lambda: cf(f"user.status?handle={CF_HANDLE}&from=1&count=1000"))
save("contests.json", lambda: cf("contest.list?gym=false"))

repos = save("repos.json", lambda: get(f"https://api.github.com/users/{GH_USER}/repos?per_page=100&sort=pushed", gh=True))
for r in repos or []:
    save(f"lang-{r['name']}.json", lambda r=r: get(r["languages_url"], gh=True))

events = save("events.json", lambda: get(f"https://api.github.com/users/{GH_USER}/events/public?per_page=30", gh=True))
# Push events no longer carry commit messages: look up the head commit of the latest few pushes.
msgs = {}
pushes = sorted((e for e in (events or []) if e["type"] == "PushEvent"), key=lambda e: e["created_at"], reverse=True)
for e in pushes[:8]:
    head = e["payload"].get("head")
    try:
        msgs[head] = get(f"https://api.github.com/repos/{e['repo']['name']}/commits/{head}", gh=True)["commit"]["message"]
    except Exception as ex:
        print(f"warn: commit {head}: {ex}", file=sys.stderr)
(CACHE / "commit-msgs.json").write_text(json.dumps(msgs), encoding="utf-8")
print("fetch done")

# ---- Hack The Box public profile (server-rendered page; no login needed once the profile is public).
# Fetched at most about once an hour (HTB sits behind Cloudflare rate limits). The parsed result is
# committed to data/htb-public.json so it survives between runs; on any failure the old file is kept.
HTB_PROFILE = "https://profile.hackthebox.com/profile/01a0c9bc-3ab8-704c-beee-1661b37d6295"
if time.gmtime().tm_min < 5 or os.environ.get("FORCE_HTB") or os.environ.get("GITHUB_EVENT_NAME") in ("workflow_dispatch", "push"):
    try:
        import re as _re
        req = urllib.request.Request(HTB_PROFILE, headers={"User-Agent": "Mozilla/5.0 (profile-readme-builder)"})
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
        raw = json.loads(_re.search(r'id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, _re.S).group(1))

        def val(i):
            return raw[i] if isinstance(i, int) and 0 <= i < len(raw) else i

        badges = []
        for x in raw:
            if isinstance(x, dict) and {"platform", "name", "awarded_at"} <= x.keys():
                badges.append({k: val(x[k]) for k in ("platform", "name", "description", "awarded_at")})
        if not badges and "@" not in html:
            raise RuntimeError("unexpected page")
        badges.sort(key=lambda b: str(b["awarded_at"]), reverse=True)
        Path("data/htb-public.json").write_text(json.dumps({"badges": badges, "fetched": int(time.time())}, indent=2), encoding="utf-8")
        print(f"htb: {len(badges)} badges")
    except Exception as e:
        print(f"warn: htb profile: {e}", file=sys.stderr)
