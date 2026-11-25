"""Fetch everything the profile needs into .cache/ (Codeforces + GitHub public APIs).

Each source is fetched independently; if one fails, its old cache (if any) is kept and the
build carries on, so a flaky API never breaks the profile.
"""
import json
import re
import base64
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
save("status.json", lambda: cf(f"user.status?handle={CF_HANDLE}"))  # all submissions, for the all-time solved count

repos = save("repos.json", lambda: get(f"https://api.github.com/users/{GH_USER}/repos?per_page=100&sort=pushed", gh=True))
for r in repos or []:
    save(f"lang-{r['name']}.json", lambda r=r: get(r["languages_url"], gh=True))

events = save("events.json", lambda: get(f"https://api.github.com/users/{GH_USER}/events/public?per_page=30", gh=True))
# Push events no longer carry commit messages: look up the head commit of the latest 15 pushes (enough for the 10 shown).
msgs = {}
pushes = sorted((e for e in (events or []) if e["type"] == "PushEvent"), key=lambda e: e["created_at"], reverse=True)
for e in pushes[:15]:
    head = e["payload"].get("head")
    try:
        msgs[head] = get(f"https://api.github.com/repos/{e['repo']['name']}/commits/{head}", gh=True)["commit"]["message"]
    except Exception as ex:
        print(f"warn: commit {head}: {ex}", file=sys.stderr)
(CACHE / "commit-msgs.json").write_text(json.dumps(msgs), encoding="utf-8")

# TryHackMe progress, from the history of the stats files in this repo (exact
# and up to the minute, unlike the activity feed, which lags):
#  - profile-sync/tryhackme-dagmon.json: written by the Profile Sync extension;
#    each version's stats are read from the file itself
#  - data/thm.json (older): written by the old thm-sync helper, "thm: ..." messages
def thm_history():
    out = []
    api = f"https://api.github.com/repos/{GH_USER}/{GH_USER}"
    path = "profile-sync/tryhackme-dagmon.json"
    for c in get(f"{api}/commits?path={path}&per_page=12", gh=True):
        try:
            f = get(f"{api}/contents/{path}?ref={c['sha']}", gh=True)
            st = json.loads(base64.b64decode(f["content"])).get("stats", {})
        except Exception as ex:
            print(f"warn: thm history {c['sha'][:7]}: {ex}", file=sys.stderr)
            continue
        out.append({"time": c["commit"]["author"]["date"], "level": st.get("level"),
                    "rooms": st.get("rooms"), "rank": st.get("rank")})
    for c in get(f"{api}/commits?path=data/thm.json&per_page=20", gh=True):
        m = re.match(r"thm: (\d+) rooms, rank (.+)", c["commit"]["message"].splitlines()[0])
        if m:
            out.append({"time": c["commit"]["author"]["date"], "level": None,
                        "rooms": int(m.group(1)), "rank": m.group(2)})
    return out


save("thm-history.json", thm_history)
print("fetch done")

# ---- TryHackMe: the official public badge image (tryhackme.com/p/DAGMON). Its JSON API sits behind a
# bot checkpoint, but THM publishes this PNG for embedding: rank, level, badges, rooms, streak.
# Stored in .cache; make_live.py embeds it in the card. On failure the committed copy in assets/ is used.
try:
    req = urllib.request.Request("https://tryhackme-badges.s3.amazonaws.com/DAGMON.png",
                                 headers={"User-Agent": "profile-readme-builder"})
    png = urllib.request.urlopen(req, timeout=20).read()
    if not png.startswith(b"\x89PNG"):
        raise RuntimeError("not a png")
    (CACHE / "thm-badge.png").write_bytes(png)
    print(f"thm: badge {len(png)} bytes")
except Exception as e:
    print(f"warn: thm badge: {e}", file=sys.stderr)
