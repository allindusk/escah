#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站高频词汇「翻译 → 回流 glossary → 归档」的可复用工作流。

临时工作目录 tools/_todo_translate/ 存放每批次高频词的待处理文件：
  high_freq_terms_<date>.txt            频率<TAB>日文（提取产物，待翻译参考）
  high_freq_terms_<date>_translated.txt 空白译文模板（日文<TAB>留空）或被译者填好的译文
  high_freq_terms_<date>_paired.txt     完整 ja→zh 配对（回流权威源，由 merge 生成）
  high_freq_terms_<date>_missing.txt    真·漏翻（含假名、原样未翻，merge 生成）
  high_freq_terms_<date>_same_shape.txt 中日同形词确认（merge 生成）

处理完（build 出 glossary 后），archive 把这些文件按角色归档留存：
  - 待翻译（参考/确认类）：频率清单 + same_shape → tools/_texts_for_translation/
  - 已翻译（成果类）    ：translated + paired + missing → tools/_translated_texts/

子命令
------
  template  从频率清单生成空白译文模板（日文<TAB>留空，**绝不带频率列**）
  merge     对齐译文与频率清单 → paired/missing/same_shape；支持 --overlay 叠加补翻
  build     从 paired 生成 glossary/high_freq.yaml（仅保留 ja!=zh，长词优先）
  archive   把本批次文件按角色移到两个留存文件夹（_todo_translate 清空）
  process   merge + build + archive 一步封装（不含翻译本身，翻译由人工/模型完成）

约定
----
  - 空白译文模板**绝不带频率列**（格式：日文<TAB>中文）。否则译者会在带频率清单上
    翻译、覆盖日文列，导致日文丢失、无法回流（2026-07-28 教训）。
  - merge 自动识别两种译文格式：
      A) 日文<TAB>中文        （理想格式，直接配对）
      B) 频率<TAB>中文        （误覆盖日文列，按行号对齐频率清单恢复日文）
  - 同形词（ja==zh，如 速度/自身/魔法）不算漏翻，剔除出 missing、不进 glossary。
  - build 时 ja==zh 与空行自动跳过，不会污染词表。
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
TODO_DIR = TOOLS / "_todo_translate"
TEXTS_FOR_TRANS_DIR = TOOLS / "_texts_for_translation"
TRANSLATED_DIR = TOOLS / "_translated_texts"
GLOSSARY_DIR = ROOT / "glossary"

for _d in (TODO_DIR, TEXTS_FOR_TRANS_DIR, TRANSLATED_DIR, GLOSSARY_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# 含长音 ー，覆盖片假名名词
_KANA_RE = re.compile(r"[ぁ-んァ-ヶー]")


# -------------------------------------------------------------------------- 读取
def _data_lines(path: Path) -> list[str]:
    """返回文件中的「数据行」（去掉 # 注释与空行）。"""
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path}")
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        out.append(ln)
    return out


def load_freq_list(path: Path) -> list[tuple[int, str]]:
    """频率清单 → [(freq, ja), ...]（按原顺序）。"""
    rows = []
    for ln in _data_lines(path):
        parts = ln.split("\t")
        if len(parts) < 2:
            continue
        try:
            freq = int(parts[0])
        except ValueError:
            continue
        rows.append((freq, parts[1]))
    return rows


def _is_numeric(s: str) -> bool:
    return bool(s) and all(c.isdigit() for c in s)


def load_translated(path: Path) -> tuple[list[tuple[str, str]], str]:
    """译文文件 → ([(col0, col1), ...], 模式)。

    模式 'numeric'：频率<TAB>中文（误覆盖日文列，按行号对齐恢复）。
    模式 'ja'    ：日文<TAB>中文（理想格式，直接配对）。
    """
    rows: list[tuple[str, str]] = []
    for ln in _data_lines(path):
        parts = ln.split("\t")
        if len(parts) < 2:
            rows.append((parts[0], ""))
        else:
            rows.append((parts[0], parts[1]))
    mode = "numeric" if rows and all(_is_numeric(c0) for c0, _ in rows) else "ja"
    return rows, mode


# -------------------------------------------------------------------------- 写出
def _write_pairs(path: Path, paired: dict[str, str], freq_list: list[tuple[int, str]], header: str) -> None:
    order = {ja: i for i, (_, ja) in enumerate(freq_list)}
    items = sorted(paired.items(), key=lambda kv: order.get(kv[0], 1 << 30))
    lines = [f"# {header}", "# 格式：日文<TAB>中文", ""]
    for ja, zh in items:
        lines.append(f"{ja}\t{zh}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_list(path: Path, jas: list[str], header: str) -> None:
    lines = [f"# {header}", "# 格式：日文<TAB>中文（请填写）", ""]
    for ja in jas:
        lines.append(f"{ja}\t")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# -------------------------------------------------------------------------- 子命令
def cmd_template(args: argparse.Namespace) -> None:
    date = args.date
    freq_path = TODO_DIR / f"high_freq_terms_{date}.txt"
    if not freq_path.exists():
        sys.exit(f"[err] 频率清单不存在：{freq_path}（先跑 tools/_analyze_freq.py）")
    freq_list = load_freq_list(freq_path)
    out = TODO_DIR / f"high_freq_terms_{date}_translated.txt"
    lines = [
        "# 空白译文文件 — 全站高频词汇精翻（与 high_freq_terms_<date>.txt 一一对应）",
        "# 格式：日文<TAB>中文   （请在 TAB 后填写中文，不要删除日文或改动 TAB）",
        "# 不翻译的词请留空；翻译完把本文件发回，脚本按行回流进 glossary。",
        "# ⚠️ 本文件绝不带频率列；勿在带频率清单上翻译（会覆盖日文列导致无法回流）。",
        "",
    ]
    for _, ja in freq_list:
        lines.append(f"{ja}\t")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[done] 空白译文模板：{out}（{len(freq_list)} 条）")


def cmd_merge(args: argparse.Namespace) -> None:
    date = args.date
    freq_path = TODO_DIR / f"high_freq_terms_{date}.txt"
    tr_path = TODO_DIR / f"high_freq_terms_{date}_translated.txt"
    freq_list = load_freq_list(freq_path)
    tr_rows, mode = load_translated(tr_path)

    paired: dict[str, str] = {}
    if mode == "numeric":
        if len(tr_rows) != len(freq_list):
            sys.exit(f"[err] 译文行数 {len(tr_rows)} ≠ 频率清单行数 {len(freq_list)}，无法按行号对齐")
        for (freq, ja), (c0, zh) in zip(freq_list, tr_rows):
            if _is_numeric(c0) and int(c0) != freq:
                print(f"[warn] 行号对齐不一致：译文频率 {c0} ≠ 清单频率 {freq}（{ja}）", file=sys.stderr)
            paired[ja] = zh.strip()
    else:  # ja 模式：直接配对
        for ja, zh in tr_rows:
            paired[ja] = zh.strip()

    # 叠加补翻清单（格式 A：日文<TAB>中文）
    if args.overlay:
        ov_path = Path(args.overlay)
        if not ov_path.exists():
            ov_path = TODO_DIR / args.overlay
        if not ov_path.exists():
            sys.exit(f"[err] overlay 文件不存在：{ov_path}")
        ov_rows, ov_mode = load_translated(ov_path)
        if ov_mode != "ja":
            print("[warn] overlay 应为 日文<TAB>中文 格式，跳过", file=sys.stderr)
        else:
            n = 0
            for ja, zh in ov_rows:
                zh = zh.strip()
                if zh and zh != ja:
                    paired[ja] = zh
                    n += 1
            print(f"[overlay] 叠加 {n} 条补翻")

    # 拆出 漏翻 / 同形
    order = {ja: i for i, (_, ja) in enumerate(freq_list)}
    missing, same_shape = [], []
    for ja, zh in paired.items():
        if not zh or zh == ja:
            if _KANA_RE.search(ja):
                missing.append(ja)           # 含假名 + 原样未翻 = 真漏翻
            else:
                same_shape.append(ja)        # 纯汉字 + 同形 = 一般无需翻
    missing.sort(key=lambda j: order.get(j, 1 << 30))
    same_shape.sort(key=lambda j: order.get(j, 1 << 30))

    paired_path = TODO_DIR / f"high_freq_terms_{date}_paired.txt"
    missing_path = TODO_DIR / f"high_freq_terms_{date}_missing.txt"
    same_path = TODO_DIR / f"high_freq_terms_{date}_same_shape.txt"
    _write_pairs(paired_path, paired, freq_list, "完整配对（回流权威源）")
    _write_list(missing_path, missing, "真·漏翻清单（含假名、原样未翻；请填写）")
    _write_list(same_path, same_shape, "中日同形词确认清单（中文写法与日文相同，一般无需翻译；如需译法可填）")

    n_done = sum(1 for ja, zh in paired.items() if zh and zh != ja)
    print(f"[done] paired={len(paired)}  已译(ja!=zh)={n_done}  漏翻={len(missing)}  同形={len(same_shape)}")


def cmd_build(args: argparse.Namespace) -> None:
    date = args.date
    paired_path = TODO_DIR / f"high_freq_terms_{date}_paired.txt"
    if not paired_path.exists():
        # 归档后可能已移走，回退到 _translated_texts 查找
        alt = TRANSLATED_DIR / f"high_freq_terms_{date}_paired.txt"
        if alt.exists():
            paired_path = alt
        else:
            sys.exit(f"[err] 先跑 merge：{paired_path}")
    pairs = []
    for ln in _data_lines(paired_path):
        parts = ln.split("\t")
        if len(parts) < 2:
            continue
        ja, zh = parts[0], parts[1].strip()
        if ja and zh and zh != ja:
            pairs.append((ja, zh))
    pairs.sort(key=lambda kv: len(kv[0]), reverse=True)  # 长词优先
    out = GLOSSARY_DIR / "high_freq.yaml"
    header = (
        "# ============================================================================\n"
        "# 全站高频游戏术语（日 → 中），render-time 子串最高优先级覆盖\n"
        "# ----------------------------------------------------------------------------\n"
        "# 来源：tools/_todo_translate/ 高频词精译回流（tools/translate_glossary.py build）\n"
        "# 应用：pipeline/escah_pipeline/i18n.py 双层覆盖（仅 zh 站；ja 站不受影响）：\n"
        "#       - 含假名词条 → 子串替换（假名必为日语，安全；覆盖句内残留）\n"
        "#       - 纯汉字词条 → 整词精确匹配（防污染中文，不子串误改）\n"
        "# 维护：重跑 translate_glossary.py build 即可刷新（从 paired.txt 重建）。\n"
        "# ============================================================================\n"
    )
    body = yaml.safe_dump(
        {"high_freq": {ja: zh for ja, zh in pairs}},
        allow_unicode=True, sort_keys=False, default_flow_style=False,
    )
    out.write_text(header + body, encoding="utf-8")
    print(f"[done] glossary/high_freq.yaml：{len(pairs)} 条（长词优先）")


def _classify(date: str) -> tuple[list[Path], list[Path]]:
    """按角色分类 _todo_translate 内本批次文件。

    待翻译（参考/确认类）：频率清单 <date>.txt + _same_shape.txt
    已翻译（成果类）    ：_translated.txt + _paired.txt + _missing.txt
    """
    pending, translated = [], []
    prefix = f"high_freq_terms_{date}"
    for p in sorted(TODO_DIR.glob(f"{prefix}*")):
        name = p.name
        if name.endswith("_same_shape.txt") or name == f"{prefix}.txt":
            pending.append(p)
        elif (name.endswith("_translated.txt") or name.endswith("_paired.txt")
              or name.endswith("_missing.txt")):
            translated.append(p)
        else:
            translated.append(p)  # 兜底：未知后缀按已翻译处理，避免遗留在 _todo_translate
    return pending, translated


def cmd_archive(args: argparse.Namespace) -> None:
    date = args.date
    pending, translated = _classify(date)
    for p in pending:
        dst = TEXTS_FOR_TRANS_DIR / p.name
        shutil.move(str(p), str(dst))
        print(f"[待翻译] {p.name} → _texts_for_translation/")
    for p in translated:
        dst = TRANSLATED_DIR / p.name
        shutil.move(str(p), str(dst))
        print(f"[已翻译] {p.name} → _translated_texts/")
    print(f"[done] 归档完成：待翻译 {len(pending)} / 已翻译 {len(translated)}；_todo_translate 已清空")


def cmd_process(args: argparse.Namespace) -> None:
    cmd_merge(args)
    cmd_build(args)
    cmd_archive(args)


# -------------------------------------------------------------------------- CLI
def main() -> None:
    ap = argparse.ArgumentParser(description="高频词翻译回流工作流（操作 tools/_todo_translate）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("template", "merge", "build", "archive", "process"):
        sp = sub.add_parser(name)
        sp.add_argument("--date", required=True, help="日期 YYYYMMDD")
        if name in ("merge", "process"):
            sp.add_argument("--overlay", default=None,
                            help="叠加补翻清单路径（日文<TAB>中文，可只写文件名，自动在 _todo_translate 查找）")

    args = ap.parse_args()
    {"template": cmd_template, "merge": cmd_merge, "build": cmd_build,
     "archive": cmd_archive, "process": cmd_process}[args.cmd](args)


if __name__ == "__main__":
    main()
