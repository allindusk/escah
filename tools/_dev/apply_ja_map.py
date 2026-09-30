# -*- coding: utf-8 -*-
"""按**原文映射**落盘译文：一次写 `原文<TAB>译文`，自动传播到该页所有同原文节点。

为什么（2026-09-27）：
  · 同一段原文在真值里有 `keyN` 与 `blkN#i` 两套节点 ✗ —— 只改一边就会残留旧译文、
    或造成用户看到的"目录/正文不一致" ✗；
  · 逐条写 id 既慢又容易漏 ⇒ 改为写**原文→译文**映射，脚本按 trim 后的原文精确匹配，
    把新译文写到该页**所有**同原文的 key 与块段落上 ⇒ 页内分歧结构性归零 ✓。

映射文件格式（UTF-8，一行一条，`#` 开头为注释）：
    スタミナ<TAB>体力
    20秒間、自軍フィールドの命中50アップ<TAB>20秒内，我方场地命中提升50

用法：
  python tools/_dev/apply_ja_map.py <slug> <mapfile>            # dry-run：只报告会改哪些
  python tools/_dev/apply_ja_map.py <slug> <mapfile> --apply    # 落盘（内部调用 mt apply --write）
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_page_for_review import all_pairs  # noqa: E402


def _norm(s: str) -> str:
    """归一化：去掉变体选择符、NFKC 统一全半角/兼容字符、压缩空白。

    为什么需要：同一段原文在 key 与块段落里可能带不同的**不可见字符**
    （如星号 `⭐︎`＝U+2B50+U+FE0E 与 `⭐`），逐字匹配会漏掉一半节点，
    于是"改了一处、另一套还是旧译文" ✗（实测每页的星等说明行都中招）。
    """
    s = s.replace("\ufe0e", "").replace("\ufe0f", "")   # variation selectors
    s = unicodedata.normalize("NFKC", s)
    return " ".join(s.split())


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    slug, mapfile = sys.argv[1], sys.argv[2]
    apply = "--apply" in sys.argv

    mapping: "dict[str, str]" = {}
    for raw in Path(mapfile).read_text(encoding="utf-8").splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" not in line:
            print(f"!! 跳过（缺 TAB 分隔）：{line[:70]!r}")
            continue
        ja, zh = line.split("\t", 1)
        mapping[_norm(ja)] = zh.strip()

    pairs = all_pairs(slug)
    lines: "list[str]" = []
    hit: "dict[str, int]" = {}
    same = 0
    for tid, ja, zh in pairs:
        j = _norm(ja)
        if j not in mapping:
            continue
        want = mapping[j]
        hit[j] = hit.get(j, 0) + 1
        if want == zh.strip():
            same += 1
            continue
        lines.append(f"[{tid}] {want}")

    print(f"{slug}：映射 {len(mapping)} 条｜命中节点 {sum(hit.values())} 个｜"
          f"其中已是目标值 {same} 个｜**待改 {len(lines)} 条**")
    for j, n in hit.items():
        if n == 1 and len(j) > 24:
            pass  # 只命中 1 处的长句属正常
    unmatched = [j for j in mapping if j not in hit]
    if unmatched:
        print(f"⚠ 映射里 {len(unmatched)} 条**未命中任何节点**（原文写错？）：")
        for j in unmatched[:12]:
            print(f"     {j[:88]!r}")
    if not lines:
        print("（无需改动）")
        return 0
    if not apply:
        print("（dry-run；加 --apply 生效）")
        for ln in lines[:8]:
            print("   " + ln[:110])
        return 0

    tmp = Path(tempfile.gettempdir()) / f"_jamap_{slug.replace('/', '__')}.txt"
    tmp.write_text(f"=== {slug} ===\n" + "\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    r = subprocess.run([sys.executable, "-m", "escah_pipeline.cli", "mt", "apply", str(tmp), "--write"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((r.stdout or r.stderr).strip().splitlines()[-1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
