#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性修复 list-ssr 译文文件的列错位：Wiki 在「攻撃力」与「魔法力」之间新增了
「防御力」列，JA 源已更新但手工译文文件缺这一列，导致 [N] 从 17 起整体右移一格。
本脚本在 [16] 攻击力 后插入 [17] 防御力，并把所有 >=17 的编号顺移 +1。
（仅用于 list-ssr；list-sr / list-r 已正确包含 防御力，不受影响。）
"""
import re
from pathlib import Path

P = Path("tools/_translated_texts/list-ssr.txt")
ENTRY = re.compile(r"^\[(\d+)\]\s?(.*)$")

lines = P.read_text(encoding="utf-8").split("\n")
out = []
for line in lines:
    m = ENTRY.match(line)
    if not m:
        out.append(line)
        continue
    n = int(m.group(1))
    text = m.group(2)
    if n < 16:
        out.append(f"[{n}] {text}")
    elif n == 16:
        out.append(f"[16] {text}")   # 攻击力
        out.append("[17] 防御力")     # 补回缺失列
    else:  # n >= 17
        out.append(f"[{n + 1}] {text}")

P.write_text("\n".join(out), encoding="utf-8")
print("repaired list-ssr.txt")
