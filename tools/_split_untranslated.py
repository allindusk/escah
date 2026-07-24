#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 _untranslated.txt 按字符数均匀拆分为 20 个文件 → tools/_untranslated/。"""
from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "_untranslated.txt"
OUT_DIR = ROOT / "tools" / "_untranslated"
N_PARTS = 20

PROMPT = """请将下文中的日文翻译为简体中文。
规则：
1. 数字、英文缩写（SSR/SR/R/CV/NPC等）保持不变。
2. 专用名：角色名、技能名、装备名保留日文不翻译。
3. 与中文不冲突的汉字词可直接沿用。
4. 术语统一：キャラ→角色、スタミナ→体力、ガチャ→扭蛋、レイド→讨伐战、バフ→增益、デバフ→减益、必殺技→必杀技、固有効果→固有效果、限界突破→界限突破、覚醒→觉醒。
5. 语气简洁准确，与游戏Wiki一致。
输出：只输出译文，每段一行，保持序号和顺序不变。

"""


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 找正文起始（跳过文件头统计信息）
    start = 0
    for i, line in enumerate(lines):
        if line == "=== annihilation":
            start = i
            break
    body = lines[start:]

    # 收集所有 [N] 段的行号及字符数
    seg_starts: list[int] = []
    seg_chars: list[int] = []
    for i, line in enumerate(body):
        if re.match(r"^\[\d+\]", line):
            seg_starts.append(i)
            seg_chars.append(len(line) + 1)  # +1 for newline

    total_chars = sum(seg_chars)
    target = total_chars / N_PARTS
    print(f"总计 {len(seg_starts)} 段, {total_chars:,} 字符, 每目标 ~{target:.0f} 字符")

    # 按字符数分配段到各文件
    boundaries = [0]
    acc = 0
    for i, ch in enumerate(seg_chars):
        acc += ch
        if acc >= target and len(boundaries) < N_PARTS:
            boundaries.append(i + 1)
            acc = 0
    boundaries.append(len(seg_starts))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for fi in range(N_PARTS):
        s = seg_starts[boundaries[fi]]
        e = seg_starts[boundaries[fi + 1] - 1] + 1
        if fi == N_PARTS - 1:
            e = len(body)

        part = body[s:e]
        seg_count = sum(1 for line in part if re.match(r"^\[\d+\]", line))
        char_count = sum(len(l) + 1 for l in part)

        filename = f"{fi+1:03d}.txt"
        filepath = OUT_DIR / filename

        # 提取页面名
        pages = sorted(set(
            m.group(1) for line in part if (m := re.search(r"^=== (.+)$", line))
        ))

        content = f"=== 第 {fi+1}/{N_PARTS} 部分 ===\n" + PROMPT
        if pages:
            content += f"包含页面：{'、'.join(pages)}\n"
        content += f"{'='*60}\n"
        content += "\n".join(part)
        if not content.endswith("\n"):
            content += "\n"

        filepath.write_text(content, encoding="utf-8")
        print(f"  {filename}: {char_count:>8,} 字符, {seg_count:>4} 段, {pages[0] if pages else '?'}…")

    print(f"\n完成！{N_PARTS} 个文件 → {OUT_DIR}")


if __name__ == "__main__":
    main()
