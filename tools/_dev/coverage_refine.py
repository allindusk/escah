# -*- coding: utf-8 -*-
"""逐个角色页核对：`tools/_mt_refine/` 留档**覆盖了该页多少条**，差的是哪些。

为什么用这个口径（而不是"有没有留档"）：
  · 页面会**长大**（原站新增内容 → extract 出新条目），而留档是当时的快照；
  · 我以前是按 extract 队列精翻的，队列里的条目 ≠ 页面全部条目
    → 于是出现「有留档、但页里仍有若干条是纯机翻」✗ —— 本脚本就是找出这些缺口。

用法：
  python tools/_dev/coverage_refine.py                 # 汇总（用户点名那批 + 参照页）
  python tools/_dev/coverage_refine.py --page <slug>   # 列出某页未覆盖条目的 id / ja / zh
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline.i18n import _blocks_of, _keys_of, has_i18n, load_entries  # noqa: E402
from escah_pipeline.registry import load_registry  # noqa: E402

BR = "\x01"
ENTRY_RE = re.compile(r"^\[([^\]]+)\]\s?(.*)$")

LISTED = [
    "真夏のエスカ・オニキス",
    "盛夏のエスカレイヤー",
    "真夏のキクリ",
    "エスカ・セブン",
    "バニーガールゲッカ",
    "バトラー・ヘプタスロン",
    "神騎ハウゼル",
    "閃忍ホーネット",
]


def page_ids(slug: str) -> "dict[str, tuple[str, str]]":
    """该页全部条目：id -> (ja, zh)。"""
    out: "dict[str, tuple[str, str]]" = {}
    en = load_entries(slug)
    for tid, ent in _keys_of(en).items():
        out[tid] = (ent.get("ja") or "", ent.get("zh") or "")
    for bid, blk in _blocks_of(en).items():
        ja_segs = (blk.get("ja") or "").split(BR)
        zh_segs = (blk.get("zh") or "").split(BR)
        for i, j in enumerate(ja_segs, 1):
            out[f"{bid}#{i}"] = (j, zh_segs[i - 1] if i - 1 < len(zh_segs) else "")
    return out


def refine_ids(slug: str) -> "set[str]":
    pats = list((ROOT / "tools" / "_mt_refine").glob(f"*{slug.replace('/', '__')}*"))
    if not pats:
        pats = list((ROOT / "tools" / "_mt_refine").glob(f"*{slug.split('/')[-1]}*"))
    ids: "set[str]" = set()
    for p in pats:
        for line in p.read_text(encoding="utf-8").splitlines():
            m = ENTRY_RE.match(line)
            if m:
                ids.add(m.group(1).strip())
    return ids


def main() -> int:
    reg = {e["name"]: e for e in load_registry()}

    if "--page" in sys.argv:
        slug = sys.argv[sys.argv.index("--page") + 1]
        ids = refine_ids(slug)
        page = page_ids(slug)
        missing = [(k, v) for k, v in page.items() if k not in ids]
        print(f"===== {slug}：真值 {len(page)} 条｜留档覆盖 {len(page) - len(missing)} 条"
              f"｜**未覆盖 {len(missing)} 条**")
        for tid, (ja, zh) in missing:
            if not ja.strip():
                continue
            print(f"\n   [{tid}]")
            print(f"        ja: {ja.strip()[:96]!r}")
            print(f"        zh: {zh.strip()[:96]!r}")
        return 0

    print("===== 参照页（标准=魔法少女ヒトミ）")
    for name in ["魔法少女ヒトミ", "閃忍ハルカ"]:
        e = reg.get(name)
        if e:
            page, ids = page_ids(e["slug"]), refine_ids(e["slug"])
            miss = [k for k in page if k not in ids]
            print(f"   {name}: 真值 {len(page)}｜留档 {len(ids)}｜未覆盖 {len(miss)}")

    print("\n===== 用户点名这批：留档覆盖率")
    todo = []
    for name in LISTED:
        e = reg.get(name)
        if not e:
            print(f"   {name}: 未在注册表")
            continue
        slug = e["slug"]
        if not has_i18n(slug):
            print(f"   {name}: 无 i18n")
            continue
        page, ids = page_ids(slug), refine_ids(slug)
        miss = [k for k in page if k not in ids]
        flag = "✓ 已覆盖全" if not miss else f"✗ 缺 {len(miss)} 条"
        print(f"   {name:22s} 真值 {len(page):4d}｜留档 {len(ids):4d}｜{flag}")
        if miss:
            todo.append((name, slug, len(miss)))
    print(f"\n   → 需要精校的页：{len(todo)} 页 / 合计缺 {sum(t for _n, _s, t in todo)} 条")
    for name, slug, t in todo:
        print(f"        {name}  (缺 {t})  slug={slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
