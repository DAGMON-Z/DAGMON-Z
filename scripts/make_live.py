"""Build the Codeforces stats card from the Codeforces API cache.

Usage: python3 make_live.py <cache_dir> <out_dir>
"""
import json
import sys
import time
from pathlib import Path
from xml.sax.saxutils import escape

src, out = Path(sys.argv[1]), Path(sys.argv[2])
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

# ---- rating graph (right half)
pts = [r["newRating"] for r in rating] or [0]
lo, hi = min(pts), max(pts)
span = max(hi - lo, 1)
n = len(pts)
x0, x1, y0, y1 = 470, 830, 160, 50
coords = [(x0 + (x1 - x0) * (i / max(n - 1, 1)), y0 - (y0 - y1) * ((p - lo) / span)) for i, p in enumerate(pts)]
poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in coords)
dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="{rc}"/>' for x, y in coords)
labels = "".join(f'<text x="{x:.0f}" y="{y - 12:.0f}" text-anchor="middle" class="t" style="font-size:11px;fill:#565f89">{p}</text>'
                 for (x, y), p in zip(coords, pts))

# ---- next contest
_up = sorted((x for x in contests if x["phase"] == "BEFORE"), key=lambda x: x["startTimeSeconds"])
if _up:
    _d = int(_up[0]["startTimeSeconds"] - time.time())
    _when = f"{_d // 86400} days" if _d >= 86400 else (f"{_d // 3600}h" if _d >= 3600 else "under 1h")
    next_line = f'next round in {_when} · {escape(_up[0]["name"][:34])}'
else:
    next_line = "no upcoming rounds"

stats = f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="200" viewBox="0 0 860 200">
<style>
.t {{ font:14px {FONT}; fill:#c0caf5; }}
.h {{ font-size:13px; fill:#565f89; letter-spacing:1px; }}
.line {{ stroke-dasharray:800; stroke-dashoffset:800; animation:draw 2s ease-out forwards .3s; }}
@keyframes draw {{ to {{ stroke-dashoffset:0; }} }}
</style>
<rect width="860" height="200" rx="12" fill="#1a1b26" stroke="#292e42"/>
<text x="24" y="36" class="t h">CODEFORCES · {escape(info["handle"])}</text>
<text x="24" y="84" class="t" style="font-size:34px;font-weight:bold;fill:{rc}">{cur}</text>
<text x="112" y="84" class="t" style="font-size:16px;fill:{rc}">{escape(rank.title())}</text>
<text x="24" y="116" class="t" style="fill:#9ece6a">↗ +{gain} in {len(rating)} contests</text>
<text x="24" y="142" class="t">max {mx} · {solved} solved · C++23</text>
<text x="24" y="176" class="t" style="font-size:12px;fill:#e0af68">⏱ {next_line}</text>
<line x1="440" y1="24" x2="440" y2="176" stroke="#292e42"/>
<line x1="{x0}" y1="{y0 + 14}" x2="{x1}" y2="{y0 + 14}" stroke="#292e42"/>
<polyline class="line" fill="none" stroke="#7aa2f7" stroke-width="2.5" points="{poly}"/>{dots}{labels}
<text x="{x1}" y="{y0 + 32}" text-anchor="end" class="t" style="font-size:11px;fill:#565f89">rating history</text>
</svg>'''
(out / "stats.svg").write_text(stats, encoding="utf-8")
print(f"stats: {cur} {rank}, {solved} solved")
