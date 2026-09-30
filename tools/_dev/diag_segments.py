# -*- coding: utf-8 -*-
"""统计每个 sheet 按空行切出的"段"数与各段的形态，用来区分**真假分块边界**。

问题（2026-09-30）：按空行分块后，宝箱页的表数从 23 暴增到 183 ✗ —— 因为**记录型** sheet
（如 `検証` 190 行）里散布着零星空行✗，它们并不是"换了一块数据"的边界 ✓。
本脚本列出每个 sheet 的：段数、各段的 (行数, 最小列, 最大列, 首行前 3 格) ✓，
据此判断：真边界 = 列范围/缩进发生变化的段 ✓；假边界 = 列范围完全一致的段 ✗。

用法：python tools/_dev/diag_segments.py <包key> [只看段数≥N的sheet]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline import statpages  # noqa: E402

STAT = ROOT / "data" / "statdata"


def seg_range(seg):
    mins = [min(i for i, c in enumerate(r) if (c.get("t") or "").strip()) for r in seg]
    maxs = [max(i for i, c in enumerate(r) if (c.get("t") or "").strip()) for r in seg]
    return min(mins), max(maxs)


def main() -> int:
    key = sys.argv[1] if len(sys.argv) > 1 else "treasure-open"
    only_big = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    data = json.loads((STAT / f"{key}.json").read_text(encoding="utf-8"))
    print(f"### {key}：{len(data['sheets'])} 个 sheet")
    tot = 0
    for sheet in data["sheets"]:
        for t in sheet["tables"]:
            rows = list(t.get("header") or []) + list(t.get("rows") or [])
            segs = statpages.split_segments(rows)
            tot += len(segs)
            if len(segs) < only_big:
                continue
            print(f"\n[{sheet['name']}] {t['nrows']}行 → {len(segs)} 段")
            for i, s in enumerate(segs[:12], 1):
                lo, hi = seg_range(s)
                head = " | ".join((c.get("t") or "").strip()[:14] for c in s[0]
                                  if (c.get("t") or "").strip())
                print(f"    段{i:>3}: {len(s):>3}行 列{lo:>2}-{hi:>2}  {head[:70]}")
            if len(segs) > 12:
                print(f"    …（共 {len(segs)} 段）")
    print(f"\n合计切出 {tot} 段（即当前会渲染成 {tot} 张表 ✗ 太多）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
