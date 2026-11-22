"""Profile CTF checker. Issue title format:  flag: <level> <sha256(flag + github_username)>

The real flags live only in the CTF_FLAGS repository secret ({"1": "flag{...}", ...}).
Submissions are personalised hashes, so a hash posted in a public issue is useless to anyone else.
Env: ISSUE_TITLE, ISSUE_USER, CTF_FLAGS. Writes .cache/reply.md and .cache/ctf-redact (if a raw flag was posted).
Run with no env vars to just redraw assets/ctf-hof.svg from data/ctf-solves.json.
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "'JetBrains Mono','Fira Code',ui-monospace,Menlo,Consolas,monospace"
SOLVES = Path("data/ctf-solves.json")
LEVELS = [("1", "easy", "#9ece6a", "somewhere in this README"),
          ("2", "medium", "#e0af68", "inside an image's source code"),
          ("3", "hard", "#ff9e64", "buried in this repo's git history"),
          ("4", "insane", "#f7768e", "a packet capture (.pcap) in this repo")]


def render(solves):
    lines = ['<tspan fill="#f7768e">🚩 PROFILE CTF</tspan>   4 flags are hidden across this profile', ""]
    for lv, diff, col, where in LEVELS:
        n = len(solves[lv])
        lines.append(f' Level {lv} <tspan fill="{col}">{"[" + diff + "]":<9}</tspan> {where:<38}<tspan fill="#565f89">solved by {n}</tspan>')
    fb = "   ".join(f'L{lv} <tspan fill="#bb9af7">{"@" + escape(solves[lv][0]["user"]) if solves[lv] else "???"}</tspan>' for lv, *_ in LEVELS)
    lines += ["", f'<tspan fill="#7aa2f7">🏆 First bloods</tspan>   {fb}',
              '<tspan fill="#565f89">submit a personalised hash as an issue · a bot checks it and updates this board</tspan>']
    h = 80 + 24 * len(lines)
    body = "".join(f'<text x="24" y="{62 + i * 24}" class="t l" style="animation-delay:{0.3 + i * 0.3:.1f}s">{ln}</text>'
                   for i, ln in enumerate(lines))
    Path("assets/ctf-hof.svg").write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{h}" viewBox="0 0 860 {h}">
<style>.t {{ font:14px {FONT}; fill:#c0caf5; white-space:pre; }} .l {{ opacity:0; animation:show .01s forwards; }} @keyframes show {{ to {{ opacity:1; }} }}</style>
<rect width="860" height="{h}" rx="12" fill="#1a1b26"/>
<rect width="860" height="34" rx="12" fill="#16161e"/><rect y="22" width="860" height="12" fill="#16161e"/>
<circle cx="22" cy="17" r="6" fill="#f7768e"/><circle cx="42" cy="17" r="6" fill="#e0af68"/><circle cx="62" cy="17" r="6" fill="#9ece6a"/>
<text x="430" y="22" text-anchor="middle" class="t" style="font-size:13px;fill:#565f89">profile-ctf · hall of fame</text>
{body}</svg>''', encoding="utf-8")


solves = json.loads(SOLVES.read_text()) if SOLVES.exists() else {lv: [] for lv, *_ in LEVELS}
title, user, flags = os.environ.get("ISSUE_TITLE"), os.environ.get("ISSUE_USER"), os.environ.get("CTF_FLAGS")
if title is not None and user and flags:
    flags = json.loads(flags)
    Path(".cache").mkdir(exist_ok=True)
    m = re.match(r"^\s*flag:\s*([1-4])\s+([0-9a-fA-F]{64})\s*$", title)
    if "flag{" in title.lower() or any(f.lower() in title.lower() for f in flags.values()):
        Path(".cache/ctf-redact").write_text("1")
        reply = ("⚠️ That looks like a **raw flag**. Please never post flags publicly; it spoils it for everyone. "
                 "It was not counted.\n\nSubmit a personalised hash instead:\n"
                 "```bash\necho -n 'flag{...}" + user + "' | sha256sum\n```\n"
                 "and open an issue titled `flag: <level> <hash>`.")
    elif not m:
        reply = "🤔 Format not recognised. Use a title like `flag: 2 <64-char sha256>`."
    else:
        lv, got = m.group(1), m.group(2).lower()
        want = hashlib.sha256((flags[lv] + user).encode()).hexdigest()
        if got != want:
            reply = f"❌ Not quite. That isn't the level {lv} flag (or the hash wasn't made with your username `{user}`). Keep digging!"
        elif any(s["user"].lower() == user.lower() for s in solves[lv]):
            reply = f"✅ Correct, but you already solved level {lv}. Try the next one!"
        else:
            solves[lv].append({"user": user, "t": int(time.time())})
            SOLVES.write_text(json.dumps(solves, indent=2), encoding="utf-8")
            blood = " 🩸 **FIRST BLOOD!**" if len(solves[lv]) == 1 else ""
            reply = f"✅ **Level {lv} solved!** You are solver #{len(solves[lv])}.{blood}\n\nYou're on the board 👉 https://github.com/DAGMON-Z"
    Path(".cache/reply.md").write_text(reply + "\n", encoding="utf-8")
render(solves)
print("ctf: rendered", {k: len(v) for k, v in solves.items()})
