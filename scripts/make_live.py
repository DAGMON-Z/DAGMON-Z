"""One card, two halves: Codeforces (left) and Hack The Box as msfconsole loot (right).

Usage: python3 make_live.py <cache_dir> <out_dir>
Reads the Codeforces API cache, data/htb-public.json (badges, refreshed automatically)
and data/htb.json ("privilege": guest | user | www-data | admin | root).
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
W, H = 860, 250

# ---------------- Codeforces (left) ----------------
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
x0, x1, y0, y1 = 24, 400, 196, 150
coords = [(x0 + (x1 - x0) * (i / max(len(pts) - 1, 1)), y0 - (y0 - y1) * ((p - lo) / span)) for i, p in enumerate(pts)]
poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in coords)
dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3.5" fill="{rc}"/>' for x, y in coords)

_up = sorted((x for x in contests if x["phase"] == "BEFORE"), key=lambda x: x["startTimeSeconds"])
if _up:
    _d = int(_up[0]["startTimeSeconds"] - time.time())
    _when = f"{_d // 86400} days" if _d >= 86400 else (f"{_d // 3600}h" if _d >= 3600 else "under 1h")
    next_line = f'next round in {_when} · {escape(_up[0]["name"][:28])}'
else:
    next_line = "no upcoming rounds"

# ---------------- Hack The Box (right) ----------------
cfg = json.loads(Path("data/htb.json").read_text())
pub = Path("data/htb-public.json")
badges = json.loads(pub.read_text())["badges"] if pub.exists() else []
LADDER = ["guest", "user", "www-data", "admin", "root"]
priv = cfg.get("privilege", "user")


def short(desc):
    d = (desc or "").replace(" module completed", "").replace("Awarded when you achieve your ", "").replace("Awarded after ", "")
    return d[:27]


loot = []
for b in badges[:3]:
    loot.append(f'<tspan fill="#9ece6a">[+]</tspan> {escape(b["name"][:16]):<16}  <tspan fill="#a9b1d6">{escape(short(b.get("description")))}</tspan>')
if len(badges) > 3:
    loot.append(f'<tspan fill="#565f89">    … +{len(badges) - 3} more</tspan>')
if not badges:
    loot.append('<tspan fill="#565f89">[*] no loot yet. the hunt continues.</tspan>')

ladder = ""
for step in LADDER:
    col = "#9ece6a" if LADDER.index(step) < LADDER.index(priv) else ("#e0af68" if step == priv else "#565f89")
    ladder += f'<tspan fill="{col}">{step}</tspan>' + ('<tspan fill="#565f89"> ▸ </tspan>' if step != "root" else "")

right = [f'<tspan fill="#f7768e">msf6</tspan> &gt; loot'] + loot
rows = "".join(f'<text x="456" y="{66 + i * 22}" class="t l" style="font-size:13px;animation-delay:{0.4 + i * 0.2:.1f}s">{ln}</text>'
               for i, ln in enumerate(right))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
.t {{ font:14px {FONT}; fill:#c0caf5; white-space:pre; }}
.h {{ font-size:13px; fill:#565f89; letter-spacing:1px; }}
.l {{ opacity:0; animation:show .01s forwards; }} @keyframes show {{ to {{ opacity:1; }} }}
.line {{ stroke-dasharray:800; stroke-dashoffset:800; animation:draw 2s ease-out forwards .3s; }}
@keyframes draw {{ to {{ stroke-dashoffset:0; }} }}
</style>
<rect width="{W}" height="{H}" rx="12" fill="#1a1b26" stroke="#292e42"/>

<text x="24" y="36" class="t h">🏁 CODEFORCES · {escape(info["handle"])}</text>
<text x="24" y="82" class="t" style="font-size:32px;font-weight:bold;fill:{rc}">{cur}</text>
<text x="108" y="82" class="t" style="font-size:15px;fill:{rc}">{escape(rank.title())}</text>
<text x="24" y="110" class="t" style="fill:#9ece6a">↗ +{gain} in {len(rating)} contests</text>
<text x="24" y="134" class="t">max {mx} · {solved} solved · C++23</text>
<polyline class="line" fill="none" stroke="#7aa2f7" stroke-width="2.5" points="{poly}"/>{dots}
<text x="24" y="228" class="t" style="font-size:12px;fill:#e0af68">⏱ {next_line}</text>

<line x1="430" y1="24" x2="430" y2="226" stroke="#292e42"/>

<text x="456" y="36" class="t h">🛡️ HACK THE BOX · {escape(cfg.get("user", "DAGMON"))}</text>
{rows}
<text x="456" y="186" class="t l" style="font-size:13px;animation-delay:1.4s"><tspan fill="#7aa2f7">[*]</tspan> priv: {ladder}</text>
<text x="456" y="208" class="t l" style="font-size:13px;animation-delay:1.6s"><tspan fill="#7aa2f7">[*]</tspan> target: <tspan fill="#bb9af7">{escape(cfg.get("path", "Penetration Tester"))}</tspan> → CPTS</text>
<text x="456" y="228" class="t l" style="font-size:12px;fill:#e0af68;animation-delay:1.8s">    status: exploiting…</text>
</svg>'''
(out / "stats.svg").write_text(svg, encoding="utf-8")
print(f"stats: {cur} {rank}, {solved} solved · htb: {len(badges)} badges, priv {priv}")
