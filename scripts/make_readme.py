"""Fill README.tpl.md -> README.md. Keeps the old projects block if a fresh one isn't available."""
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
Path("README.md").write_text(out, encoding="utf-8")
print("README.md written")
