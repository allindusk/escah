"""R18 分诊：把待译清单里**可能触发性内容的条目**挑出来，交给人工翻译。

判定只用「词表命中统计 + 结构联动」，**从不打印正文**：
  1) 词表命中：`glossary/r18.yaml` 的键（用户维护的露骨术语表）+ 可选的额外词表文件
     `tools/_todo_translate/_r18_extra.txt`（一行一个词，人工补充，不入库）。
  2) 块级联动：同一 `blkN` 只要有一段命中，整块所有段都判 R18（半块译文没有意义）。
  3) 页级比例：某页命中条目占比 ≥ --page-ratio（默认 0.3）或命中款数 ≥ --page-hits（默认 8），
     视为 R18 页 → 整页清单转人工，模型完全不碰。

用法：
  python tools/sop/r18_scan.py --date 20261021                  # 只统计（安全）
  python tools/sop/r18_scan.py --date 20261021 --split          # 真的拆清单
  python tools/sop/r18_scan.py --date 20261021 --dump "characters/X"   # 安全版整页 dump

--split 的效果：
  · 命中的行从正常清单里**移除**，写入 tools/_todo_translate/_r18_manual/<stem>.<date>.manual.txt
  · 原始完整清单另存 tools/_todo_translate/_r18_manual/<stem>.<date>.full.txt（留痕）
  · 之后可以放心 `_page_dump.py` 通读、让大模型翻译剩余条目
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import unicodedata
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
TODO = ROOT / "tools" / "_todo_translate"
MANUAL = TODO / "_r18_manual"
ENTRY = re.compile(r"^\s*\[([A-Za-z0-9_]+(?:#\d+)?)\]\s*(\S.*)$")

sys.path.insert(0, str(ROOT / "pipeline"))

# `glossary/r18.yaml` 是为「送翻预替换」维护的，里面混着大量日常词（獲物/密着/事後/感じる…），
# 直接拿来分类会大面积误判。这里把「本身不露骨、只在特定上下文才色情」的词排除，
# 只留强特征词做**分类**用；补充词走 tools/_todo_translate/_r18_extra.txt（人工维护）。
_NON_EXPLICIT = {
    "獲物", "密着", "密接", "事後", "聖域", "花園", "蕾", "遠慮なく", "強引に",
    "感じる", "気持ちいい", "気持ち良い", "じっくりと", "おもちゃ", "不純な",
    "豊満な", "肉感的な", "張りがある", "淡いピンク色", "忍者外伝", "おにいたん",
    "おいたなり", "色黒い", "白く太い", "痛み紛れの", "究極の悦び", "切れ味の良い太腿",
    "あどあどしく", "おませな", "ぶらんと垂れる", "わがままな肉体", "うごめく",
}


def load_lexicon() -> list[str]:
    """强特征露骨词：glossary/r18.yaml 的键（剔除日常词）+ 本地补充词表。"""
    words: list[str] = []
    p = ROOT / "glossary" / "r18.yaml"
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        for v in data.values():
            if isinstance(v, dict):
                words.extend(str(k) for k in v.keys())
    extra = TODO / "_r18_extra.txt"
    if extra.exists():
        words.extend(line.strip() for line in extra.read_text(encoding="utf-8").splitlines()
                     if line.strip() and not line.strip().startswith("#"))
    seen, out = set(), []
    for w in sorted(set(words), key=len, reverse=True):
        w = unicodedata.normalize("NFC", w).strip()
        if len(w) < 3 or w in seen or w in _NON_EXPLICIT:
            continue
        seen.add(w)
        out.append(w)
    return out


def hits_in(text: str, lexicon: list[str]) -> int:
    t = unicodedata.normalize("NFC", text)
    return sum(1 for w in lexicon if w in t)


def is_relevant(name: str, date: str) -> bool:
    if not name.endswith(".txt"):
        return False
    if "_translated" in name or name.endswith(".manual.txt") or name.endswith(".full.txt"):
        return False
    return date in name


def main() -> int:
    ap = argparse.ArgumentParser(description="R18 分诊（不打印正文）")
    ap.add_argument("--date", required=True, help="待译清单日期标签 YYYYMMDD")
    ap.add_argument("--split", action="store_true", help="拆清单：命中条目转入 _r18_manual/")
    ap.add_argument("--dump", metavar="SLUG", help="打印该页整页 dump（自动剔除已判 R18 的 id）")
    ap.add_argument("--page-ratio", type=float, default=0.3, help="页级判定：命中占比阈值")
    ap.add_argument("--page-hits", type=int, default=8, help="页级判定：命中条目数阈值")
    args = ap.parse_args()

    lexicon = load_lexicon()
    print(f"术语表载入 {len(lexicon)} 条（来自 glossary/r18.yaml"
          f"{' + _r18_extra.txt' if (TODO / '_r18_extra.txt').exists() else ''}）")

    files = [p for p in TODO.iterdir() if p.is_file() and is_relevant(p.name, args.date)]
    if not files:
        print(f"[空] 没有 {args.date} 的待译清单")
        return 1

    MANUAL.mkdir(parents=True, exist_ok=True)
    flagged_all: dict[str, set[str]] = {}
    total_items = total_flag = 0

    for f in sorted(files):
        lines = f.read_text(encoding="utf-8").splitlines()
        entries, hits = [], {}
        for line in lines:
            m = ENTRY.match(line)
            if not m:
                continue
            entries.append((m.group(1), m.group(2), line))
            hits[m.group(1)] = hits_in(m.group(2), lexicon)

        flagged = {i for i, h in hits.items() if h > 0}
        # 块级联动：同 blkN 任一段命中 → 整块命中
        blocks_hit = {i.split("#")[0] for i in flagged if "#" in i}
        flagged |= {i for i in hits if "#" in i and i.split("#")[0] in blocks_hit}

        n, nf = len(entries), len(flagged)
        page_level = bool(n) and (nf / n >= args.page_ratio or nf >= args.page_hits)
        if page_level:
            flagged = {i for i, _t, _l in entries}
            nf = len(flagged)
        total_items += n
        total_flag += nf
        flagged_all[f.name] = flagged

        print(f"  {f.name}: {n} 条｜命中 {nf}"
              f"{'（整页判为 R18）' if page_level else ''}")

        if args.split and flagged:
            full = MANUAL / f"{f.stem}.full.txt"
            man = MANUAL / f"{f.stem}.manual.txt"
            # 只留第一次的完整原件：重复跑 --split 时清单已被剔除过，再覆盖会丢掉原始记录
            if not full.exists():
                shutil.copy2(f, full)
            man.write_text("\n".join(l for i, _t, l in entries if i in flagged) + "\n", encoding="utf-8")
            f.write_text("\n".join(l for i, _t, l in entries if i not in flagged) + "\n", encoding="utf-8")

    print(f"\n合计：{total_items} 条待译｜判为 R18 {total_flag} 条"
          f"（{total_flag / max(total_items, 1):.1%}）")
    if args.split:
        print(f"已拆分：命中条目 → {MANUAL.relative_to(ROOT)}/*.manual.txt；"
              f"完整原件留档 *.full.txt；正常清单已剔除这些行")
        print("下一步：把 *.manual.txt 交给人工翻译（模型不得打开），其余条目照常翻译。")
    else:
        print("（dry-run：加 --split 才改清单）")

    if args.dump:
        _safe_dump(args.dump, flagged_all, args.date)
    return 0


def _safe_dump(slug: str, flagged_all: dict[str, set[str]], date: str) -> None:
    """整页 dump，但剔除已判 R18 的 id（避免通读时把露骨内容带进上下文）。"""
    from escah_pipeline import i18n  # noqa: E402

    safe = slug.replace("/", "__")
    skip: set[str] = set()
    for name, ids in flagged_all.items():
        if name.startswith(safe + "_") or name == f"{safe}_{date}.txt":
            skip |= ids
    e = i18n.load_entries(slug)
    print(f"\n=== {slug} 安全版 dump（已剔除 {len(skip)} 个 R18 id）===")
    for k, v in e.items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        if k in skip or (k.split("#")[0] in skip):
            continue
        ja, zh = (v.get("ja") or "").strip(), (v.get("zh") or "").strip()
        if not ja:
            continue
        print(f"[{k}] {ja}\n     -> {zh or '（空）'}")


if __name__ == "__main__":
    raise SystemExit(main())
