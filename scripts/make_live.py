"""One card with everything: full Codeforces panel (top) + TryHackMe session (bottom).

Usage: python3 make_live.py <cache_dir> <out_dir>
Reads the Codeforces API cache, the official TryHackMe badge PNG (refreshed every run)
and data/thm.json ("privilege": guest | user | www-data | admin | root).
"""
import base64
import json
import sys
import time
from pathlib import Path
from xml.sax.saxutils import escape
import thm_stats

src, out = Path(sys.argv[1]), Path(sys.argv[2])
info = json.loads((src / "info.json").read_text())["result"][0]
rating = json.loads((src / "rating.json").read_text())["result"]
subs = json.loads((src / "status.json").read_text())["result"]

FONT = "'JetBrains Mono','Fira Code',ui-monospace,Menlo,Consolas,monospace"
W = 860

# ======================= Codeforces (top, y 0..200) =======================
RANK_COLOR = {"newbie": "#a9b1d6", "pupil": "#9ece6a", "specialist": "#03a89e", "expert": "#7aa2f7",
              "candidate master": "#bb9af7", "master": "#ff9e64", "international master": "#ff9e64"}
rank = info.get("rank", "unrated")
rc = RANK_COLOR.get(rank, "#f7768e")
cur, mx = info.get("rating", 0), info.get("maxRating", 0)
solved = len({(s["problem"].get("contestId"), s["problem"]["index"]) for s in subs if s.get("verdict") == "OK"})
gain = (rating[-1]["newRating"] - rating[0]["newRating"]) if len(rating) > 1 else 0

pts = [r["newRating"] for r in rating] or [0]
lo, hi = min(pts), max(pts)
span = max(hi - lo, 1)
x0, x1, y0, y1 = 470, 830, 160, 50
coords = [(x0 + (x1 - x0) * (i / max(len(pts) - 1, 1)), y0 - (y0 - y1) * ((p - lo) / span)) for i, p in enumerate(pts)]
poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in coords)
dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="{rc}"/>' for x, y in coords)
labels = "".join(f'<text x="{x:.0f}" y="{y - 12:.0f}" text-anchor="middle" class="t" style="font-size:11px;fill:#565f89">{p}</text>'
                 for (x, y), p in zip(coords, pts))

top = f'''<text x="24" y="36" class="t h">🏁 CODEFORCES · {escape(info["handle"])}</text>
<text x="24" y="96" class="t" style="font-size:34px;font-weight:bold;fill:{rc}">{cur}</text>
<text x="112" y="96" class="t" style="font-size:16px;fill:{rc}">{escape(rank.title())}</text>
<text x="24" y="136" class="t" style="fill:#9ece6a">↗ +{gain} in {len(rating)} contests</text>
<text x="24" y="170" class="t">max {mx} · {solved} solved · C++23</text>
<line x1="440" y1="24" x2="440" y2="176" stroke="#292e42"/>
<line x1="{x0}" y1="{y0 + 14}" x2="{x1}" y2="{y0 + 14}" stroke="#292e42"/>
<polyline class="line" fill="none" stroke="#7aa2f7" stroke-width="2.5" points="{poly}"/>{dots}{labels}
<text x="{x1}" y="{y0 + 32}" text-anchor="end" class="t" style="font-size:11px;fill:#565f89">rating history</text>'''

# ======================= TryHackMe (bottom) =======================
cfg = json.loads(Path("data/thm.json").read_text())
user = cfg.get("user", "DAGMON")
# Fresh badge from this run if the download worked, otherwise the last good copy in assets/.
fresh = src / "thm-badge.png"
if fresh.exists():
    (out / "thm-badge.png").write_bytes(fresh.read_bytes())
badge = out / "thm-badge.png"
b64 = base64.b64encode(badge.read_bytes()).decode() if badge.exists() else ""
LADDER = ["guest", "user", "www-data", "admin", "root"]
priv = cfg.get("privilege", "guest")
P = '<tspan fill="#f7768e">msf6</tspan> &gt; '

ladder = ""
for step in LADDER:
    col = "#9ece6a" if LADDER.index(step) < LADDER.index(priv) else ("#e0af68" if step == priv else "#565f89")
    ladder += f'<tspan fill="{col}">{"root (Red Teamer)" if step == "root" else step}</tspan>'
    if step != "root":
        ladder += '<tspan fill="#565f89"> ─▶ </tspan>'

TOP_H = 204                 # height of the Codeforces block
BW, BH = 374, 87            # badge drawn at 1.5x (249x58 source)
BY = TOP_H + 52
# Stats from the Profile Sync extension (profile-sync/tryhackme-<user>.json),
# drawn here, so they're always current. Without them, the badge PNG is shown.
stats = thm_stats.load(user)


def num(v):
    return f"{v:,}" if isinstance(v, (int, float)) and not isinstance(v, bool) else "?"


def badge_card():
    lvl = stats.get("level")
    cx, cy = 24 + 42, BY + BH // 2
    # rank is a number (#98,321), or text like "Top 90%" for newer accounts
    rank, top = stats.get("rank"), stats.get("topPercentage")
    if isinstance(rank, str):
        rank_txt, top = escape(rank.lower()), ""
    else:
        rank_txt = f"#{num(rank)}"
        top = f" · top {top}%" if isinstance(top, (int, float)) else ""
    league = stats.get("leagueTier")
    league = f' <tspan fill="#565f89">· {escape(str(league).lower())} league</tspan>' if league else ""
    streak = stats.get("streak")
    streak = f"   🔥 {num(streak)}" if isinstance(streak, (int, float)) else ""
    rows = [
        (14.5, f'<tspan fill="#c0caf5" font-weight="bold">{escape(str(stats.get("username", user)))}</tspan>{league}'),
        (13, f'<tspan fill="#e0af68">🏆 {rank_txt}</tspan><tspan fill="#565f89">{top}</tspan>'),
        (13, f'🚪 {num(stats.get("completedRoomsNumber"))} rooms   🏅 {num(stats.get("badgesNumber"))}{streak}'),
    ]
    g = (f'<rect x="24" y="{BY}" width="{BW}" height="{BH}" rx="10" fill="#16161e" stroke="#9ece6a" stroke-opacity=".45"/>'
         f'<circle cx="{cx}" cy="{cy}" r="29" fill="#1a1b26" stroke="#9ece6a" stroke-width="2"/>'
         f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" class="t" style="font-size:14px;fill:#9ece6a;font-weight:bold">'
         f'{hex(lvl) if isinstance(lvl, int) else "lvl"}</text>')
    g += "".join(f'<text x="118" y="{BY + 26 + i * 23}" class="t" style="font-size:{size}px">{txt}</text>'
                 for i, (size, txt) in enumerate(rows))
    return (f'<a href="https://tryhackme.com/p/{escape(user)}"><g class="l" style="animation-delay:.4s">{g}</g></a>')


synced = time.strftime("%d %b %H:%M UTC", time.gmtime(stats["synced"])) if stats.get("synced") else ""

side = [P + "db_status",
        '<tspan fill="#7aa2f7">[*]</tspan> live from tryhackme.com/p/' + escape(user),
        '<tspan fill="#565f89">    rank · level · badges · rooms</tspan>',
        (f'<tspan fill="#565f89">    synced {synced}, as I solve rooms</tspan>' if stats
         else '<tspan fill="#565f89">    auto-refreshed every 5 minutes</tspan>')]
lines = [P + "sessions -i 1",
         f'<tspan fill="#7aa2f7">[*]</tspan> Target: <tspan fill="#bb9af7">{escape(cfg.get("path", "Red Teamer"))} path</tspan> on TryHackMe   status: <tspan fill="#e0af68">exploiting…</tspan>',
         f'<tspan fill="#7aa2f7">[*]</tspan> Privilege: {ladder}',
         f'<tspan fill="#565f89">    current: </tspan><tspan fill="#e0af68">{escape(priv)}</tspan><tspan fill="#565f89"> · next stop: root</tspan>']

bottom = (f'<line x1="24" y1="{TOP_H}" x2="{W - 24}" y2="{TOP_H}" stroke="#292e42"/>'
          f'<text x="24" y="{TOP_H + 34}" class="t h">🛡️ TRYHACKME · {escape(user)}</text>')
if stats:
    bottom += badge_card()
elif b64:
    bottom += (f'<a href="https://tryhackme.com/p/{escape(user)}"><image class="l" style="animation-delay:.4s" x="24" y="{BY}" '
               f'width="{BW}" height="{BH}" href="data:image/png;base64,{b64}"/></a>')
bottom += "".join(f'<text x="430" y="{BY + 16 + i * 22}" class="t l" style="font-size:13px;animation-delay:{0.6 + i * 0.18:.2f}s">{ln}</text>'
                  for i, ln in enumerate(side))
BASE = BY + BH + 40
bottom += "".join(f'<text x="24" y="{BASE + i * 24}" class="t l" style="font-size:13.5px;animation-delay:{1.4 + i * 0.18:.2f}s">{ln}</text>'
                  for i, ln in enumerate(lines))
H = BASE + 24 * (len(lines) - 1) + 30

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
.t {{ font:14px {FONT}; fill:#c0caf5; white-space:pre; }}
.h {{ font-size:13px; fill:#565f89; letter-spacing:1px; }}
.l {{ opacity:0; animation:show .01s forwards; }} @keyframes show {{ to {{ opacity:1; }} }}
.line {{ stroke-dasharray:800; stroke-dashoffset:800; animation:draw 2s ease-out forwards .3s; }}
@keyframes draw {{ to {{ stroke-dashoffset:0; }} }}
</style>
<rect width="{W}" height="{H}" rx="12" fill="#1a1b26" stroke="#292e42"/>
{top}
{bottom}
</svg>'''
(out / "stats.svg").write_text(svg, encoding="utf-8")
print(f"stats: {cur} {rank}, {solved} solved · thm {'synced stats' if stats else 'badge ok' if b64 else 'missing'}, priv {priv}")
