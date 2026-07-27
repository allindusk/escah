#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 skill_unique_effects 译文重复/header 不一致，并按 JA 文本匹配覆盖回填 i18n。

步骤：
 1) 读源(日文)与译文(中文)，按段 label 解析；
 2) 规范化 header（去掉可选 `# ` 前缀 + 多余空白），同一 label 多次出现时保留最后一次（最完整）块 —— 修复 DG 双 header 与 IU 重复翻译；
 3) 把修复后的译文写回原文件（原地覆盖，已先备份到 recycle_bin）；
 4) 按 label→slug（源 # MAP）构建 {_norm(ja): zh} page_map，覆盖写回 369 角色页 i18n（现有为机翻，用户精翻应覆盖）。
"""
import re, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from escah_pipeline import i18n as I  # noqa: E402

SRC = ROOT / "tools" / "_translated_texts" / "skill_unique_effects_20260727.txt"
TR = ROOT / "tools" / "_translated_texts" / "skill_unique_effects_20260727_translated.txt"

SEP_RE = re.compile(r"^#?\s*===\s*([A-Za-z]+)\s*===\s*$")
MAP_RE = re.compile(r"^#\s*MAP\s+(.*)$", re.M)
ENT_RE = re.compile(r"^\[(\d+)\]\s*(.*)$", re.M)


def parse_blocks(text):
    """按 header 切块 → [(label, [raw_lines_after_header...])]，last-wins 聚合。"""
    blocks = {}
    order = []
    cur_label = None
    cur_lines = None
    for line in text.splitlines():
        m = SEP_RE.match(line)
        if m:
            if cur_label is not None:
                blocks[cur_label] = cur_lines
            cur_label = m.group(1)
            if cur_label not in blocks:
                order.append(cur_label)
            cur_lines = []
            continue
        if cur_label is not None:
            cur_lines.append(line)
    if cur_label is not None:
        blocks[cur_label] = cur_lines
    return order, blocks


def parse_entries(block_lines):
    out = []
    for ln in block_lines:
        m = ENT_RE.match(ln.strip())
        if m:
            out.append((int(m.group(1)), m.group(2).strip()))
    return out


def rebuild_file(order, blocks, out_path):
    """规范 header 为 `===X===`，按 order 逐段写出（blocks 已 last-wins）。"""
    lines = []
    for label in order:
        lines.append(f"==={label}===")
        for ln in blocks[label]:
            if ln.strip():
                lines.append(ln)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_overwrite(slug, page_map):
    """覆盖匹配条目（key/block 均可），返回 (filled, already)。"""
    e = I.load_entries(slug)
    keys = I._keys_of(e)
    blks = I._blocks_of(e)
    kmap, bmap = {}, {}
    for k, v in keys.items():
        kmap.setdefault(I._norm(v.get("ja", "")), []).append(k)
    for k, v in blks.items():
        bmap.setdefault(I._norm(v.get("ja", "")), []).append(k)
    filled = already = 0
    for nj, zh in page_map.items():
        if nj in kmap:
            for k in kmap[nj]:
                if keys[k].get("zh") != zh:
                    keys[k]["zh"] = zh
                    filled += 1
                else:
                    already += 1
        if nj in bmap:
            for k in bmap[nj]:
                if blks[k].get("zh") != zh:
                    blks[k]["zh"] = zh
                    filled += 1
                else:
                    already += 1
    if filled:
        I._save_entries(slug, e)
    return filled, already


def main():
    src_text = SRC.read_text(encoding="utf-8", errors="replace")
    tr_text = TR.read_text(encoding="utf-8", errors="replace")

    src_map = I._parse_map(src_text)
    tr_order, tr_blocks = parse_blocks(tr_text)
    src_order, src_blocks = parse_blocks(src_text)

    # 1) 修复译文文件
    rebuild_file(tr_order, tr_blocks, TR)
    tr_order, tr_blocks = parse_blocks(TR.read_text(encoding="utf-8"))
    assert len(tr_order) == len(src_order), \
        f"修复后段数 {len(tr_order)} != 源 {len(src_order)}"
    print(f"修复后译文段数={len(tr_order)}（源={len(src_order)}，# MAP={len(src_map)}）")

    # 2) 覆盖回填
    total_filled = total_already = 0
    skipped = []
    nomatch = 0
    for label in tr_order:
        slug = src_map.get(label)
        if not slug or not I.has_i18n(slug):
            skipped.append(label)
            continue
        src_entries = {n: t for n, t in parse_entries(src_blocks[label])}
        tr_entries = {n: t for n, t in parse_entries(tr_blocks[label])}
        page_map = {}
        for n, ja in src_entries.items():
            zh = tr_entries.get(n)
            if not zh or not ja:
                continue
            if zh == I._norm(ja) and I._KANA_RE.search(zh):
                continue  # 中日同形仍含假名 → 未译
            page_map[I._norm(ja)] = zh
        if not page_map:
            continue
        # 统计未匹配数（页内已匹配条目 vs 页内应有条目）
        filled, already = apply_overwrite(slug, page_map)
        total_filled += filled
        total_already += already
        if filled == 0 and already == 0:
            nomatch += 1

    print(f"覆盖回填：新增/更新 {total_filled} 条，已相同(未改) {total_already} 条")
    if skipped:
        print(f"跳过(no slug/i18n)：{skipped}")
    if nomatch:
        print(f"未匹配页(0命中)数：{nomatch}")


if __name__ == "__main__":
    main()
