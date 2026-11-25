"""Wireshark-style capture of my 10 newest activities: TryHackMe progress and Codeforces solves.

Usage: python3 make_capture.py <cache_dir> <out_dir>
"""
import json
import sys
from datetime import datetime, timezone
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
        if low.startswith(("tryhackme:", "thm:")):
            info = first.split(":", 1)[1].strip()
            info = info.removeprefix(ME + ",").strip()  # "DAGMON, level 3" -> "level 3"
            rows.append((t, ME, "tryhackme", "PROGRESS", "#f7768e", info[:44]))
        elif low.startswith("codeforces:"):
            continue  # already shown as solved problems
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
# Repeated TryHackMe syncs with the same stats aren't progress: keep the first
rows.sort(key=lambda r: r[0])
deduped, last_thm = [], None
for r in rows:
    if r[2] == "tryhackme":
        if r[5] == last_thm:
            continue
        last_thm = r[5]
    deduped.append(r)
rows = deduped

# The 10 newest packets of TryHackMe progress and Codeforces solves, newest first
# (GitHub pushes are left out: the projects above already show that work)
rows = [r for r in rows if r[2] == "tryhackme"]
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
