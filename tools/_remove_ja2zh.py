#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性脚本：将 zh_patch.py 里硬编码的 JA2ZH 散文词典整体移除（2026-07-26）。

- 用 AST 精确定位 JA2ZH 赋值节点（含其起止行），避免误删字典 value 中可能含有的 `}`。
- 原块完整备份到 recycle_bin/tools/zh_patch_ja2zh_removed_20260726.py（遵循"不永久删文件"约定）。
- 在原位置替换为空字典 + 说明注释；后续 _manual_zh.json（用户手工译文）经 merge 载入成为唯一来源。
运行后会自检语法。
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "zh_patch.py"
BACKUP = ROOT / "recycle_bin" / "tools" / "zh_patch_ja2zh_removed_20260726.py"

src_text = SRC.read_text(encoding="utf-8")
tree = ast.parse(src_text)
lines = src_text.splitlines(keepends=True)

target = None
for node in tree.body:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        t = node.targets[0] if isinstance(node, ast.Assign) else node.target
        if isinstance(t, ast.Name) and t.id == "JA2ZH":
            target = node
            break
if target is None:
    print("[ERROR] 未找到顶层 JA2ZH 赋值")
    sys.exit(1)

start = target.lineno           # 1-based
end = target.end_lineno         # 1-based inclusive
print(f"JA2ZH 节点: 行 {start} - {end} (共 {end - start + 1} 行)")

# 1) 备份原始块（完整、原样）
BACKUP.parent.mkdir(parents=True, exist_ok=True)
backup_header = (
    "# ===========================================================================\n"
    "# 备份：原 zh_patch.py 中硬编码的 JA2ZH 散文词典（40,473 条）。\n"
    "# 2026-07-26 由 tools/_remove_ja2zh.py 整体移出活跃代码（散文需上下文翻译，无实用价值）。\n"
    "# 仅作数据存档，不再被任何模块 import。如需恢复可从本文件 / git 历史取回。\n"
    "# ===========================================================================\n\n"
)
BACKUP.write_text(backup_header + "".join(lines[start - 1 : end]), encoding="utf-8")
print(f"[备份] -> {BACKUP}")

# 2) 替换为空字典 + 说明
new_block = (
    "# ---------------------------------------------------------------------------\n"
    "# 日->中 替换词表（手工译文覆盖层）\n"
    "# 2026-07-26：原硬编码 JA2ZH 散文词典（40,473 条）已整体移除——散文需结合上下文\n"
    "#   翻译，硬编码无实用价值。现仅以 tools/_manual_zh.json（用户手工译文）为准，\n"
    "#   经下方 merge 载入；另保留 REGEX_RULES（公式化）+ GENERIC（通用术语）两层。\n"
    "# ---------------------------------------------------------------------------\n"
    "JA2ZH: dict[str, str] = {}\n"
)
new_text = "".join(lines[: start - 1] + [new_block] + lines[end:])
SRC.write_text(new_text, encoding="utf-8")

# 3) 语法自检
try:
    ast.parse(new_text)
    print("[OK] zh_patch.py 语法自检通过")
except SyntaxError as e:  # noqa: BLE001
    print(f"[ERROR] 语法错误: {e}")
    sys.exit(1)

print("[完成] JA2ZH 硬翻译块已移除，手工译文 (_manual_zh.json) 成为唯一来源。")
