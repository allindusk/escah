"""按 i18n id 批量写 zh（**会覆盖已有译文**，这是 fill 做不到的部分）。

`i18n fill` 只填空译；二次精校要改的是「已有译文」，必须走本脚本（或 apply_ja_map --force）。

两种输入：
  单页：python tools/sop/set_zh.py "characters/八爪妖蠱ハツネ" fix.json [--apply]
  多页：python tools/sop/set_zh.py MULTI fix.json [--apply]
        fix.json = {"characters/X": {"key12": "译文", "blk3#2": "译文"}, "shop": {...}}

id 形态：
  keyN        → 顶层节点
  blkN#i      → 块内第 i 段（不改段数；越界会跳过并提示）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "data" / "parsed" / "i18n"
BR = "\x01"


def apply_one(slug: str, fix: dict[str, str], write: bool) -> int:
    p = I18N / f"{slug}.json"
    if not p.exists():
        print(f"[SKIP] {slug} 不存在")
        return 0
    d = json.loads(p.read_text(encoding="utf-8"))
    n = 0
    for tid, txt in fix.items():
        if "#" in tid:
            bid, _, seg = tid.partition("#")
            b = (d.get("_blocks") or {}).get(bid)
            if not b:
                print(f"[SKIP] {bid} 不存在")
                continue
            segs = (b.get("zh") or "").split(BR)
            i = int(seg) - 1
            if i >= len(segs):
                print(f"[SKIP] {tid} 越界（该块 zh 只有 {len(segs)} 段，先确认段数）")
                continue
            if segs[i].strip() == txt.strip():
                continue
            segs[i] = txt
            b["zh"] = BR.join(segs)
        else:
            node = d.get(tid)
            if not isinstance(node, dict):
                print(f"[SKIP] {tid} 不存在")
                continue
            if (node.get("zh") or "").strip() == txt.strip():
                continue
            node["zh"] = txt
        n += 1
    if write and n:
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    slug, df = sys.argv[1], Path(sys.argv[2])
    raw = json.loads(df.read_text(encoding="utf-8"))
    write = "--apply" in sys.argv
    if slug.upper() == "MULTI":
        total = sum(apply_one(s, fix, write) for s, fix in raw.items())
        print(f"{'已写盘' if write else 'dry-run'}：合计 {total} 处")
        return 0
    n = apply_one(slug, raw, write)
    print(f"{'已写盘' if write else 'dry-run'}：{n} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
