"""把块级 `blk.zh` 的各段，用同名节点（keyN）的现译重新拼一遍。

为什么需要：渲染规则是「块级 zh 存在 → 整块用 blk.zh 替换，节点级结构不保留」，
所以**只改 keyN.zh 时页面不会变**。改完节点必须同步块级（或改用 set_zh.py 直接改 blkN#i）。

匹配方式：按段内 ja 归一化文本找同名节点；段尾带评论签名 / `[ID]` 的会剥掉尾巴再匹配。
命中且有 zh → 用节点译文；否则保留该段旧译。

用法：
  python tools/sop/block_sync.py "characters/八爪妖蠱ハツネ"            # dry-run
  python tools/sop/block_sync.py "characters/八爪妖蠱ハツネ" --apply
  python tools/sop/block_sync.py "slug1" "slug2" --apply

⚠️ 不要对全站无脑跑：人工精校过的块级译文可能比旧节点译文更好，整页重拼会把它换掉。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "data" / "parsed" / "i18n"
sys.path.insert(0, str(ROOT / "pipeline"))
from escah_pipeline import i18n  # noqa: E402

BR = "\x01"


def sync(slug: str, write: bool) -> tuple[int, int]:
    p = I18N / f"{slug}.json"
    if not p.exists():
        print(f"[SKIP] {slug} 不存在")
        return 0, 0
    d = json.loads(p.read_text(encoding="utf-8"))
    keys = {k: v for k, v in d.items() if not k.startswith("_") and isinstance(v, dict)}
    idx: dict[str, str] = {}
    for v in keys.values():
        ja, zh = v.get("ja") or "", (v.get("zh") or "").strip()
        if ja and zh:
            idx.setdefault(i18n._norm(ja), zh)
            idx.setdefault(i18n._norm_ns(ja), zh)

    touched = segs_hit = 0
    for _bid, blk in (d.get("_blocks") or {}).items():
        old = blk.get("zh") or ""
        if not old.strip():
            continue
        ja_segs = (blk.get("ja") or "").split(BR)
        old_segs = old.split(BR)
        new_segs, hit = [], 0
        for i, seg in enumerate(ja_segs):
            zh = idx.get(i18n._norm(seg)) or idx.get(i18n._norm_ns(seg))
            if not zh:
                bare = i18n._strip_comment_sig(seg)
                bare = re.sub(r"[\[［][A-Za-z0-9._/]{6,}[\]］]", "", bare).strip()
                zh = idx.get(i18n._norm(bare)) or idx.get(i18n._norm_ns(bare))
            if zh:
                new_segs.append(zh)
                hit += 1
            else:
                new_segs.append(old_segs[i] if i < len(old_segs) else "")
        new = BR.join(new_segs)
        if hit and new != old:
            touched += 1
            segs_hit += hit
            if write:
                blk["zh"] = new
    if write and touched:
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return touched, segs_hit


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--apply" in sys.argv
    if not args:
        print(__doc__)
        return 2
    t = c = 0
    for s in args:
        a, b = sync(s, write)
        if a:
            print(f"  {s}: 块 {a} 个 / 覆盖 {b} 段")
        t += a
        c += b
    print(f"合计：{t} 块 / {c} 段｜{'已写盘' if write else 'dry-run'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
