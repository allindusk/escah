#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取所有未译日文文本片段 → _untranslated.txt（可发给豆包批量翻译）

逻辑：凡在 data/parsed/zh/ 文件中仍含平假名/片假名的标签间纯文本=待译内容。
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZH_DIR = ROOT / "data" / "parsed" / "zh"
OUT = ROOT / "tools" / "_untranslated.txt"

HAS_KANA = re.compile(r"[\u3040-\u309f\u30a0-\u30ffー]")

# 如果一行全部由下列字符组成，则视为纯专名保留项，跳过
SKIP_PURE_TERM = re.compile(
    r"^[\u3040-\u309f\u30a0-\u30ffー〜A-Za-z・/・\s\-×()（）【】「」『』]+$"
)


def strip_and_split(html: str) -> list[str]:
    """去标签后按句号/换行分割为合理片段。"""
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"&[a-z]+;", "", text)       # 去 HTML 实体
    text = re.sub(r"\s+", "", text)            # 去空白
    segs = re.split(r"[。\n]+", text)
    return [s.strip() for s in segs if s.strip()]


def main() -> None:
    total_fragments = 0
    total_chars = 0
    lines: list[str] = []

    for f in sorted(ZH_DIR.rglob("*.html")):
        rel = f.relative_to(ZH_DIR)
        slug = str(rel.with_suffix("")).replace("\\", "/")
        html = f.read_text(encoding="utf-8")
        segs = strip_and_split(html)

        untranslated = []
        for s in segs:
            if len(s) < 4:
                continue
            if not HAS_KANA.search(s):
                continue
            if SKIP_PURE_TERM.match(s):
                continue
            untranslated.append(s)

        if not untranslated:
            continue

        lines.append(f"\n{'='*60}")
        lines.append(f"=== {slug}")
        lines.append(f"{'='*60}")
        for i, s in enumerate(untranslated, 1):
            lines.append(f"[{i}] {s}")
            total_fragments += 1
            total_chars += len(s)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"=== 超昂大戦 WIKI 未译日文文本 ===\n"
        f"总计 {total_fragments} 段，{total_chars} 字符\n"
        f"按页分组（角色页用 characters/xxx 表示）\n"
        f"{'='*60}\n"
    )
    OUT.write_text(header + "\n".join(lines), encoding="utf-8")
    print(f"已导出 {total_fragments} 段，{total_chars} 字符 → {OUT}")
    print(f"文件大小: {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
