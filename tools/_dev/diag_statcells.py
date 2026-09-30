# -*- coding: utf-8 -*-
"""逐格比对「JSON 非空单元格」与「渲染出的非空单元格」，定位多余/缺失的那一格。

背景（2026-09-30）：完整性校验发现部分表**页面比 JSON 多 1 格** ✗，
且只出现在"无表头、由首行提升为表头"的那几张表 ✓。这里把多出来的那格**打印出来** ✓。

用法：python tools/_dev/diag_statcells.py <slug> [表序号]
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline import statpages  # noqa: E402

CELL_RE = re.compile(r"<t[dh][\s>][^>]*>(?:(?!</t[dh]>).)+?</t[dh]>", re.S)


def texts_of(html: str) -> "list[str]":
    """取单元格文本；**只保留非空** ✓ —— 因为校验比的是"非空单元格数" ✓，
    渲染成空的格（= 内容丢了 ✗）必须暴露出来 ✓。"""
    return [t for t in (re.sub(r"<[^>]+>", "", m).strip() for m in CELL_RE.findall(html)) if t]


def main() -> int:
    slug = sys.argv[1] if len(sys.argv) > 1 else "stat-d2p-gacha"
    page = next(p for p in statpages.PAGES if p["slug"] == slug)
    data = statpages._pkg(page["package"])
    labels = statpages.load_labels()
    ti = 0
    for sheet in statpages._pick_sheets(data, page.get("sheets") or []):
        for t in sheet["tables"]:
            ti += 1
            if len(sys.argv) > 2 and str(ti) != sys.argv[2]:
                continue
            # 逐行比"非空单元格数"的**序列** ✓（能指出到底是哪几行丢了格 ✓）
            jrows = [[(c.get("t") or "").strip() for c in r if (c.get("t") or "").strip()]
                     for r in (t.get("header") or []) + (t.get("rows") or [])]
            jrows = [r for r in jrows if r]
            html = statpages.render_table(t, labels, "zh")
            hrows = [texts_of(m) for m in re.findall(r"<tr>.*?</tr>", html, re.S)]
            hrows = [r for r in hrows if r]
            jn, hn = sum(len(r) for r in jrows), sum(len(r) for r in hrows)
            print(f"\n===== 表{ti} [{sheet['name']}] {t['nrows']}行  JSON {jn} / 页面 {hn}"
                  f"（行数 {len(jrows)} / {len(hrows)}）")
            if jn == hn and len(jrows) == len(hrows):
                continue
            for i in range(max(len(jrows), len(hrows))):
                a = jrows[i] if i < len(jrows) else None
                b = hrows[i] if i < len(hrows) else None
                if a is None or b is None or len(a) != len(b):
                    print(f"  行{i}: JSON {len(a) if a is not None else '—'} 格 {(a or [])[:6]}"
                          f"  →  页面 {len(b) if b is not None else '—'} 格 {(b or [])[:6]}")
                    if i > 24:
                        print("  …（只列前若干行）")
                        break
            # 顺带把"词表里出现空译文"的情况揪出来 ✓（这正是单元格被判空的头号嫌疑 ✓）
            empties = [k for k, v in labels.items() if not str(v).strip()]
            if empties:
                print(f"  ⚠ 词表里有 {len(empties)} 个**空译文**键（会把内容抹成空 ✗）: {empties[:8]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
