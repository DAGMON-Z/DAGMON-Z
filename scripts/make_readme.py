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


# Fresh images at once: GitHub serves README images through a cache that keeps
# each file for 5 minutes and ignores "?v=" tags. So the README points to a copy
# whose name contains a hash of the content (assets/v/stats-1a2b3c4d5e.svg). A
# changed image gets a name no cache has seen, so it shows immediately. Copies
# no longer used are deleted. The original files (assets/stats.svg ...) stay as
# they are, for anything that links to them directly.
VERSIONS = Path("assets/v")
VERSIONS.mkdir(parents=True, exist_ok=True)
used = set()


def versioned(m):
    path = Path(m.group(2))
    if not path.is_file():
        return m.group(0)
    data = path.read_bytes()
    copy = VERSIONS / f"{path.stem}-{hashlib.sha256(data).hexdigest()[:10]}{path.suffix}"
    if not copy.exists() or copy.read_bytes() != data:
        copy.write_bytes(data)
    used.add(copy.name)
    return f'{m.group(1)}{copy.as_posix()}"'


out = re.sub(r'(src=")(assets/[^"?/]+)(?:\?v=[0-9a-f]+)?"', versioned, out)
for old in VERSIONS.iterdir():
    if old.name not in used:
        old.unlink()
Path("README.md").write_text(out, encoding="utf-8")
print("README.md written")
