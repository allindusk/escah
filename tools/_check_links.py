# -*- coding: utf-8 -*-
"""扫描 frag 中的站内绝对链接，检查目标页面是否真实存在。

用法: python tools/_check_links.py [--base /escah/]

输出:
  1) 各类 href 前缀的统计（用于确认写死的 base）
  2) 目标不存在的链接清单（真实死链，与 base 无关）
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
FRAG = ROOT / "site" / ".vitepress" / "frag"
DIST = ROOT / "site" / ".vitepress" / "dist"

HREF_RE = re.compile(r'href="([^"]+)"')
SITE_BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "/escah/"


def build_existing() -> set[str]:
    """dist 下存在的页面相对路径集合（不含 base）"""
    out: set[str] = set()
    if not DIST.exists():
        return out
    for p in DIST.rglob("*.html"):
        out.add("/" + p.relative_to(DIST).as_posix())
    return out


def main() -> int:
    existing = build_existing()
    print(f"[info] dist 页面数: {len(existing)}")

    prefix_counter: Counter[str] = Counter()
    broken: dict[str, list[str]] = {}
    internal = 0

    for f in sorted(FRAG.rglob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        html = data.get("html") if isinstance(data, dict) else None
        if not isinstance(html, str):
            continue
        for href in HREF_RE.findall(html):
            if not href.startswith("/") or href.startswith("//"):
                continue
            internal += 1
            clean = href.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            # 前缀归类
            m = re.match(r"^(/[^/]+/)?((?:ja|zh)/.*)$", clean)
            prefix_counter[(m.group(1) if m else "(其他)")] += 1

            # 去掉 base、解码百分号后核对目标
            rel = unquote(clean)
            if SITE_BASE != "/" and rel.startswith(SITE_BASE):
                rel = "/" + rel[len(SITE_BASE):]
            if not rel.endswith(".html") and "." not in rel.rsplit("/", 1)[-1]:
                rel = rel.rstrip("/") + ".html"
            if rel in existing:
                continue
            # 角色页常见形态：/zh/名字.html 少了 characters/ 段
            guess = rel.replace("/zh/", "/zh/characters/", 1).replace(
                "/ja/", "/ja/characters/", 1
            )
            tag = "MISS_CHARACTERS_DIR" if guess in existing else "MISS"
            broken.setdefault(f"[{tag}] {rel}", []).append(str(f.relative_to(FRAG)))

    print(f"[info] 站内绝对链接总数: {internal}")
    print("[info] 前缀分布(前 10):")
    for pref, n in prefix_counter.most_common(10):
        print(f"       {pref!r:20} {n}")

    print(f"\n[result] 目标不存在的链接: {len(broken)} 种 / {sum(len(v) for v in broken.values())} 处")
    for rel, files in sorted(broken.items())[:40]:
        print(f"  {rel}   <- {len(files)} 个页, e.g. {files[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
