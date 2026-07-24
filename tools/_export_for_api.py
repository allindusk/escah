#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
段落级导出 — 将未译日文按段落（而非句子）整理，供 LLM API 翻译。

核心思路：
- 同时读取 data/parsed/ja/（日文原文）和 data/parsed/zh/（词典已部分翻译）
- 按相同块级标签边界切割，ja→zh 块一一对齐
- 当 zh 块仍有假名残留（词典未完全覆盖）→ 输出对应的 ja 纯日文原文
- 每段为一个完整段落/表格格，不按「。」拆句
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JA_DIR = ROOT / "data" / "parsed" / "ja"
ZH_DIR = ROOT / "data" / "parsed" / "zh"
ZH_PATCH_SRC = ROOT / "tools" / "zh_patch.py"

HAS_KANA = re.compile(r"[\u3040-\u309f\u30a0-\u30ffー]")


# ====== 解析 zh_patch.py 的 JA2ZH 字典 key ======

def parse_ja2zh_keys(py_src: str) -> set[str]:
    """从 zh_patch.py 的 JA2ZH 字典提取所有 key（AnnAssign 或 Assign）。"""
    try:
        tree = ast.parse(py_src, filename="zh_patch.py")
    except SyntaxError as e:
        print(f"  AST 解析失败，用正则回退: {e}", file=sys.stderr)
        return set(re.findall(r"^\s+'([^']+)':\s*'", py_src, re.MULTILINE))

    keys: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            t = node.target
            if isinstance(t, ast.Name) and t.id == "JA2ZH" and isinstance(node.value, ast.Dict):
                for k in node.value.keys:
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        keys.add(k.value)
                break
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "JA2ZH":
                    if isinstance(node.value, ast.Dict):
                        for k in node.value.keys:
                            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                                keys.add(k.value)
                        break
    if not keys:
        keys = set(re.findall(r"^\s+'([^']+)':\s*'", py_src, re.MULTILINE))
    return keys


# ====== 段落提取（同时处理 ja 和 zh 对齐）======

def extract_paragraphs(html: str) -> list[str]:
    """按块级标签提取段落，每个块为一段（不拆分句子）。"""
    html = re.sub(r"<br\s*/?>", "\n", html)
    block_re = re.compile(
        r"(</?(?:p|div|li|td|th|h[1-6]|ul|ol|table|tr|section|blockquote)\b[^>]*>)"
    )
    html = block_re.sub(r"\n\1\n", html)

    lines = html.split("\n")
    blocks = []
    current_part = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_part:
                blocks.append("".join(current_part))
                current_part = []
            continue
        if re.match(r"^</?(?:p|div|li|td|th|h[1-6]|ul|ol|table|tr|section|blockquote)\b", stripped):
            if current_part:
                blocks.append("".join(current_part))
                current_part = []
            continue
        current_part.append(stripped)

    if current_part:
        blocks.append("".join(current_part))

    result = []
    for b in blocks:
        b = re.sub(r"<[^>]+>", "", b)
        b = re.sub(r"&[a-z]+;", "", b)
        b = re.sub(r"\s+", "", b)
        b = b.strip()
        if b:
            result.append(b)
    return result


def main() -> None:
    # 1. 加载已有字典 key
    print("解析 zh_patch.py 已有词表...", file=sys.stderr)
    patch_src = ZH_PATCH_SRC.read_text(encoding="utf-8")
    existing_keys = parse_ja2zh_keys(patch_src)
    print(f"  JA2ZH 已有 {len(existing_keys)} 个 key", file=sys.stderr)

    # 2. 遍历 JA+ZH 页面
    total_ja_segs = 0
    total_ja_new = 0
    pages_new = 0
    output_lines: list[str] = []

    for f in sorted(JA_DIR.rglob("*.html")):
        rel = f.relative_to(JA_DIR)
        slug = str(rel.with_suffix("")).replace("\\", "/")

        # 读取 ja（原始日文）和 zh（词典已部分翻译）
        ja_html = f.read_text(encoding="utf-8")
        zh_file = ZH_DIR / rel
        if not zh_file.exists():
            continue  # zh 文件不存在，跳过
        zh_html = zh_file.read_text(encoding="utf-8")

        ja_blocks = extract_paragraphs(ja_html)
        zh_blocks = extract_paragraphs(zh_html)

        # 按索引对齐，找 zh 仍有假名的块
        pairs: list[tuple[str, str]] = []  # (ja原文, zh词典后)
        for idx in range(min(len(ja_blocks), len(zh_blocks))):
            ja_text = ja_blocks[idx]
            zh_text = zh_blocks[idx]

            # zh 无假名 → 已完全翻译，跳过
            if not HAS_KANA.search(zh_text):
                continue

            # ja 文本整体已在字典中 → 跳过
            if ja_text in existing_keys:
                continue

            pairs.append((ja_text, zh_text))

        if not pairs:
            continue

        # 输出
        output_lines.append(f"\n{'='*60}")
        output_lines.append(f"=== {slug}")
        output_lines.append(f"{'='*60}")

        total_ja_segs += len(ja_blocks)
        total_ja_new += len(pairs)
        pages_new += 1

        for i, (ja_text, zh_text) in enumerate(pairs, 1):
            output_lines.append(f"[{i}] {ja_text}")

        print(f"  {slug}: {len(ja_blocks)} 块 → {len(pairs)} 待译", file=sys.stderr)

    # 3. 写出
    out_path = ROOT / "tools" / "_for_api.txt"
    header = (
        f"=== 超昂大戦 WIKI 未译日文文本（段落版·纯日文原文）===\n"
        f"总计 {total_ja_new} 段（来自 {pages_new} 页面, 全站 {total_ja_segs} 块）\n"
        f"每段为一个完整段落/表格格/列表项，不拆分句子\n"
        f"来源：data/parsed/ja/ 纯日文原文（非 zh 混合残片）\n"
        f"已排除 JA2ZH 精确匹配词条\n"
        f"{'='*60}\n"
    )
    out_path.write_text(header + "\n".join(output_lines), encoding="utf-8")
    print(f"\n已导出 {total_ja_new} 段纯日文 → {out_path}", file=sys.stderr)
    print(f"文件大小: {out_path.stat().st_size / 1024:.0f} KB", file=sys.stderr)
    print(f"全站块数: {total_ja_segs}", file=sys.stderr)


if __name__ == "__main__":
    main()
