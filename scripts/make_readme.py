"""Fill README.tpl.md -> README.md. Keeps the old projects block if a fresh one isn't available."""
import hashlib
import re
from pathlib import Path

tpl = Path("README.tpl.md").read_text(encoding="utf-8")
fresh = Path(".cache/projects.md")
if fresh.exists():
    projects = fresh.read_text(encoding="utf-8").strip()
else:
    old = Path("README.md").read_text(encoding="utf-8") if Path("README.md").exists() else ""
    m = re.search(r"<!-- projects:start -->\n(.*?)\n<!-- projects:end -->", old, re.S)
    projects = m.group(1) if m else ""
out = tpl.replace("{{PROJECTS}}", f"<!-- projects:start -->\n{projects}\n<!-- projects:end -->")


# Cache busting: browsers and GitHub keep README images for a few minutes, so a
# changed image (like the CTF scoreboard) showed up late. Add "?v=<hash of the
# file>" to every local image: a changed file gets a new link, which no cache
# has yet, so it shows at once. An unchanged file keeps its link and stays cached.
def versioned(m):
    path = Path(m.group(2))
    if not path.is_file():
        return m.group(0)
    v = hashlib.sha256(path.read_bytes()).hexdigest()[:10]
    return f'{m.group(1)}{m.group(2)}?v={v}"'


out = re.sub(r'(src=")(assets/[^"?]+)"', versioned, out)
Path("README.md").write_text(out, encoding="utf-8")
print("README.md written")
