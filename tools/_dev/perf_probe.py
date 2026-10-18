"""构建产物体积/资源加载分析（只读，不改站）。"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DIST = Path(__file__).resolve().parents[2] / "site" / ".vitepress" / "dist"


def head_assets(page: str) -> None:
    p = DIST / page
    c = p.read_text(encoding="utf-8", errors="replace")
    print(f"=== {page}  html={len(c)/1024:.0f}KB")
    for m in re.finditer(r"<(?:link|script)\b[^>]*>", c):
        s = m.group(0)
        if re.search(r'rel="(modulepreload|preload|stylesheet|icon)"|src="', s):
            print("   ", s[:200])
    print("    img:", len(re.findall(r"<img\b", c)), " lazy:", len(re.findall(r'loading="', c)),
          " width attr:", len(re.findall(r"<img[^>]*\bwidth=", c)))


for page in [
    "zh/index.html",
    "zh/characters.html",
    "zh/getting-started.html",
    "zh/equip-067.html",
    "mirror/treasure-open.html",
]:
    if (DIST / page).exists():
        head_assets(page)

# 图片资源总览
import collections

dirs = collections.Counter()
tot = 0
for f in (DIST / "img").rglob("*"):
    if f.is_file():
        sz = f.stat().st_size
        tot += sz
        dirs[f.suffix.lower()] += sz
print("\n=== /img 总体积 %.1f MB" % (tot / 1048576))
for k, v in dirs.most_common():
    print(f"    {k or '(none)'}: {v/1048576:.1f} MB")
big = sorted(((f.stat().st_size, f) for f in (DIST / "img").rglob("*") if f.is_file()), reverse=True)[:10]
print("    最大的 10 个:")
for sz, f in big:
    print(f"      {sz/1024:8.0f}KB {f.relative_to(DIST)}")
