#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出翻译稿 docx 中 [N] 序号被写成【N】或挪到句中的具体位置。"""
import re
import docx
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
SRC_DIR = TOOLS / "_texts_for_translation" / "characters"
MERGED_DIR = TOOLS / "_merged_chars"
MANIFEST = MERGED_DIR / "manifest.txt"
DOCX = MERGED_DIR / "characters_merged_translated.docx"

_ENTRY = re.compile(r"^\[(\d+)\]")
_MARK = re.compile(r"^A\d+$")


def src_map(path):
    m = {}
    cur = None
    for line in path.read_text(encoding="utf-8").splitlines():
        mm = _ENTRY.match(line)
        if mm:
            cur = int(mm.group(1))
            m[cur] = line
        elif cur is not None and line.strip():
            m[cur] += " / " + line
    return m


def main():
    name_map = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if "<=>" in line:
            k, n = line.split("<=>", 1)
            name_map[k.strip()] = n.strip()

    doc = docx.Document(str(DOCX))
    paras = [p.text for p in doc.paragraphs]

    files = {}
    cur = None
    for i, line in enumerate(paras):
        s = line.strip()
        if _MARK.match(s):
            cur = s
            files[cur] = []
        elif cur is not None:
            files[cur].append((i + 1, line))  # (Word 行号, 文本)

    print("翻译稿中 [N] 格式异常的具体位置（共 14 处）：\n")
    n = 0
    for akey in [f"A{i:03d}" for i in range(1, 370)]:
        fname = name_map.get(akey)
        if not fname:
            continue
        sm = src_map(SRC_DIR / fname)
        for (lno, text) in files.get(akey, []):
            if text.strip() and not _ENTRY.match(text):  # 不以 [N] 开头
                n += 1
                m = re.search(r"\d+", text)
                idx = m.group(0) if m else "?"
                jp = sm.get(int(idx), "") if idx.isdigit() else ""
                print(f"{n:>2}. 文件：{fname}")
                print(f"     Word 第 {lno} 行，应为 [{idx}]")
                print(f"     原日文：{jp[:90]}")
                print(f"     译文写法：{text[:90]}")
                print()


if __name__ == "__main__":
    main()
