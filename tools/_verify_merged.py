#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""终检：_translated_texts/characters 的 [N] 序号是否覆盖日文源文件全部条目。"""
import re
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
SRC = TOOLS / "_texts_for_translation" / "characters"
DST = TOOLS / "_translated_texts" / "characters"
_ENTRY = re.compile(r"^\[(\d+)\]")


def idx_of(path):
    s = set()
    for ln in path.read_text(encoding="utf-8").splitlines():
        m = _ENTRY.match(ln)
        if m:
            s.add(int(m.group(1)))
    return s


def main():
    files = sorted(SRC.glob("*.txt"))
    bad = 0
    empty = 0
    for f in files:
        d = DST / f.name
        if not d.is_file() or not d.read_text(encoding="utf-8").strip():
            empty += 1
            print(f"[ERR] 缺失/空: {f.name}")
            bad += 1
            continue
        src = idx_of(f)
        dst = idx_of(d)
        if src != dst:
            miss = sorted(src - dst)
            extra = sorted(dst - src)
            msg = []
            if miss:
                msg.append(f"缺 {miss[:15]}{'...' if len(miss) > 15 else ''}")
            if extra:
                msg.append(f"多 {extra[:15]}{'...' if len(extra) > 15 else ''}")
            print(f"[WARN] {f.name}: {'; '.join(msg)}")
            bad += 1
    print(f"\n检查 {len(files)} 个文件；问题 {bad}；空/缺 {empty}")
    print("结论：", "全部对齐 ✅" if bad == 0 else "仍有问题，见上")


if __name__ == "__main__":
    main()
