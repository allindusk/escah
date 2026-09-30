# -*- coding: utf-8 -*-
"""把一张 sheet 的「数据版图」画成 ASCII 图，用来判断它到底是**一张表**还是**多块独立数据**。

背景（2026-09-30 用户反馈"把本来不一样的数据放进了同一个表格"）：
解析器把 Google 表格导出的 `<table>` 原样当成"一张表"渲染 ✗，但实际一个 sheet 里常常
**纵向堆着好几块互不相关的数据**（结果表 / 明细 / 注意事项 / 变更点…），
用同一个表头去套 → 视觉上就是"不同数据挤在同一格网里" ✗。

输出：
  `#` = 该格有内容；`.` = 空；左侧数字 = 行号；右侧 = 该行非空格数 + 前几个文本
  整行为空的行会标 `--- 空行（可能是分块边界）---`

用法：python tools/_dev/diag_sheet_layout.py <包key> <sheet名前缀> [最大行数]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
STAT = ROOT / "data" / "statdata"


def main() -> int:
    key = sys.argv[1] if len(sys.argv) > 1 else "treasure-open"
    prefix = sys.argv[2] if len(sys.argv) > 2 else "結果(合計)"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    data = json.loads((STAT / f"{key}.json").read_text(encoding="utf-8"))
    sheet = next((s for s in data["sheets"] if s["name"].startswith(prefix)), None)
    if sheet is None:
        print("未找到 sheet")
        return 1
    print(f"### {sheet['name']}  （{len(sheet['tables'])} 张表）")
    for ti, t in enumerate(sheet["tables"], 1):
        rows = list(t.get("rows") or [])
        header = list(t.get("header") or [])
        print(f"\n--- 表{ti}: {t['nrows']}行×{t['ncols']}列  header行数={len(header)} 数据行数={len(rows)}")
        allrows = header + rows
        width = max((len(r) for r in allrows), default=0)
        print(f"    最大列数={width}（下面每行标出非空格数与前几格文本）")
        for i, r in enumerate(allrows[:limit]):
            marks = "".join("#" if (c.get("t") or "").strip() else "." for c in r)
            marks = marks.ljust(width, ".")
            ne = [c.get("t", "").strip() for c in r if (c.get("t") or "").strip()]
            if not ne:
                print(f"   {i:>3} {marks}  --- 空行 ---")
            else:
                print(f"   {i:>3} {marks}  {len(ne):>2}格  " + " | ".join(x[:16] for x in ne[:5]))
        if len(allrows) > limit:
            print(f"   …（共 {len(allrows)} 行，只列前 {limit} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
