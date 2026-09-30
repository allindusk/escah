# -*- coding: utf-8 -*-
"""逐条精校导出（v2）：**按原文去重**，一行一条，标出分歧。

为什么改（2026-09-27，连续精校 6 页）：
  · 角色页里同一段原文会以 `keyN` 与 `blkN#i` **两套节点**并存，逐条导出会重复出现
    （例如 `出撃完了時、` 一页出现 5 次）→ 人工审两遍纯属浪费；
  · 与 `apply_ja_map.py` 配套：审完只写 `原文<TAB>译文` 的映射，由脚本传播到**所有**同原文节点，
    结构上保证「页内分歧归零」✓。

用法：
  python tools/_dev/dump_page_for_review.py <slug> --review
      → 输出 `<出现次数>x 原文 ⇒ 译文`，多译时用 ‖ 分隔并标 ⚠
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline.i18n import _blocks_of, _keys_of, load_entries  # noqa: E402

BR = "\x01"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \([月火水木金土日]\) \d{2}:\d{2}:\d{2}$")


def all_pairs(slug: str) -> "list[tuple[str, str, str]]":
    """[(id, ja, zh)]，含全部 key 与块内段落。"""
    en = load_entries(slug)
    out: "list[tuple[str, str, str]]" = []
    for tid, ent in _keys_of(en).items():
        out.append((tid, ent.get("ja") or "", ent.get("zh") or ""))
    for bid, blk in _blocks_of(en).items():
        ja_segs = (blk.get("ja") or "").split(BR)
        zh_segs = (blk.get("zh") or "").split(BR)
        for i, j in enumerate(ja_segs, 1):
            out.append((f"{bid}#{i}", j, zh_segs[i - 1] if i - 1 < len(zh_segs) else ""))
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    slug = sys.argv[1]

    if "--review" in sys.argv:
        pairs = all_pairs(slug)
        by_ja: "dict[str, list[str]]" = collections.defaultdict(list)
        cnt: "collections.Counter[str]" = collections.Counter()
        for _tid, ja, zh in pairs:
            j = ja.strip()
            if not j:
                continue
            cnt[j] += 1
            z = zh.strip()
            if z not in by_ja[j]:
                by_ja[j].append(z)
        print(f"### {slug}  节点 {len(pairs)} 条 → 去重原文 {len(by_ja)} 种")
        for j in sorted(by_ja, key=lambda x: (DATE_RE.match(x) is not None, x)):
            zs = by_ja[j]
            mark = "  ⚠分歧" if len(zs) > 1 else ""
            shown = " ‖ ".join(z if z else "**空译**" for z in zs)
            print(f"{cnt[j]}x {j} ⇒ {shown}{mark}")
        return 0

    # 兼容旧用法：全量明细（含 id），需要时用
    zh_only = "--zh-only" in sys.argv
    n = 0
    print(f"=== {slug} ===")
    for tid, ja, zh in all_pairs(slug):
        if not ja.strip() and not zh.strip():
            continue
        n += 1
        print(f"[{tid}] {ja.strip()}")
        if not zh_only:
            print(f"    ⇒ {zh.strip()}")
    print(f"\n# 共 {n} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
