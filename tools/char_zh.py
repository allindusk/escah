"""角色详情 JSON 补译：用 zh_patch 词表把 tr 单元格的 t 译为 zh 字段。

幂等：每次全量重算 zh；词表增长后重跑即应用新译文。
仅当译文与原文不同（词表命中）时写入 zh；完全未命中的保持无 zh 字段（站点回退显示日文）。
运行：python tools/char_zh.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from zh_patch import patch, residual_kana  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CHAR_DIR = ROOT / "data" / "parsed" / "characters"

# 值为专有人名（声优/画师/本名等）的行表头：按约定保留日文，不算残留
NAME_HEADERS = {"CV", "イラスト", "本名", "名前", "名称", "イラストレーター", "原画"}


def _process_file(f: Path) -> tuple[bool, int, int, dict]:
    """处理单个角色 JSON（可在独立进程内运行，无共享可变状态）。"""
    data = json.loads(f.read_text(encoding="utf-8"))
    changed = False
    cells_set = 0
    cells_clean = 0
    remain_local: dict[str, list] = {}
    for section in data.get("sections", {}).values():
        for row in section.get("rows", []):
            header = next((c.get("t", "") for c in row if c.get("h")), "")
            is_name_row = header in NAME_HEADERS
            for cell in row:
                if not (cell.get("tr") and cell.get("t")):
                    continue
                src = cell["t"]
                zh = patch(src)
                if zh != src:
                    if cell.get("zh") != zh:
                        cell["zh"] = zh
                        changed = True
                    cells_set += 1
                    if residual_kana(zh) == 0:
                        cells_clean += 1
                    elif not (is_name_row and not cell.get("h")):
                        r = remain_local.setdefault(src, [0, zh])
                        r[0] += 1
                        r[1] = zh
                else:
                    if "zh" in cell:  # 词表回退时清掉过期译文
                        del cell["zh"]
                        changed = True
                    if residual_kana(src) == 0:
                        cells_clean += 1  # 纯汉字/ASCII，中日同形，无需译
                    elif not (is_name_row and not cell.get("h")):
                        r = remain_local.setdefault(src, [0, src])
                        r[0] += 1
    if changed:
        f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return changed, cells_set, cells_clean, remain_local


def main() -> int:
    files = sorted(CHAR_DIR.glob("*.json"))
    workers = max(1, min(os.cpu_count() or 4, 16))
    changed_files = 0
    cells_set = 0
    cells_clean = 0
    # 仍含假名的文本：原文 → [出现次数, 当前译文]
    remain: dict[str, list] = {}

    with ProcessPoolExecutor(max_workers=workers) as ex:
        for changed, cs, cc, rloc in ex.map(_process_file, files):
            if changed:
                changed_files += 1
            cells_set += cs
            cells_clean += cc
            for s, v in rloc.items():
                cur = remain.setdefault(s, [0, v[1]])
                cur[0] += v[0]
                cur[1] = v[1]

    print(f"角色 JSON：{len(files)} 个；本次写入变更 {changed_files} 个（进程池 workers={workers}）")
    print(f"tr 单元格：命中词表并写 zh {cells_set}；译净/同形 {cells_clean}")
    print(f"残留唯一文本（含假名、非人名行）{len(remain)} 条")
    top = sorted(remain.items(), key=lambda x: (-x[1][0], -len(x[0])))[:300]
    out = "\n".join(f"{v[0]}\tSRC\t{s}\n\tCUR\t{v[1]}" for s, v in top)
    (ROOT / "tools" / "_char_remain.txt").write_text(out, encoding="utf-8")
    print("残留 Top300（原文+当前译文）已写 tools/_char_remain.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
