# -*- coding: utf-8 -*-
"""把 data/statdata/*.json 的结构压成一份**人可读概览**，用于设计页面：每张表列出
表头与 2 行样例，便于我逐表判断「这张表怎么展示最有用」。

用法：python tools/_dev/dump_statdata.py [包的 key] [页名前缀]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
STAT = ROOT / "data" / "statdata"


def cell_text(c: dict) -> str:
    t = c.get("t", "")
    if c.get("cs"):
        t += f"⟨cs{c['cs']}⟩"
    if c.get("rs"):
        t += f"⟨rs{c['rs']}⟩"
    if c.get("h"):
        t += "⟨h⟩"
    return t


def row_text(row: list[dict]) -> str:
    return " | ".join(cell_text(c) for c in row)


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    name_prefix = sys.argv[2] if len(sys.argv) > 2 else None
    for p in sorted(STAT.glob("*.json")):
        if only and only not in p.name:
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        print("=" * 110)
        print(f"### {data['key']}  ←  {data['dir']}")
        for sheet in data["sheets"]:
            if name_prefix and not sheet["name"].startswith(name_prefix):
                continue
            if not sheet["tables"]:
                raw = sheet.get("rawTables") or []
                print(f"\n  [{sheet['name']}]  （原始明细 {len(raw)} 张，未收录数据）")
                continue
            print(f"\n  [{sheet['name']}]  ({len(sheet['tables'])} 张表)")
            for ti, t in enumerate(sheet["tables"], 1):
                print(f"    表{ti}: {t['nrows']} 行 × {t['ncols']} 列")
                for hr in t["header"]:
                    print(f"      表头: {row_text(hr)}")
                for r in t["rows"][:2]:
                    print(f"      样例: {row_text(r)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
