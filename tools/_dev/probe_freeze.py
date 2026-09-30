# -*- coding: utf-8 -*-
"""逐工作表取证：**真正的表头在第几行**、**左侧哪几列是行标签**，用于逐表定冻结行列。

用户批评（2026-09-30）："我不是说让你理解表格内容再定冻结行列吗，为什么你统一处理" ✗ ——
确实：统一冻"首行 + 首列"太粗糙 ✗，因为
  · 首行是 `A B C…` 列字母行 ✓，真正的列标题常在第 2~3 行 ✓（如 `敵 / ポイント / 累計撃退数` ✓）；
  · 首列是 `1 2 3…` 行号 ✓，但**第 2 列**常常才是"名称/标签"列 ✓（应一并冻结 ✓），
    而有些表第 2 列直接是数据 ✗（冻了就占屏 ✗）。

输出（每表两行，供人工判断 ✓）：
  行 A/B/C…  → 各行非空数 + 前几格文本（找"哪一行开始是列标题" ✓）
  列 1/2/3   → 各列前几格文本（找"哪几列是标签" ✓）

用法：python tools/_dev/probe_freeze.py [包key]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_sheet_mirror import PKGS, RAW, extract_table  # noqa: E402

import lxml.html as LH  # noqa: E402


def cells(table) -> "list[list[str]]":
    out = []
    for tr in table.xpath(".//tr"):
        row = []
        for c in tr.xpath("./th|./td"):
            row.append(" ".join((c.text_content() or "").split()))
        out.append(row)
    return out


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for key, prefix in PKGS.items():
        if only and key != only:
            continue
        d = next((p for p in RAW.glob(prefix + "*") if p.is_dir()), None)
        if d is None:
            continue
        for f in sorted(d.glob("*.html")):
            frag = extract_table(f)
            if not frag:
                continue
            t = LH.fragment_fromstring(frag, create_parent="div").xpath(".//table")[0]
            rows = cells(t)
            print(f"\n## {key} / {f.stem}  （{len(rows)} 行）")
            for i, r in enumerate(rows[:4], 1):
                ne = [x for x in r if x]
                head = " | ".join(ne[:5])
                print(f"   行{i}: {len(ne):>2}格  {head[:86]}")
            ncol = max((len(r) for r in rows), default=0)
            for c in range(min(3, ncol)):
                sample = [r[c] for r in rows[:6] if c < len(r) and r[c]]
                print(f"   列{c + 1}: {len(sample)}/6 有值  " + " | ".join(s[:14] for s in sample[:4]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
