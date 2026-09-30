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
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
TODO_DIR = TOOLS / "_todo_translate"
GLOSSARY_TODO_DIR = TODO_DIR / "glossary"   # 词表待译单独放这个子目录（与页面待译分离）
TEXTS_FOR_TRANS_DIR = TOOLS / "_texts_for_translation"
TRANSLATED_DIR = TOOLS / "_translated_texts"
GLOSSARY_DIR = ROOT / "glossary"
HF_FILE = GLOSSARY_DIR / "high_freq.yaml"

for _d in (TODO_DIR, GLOSSARY_TODO_DIR, TEXTS_FOR_TRANS_DIR, TRANSLATED_DIR, GLOSSARY_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# 文件开头固定指令（与 i18n extract 页面待译保持一致，见 i18n.py _TODO_INSTRUCTION）。
_TODO_INSTRUCTION = (
    "你是一名专业的日语翻译简体中文的游戏本地化翻译员，负责游戏《超昂大战》（エスカレーション・ヒロインズ）WIKI 内容翻译。严格遵循：每行格式为 `[N] 日文`，你必须返回 `[N] 中文`，N 与输入完全一致，不得遗漏、合并、重排或增删任何行，翻译的时候需要结合整个文本的上下文翻译。\n"
)

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
    """从 glossary/high_freq.yaml 读 zh 为空的词，生成「页面格式」待译到 _todo_translate/glossary/。

    页面格式（与 i18n extract --per-page 一致）：
      - 首行翻译指令 _TODO_INSTRUCTION（原样）
      - 第二行 `# 页 glossary 卷 1/1（v2 key 模式：条目 [keyN]/[blkN] 直接对应 i18n id）`
      - 每行 `[N] 日文`（N 从 1 起）
    同时生成 <stem>_index.json：{N: {ja, vol, kind}}（供 merge 对齐）。
    """
    date = args.date
    # 从 high_freq.yaml 读空译词（zh 为空 → 待翻译）
    todo_words: list[str] = []
    if HF_FILE.exists():
        try:
            loaded = yaml.safe_load(HF_FILE.read_text(encoding="utf-8")) or {}
            hf = loaded.get("high_freq", {}) or {}
            todo_words = [k for k, v in hf.items() if k and not v]
        except Exception as e:
            sys.exit(f"[err] 读取 {HF_FILE} 失败：{e}")
    if not todo_words:
        print(f"[done] {HF_FILE} 无待翻译词（zh 全空或文件为空）")
        return

    stem = f"glossary_high_freq_{date}"
    fname = f"{stem}.txt"
    out = GLOSSARY_TODO_DIR / fname
    lines = [_TODO_INSTRUCTION,
             f"# 页 glossary 卷 1/1（v2 key 模式：条目 [keyN]/[blkN] 直接对应 i18n id）\n"]
    for i, ja in enumerate(todo_words, 1):
        lines.append(f"[{i}] {ja}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    index = {str(i): {"ja": ja, "vol": fname, "kind": "key"} for i, ja in enumerate(todo_words, 1)}
    (GLOSSARY_TODO_DIR / f"{stem}_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[done] 待译（页面格式）：{out}（{len(todo_words)} 条）→ {GLOSSARY_TODO_DIR}")


def cmd_merge(args: argparse.Namespace) -> None:
    """读 _todo_translate/glossary/ 下翻译完成的待译文件（页面格式 [N] 中文），回写 high_freq.yaml。

    用 <stem>_index.json 的 N→ja 对齐（与 i18n fill 的 index 机制一致，非位置匹配）：
      - 译文文件 = <stem>_translated.txt，每行 `[N] 中文`（可含 `[N] 日文` 未翻行，跳过）。
      - 对 zh 非空且 != ja 的词，更新 high_freq.yaml 对应 ja 的译文（zh 空者回填）。
    只更新 high_freq.yaml 里已存在的键；新增键不写入（防止拼写错误污染词表）。
    """
    date = args.date
    stem = f"glossary_high_freq_{date}"
    idx_path = GLOSSARY_TODO_DIR / f"{stem}_index.json"
    tr_path = GLOSSARY_TODO_DIR / f"{stem}_translated.txt"
    if not idx_path.exists():
        sys.exit(f"[err] 找不到 {idx_path}（先跑 template）")
    if not tr_path.exists():
        sys.exit(f"[err] 找不到译文文件 {tr_path}")

    index: dict[str, dict] = json.loads(idx_path.read_text(encoding="utf-8"))
    # 解析译文文件每行 `[N] 中文`
    translations: dict[str, str] = {}  # N -> zh
    for ln in tr_path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or not s.startswith("["):
            continue
        m = re.match(r"^\[(\d+)\]\s*(.*)$", s)
        if not m:
            continue
        n, zh = m.group(1), m.group(2).strip()
        translations[n] = zh

    if not HF_FILE.exists():
        sys.exit(f"[err] 找不到 {HF_FILE}")
    loaded = yaml.safe_load(HF_FILE.read_text(encoding="utf-8")) or {}
    hf: dict = loaded.get("high_freq", {}) or {}

    filled = 0
    for n, meta in index.items():
        ja = meta.get("ja", "")
        zh = translations.get(n, "")
        if not ja or not zh or zh == ja:
            continue
        if ja in hf and not hf.get(ja):  # 只回填 zh 为空的既有键
            hf[ja] = zh
            filled += 1

    header = (
        "# ============================================================================\n"
        "# 全站高频游戏术语（日 → 中），render-time / inject 子串最高优先级覆盖\n"
        "# ----------------------------------------------------------------------------\n"
        "# 重生成：pipeline/escah_pipeline/glossary_scan.py；待译回流：tools/translate_glossary.py\n"
        "# 新规则(2026-08-19)：频次≥3、长度不限、符号剥离、纯符号排除、同形词排除（同形由 inject 层处理）\n"
        "# 应用：i18n.py 三级 inject 第 4 级（high_freq）；仅 zh 站；ja 站不受影响。\n"
        "# 维护：重跑 glossary_scan.py 即可刷新；zh 留空者由 inject 同形层/人工补全。\n"
        "# ============================================================================\n"
    )
    body = yaml.safe_dump(
        {"high_freq": hf},
        allow_unicode=True, sort_keys=False, default_flow_style=False,
    )
    HF_FILE.write_text(header + body, encoding="utf-8")
    print(f"[done] 回写 {HF_FILE}：已填 {filled} 条（仍空 {sum(1 for v in hf.values() if not v)} 条）")


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


def cmd_archive(args: argparse.Namespace) -> None:
    """把 glossary 待译批次归档：待译（未填译文）+ 已译（_translated.txt + index）分开留存。

    待翻译（参考/确认类）：<stem>.txt（原始待译，未翻译时留存）
    已翻译（成果类）    ：<stem>_translated.txt + <stem>_index.json
    """
    date = args.date
    prefix = f"glossary_high_freq_{date}"
    pending: list[Path] = []
    translated: list[Path] = []
    for p in sorted(GLOSSARY_TODO_DIR.glob(f"{prefix}*")):
        name = p.name
        if name.endswith("_translated.txt"):
            translated.append(p)
        elif name.endswith("_index.json"):
            translated.append(p)  # index 随已译留存
        else:
            pending.append(p)     # 原始待译（未翻译）
    for p in pending:
        shutil.move(str(p), str(TEXTS_FOR_TRANS_DIR / p.name))
        print(f"[待翻译] {p.name} → _texts_for_translation/")
    for p in translated:
        shutil.move(str(p), str(TRANSLATED_DIR / p.name))
        print(f"[已翻译] {p.name} → _translated_texts/")
    print(f"[done] 归档完成：待翻译 {len(pending)} / 已翻译 {len(translated)}；glossary 待译目录已清空")


def cmd_process(args: argparse.Namespace) -> None:
    cmd_merge(args)      # merge 已直接回写 high_freq.yaml（不再需要 build）
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
