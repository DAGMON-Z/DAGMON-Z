"""One terminal: DAGMON OS boots, clears the screen, then guest runs nmap on dagmon."""
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
FONT = "'JetBrains Mono','Fira Code',ui-monospace,Menlo,Consolas,monospace"
W, H = 860, 470
CLEAR = 3.3           # moment the boot screen clears
N0 = CLEAR + 0.3      # nmap phase starts

boot = [
    (0.2, '<tspan class="dim">:: </tspan>running early hook [<tspan class="acc">udev</tspan>]'),
    (0.5, '[  <tspan class="ok">OK</tspan>  ] Mounted <tspan class="acc">/home/dagmon</tspan>'),
    (0.8, '[  <tspan class="ok">OK</tspan>  ] Started <tspan class="mag">Competitive Programming Daemon</tspan> (cp.service)'),
    (1.1, '[  <tspan class="ok">OK</tspan>  ] Started <tspan class="mag">Packet Sniffer Service</tspan> (wireshark.service)'),
    (1.4, '[<tspan class="red"> *** </tspan> ] A start job is running for <tspan class="red">Red Teamer path</tspan> <tspan class="dim">(rooms… / no limit)</tspan>'),
    (1.7, '[ <tspan class="warn">WARN</tspan> ] sleep.service: unit not found, continuing anyway'),
    (2.0, '[  <tspan class="ok">OK</tspan>  ] Started <tspan class="acc">Hyprland</tspan> compositor · theme <tspan class="mag">Tokyo Night</tspan>'),
    (2.5, 'Welcome to <tspan class="acc" font-weight="bold">DAGMON OS</tspan>  ·  login: <tspan class="ok">guest</tspan>'),
]
P = '<tspan class="ok">guest@dagmon</tspan> <tspan class="acc">~</tspan> <tspan class="mag">❯</tspan> '
scan = [
    (98, 0.9, '<tspan class="dim">Starting Nmap 7.95 ( https://nmap.org )</tspan>'),
    (122, 1.2, 'Nmap scan report for <tspan class="cy">dagmon-z</tspan> (github.com/DAGMON-Z)'),
    (146, 1.4, 'Host is up: <tspan class="ok">competitive programmer</tspan> · <tspan class="red">pentester in training</tspan>'),
    (182, 1.7, '<tspan class="acc" font-weight="bold">PORT       STATE     SERVICE            VERSION</tspan>'),
    (208, 1.95, '22/tcp     <tspan class="ok">open</tspan>      <tspan class="cy">arch-linux</tspan>         Hyprland · Tokyo Night · btw'),
    (232, 2.2, '443/tcp    <tspan class="ok">open</tspan>      <tspan class="cy">competitive-prog</tspan>   C++23 · Codeforces (DAGMON)'),
    (256, 2.45, '1337/tcp   <tspan class="warn">learning</tspan>  <tspan class="cy">pentesting</tspan>         TryHackMe · Red Teamer path'),
    (280, 2.7, '8080/tcp   <tspan class="ok">open</tspan>      <tspan class="cy">networking</tspan>         TCP/IP · Wireshark · subnetting'),
    (304, 2.95, '31337/tcp  <tspan class="warn">filtered</tspan>  <tspan class="red">???</tspan>                find the flag below 🚩'),
    (340, 3.25, '<tspan class="dim">OS details:</tspan> Arch Linux (rolling release, always learning)'),
    (364, 3.4, '<tspan class="dim">Uptime guess:</tspan> since Nov 2024'),
    (400, 3.6, '<tspan class="dim">Nmap done: 1 human scanned in 0.42 seconds</tspan>'),
    (440, 3.85, P + '<tspan class="cur">█</tspan>'),
]

b = "".join(f'<text x="24" y="{66 + i * 26 + (14 if i == 7 else 0)}" class="t l" style="animation-delay:{d}s">{s}</text>'
            for i, (d, s) in enumerate(boot))
n = "".join(f'<text x="24" y="{y}" class="t l" style="animation-delay:{N0 + d:.2f}s">{s}</text>' for y, d, s in scan)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
.t {{ font:15px {FONT}; fill:#c0caf5; white-space:pre; }}
.ok {{ fill:#9ece6a; }} .warn {{ fill:#e0af68; }} .dim {{ fill:#565f89; }} .acc {{ fill:#7aa2f7; }}
.mag {{ fill:#bb9af7; }} .red {{ fill:#f7768e; }} .cy {{ fill:#7dcfff; }}
.l {{ opacity:0; animation:show .01s forwards; }}
@keyframes show {{ to {{ opacity:1; }} }}
.boot {{ animation:hide .01s forwards {CLEAR}s; }}
@keyframes hide {{ to {{ opacity:0; }} }}
.cur {{ animation:blink 1s steps(1) infinite; }}
@keyframes blink {{ 50% {{ opacity:0; }} }}
</style>
<defs><clipPath id="type"><rect x="0" y="40" height="30" width="0">
  <animate attributeName="width" from="150" to="860" begin="{N0 + 0.1:.1f}s" dur="1.3s" fill="freeze"/>
</rect></clipPath></defs>
<rect width="{W}" height="{H}" rx="12" fill="#1a1b26"/>
<!-- 31337/tcp banner: synt{{i13j_f0hep3_1f_4_fhc3ec0j3e_ps63o2}}  (rotate your thinking: 13) -->
<rect width="{W}" height="34" rx="12" fill="#16161e"/><rect y="22" width="{W}" height="12" fill="#16161e"/>
<circle cx="22" cy="17" r="6" fill="#f7768e"/><circle cx="42" cy="17" r="6" fill="#e0af68"/><circle cx="62" cy="17" r="6" fill="#9ece6a"/>
<text x="{W // 2}" y="22" text-anchor="middle" class="t dim" style="font-size:13px">guest@dagmon: ~</text>
<g class="boot">{b}</g>
<g class="l" style="animation-delay:{N0}s" clip-path="url(#type)"><text x="24" y="62" class="t">{P}nmap -sV -A dagmon-z</text></g>
{n}
</svg>'''
(OUT / "main.svg").write_text(svg, encoding="utf-8")
print("ok")
