"""Shared-shell bot. Reads a visitor's command from an issue title, picks a canned reply
(nothing is ever executed), logs it, and redraws assets/issue-shell.svg.

Env: ISSUE_TITLE, ISSUE_USER. Writes the issue comment to .cache/reply.md.
Run with no env vars to just redraw the SVG from data/shell-log.json.
"""
import json
import os
import re
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "'JetBrains Mono','Fira Code',ui-monospace,Menlo,Consolas,monospace"
LOG = Path("data/shell-log.json")
replies = json.loads(Path("data/shell.json").read_text(encoding="utf-8"))


def clean(s, n):
    s = re.sub(r"[^\x20-\x7e]", "", s)          # printable ASCII only
    s = re.sub(r"\s+", " ", s).replace("`", "'").strip()
    return s[:n]


def reply_for(cmd):
    low = cmd.lower()
    if low in replies["exact"]:
        return replies["exact"][low]
    first = low.split(" ")[0] if low else ""
    if first == "echo":
        return cmd[5:] or ""
    if first in replies["prefix"]:
        return replies["prefix"][first]
    return f"zsh: command not found: {cmd.split(' ')[0]}" if cmd else "zsh: empty command"


def render(log):
    lines = ['<tspan fill="#565f89"># Click a command above. It opens an issue; a bot replies and your command appears here.</tspan>', ""]
    if not log["last"]:
        lines += ['<tspan fill="#565f89">no commands yet. be the first one!</tspan>', ""]
    for e in log["last"]:
        lines.append(f'<tspan fill="#9ece6a">@{escape(e["user"])}</tspan> <tspan fill="#7aa2f7">❯</tspan> {escape(e["cmd"])}')
        for r in (e["reply"].split("\n")[:2] if e["reply"] else []):
            lines.append("    " + escape(r[:80]))
    lines += ["", f'<tspan fill="#565f89">last {len(log["last"])} visitor commands · {log["count"]} commands run so far</tspan>']
    h = 80 + 22 * len(lines)
    body = "".join(f'<text x="24" y="{62 + i * 22}" class="t l" style="animation-delay:{0.2 + i * 0.15:.2f}s">{ln}</text>'
                   for i, ln in enumerate(lines))
    Path("assets/issue-shell.svg").write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{h}" viewBox="0 0 860 {h}">
<style>.t {{ font:14px {FONT}; fill:#c0caf5; white-space:pre; }} .l {{ opacity:0; animation:show .01s forwards; }} @keyframes show {{ to {{ opacity:1; }} }}</style>
<rect width="860" height="{h}" rx="12" fill="#1a1b26"/>
<rect width="860" height="34" rx="12" fill="#16161e"/><rect y="22" width="860" height="12" fill="#16161e"/>
<circle cx="22" cy="17" r="6" fill="#f7768e"/><circle cx="42" cy="17" r="6" fill="#e0af68"/><circle cx="62" cy="17" r="6" fill="#9ece6a"/>
<text x="430" y="22" text-anchor="middle" class="t" style="font-size:13px;fill:#565f89">guest@dagmon-z · shared shell (via GitHub Issues)</text>
{body}</svg>''', encoding="utf-8")


log = json.loads(LOG.read_text()) if LOG.exists() else {"count": 0, "last": []}
title, user = os.environ.get("ISSUE_TITLE"), os.environ.get("ISSUE_USER")
if title is not None and user:
    cmd = clean(re.sub(r"^\s*shell:\s*", "", title, flags=re.I), 60)
    rep = "\n".join(clean(x, 90) for x in reply_for(cmd).split("\n"))
    log["count"] += 1
    log["last"] = ([{"user": clean(user, 39), "cmd": cmd, "reply": rep}] + log["last"])[:3]
    LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
    Path(".cache").mkdir(exist_ok=True)
    Path(".cache/reply.md").write_text(
        f"```console\nguest@dagmon ❯ {cmd}\n{rep}\n```\n\n"
        f"Your command is now on the profile 👉 https://github.com/DAGMON-Z\n"
        f"(it can take a minute to show up; refresh the page)\n", encoding="utf-8")
render(log)
print("shell: rendered", log["count"])
