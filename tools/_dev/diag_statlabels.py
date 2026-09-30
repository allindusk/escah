# -*- coding: utf-8 -*-
"""诊断统计数据页的标签翻译：为什么词表里的词没生效？

排查三件事（2026-09-30，用户在页面上看到 `合計` 未翻译 ✗，而它明明写在
glossary/stat_labels.yaml 里 ✗）：
  ① stat_labels.yaml 到底有没有被读进来？（YAML 解析失败会被 except 静默吞掉 ✗）
  ② 数据里那些"看起来没译"的单元格，**真实原文**是什么（可能有全角/空白差异 ✗）
  ③ 渲染时 `label()` 对这些原文的实际返回值

用法：python tools/_dev/diag_statlabels.py [slug...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline import statpages  # noqa: E402

PROBE = ["合計", "確率", "変更履歴", "宝箱", "結果", "開封箱数", "消費ST",
         "獲得宝箱数量", "パンドラ出現数量", "1-2-8H上の対比", "銅四円玉", "道具"]


def main() -> int:
    # ① 词表加载
    raw = statpages.LABELS_PATH
    print(f"stat_labels.yaml 存在: {raw.exists()}  大小 {raw.stat().st_size if raw.exists() else 0} 字节")
    try:
        import yaml
        data = yaml.safe_load(raw.read_text(encoding="utf-8"))
        print(f"YAML 解析: {'成功' if data else '失败/空'}  顶层键 {list((data or {}).keys())}")
        print(f"  labels 条目数 {len((data or {}).get('labels') or {})}")
    except Exception as e:  # noqa: BLE001
        print(f"YAML 解析**失败** ✗: {type(e).__name__}: {e}")

    labels = statpages.load_labels()
    print(f"\nload_labels() 合计 {len(labels)} 条")
    print("\n② 探针词的实际命中：")
    for k in PROBE:
        print(f"   {k!r:<24} → {labels.get(k, '（不在词表）')!r}")

    # ③ 数据里的真实原文
    slugs = sys.argv[1:] or ["box"]
    for slug in slugs:
        p = statpages.STAT_DIR / f"{slug}.json"
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        seen: dict[str, int] = {}
        for sheet in data["sheets"]:
            for t in sheet["tables"]:
                for r in (t.get("header") or []) + (t.get("rows") or []):
                    for c in r:
                        txt = (c.get("t") or "").strip()
                        if txt and not statpages._NUM_RE.match(txt):
                            seen[txt] = seen.get(txt, 0) + 1
        print(f"\n③ {slug}: 非数字文本 {len(seen)} 种；抽查渲染结果")
        for txt in list(seen)[:26]:
            got = statpages.label(txt, labels, "zh")
            flag = "✗ 仍日文" if got == txt and any(
                "\u3040" <= ch <= "\u30ff" for ch in txt
            ) else "✓"
            print(f"   {flag} {txt[:34]!r:<38} → {got[:34]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
