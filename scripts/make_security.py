"""Security section as an msfconsole session: HTB badges become loot, plus a privilege-escalation line.

Usage: python3 make_security.py <out_dir>
Reads data/htb-public.json (badges, refreshed automatically from the public HTB profile)
and data/htb.json ("privilege": guest | user | www-data | admin | root).
"""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

out = Path(sys.argv[1])
FONT = "'JetBrains Mono','Fira Code',ui-monospace,Menlo,Consolas,monospace"
cfg = json.loads(Path("data/htb.json").read_text())
pub = Path("data/htb-public.json")
badges = json.loads(pub.read_text())["badges"] if pub.exists() else []

LADDER = ["guest", "user", "www-data", "admin", "root"]
priv = cfg.get("privilege", "user")
P = '<tspan fill="#f7768e">msf6</tspan> <tspan fill="#c0caf5">&gt;</tspan> '


def short(desc):
    d = (desc or "").replace(" module completed", "").replace("Awarded when you achieve your ", "").replace("Awarded after ", "")
    return d[:44]


lines = [P + "loot", "",
         '<tspan fill="#7aa2f7">Loot (Hack The Box · ' + escape(cfg.get("user", "DAGMON")) + ')</tspan>',
         '<tspan fill="#565f89">' + "=" * 30 + "</tspan>"]
if badges:
    for b in badges[:6]:
        date = str(b.get("awarded_at", ""))[:10]
        lines.append(f'<tspan fill="#9ece6a">[+]</tspan> {escape(b["name"][:18]):<18}  '
                     f'{escape(short(b.get("description"))):<44}  <tspan fill="#565f89">{date}</tspan>')
    if len(badges) > 6:
        lines.append(f'<tspan fill="#565f89">    … and {len(badges) - 6} more</tspan>')
else:
    lines.append('<tspan fill="#565f89">[*] no loot yet. the hunt continues.</tspan>')

ladder = ""
for step in LADDER:
    col = "#9ece6a" if LADDER.index(step) < LADDER.index(priv) else ("#e0af68" if step == priv else "#565f89")
    ladder += f'<tspan fill="{col}">{"root (CPTS)" if step == "root" else step}</tspan>'
    if step != "root":
        ladder += '<tspan fill="#565f89"> ─▶ </tspan>'

lines += ["", P + "sessions -i 1",
          f'<tspan fill="#7aa2f7">[*]</tspan> Target: <tspan fill="#bb9af7">{escape(cfg.get("path", "Penetration Tester"))} path</tspan> → CPTS   status: <tspan fill="#e0af68">exploiting…</tspan>',
          f'<tspan fill="#7aa2f7">[*]</tspan> Privilege: {ladder}',
          f'<tspan fill="#565f89">    current: </tspan><tspan fill="#e0af68">{escape(priv)}</tspan><tspan fill="#565f89"> · next stop: root</tspan>',
          "", P + '<tspan class="cur">█</tspan>']

h = 80 + 24 * len(lines)
body = "".join(f'<text x="24" y="{62 + i * 24}" class="t l" style="animation-delay:{0.3 + i * 0.22:.2f}s">{ln}</text>'
               for i, ln in enumerate(lines))
(out / "security.svg").write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{h}" viewBox="0 0 860 {h}">
<style>.t {{ font:13.5px {FONT}; fill:#c0caf5; white-space:pre; }} .l {{ opacity:0; animation:show .01s forwards; }} @keyframes show {{ to {{ opacity:1; }} }}
.cur {{ animation:blink 1s steps(1) infinite; }} @keyframes blink {{ 50% {{ opacity:0; }} }}</style>
<rect width="860" height="{h}" rx="12" fill="#1a1b26"/>
<rect width="860" height="34" rx="12" fill="#16161e"/><rect y="22" width="860" height="12" fill="#16161e"/>
<circle cx="22" cy="17" r="6" fill="#f7768e"/><circle cx="42" cy="17" r="6" fill="#e0af68"/><circle cx="62" cy="17" r="6" fill="#9ece6a"/>
<text x="430" y="22" text-anchor="middle" class="t" style="font-size:13px;fill:#565f89">msfconsole · dagmon@arch</text>
{body}</svg>''', encoding="utf-8")
print("security:", len(badges), "badges, privilege", priv)
