"""把 R18 页面的待译清单**原样导出**给人工翻译，全程不打印任何正文。

为什么要「原样复制」而不是「模型挑出来」：一旦模型把待译行读进上下文，就等于把露骨
内容喂给了模型（会触发内容审查，实测过）。所以正确做法是用本脚本按页面把清单整段
复制到独立目录，模型只统计行数，不打开内容。

用法：
  python tools/sop/r18_export.py --date 20261021
  python tools/sop/r18_export.py --date 20261021 --slugs bedroom-scenes --out tools/_todo_translate/_r18_manual

产物：<out>/<safe>_<date>[_A|_B].txt 与同名 _index.json（与待译清单同格式，
      人工翻译后按 `[id] 中文` 一行一条写回，再用 tools/sop/r18_apply.py 并入）。
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
TODO = ROOT / "tools" / "_todo_translate"
DEFAULT_SLUGS = ("bedroom-scenes",)


def main() -> int:
    ap = argparse.ArgumentParser(description="导出 R18 页待译清单（不打印正文）")
    ap.add_argument("--date", required=True, help="待译清单日期标签 YYYYMMDD")
    ap.add_argument("--slugs", nargs="+", default=list(DEFAULT_SLUGS),
                    help="R18 页 slug（默认 bedroom-scenes）；可给多个")
    ap.add_argument("--out", default=str(TODO / "_r18_manual"), help="导出目录")
    args = ap.parse_args()

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)

    total = 0
    for slug in args.slugs:
        safe = slug.replace("/", "__")
        pats = [f"{safe}_{args.date}.txt"] + [f"{safe}_{args.date}_{c}.txt" for c in "ABCDEFGH"]
        files = [TODO / p for p in pats if (TODO / p).exists()]
        if not files:
            print(f"[跳过] {slug}: 该日期没有待译清单")
            continue
        for f in files:
            shutil.copy2(f, out / f.name)
            n = sum(1 for line in f.read_text(encoding="utf-8").splitlines()
                    if line.lstrip().startswith("["))
            total += n
            print(f"  {f.name}: {n} 条 → {out.name}/")
        idx = TODO / f"{safe}_{args.date}_index.json"
        if idx.exists():
            shutil.copy2(idx, out / idx.name)
            print(f"  {idx.name}: {len(json.loads(idx.read_text(encoding='utf-8')))} 个 id → {out.name}/")

    print(f"\n已导出 {total} 条待人工翻译。请把译文按 `[id] 中文` 一行一条写回本目录同名文件，"
          f"再把文件名加 `_translated` 后缀（例：xxx_20261021_A_translated.txt），"
          f"然后执行 python tools/sop/r18_apply.py --date {args.date}。")
    print("注意：以上过程模型不得打开这些文件查看内容。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
