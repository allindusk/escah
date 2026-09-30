# -*- coding: utf-8 -*-
"""盘点：角色页里哪些还没有「手工精校留档」，以及用户点名那批的现状。

背景：本轮要把剩余角色页按「魔法少女ヒトミ」的标准逐条精校。
判据不能靠印象 —— 用 `tools/_mt_refine/` 里有没有**该页的留档文件**来判断，
并结合真值里"看起来还是机翻"的信号（含假名残留 / 与同页其他条目明显不一致）。
"""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline.i18n import _blocks_of, _keys_of, has_i18n, load_entries  # noqa: E402
from escah_pipeline.registry import load_registry  # noqa: E402

BR = "\x01"

# 用户点名的顺序（第 8 项见备注：用户说"7 页"但列了 8 个）
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
REF_PAGE = "魔法少女ヒトミ"


def stats(slug: str) -> dict:
    if not has_i18n(slug):
        return {"n": 0, "kana": 0, "empty": 0}
    try:
        en = load_entries(slug)
    except Exception:  # noqa: BLE001
        return {"n": 0, "kana": 0, "empty": 0}
    n = kana = empty = 0
    for ent in list(_keys_of(en).values()):
        n += 1
        ja, zh = ent.get("ja") or "", ent.get("zh") or ""
        if not zh.strip():
            empty += 1
        elif zh.strip() != ja.strip():
            outside = zh
            if any("\u3040" <= c <= "\u30ff" for c in outside):
                kana += 1
    for blk in _blocks_of(en).values():
        ja_segs = (blk.get("ja") or "").split(BR)
        zh_segs = (blk.get("zh") or "").split(BR)
        for i, j in enumerate(ja_segs):
            n += 1
            z = zh_segs[i] if i < len(zh_segs) else ""
            if not z.strip():
                empty += 1
            elif z.strip() != j.strip() and any("\u3040" <= c <= "\u30ff" for c in z):
                kana += 1
    return {"n": n, "kana": kana, "empty": empty}


def has_refine(slug: str) -> str:
    pats = [f"*{slug}*", f"*{slug.replace('/', '__')}*"]
    hits = []
    for p in pats:
        hits += [os.path.basename(x) for x in glob.glob(str(ROOT / "tools" / "_mt_refine" / p))]
    return hits[0] if hits else ""


def main() -> int:
    reg = {e["name"]: e for e in load_registry()}

    print("===== ① 参照页（标准）")
    for name in [REF_PAGE, "閃忍ハルカ"]:
        e = reg.get(name)
        if not e:
            print(f"   {name}: 未在注册表")
            continue
        s = stats(e["slug"])
        print(f"   {name}  slug={e['slug']}  条目={s['n']}  假名残留={s['kana']}  精翻留档={has_refine(e['slug']) or '无'}")

    print("\n===== ② 用户点名这批的现状")
    for i, name in enumerate(LISTED, 1):
        e = reg.get(name)
        if not e:
            print(f"   {i}. {name}: **未在注册表**")
            continue
        s = stats(e["slug"])
        print(f"   {i}. {name}")
        print(f"      slug={e['slug']}  条目={s['n']}  假名残留={s['kana']}  "
              f"空译={s['empty']}  精翻留档={has_refine(e['slug']) or '无'}")

    print("\n===== ③ 所有角色页：有无精翻留档（存量 ~条目数降序）")
    rows = []
    for e in load_registry():
        slug = e["slug"]
        if not (slug.startswith("characters/") or e.get("name") in reg):
            continue
        if not has_i18n(slug):
            continue
        ref = has_refine(slug)
        if ref:
            continue
        st = stats(slug)
        rows.append((st["n"], e["name"], slug, st["kana"]))
    for n, name, slug, kana in sorted(rows, reverse=True):
        print(f"   {n:5d} 条  假名残留 {kana:3d}  {name}  ({slug})")
    print(f"   合计 {len(rows)} 页无留档")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
