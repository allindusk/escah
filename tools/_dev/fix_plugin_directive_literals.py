# -*- coding: utf-8 -*-
"""把**漏进翻译队列的 PukiWiki 插件指令**还原为原文（不翻译标记本身）。

背景（2026-09-27，随 raid-buff-debuff 标题不一致一并查出）：
  `special-attributes` 页有两处 `#region(...)` / `#includex(...)` 插件指令被当成正文
  送进机翻 ✗，产出 `#region（Choko Seishen 的号角颜色列表）` 这种**把指令参数也翻了**的垃圾 ✗✗
  —— 指令参数是**页面名引用**，一旦翻译就彻底失效。

本脚本只做一件事：对指定的 (slug, id)，把 zh 置为 **ja 原文逐字**（不臆造译法）。
彻底修法是解析期不把插件指令纳入 i18n ✗（属另一件事，见汇报中的建议）。

用法：python tools/_dev/fix_plugin_directive_literals.py [--apply]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline.i18n import _blocks_of, _keys_of, load_entries  # noqa: E402

BR = "\x01"

# (slug, id) —— 值一律取该 id 的 ja 原文
TARGETS = [
    ("special-attributes", "key26"),
    ("special-attributes", "blk4#1"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    for slug, tid in TARGETS:
        en = load_entries(slug)
        K, B = _keys_of(en), _blocks_of(en)
        if "#" in tid:
            bid, seg = tid.split("#", 1)
            blk = B.get(bid) or {}
            ja = (blk.get("ja") or "").split(BR)
            i = int(seg) - 1
            old = (blk.get("zh") or "").split(BR)
            cur = old[i] if i < len(old) else ""
            want = ja[i] if i < len(ja) else ""
            print(f"{slug} [{tid}]")
            print(f"    ja  : {want[:110]!r}")
            print(f"    zh  : {cur[:110]!r}")
            print(f"    →   : {want[:110]!r}（逐字还原）")
        else:
            ent = K.get(tid) or {}
            cur = ent.get("zh") or ""
            want = ent.get("ja") or ""
            print(f"{slug} [{tid}]")
            print(f"    ja  : {want[:110]!r}")
            print(f"    zh  : {cur[:110]!r}")
            print(f"    →   : {want[:110]!r}（逐字还原）")
        if apply:
            # 直接用 i18n 的写回入口（mt.apply 同款），保证格式一致
            import subprocess
            tmp = ROOT / "tools" / "_mt_refine" / "_tmp_directive.txt"
            tmp.write_text(f"=== {slug} ===\n[{tid}] {want}\n", encoding="utf-8", newline="\n")
            r = subprocess.run([sys.executable, "-m", "escah_pipeline.cli", "mt", "apply",
                                str(tmp), "--write"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            print("    " + (r.stdout or r.stderr).strip().splitlines()[-1])
    if not apply:
        print("\n（dry-run，未写入；加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
