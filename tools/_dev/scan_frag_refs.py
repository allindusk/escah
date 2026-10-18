"""扫 site/**/*.md 里实际 import 的 frag 文件；列出 frag 目录里没人引用的孤儿。"""
import io
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
FRAG = SITE / ".vitepress" / "frag"
RE = re.compile(r'from\s+"([^"]*\.vitepress/frag/[^"]+)"')

used = set()
for md in SITE.rglob("*.md"):
    if ".vitepress" in md.parts:
        continue
    try:
        text = io.open(md, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    for m in RE.finditer(text):
        rel = m.group(1).replace("../../.vitepress/frag/", "").replace("../.vitepress/frag/", "")
        used.add(rel)

allfrag = {str(p.relative_to(FRAG)).replace("\\", "/") for p in FRAG.rglob("*.json")}
orphan = sorted(allfrag - used)
print(f"md 引用 frag: {len(used)} 个；frag 目录文件 {len(allfrag)} 个；孤儿 {len(orphan)} 个")
charts = [o for o in orphan if o.startswith("characters/") and not re.search(r"\.(ja|zh)\.json$", o)]
print(f"其中 characters 下「无 locale」的旧文件: {len(charts)} 个，样例 {charts[:3]}")
others = [o for o in orphan if not o.startswith("characters/") or re.search(r"\.(ja|zh)\.json$", o)]
print(f"其它孤儿: {len(others)} 个，样例 {others[:5]}")
Path(ROOT / "tools" / "_dev" / "_frag_orphans.txt").write_text("\n".join(orphan), encoding="utf-8")
