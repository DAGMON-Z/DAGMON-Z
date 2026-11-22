"""Build the stats card (Codeforces + HTB CPTS progress).

Usage: python3 make_live.py <cache_dir> <out_dir> [data/htb.json]
This is the same logic the GitHub Action will run daily.
"""
import json
import sys
import time
from pathlib import Path
from xml.sax.saxutils import escape

src, out = Path(sys.argv[1]), Path(sys.argv[2])
HTB_FILE = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("data/htb.json")
info = json.loads((src / "info.json").read_text())["result"][0]
rating = json.loads((src / "rating.json").read_text())["result"]
subs = json.loads((src / "status.json").read_text())["result"]
contests = json.loads((src / "contests.json").read_text())["result"]

FONT = "'JetBrains Mono','Fira Code',ui-monospace,Menlo,Consolas,monospace"
RANK_COLOR = {"newbie": "#a9b1d6", "pupil": "#9ece6a", "specialist": "#03a89e", "expert": "#7aa2f7",
              "candidate master": "#bb9af7", "master": "#ff9e64", "international master": "#ff9e64"}
rank = info.get("rank", "unrated")
rc = RANK_COLOR.get(rank, "#f7768e")
cur, mx = info.get("rating", 0), info.get("maxRating", 0)
solved = len({(s["problem"].get("contestId"), s["problem"]["index"]) for s in subs if s.get("verdict") == "OK"})
gain = (rating[-1]["newRating"] - rating[0]["newRating"]) if len(rating) > 1 else 0

# ---- rating sparkline
pts = [r["newRating"] for r in rating] or [0]
lo, hi = min(pts), max(pts)
span = max(hi - lo, 1)
n = len(pts)
x0, x1, y0, y1 = 24, 400, 186, 128
coords = [(x0 + (x1 - x0) * (i / max(n - 1, 1)), y0 - (y0 - y1) * ((p - lo) / span)) for i, p in enumerate(pts)]
poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in coords)
dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3.5" fill="{rc}"/>' for x, y in coords)

# ---- HTB Academy CPTS progress (no public API: edit these by hand, e.g. in htb.json)
HTB = json.loads(HTB_FILE.read_text())
_pub = HTB_FILE.parent / "htb-public.json"
BADGES = json.loads(_pub.read_text())["badges"] if _pub.exists() else []
badge_line = (f"🏅 {len(BADGES)} badges · latest: {escape(BADGES[0]['name'])}" if BADGES else "")
now_part = (f' · <tspan style="fill:#e0af68">now:</tspan> {escape(HTB["current"][:24])}' if HTB.get("current") else "")
pct = round(100 * HTB["done"] / HTB["total"])
bar_w = int(300 * HTB["done"] / HTB["total"])

# ---- next contest
_up = sorted((x for x in contests if x["phase"] == "BEFORE"), key=lambda x: x["startTimeSeconds"])
if _up:
    _d = int(_up[0]["startTimeSeconds"] - time.time())
    _when = f"{_d // 86400} days" if _d >= 86400 else (f"{_d // 3600}h" if _d >= 3600 else "under 1h")
    next_line = f'next round in {_when} · {escape(_up[0]["name"][:34])}'
else:
    next_line = "no upcoming rounds"

stats = f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="230" viewBox="0 0 860 230">
<style>
.t {{ font:14px {FONT}; fill:#c0caf5; }}
.h {{ font-size:13px; fill:#565f89; letter-spacing:1px; }}
.line {{ stroke-dasharray:800; stroke-dashoffset:800; animation:draw 2s ease-out forwards .3s; }}
@keyframes draw {{ to {{ stroke-dashoffset:0; }} }}
</style>
<rect width="860" height="230" rx="12" fill="#1a1b26" stroke="#292e42"/>
<text x="24" y="36" class="t h">CODEFORCES · {escape(info["handle"])}</text>
<text x="24" y="80" class="t" style="font-size:30px;font-weight:bold;fill:{rc}">{cur}</text>
<text x="100" y="80" class="t" style="fill:{rc}">{escape(rank.title())}</text>
<text x="210" y="80" class="t" style="fill:#9ece6a">↗ +{gain} in {len(rating)} contests</text>
<text x="24" y="108" class="t">max {mx} · {solved} solved · C++23</text>
<polyline class="line" fill="none" stroke="#7aa2f7" stroke-width="2.5" points="{poly}"/>{dots}
<text x="24" y="210" class="t" style="font-size:12px;fill:#e0af68">⏱ {next_line}</text>
<line x1="430" y1="24" x2="430" y2="206" stroke="#292e42"/>
<text x="456" y="36" class="t h">HACK THE BOX · {HTB["user"]}</text>
<text x="456" y="70" class="t" style="font-size:17px;font-weight:bold;fill:#9ece6a">{HTB["path"]}</text>
<text x="456" y="90" class="t" style="font-size:12px;fill:#565f89">HTB Academy job-role path  →  🎯 CPTS</text>
<rect x="456" y="102" width="300" height="10" rx="5" fill="#292e42"/>
<rect x="456" y="102" width="0" height="10" rx="5" fill="#9ece6a"><animate attributeName="width" to="{bar_w}" begin=".6s" dur="1.2s" fill="freeze"/></rect>
<text x="766" y="112" class="t" style="font-size:12px;fill:#9ece6a">{pct}%</text>
<text x="456" y="136" class="t">{HTB["done"]}/{HTB["total"]} modules completed{now_part}</text>
<text x="456" y="166" class="t">Lvl <tspan style="fill:#9ece6a;font-weight:bold">{HTB["level"]}</tspan> · {escape(HTB["rank"])} · {HTB["xp"]} XP</text>
<text x="456" y="192" class="t">{badge_line}</text>
</svg>'''
(out / "stats.svg").write_text(stats, encoding="utf-8")


print(f"stats: {cur} {rank}, {solved} solved")
