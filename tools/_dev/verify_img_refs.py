"""校验：全站所有 /img/<name> 引用都能在 data/assets/img 找到实体文件（0 死链）。

用法: python -u tools/_dev/verify_img_refs.py
"""
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "data" / "assets" / "img"
RE = re.compile(r"(?:/?)img/([0-9a-f]{8,64}\.[a-z0-9]{2,6})")

actual = {p.name for p in IMG.iterdir() if p.is_file()}
exts = Counter(p.suffix.lower() for p in IMG.iterdir() if p.is_file())
print(f"磁盘图片 {len(actual)} 个：", dict(exts))

scan_dirs = [
    ROOT / "data" / "parsed",
    ROOT / "site" / ".vitepress" / "frag",
]
refs = Counter()
where = {}
for d in scan_dirs:
    if not d.exists():
        continue
    for f in d.rglob("*"):
        if not f.is_file() or f.suffix not in (".html", ".json", ".md"):
            continue
        try:
            text = io.open(f, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for m in RE.finditer(text):
            name = m.group(1)
            refs[name] += 1
            where.setdefault(name, str(f.relative_to(ROOT)))

print(f"被引用的图片名 {len(refs)} 个（含 data/parsed 与 frag）")
missing = {n: c for n, c in refs.items() if n not in actual}
print(f"缺失（会 404）: {len(missing)}")
for n, c in list(missing.items())[:15]:
    print(f"  ✗ {n}  引用 {c} 次  首次出现在 {where[n]}")
dup = [n for n in actual if n.rsplit('.', 1)[0] + '.png' in actual]
print(f"同一主干同时存在 png 与 webp: {len(dup)}")
