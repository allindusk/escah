# -*- coding: utf-8 -*-
"""捞出「原样镜像」页里**仍然会显示日文**的全部文本，供人工/LLM 直接翻译。

背景（2026-09-30 用户要求）："不需要做词表，词表上没有的你直接翻译就行，又没有多少文本"。
镜像是**全部工作表**（宝箱包 33 个 ✓），而之前的 `--kana` 只覆盖了"数据统计页用到的那几张" ✗，
所以多出来的工作表（`集計(…)` 等）仍是日文 ✗。

做法：遍历 4 个包所有 sheet 的**每个文本节点** ✓，跑一遍现有 `label()` 逻辑 ✓，
输出"结果里仍含假名"的**去重文本** ✓（含出现次数 ✓）→ 写到 TSV ✓ 供逐条翻译 ✓。

用法：
  python tools/_dev/collect_mirror_texts.py            # 汇总 + 预览
  python tools/_dev/collect_mirror_texts.py --write    # 写 tools/_dev/_mirror_todo.tsv
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_sheet_mirror import PKGS, RAW, extract_table  # noqa: E402
from escah_pipeline import statpages  # noqa: E402

import lxml.html as LH  # noqa: E402

OUT = Path(__file__).resolve().parent / "_mirror_todo.tsv"
KANA = re.compile(r"[\u3041-\u3096\u30a1-\u30fa\u30fd-\u30ff]")


def texts_of(frag: str) -> "list[str]":
    root = LH.fragment_fromstring(frag, create_parent="div")
    out: "list[str]" = []
    for el in root.iter():
        if not isinstance(el.tag, str) or el.tag not in ("td", "th"):
            continue
        for holder in [el] + [x for x in el.iter() if x is not el]:
            for attr in ("text", "tail"):
                raw = getattr(holder, attr, None)
                if raw and raw.strip():
                    out.append(raw.strip())
    return out


def main() -> int:
    labels = statpages.load_labels()
    per_pkg: "dict[str, collections.Counter[str]]" = {}
    for key, prefix in PKGS.items():
        d = next((p for p in RAW.glob(prefix + "*") if p.is_dir()), None)
        if d is None:
            continue
        cnt: "collections.Counter[str]" = collections.Counter()
        for f in sorted(d.glob("*.html")):
            frag = extract_table(f)
            if not frag:
                continue
            for t in texts_of(frag):
                out = statpages.label(t, labels, "zh")
                if KANA.search(out):          # 译完仍有假名 ⇒ 缺译 ✓
                    cnt[t] += 1
        per_pkg[key] = cnt
        print(f"{key:<16} 缺译 {len(cnt):>4} 种（合计 {sum(cnt.values()):>6} 处）")
    allc: "collections.Counter[str]" = collections.Counter()
    for c in per_pkg.values():
        allc.update(c)
    print(f"\n去重后共 {len(allc)} 种待译文本")
    for t, n in allc.most_common(25):
        print(f"  {n:>4}  {t[:96]}")
    if "--write" in sys.argv:
        lines = [f"{t}\t" for t, _n in allc.most_common()]
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        print(f"\n已写出 {OUT}（{len(lines)} 行，格式：日文原文 TAB 待填中文）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
