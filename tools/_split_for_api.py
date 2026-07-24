#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按页面拆分 _for_api.txt → 多个 batch 文件，每页完整不跨 batch。

拆分依据：
- 每个页面的所有段落留在同一 batch 内（不跨文件）
- 每个 batch 约 3000~5000 段（可控）
- 每个 batch 头部自动添加翻译 prompt
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "_for_api.txt"
OUT_DIR = ROOT / "tools" / "_api_batches"

# 每 batch 的段落数目标
TARGET_SEGS_PER_BATCH = 4000

# 翻译 prompt
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
    if not SRC.exists():
        print(f"请先运行 tools/_export_for_api.py 生成 {SRC}", file=sys.stderr)
        sys.exit(1)

    text = SRC.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 解析为 [(page_name, start_line, end_line, segments)], segments = [(seq, text)]
    page_data: list[tuple[str, int, list[tuple[int, str]]]] = []
    current_page: str | None = None
    current_start = 0
    current_segs: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        if line.startswith("=== ") and not line.startswith("=== 超昂"):
            # 跳过纯分隔线 "======================"
            if line.strip("=") == "":
                continue
            if current_page and current_segs:
                page_data.append((current_page, current_start, current_segs))
            # 提取页面名：格式为 "=== slug"
            current_page = line[4:].strip()
            current_start = i
            current_segs = []
        else:
            m = re.match(r"^\[(\d+)\]\s(.+)$", line)
            if m:
                current_segs.append((int(m.group(1)), m.group(2)))

    if current_page and current_segs:
        page_data.append((current_page, current_start, current_segs))

    print(f"共 {len(page_data)} 个页面, {sum(len(s) for _, _, s in page_data)} 段", file=sys.stderr)

    # 按页面分组分配 batch
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    batches: list[list[tuple[str, list[tuple[int, str]]]]] = [[]]
    batch_seg_count = 0

    for page_name, start, segs in page_data:
        if batch_seg_count + len(segs) > TARGET_SEGS_PER_BATCH and batches[-1]:
            batches.append([])
            batch_seg_count = 0
        batches[-1].append((page_name, segs))
        batch_seg_count += len(segs)

    print(f"拆分为 {len(batches)} 个 batch", file=sys.stderr)

    # 输出
    total_pages = 0
    total_segs = 0
    for bi, batch in enumerate(batches):
        # 收集页面名列表
        page_names = [p[0] for p in batch]
        # 累积的序号偏移
        offset = 0
        seg_count = sum(len(s) for _, s in batch)

        filename = f"{bi+1:03d}.txt"
        filepath = OUT_DIR / filename

        content = f"=== Batch {bi+1}/{len(batches)} ===\n"
        content += PROMPT
        content += f"包含页面：{'、'.join(page_names)}\n"
        content += f"{'='*60}\n"

        for page_name, segs in batch:
            content += f"\n--- {page_name} ---\n"
            for seq, seg_text in segs:
                content += f"[{seq}] {seg_text}\n"

        filepath.write_text(content, encoding="utf-8")
        size_kb = filepath.stat().st_size / 1024
        total_pages += len(page_names)
        total_segs += seg_count
        print(f"  {filename}: {len(page_names)} 页, {seg_count} 段, {size_kb:.0f} KB", file=sys.stderr)

    print(f"\n完成！{len(batches)} 个 batch → {OUT_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
