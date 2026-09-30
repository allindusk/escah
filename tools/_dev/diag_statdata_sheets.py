# -*- coding: utf-8 -*-
"""盘点一个统计包：原始 HTML 里有几个 sheet、解析器收了几个、页面又能展示几个。

背景（2026-09-30，用户追问）：`宝箱開封しらべるくんv2.12` 目录下有 **36 个 sheet 的 html** ✓，
但 페이지 上只出现 7 张表 ✗。需要三段对齐：原始 → JSON → 页面。

用法：python tools/_dev/diag_statdata_sheets.py treasure-open
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline import statpages  # noqa: E402

RAW = ROOT / "recycle_bin" / "data"
PFX = {"treasure-open": "宝箱開封しらべるくん", "annihilation": "殲滅戦報酬調べるくん",
       "d2p-gacha": "D2Pガチャしらべるくん", "box": "ボックスしらべるくん"}


def main() -> int:
    key = sys.argv[1] if len(sys.argv) > 1 else "treasure-open"
    raw_dir = next((d for d in RAW.glob(PFX.get(key, "") + "*")), None)
    files = sorted(p.name for p in raw_dir.glob("*.html")) if raw_dir else []
    print(f"① 原始 sheet 文件 {len(files)} 个（{raw_dir.name if raw_dir else '?'}）")

    data = json.loads((statpages.STAT_DIR / f"{key}.json").read_text(encoding="utf-8"))
    sheets = data["sheets"]
    with_tbl = [s for s in sheets if s["tables"]]
    raw_only = [s for s in sheets if not s["tables"]]
    print(f"② JSON 里 sheet {len(sheets)} 个：有表数据 {len(with_tbl)} ✓ / 只有原始明细 {len(raw_only)} ✗")
    print(f"   有表数据的 sheet：")
    for s in with_tbl:
        cells = sum(t["nrows"] * t["ncols"] for t in s["tables"])
        print(f"      {s['name']:<46} 表{len(s['tables'])} 约{cells} 格")
    print(f"   只有原始明细的 sheet（解析期被大表闸门挡下 ✗）：")
    for s in raw_only:
        n = len(s.get("rawTables") or [])
        print(f"      {s['name']:<46} 明细{n} 张")

    # ③ 页面实际会渲染哪些
    page = next(p for p in statpages.PAGES if p.get("package") == key)
    picked = statpages._pick_sheets(data, page.get("sheets") or [])
    print(f"③ 页面定义里写死的 sheet 名 {len(page.get('sheets') or [])} 个 → 实际命中 {len(picked)} 个")
    hit = {s["name"] for s in picked}
    miss = [s["name"] for s in with_tbl if s["name"] not in hit]
    print(f"   没被渲染的有数据的 sheet：{miss if miss else '（无）'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
