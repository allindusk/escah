# -*- coding: utf-8 -*-
"""诊断：**同一日文原文存在多种中文译文**（译法分歧）—— 全站扫描。

为什么需要它（2026-09-27，用户报告 raid-buff-debuff 的目录与正文标题不一致）：
  · 根因：同一个日文标题在真值里存在**多个独立 id**（正文标题一个、目录/表头链接标签一个），
    它们各自经过独立的机翻 → 译文分歧；后来手工精翻只覆盖了其中一个 ✗
    （实测 key15 =「体力回复・体力减少停止角色 一览」✓ 而 key571/572 =「抗性/耐力恢复/抗性/耐力
    降低停止角颜色列表」✗✗，三者的 ja 逐字相同）。
  · 更根本的盲区：`i18n extract` 的队列由「残留闸门」驱动 —— 它只判「**译了吗**」✗，
    不判「**译对了吗**」。像「角颜色列表」这种**通篇中文但完全错**的机翻，既无假名也无日文专用
    汉字，闸门直接判"已译"✓ → 永不入队 ✗ → 永远不会被精翻碰到 ✗✗。这就是"我叫你精翻过，为什么
    还这么差"的机制性原因。

本脚本给出两件事：
  ① **分歧清单**：同一 ja 对应 ≥2 种不同 zh 的所有条目（含涉及的页与 id），并按
     "是否疑似标题类"、"是否含明显乱译标记"排序，便于优先修。
  ② **乱译标记统计**：`角颜色/角的颜色`（把「キャラ」译成"角"✗）、`低血糖`、标题却以「。」结尾 ✗
     等高质量证据的模式在全站各有多少条。

用法：
  python tools/_dev/diag_translation_divergence.py                # 汇总
  python tools/_dev/diag_translation_divergence.py --dump 40      # 打印前 40 条分歧明细
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline import config  # noqa: E402
from escah_pipeline.i18n import _blocks_of, _keys_of, has_i18n, load_entries  # noqa: E402
from escah_pipeline.registry import load_registry  # noqa: E402

BR = "\x01"

# 明显乱译标记（高精度）：左边是模式，右边是人读得懂的名字
SUSPECT = [
    ("角颜色", "「キャラ」→角（「颜色」）"),
    ("角的颜色", "「キャラ」→角的颜色"),
    ("低血糖", "低血糖（罕见误译）"),
    ("眩光", "眩光（疑似误译）"),
    ("按能力排列的角", "「キャラ」→角"),
]


def collect(slug: str) -> "list[tuple[str, str, str]]":
    """取一页的全部 (id, ja, zh)。"""
    en = load_entries(slug)
    items: "list[tuple[str, str, str]]" = []
    for tid, ent in _keys_of(en).items():
        items.append((tid, ent.get("ja") or "", ent.get("zh") or ""))
    for bid, blk in _blocks_of(en).items():
        ja_segs = (blk.get("ja") or "").split(BR)
        zh_segs = (blk.get("zh") or "").split(BR)
        for i, j in enumerate(ja_segs, 1):
            z = zh_segs[i - 1] if i - 1 < len(zh_segs) else ""
            items.append((f"{bid}#{i}", j, z))
    return items


def main() -> int:
    # ---- 单页视图：同一页内「同一原文多种译文」= 几乎必是缺陷（用户报的就是这类）----
    if "--page" in sys.argv:
        i = sys.argv.index("--page")
        slug = sys.argv[i + 1]
        by_ja: "dict[str, list[tuple[str, str]]]" = collections.defaultdict(list)
        for tid, ja, zh in collect(slug):
            if ja.strip() and zh.strip():
                by_ja[ja.strip()].append((tid, zh.strip()))
        div = {ja: v for ja, v in by_ja.items() if len({z for _t, z in v}) >= 2}
        print(f"===== {slug}：页内分歧 {len(div)} 组")
        for ja, v in div.items():
            print(f"\n   ja: {ja[:86]!r}")
            for tid, zh in v:
                print(f"        [{tid}] → {zh[:76]!r}")
        print("\n===== 该页乱译标记命中")
        for tid, ja, zh in collect(slug):
            for pat, name in SUSPECT:
                if pat in zh:
                    print(f"   [{tid}] {name}\n        ja: {ja.strip()[:80]!r}\n"
                          f"        zh: {zh.strip()[:80]!r}")
                    break
        return 0

    # ---- 乱译明细（带原文，便于直接改）----
    if "--suspect" in sys.argv:
        print("===== 乱译标记明细（含原文）")
        for e in load_registry():
            slug = e["slug"]
            if not has_i18n(slug):
                continue
            try:
                items = collect(slug)
            except Exception:                 # noqa: BLE001
                continue
            for tid, ja, zh in items:
                for pat, name in SUSPECT:
                    if pat in zh:
                        print(f"   {slug} [{tid}] {name}")
                        print(f"        ja: {ja.strip()[:88]!r}")
                        print(f"        zh: {zh.strip()[:88]!r}")
                        break
        return 0

    dump_n = 0
    if "--dump" in sys.argv:
        i = sys.argv.index("--dump")
        dump_n = int(sys.argv[i + 1]) if i + 1 < len(sys.argv) else 20

    by_ja: "dict[str, list[tuple[str, str, str]]]" = collections.defaultdict(list)
    suspect_stat: "collections.Counter" = collections.Counter()
    suspect_examples: "dict[str, list[str]]" = collections.defaultdict(list)
    n_pages = n_entries = 0

    for e in load_registry():
        slug = e["slug"]
        if not has_i18n(slug):
            continue
        try:
            en = load_entries(slug)
        except Exception:                     # noqa: BLE001
            continue
        n_pages += 1
        items: "list[tuple[str, str, str]]" = []
        for tid, ent in _keys_of(en).items():
            items.append((tid, ent.get("ja") or "", ent.get("zh") or ""))
        for bid, blk in _blocks_of(en).items():
            ja_segs = (blk.get("ja") or "").split(BR)
            zh_segs = (blk.get("zh") or "").split(BR)
            for i, j in enumerate(ja_segs, 1):
                z = zh_segs[i - 1] if i - 1 < len(zh_segs) else ""
                items.append((f"{bid}#{i}", j, z))
        for tid, ja, zh in items:
            n_entries += 1
            ja_s = ja.strip()
            if ja_s and zh.strip():
                by_ja[ja_s].append((slug, tid, zh.strip()))
            for pat, name in SUSPECT:
                if pat in zh:
                    suspect_stat[name] += 1
                    if len(suspect_examples[pat]) < 4:
                        suspect_examples[pat].append(f"{slug} [{tid}] {zh.strip()[:56]}")
                    break

    diverged = {ja: v for ja, v in by_ja.items() if len({z for _s, _t, z in v}) >= 2}
    print(f"扫描：{n_pages} 页 / {n_entries} 条")
    print(f"① **同一原文多种译文**（分歧）：{len(diverged)} 组"
          f"，涉及条目 {sum(len(v) for v in diverged.values())} 条")
    heading_ish = {ja: v for ja, v in diverged.items()
                   if "一覧" in ja or len(ja) <= 24}
    print(f"   其中标题/短串类（含「一覧」或长度≤24）：{len(heading_ish)} 组")
    print(f"\n② 乱译标记命中：{sum(suspect_stat.values())} 条")
    for name, n in suspect_stat.most_common():
        print(f"   {n:4d}  {name}")
        for ex in suspect_examples[[p for p, nm in SUSPECT if nm == name][0]]:
            print(f"         {ex}")

    if dump_n:
        print(f"\n③ 分歧明细（前 {dump_n} 组，按涉及条目数降序）")
        for ja, v in sorted(diverged.items(), key=lambda x: -len(x[1]))[:dump_n]:
            print(f"\n   ja: {ja[:88]!r}")
            for slug, tid, zh in v:
                print(f"        {slug} [{tid}] → {zh[:70]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
