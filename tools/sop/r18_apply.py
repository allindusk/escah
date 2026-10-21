"""把人工翻好的 R18 译文并入待译清单产物，再交给 `i18n fill`。

设计要点（都是为了不把露骨内容喂进模型上下文）：
  · 只做「解析 [id] 中文 → 按卷归位 → 写 <stem>_translated.txt」，**从不打印译文/原文**；
  · 输出只有统计（条数、缺失 id、重复条数），模型据此判断是否齐全；
  · 人工译文写在哪个文件里都行（默认扫 tools/_todo_translate/temp A.txt、temp B.txt，
    也支持任意文件名），脚本按各卷待译清单的 id 自动分流。

用法：
  python tools/sop/r18_apply.py --date 20261021                 # 只看统计
  python tools/sop/r18_apply.py --date 20261021 --apply         # 写盘
  python tools/sop/r18_apply.py --date 20261021 --slug bedroom-scenes \
      --from "temp A.txt" "temp B.txt" --apply

之后执行（这就是回填，纯按 id 写，不读内容）：
  python -m escah_pipeline.cli i18n fill --date <日期> --pages <slug>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
TODO = ROOT / "tools" / "_todo_translate"
ENTRY = re.compile(r"^\s*\[([A-Za-z0-9_]+(?:#\d+)?)\]\s*(\S.*)$")


def parse(path: Path) -> tuple[dict[str, str], int]:
    out: dict[str, str] = {}
    bad = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = ENTRY.match(line)
        if not m:
            bad += 1
            continue
        out[m.group(1)] = m.group(2).strip()
    return out, bad


def sort_key(x: str) -> tuple[str, int]:
    if "#" in x:
        base, _, seg = x.partition("#")
        return base, int(seg)
    return x, 0


def main() -> int:
    ap = argparse.ArgumentParser(description="并入人工 R18 译文（不打印正文）")
    ap.add_argument("--date", required=True, help="待译清单日期标签 YYYYMMDD")
    ap.add_argument("--slug", default="bedroom-scenes", help="页面 slug（默认 bedroom-scenes）")
    ap.add_argument("--from", dest="sources", nargs="*", default=["temp A.txt", "temp B.txt"],
                    help="人工译文文件名（相对 tools/_todo_translate/）")
    ap.add_argument("--apply", action="store_true", help="真正写盘（默认只统计）")
    args = ap.parse_args()

    safe = args.slug.replace("/", "__")
    pool: dict[str, str] = {}
    for name in args.sources:
        p = TODO / name
        if not p.exists():
            print(f"[缺失] {name}")
            continue
        data, bad = parse(p)
        dup = len(set(data) & set(pool))
        pool.update(data)
        print(f"{name}: {len(data)} 条（未成行 {bad} 行，与之前重复 {dup} 条）")
    print(f"合并后译文池: {len(pool)} 条")
    if not pool:
        return 1

    idx_path = TODO / f"{safe}_{args.date}_index.json"
    index = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {}

    stems = [f"{safe}_{args.date}"] + [f"{safe}_{args.date}_{c}" for c in "ABCDEFGH"]
    stems = [s for s in stems if (TODO / f"{s}.txt").exists()]
    if not stems:
        print(f"[跳过] 该日期没有 {args.slug} 的待译清单")
        return 1

    for stem in stems:
        expect = set()
        for line in (TODO / f"{stem}.txt").read_text(encoding="utf-8").splitlines():
            m = ENTRY.match(line)
            if m:
                expect.add(m.group(1))
        got = expect & set(pool)
        missing = expect - got
        print(f"\n[{stem}] 清单 {len(expect)} 条｜已提供 {len(got)}｜缺 {len(missing)}")
        if missing:
            print("   缺 id:", sorted(missing, key=sort_key)[:12])
        if args.apply and got:
            outp = TODO / f"{stem}_translated.txt"
            lines = [f"[{k}] {pool[k]}" for k in sorted(got, key=sort_key)]
            outp.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"   → 已写出 {outp.name}（{len(lines)} 行）")

    extra = {k for k in pool if k.split("#")[0] not in index}
    if extra and index:
        print(f"\n不在 index 里的 id（前 12）: {sorted(extra, key=sort_key)[:12]}")
    if not args.apply:
        print("\n（dry-run；加 --apply 写盘，然后跑 i18n fill）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
