# -*- coding: utf-8 -*-
"""从**站内已有的译文**里收割「短原文 → 中文」对照，供统计数据页复用词表。

为什么需要（2026-09-28）：
  统计数据页里有 1160 种未覆盖的单元格文本，绝大多数是**道具名**（如 `仁王納豆`、
  `ヘビースターラーメン`）✗ —— 但站里的道具列表页**早就把它们译成中文了** ✓，
  只是那些译文在 `data/parsed/i18n/*.json` 的 zh 字段里，不在 glossary ✗。
  ⇒ 收割一份短词对照表（`data/statdata/_jalabels.json`，入库 ✓），渲染时直接复用 ✓，
    这样数据页的道具名与站内**保持一致** ✓，且无需人工重译 ✓。

策略：
  · 只收**短文本**（≤30 字 ✓），避免把整句译文带进来 ✗
  · 只收**译文不含假名**的（含假名说明该条未译完 ✗）
  · 同一原文出现多种译文时取**出现次数最多**的 ✓（分歧多数是上下文差异 ✓）
  · 输出入库（`data/statdata/_jalabels.json` 已被 workflow 的 git add 覆盖 ✓）

用法：python tools/_dev/harvest_labels.py [--apply]
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline.i18n import _blocks_of, _keys_of, has_i18n, load_entries  # noqa: E402
from escah_pipeline.registry import load_registry  # noqa: E402

BR = "\x01"
KANA_RE = re.compile(r"[\u3041-\u3096\u30a1-\u30fa\u30fd-\u30ff]")
MAX_LEN = 30
OUT = ROOT / "data" / "statdata" / "_jalabels.json"


def needed_texts() -> "set[str]":
    """`data/statdata/*.json` 里出现的**非数字单元格文本**（= 我们真正要翻的标签）。

    为什么要取交集：不加限制时收割出 50,644 条、4.2MB ✗（整站短词都收进来了 ✗），
    而数据页只用到其中 ~1300 条 ✓。取交集后产物约 50KB ✓，入库无压力 ✓。
    """
    out: "set[str]" = set()
    for p in sorted((ROOT / "data" / "statdata").glob("*.json")):
        if p.name.startswith("_"):
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        for sheet in data["sheets"]:
            out.add(sheet["name"])
            for t in sheet["tables"]:
                for r in (t.get("header") or []) + (t.get("rows") or []):
                    for c in r:
                        txt = (c.get("t") or "").strip()
                        if txt:
                            out.add(txt)
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    want = needed_texts()
    print(f"数据页需要用到的单元格文本：{len(want)} 种（取交集后才入库 ✓）")
    votes: "dict[str, collections.Counter[str]]" = collections.defaultdict(collections.Counter)
    for e in load_registry():
        slug = e["slug"]
        if not has_i18n(slug):
            continue
        try:
            en = load_entries(slug)
        except Exception:  # noqa: BLE001
            continue
        items = []
        for ent in _keys_of(en).values():
            items.append(("k", ent.get("ja") or "", ent.get("zh") or ""))
        for blk in _blocks_of(en).values():
            ja_segs = (blk.get("ja") or "").split(BR)
            zh_segs = (blk.get("zh") or "").split(BR)
            for i, j in enumerate(ja_segs):
                items.append(("b", j, zh_segs[i] if i < len(zh_segs) else ""))
        for _kind, ja, zh in items:
            j, z = ja.strip(), zh.strip()
            if not j or not z or j == z:
                continue
            if j not in want:            # 只收数据页真正用到的标签 ✓（否则 4.2MB ✗）
                continue
            if len(j) > MAX_LEN or len(z) > MAX_LEN * 2:
                continue
            if KANA_RE.search(z):        # 译文还带假名 → 未译完，不收 ✓
                continue
            votes[j][z] += 1

    table = {j: c.most_common(1)[0][0] for j, c in votes.items()}
    conflict = sum(1 for c in votes.values() if len(c) > 1)
    print(f"收割短词对照 {len(table)} 条（其中 {conflict} 条原文有多种译文，已取最高频 ✓）")
    for j in list(table)[:10]:
        print(f"    {j} ⇒ {table[j]}")
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(table, ensure_ascii=False, sort_keys=True),
                       encoding="utf-8", newline="\n")
        print(f"\n写出 {OUT.relative_to(ROOT)}（{OUT.stat().st_size / 1024:.1f} KB）")
    else:
        print("\n（dry-run；加 --apply 写出）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
