"""Wireshark-style capture of my 10 newest activities: progress on every site the extension tracks, and Codeforces solves.

Usage: python3 make_capture.py <cache_dir> <out_dir>
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

src, out = Path(sys.argv[1]), Path(sys.argv[2])
FONT = "'JetBrains Mono','Fira Code',ui-monospace,Menlo,Consolas,monospace"


def load(name, default):
    p = src / name
    return json.loads(p.read_text()) if p.exists() else default


events = load("events.json", [])
msgs = load("commit-msgs.json", {})
subs = load("status.json", {}).get("result", [])


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


ME = "DAGMON"  # one name for every packet, whatever the platform
rows = []  # (time, source, destination, proto, color, info)
for e in events:
    repo = e["repo"]["name"].split("/")[-1]
    t, p = ts(e["created_at"]), e["payload"]
    if e["type"] == "PushEvent":
        m = msgs.get(p.get("head"), "")
        first = m.splitlines()[0] if m else ""
        low = first.lower()
        # Stats commits (Profile Sync extension, or the old thm-sync helper) are
        # really TryHackMe / Codeforces activity, not work on the repo
        if low.startswith(("tryhackme:", "thm:", "codeforces:")):
            continue  # stats commits: shown from their own sources below
        else:
            rows.append((t, ME, repo, "PUSH", "#9ece6a", f'"{first[:38]}"' if first else "new commits"))
    elif e["type"] == "CreateEvent" and p.get("ref_type") == "repository":
        rows.append((t, ME, repo, "CREATE", "#7dcfff", "new repository"))
    elif e["type"] == "WatchEvent":
        rows.append((t, ME, repo, "STAR", "#e0af68", "★ starred"))
    elif e["type"] == "PullRequestEvent":
        rows.append((t, ME, repo, "PR", "#7dcfff", f'#{p.get("number")} {p.get("action")}'))
    elif e["type"] == "ReleaseEvent":
        rows.append((t, ME, repo, "RELEASE", "#bb9af7", p.get("release", {}).get("tag_name", "")))

# Codeforces: every problem solved (contest or practice), once, at its first
# accepted submission. Newest first; the 8 newest are shown, plus a count.
solved = {}
for s in subs:
    if s.get("verdict") != "OK":
        continue
    pr = s["problem"]
    key = (pr.get("contestId"), pr["index"])
    t = datetime.fromtimestamp(s["creationTimeSeconds"], timezone.utc)
    if key not in solved or t < solved[key][0]:
        kind = "contest" if s["author"].get("participantType") == "CONTESTANT" else "practice"
        solved[key] = (t, f'{pr.get("contestId", "")}{pr["index"]} {pr.get("name", "")}'[:30] + f" · {kind}")
cf_rows = sorted(((t, ME, "codeforces", "SOLVED", "#9ece6a", info) for t, info in solved.values()),
                 key=lambda r: r[0], reverse=True)
# Progress on every site the Profile Sync extension tracks, read from the git
# history of its files (profile-sync/<site>-<user>.json): each saved version is
# compared with the one before, and what changed becomes a packet. Instant, and
# no API calls. Older TryHackMe history (data/thm.json, "thm: ..." commits from
# the old helper) is read the same way.
import re
import subprocess

HIDE = {"level"}                       # never shown
HIDE_PER_SITE = {"codeforces": {"solved", "contribution"}}  # solved problems already appear by name


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def label_of(key, fields):
    for f in fields or []:
        if f.get("key") == key:
            return f.get("label") or key
    return re.sub(r"(?<!^)(?=[A-Z])", " ", key).lower()  # maxRating -> max rating


# Most telling numbers first (used when a file doesn't list its own order)
PRIORITY = ["rank", "rating", "rooms", "solved", "points", "streak", "badges", "league",
            "ranking", "contestRating", "honor", "position", "completed", "stars"]
WIDTH = 46  # characters that fit in the Info column


def ordered(stats, fields):
    if fields:
        return [f["key"] for f in fields]
    return sorted(stats, key=lambda k: PRIORITY.index(k) if k in PRIORITY else len(PRIORITY))


def fit(parts):
    out = ""
    for p in parts:
        nxt = f"{out}, {p}" if out else p
        if len(nxt) > WIDTH:
            break
        out = nxt
    return out or parts[0][:WIDTH]


def show(v):
    return f"{v:,}" if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)


progress = []
for path in sorted(Path("profile-sync").glob("*.json")):
    if path.name == "all.json":
        continue
    versions = []  # oldest first
    for line in reversed(git("log", "--format=%H %cI", "--", str(path)).split("\n")):
        if not line.strip():
            continue
        sha, when = line.split()
        try:
            versions.append((datetime.fromisoformat(when), json.loads(git("show", f"{sha}:{path}"))))
        except ValueError:
            continue
    prev = {}
    for i, (when, doc) in enumerate(versions):
        when += timedelta(microseconds=i)  # same-second saves keep their order
        stats, fields = doc.get("stats") or {}, doc.get("fields")
        site = str(doc.get("site", path.stem.split("-")[0]))
        hide = HIDE | HIDE_PER_SITE.get(site.lower(), set())
        order = ordered(stats, fields)
        changed = [k for k in order if k in stats and k not in hide and stats[k] != prev.get(k)]
        if prev and changed:
            info = fit([f"{label_of(k, fields)} {show(stats[k])}" for k in changed])  # new values only
        elif not prev:
            shown = [k for k in order if k in stats and k not in hide]
            info = fit([f"{label_of(k, fields)} {show(stats[k])}" for k in shown]) if shown else ""
        else:
            info = ""
        if info:
            dest = re.sub(r"[^a-z0-9.-]", "", site.lower()) or path.stem
            dest = re.sub(r"\.[a-z]{2,}$", "", dest)[:14]  # ctf-league.example -> ctf-league
            progress.append((when, ME, dest, "PROGRESS", "#f7768e", info))
        prev = stats

# Old TryHackMe helper: "thm: 8 rooms, rank Top 50%" commits on data/thm.json
for line in git("log", "--format=%cI %s", "--", "data/thm.json").split("\n"):
    m = re.match(r"(\S+) thm: (\d+) rooms, rank (.+)", line)
    if m:
        progress.append((datetime.fromisoformat(m.group(1)), ME, "tryhackme", "PROGRESS", "#f7768e",
                         f"rank {m.group(3)}, rooms {m.group(2)}"))
rows += progress

# Repeated syncs with the same stats aren't progress: keep the first
rows.sort(key=lambda r: r[0])
deduped, last = [], {}
for r in rows:
    if r[3] == "PROGRESS":
        if last.get(r[2]) == r[5]:
            continue
        last[r[2]] = r[5]
    deduped.append(r)
rows = deduped

# The 10 newest packets: progress on any tracked site, and Codeforces solves, newest first
# (GitHub pushes are left out: the projects above already show that work)
rows = [r for r in rows if r[3] in ("PROGRESS", "SOLVED")]
rows = sorted(cf_rows + rows, key=lambda r: r[0], reverse=True)[:10]


def ago(t):
    s = max(0, (datetime.now(timezone.utc) - t).total_seconds())
    for unit, n in (("d", 86400), ("h", 3600), ("m", 60)):
        if s >= n:
            return f"{int(s // n)}{unit} ago"
    return "just now"


lines = ['<tspan fill="#7aa2f7">No.  Age         Source    Destination    Proto    Info</tspan>',
         '<tspan fill="#565f89">' + "─" * 82 + "</tspan>"]
for i, (t, s_, d, proto, col, info) in enumerate(rows, 1):
    lines.append(f'{i:<4} {ago(t):<11} {escape(s_[:9]):<9} {escape(d[:14]):<14} '
                 f'<tspan fill="{col}">{proto:<8}</tspan> {escape(info)}')

h = 80 + 24 * len(lines)
body = "".join(f'<text x="24" y="{62 + i * 24}" class="t l" style="animation-delay:{0.3 + i * 0.3:.1f}s">{ln}</text>'
               for i, ln in enumerate(lines))
(out / "capture.svg").write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{h}" viewBox="0 0 860 {h}">
<style>.t {{ font:13.5px {FONT}; fill:#c0caf5; white-space:pre; }} .l {{ opacity:0; animation:show .01s forwards; }} @keyframes show {{ to {{ opacity:1; }} }}</style>
<rect width="860" height="{h}" rx="12" fill="#1a1b26"/>
<rect width="860" height="34" rx="12" fill="#16161e"/><rect y="22" width="860" height="12" fill="#16161e"/>
<circle cx="22" cy="17" r="6" fill="#f7768e"/><circle cx="42" cy="17" r="6" fill="#e0af68"/><circle cx="62" cy="17" r="6" fill="#9ece6a"/>
<text x="430" y="22" text-anchor="middle" class="t" style="font-size:13px;fill:#565f89">wireshark · capturing on github0</text>
{body}</svg>''', encoding="utf-8")
print("capture:", len(rows), "packets")
