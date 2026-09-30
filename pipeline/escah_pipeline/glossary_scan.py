#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描全站高频游戏术语，**补充** glossary/high_freq.yaml（只增不删）。

与旧 tools/_analyze_freq.py 的差异（2026-08-19 重构决议）：
  - 阈值从高阈值(20)下调为频次 ≥ 3（长度不限，单字如「女」「R」也收录）。
  - 符号剥离预处理：对每段日文先做装饰符号剥离
    （[出撃設定]→出撃設定、・全員AUTO→全員AUTO、◆大型ボス→大型ボス、
     ※注释、【】括号），核心词参与分词，符号本身不计入候选。
  - 纯符号排除：※/◆/・ 这类单独出现不计为词。
  - 同形词排除（不进 high_freq 候选，改由 inject 同形层处理）：
      纯 ASCII 字母串（R/SR/HP/AUTO…）与 中日同形汉字词（速度/魔法…）。
  - 表头/叶子节点文本统一从 i18n json 的 ja 字段采集（build_page 已把 <th>/<td>/
    <li>/正文 全部归一成叶子文本 key），无需重新解析 HTML。

⚠ 写盘语义（2026-09-25 改）：**合并式，只增不删**。
  历史实现是「按本轮候选全量重写」——而候选来自 janome 分词且排除纯汉字同形词，
  因此**词组/句子级条目**（人工/AI 积累）与**同形条目（k==v）**永远成不了候选，
  重扫一次就会被静默删除（实测 3552 条里丢 2567 条，含 2501 条已有译文；
  复现脚本 tools/_dev/hf_rescan_risk.py）。现在候选只负责新增/补译，
  已有译文条目一律保留，辅助段（_precise 等）也原样保留。

本文件只承载**词级**词表；两类内容请放别处（本脚本不触碰）：
  - 整串/块级译文 → glossary/phrases.yaml（i18n phrase-fill 注入真值）
  - 「保留原文（不翻译）」名单（人名/同形词）→ glossary/retain_ja.yaml

用法：
  python -m escah_pipeline.glossary_scan            # 扫描并补充（不删除任何已有条目）
  python -m escah_pipeline.glossary_scan --dry      # 仅打印候选统计，不写文件
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml
from janome.tokenizer import Tokenizer

ROOT = Path(__file__).resolve().parent.parent.parent
I18N_DIR = ROOT / "data" / "parsed" / "i18n"
CHAR_DIR = ROOT / "data" / "parsed" / "characters"
GLOSSARY = ROOT / "glossary"
HF_FILE = GLOSSARY / "high_freq.yaml"

THRESHOLD = 3

# ----------------------------------------------------------------- 符号剥离
# 装饰符号包裹（先剥外层，保留核心词）：[...] / 【...】 / 〔...〕 / (全角括号用于装饰的)
_DECOR_BRACKET_RE = re.compile(r"[\[\]【】〔〕]")
_DECOR_PREFIX_RE = re.compile(r"^[・◆※★☆●▼▲▶◀■□▼△▽✦✧]+(.*)$")
_DECOR_SUFFIX_RE = re.compile(r"(.*?)[・◆※★☆●▼▲▶◀■□▼△▽✦✧]+$")

# 纯符号（单独出现不算词）
_PURE_SYMBOL_RE = re.compile(r"^[\s・◆※★☆●▼▲▶◀■□△▽✦✧\[\]【】〔〕()（）\-\–—=]+$")
# 纯 ASCII 字母/数字串 → 同形词，排除（由 inject 同形层处理）
_ASCII_RE = re.compile(r"^[\x00-\x7f]+$")
# 全角拉丁字母/数字（ＢＯＳＳ／ＡＵＴＯ／０９）在中文里写法一致 → 同形，排除
_FULLWIDTH_ASCII_RE = re.compile(r"^[Ａ-Ｚａ-ｚ０-９A-Za-z0-9]+$")
# 纯数字/标点
_NUM_RE = re.compile(r"^[\d.,，。%＋+／/()（）\s\-]+$")
_PUNCT_RE = re.compile(r"^[\s\W_]+$")
# 纯平假名（语法/功能词）
_HIRA_RE = re.compile(r"^[\u3040-\u309f]+$")
# 含片假名
_KANA_RE = re.compile(r"[\u30a0-\u30ff\u31f0-\u31ff\u3099-\u309c]")
# 中日同形判定：纯汉字且不含任何片假名/平假名/非 BMP 日文专用汉字（如 𠀋）→ 视为可能同形
_HAN_RE = re.compile(r"[\u4e00-\u9fff]")
# ⚠️ 必须含平假名 \u3040-\u309f：否则含平假名的日文句子（评论口语 だ/よ/に/て/しろ 等）
# 会被 _is_same_shape 误判为「纯汉字同形」→ apply_glossary 把 zh 填成 ja 原文 →
# _untranslated_items 误当已译跳过 → 永远不进待译（漏译根因）。
_NON_HAN_JA_RE = re.compile(r"[\u3040-\u309f\u3400-\u4dbf\u30a0-\u30ff\u31f0-\u31ff]")

# wiki / UI 通用词（MediaWiki 导航与界面词，非游戏术语）
WIKI_UI = {
    "編集", "閲覧", "差分", "履歴", "削除", "追加", "保存", "移動", "表示", "ページ",
    "利用", "案内", "検索", "完了", "設定", "変更", "更新", "読み込み", "読込",
    "読み", "戻る", "進む", "トップ", "ヘルプ", "ログイン", "アカウント", "メニュー",
    "リンク", "タグ", "カテゴリ", "カテゴリー", "一覧", "確認", "開始", "終了",
    "コンテンツ", "ゲーム", "サイト", "ノート", "トーク", "特殊",
}


def _strip_decor(s: str) -> str:
    """剥离装饰符号，返回核心词文本。"""
    s = _DECOR_BRACKET_RE.sub(" ", s)
    s = _DECOR_PREFIX_RE.sub(r"\1", s)
    s = _DECOR_SUFFIX_RE.sub(r"\1", s)
    return s.strip()


def _is_same_shape(ja: str) -> bool:
    """纯 ASCII/全角拉丁串 或 中日同形（纯汉字、无日式专用汉字/假名）→ 视为同形词，排除。"""
    if _FULLWIDTH_ASCII_RE.match(ja):
        return True
    if not _HAN_RE.search(ja):
        return False
    # 含日式专用汉字（𠀋等扩展A）或任何假名 → 不是普通中日同形
    if _NON_HAN_JA_RE.search(ja):
        return False
    return True


# ----------------------------------------------------------------- 采集
def _glossary_exclude() -> set[str]:
    """names/terms 的 JA key 集合（专名已由 inject 第一级处理，排除出高频候选）。

    原 skills.yaml 已于 2026-08-31 移除（技能/效果译文统一由 i18n 真值承载）。
    """
    ex: set[str] = set()
    for fn in ("names.yaml", "terms.yaml"):
        p = GLOSSARY / fn
        if not p.exists():
            continue
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception as e:
            print(f"[warn] 解析 {fn} 失败：{e}", file=sys.stderr)
            continue
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, dict):
                    for k in v.keys():
                        if isinstance(k, str) and k.strip():
                            ex.add(k)
    return ex


def _collect_ja() -> list[str]:
    """采集全站日文叶子文本（i18n json 的 ja 字段 + 角色 sections）。"""
    texts: list[str] = []
    for jf in sorted(I18N_DIR.rglob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for k, ent in data.items():
            if k.startswith("_"):
                if isinstance(ent, dict):
                    for blk in ent.values():
                        if isinstance(blk, dict):
                            ja = blk.get("ja")
                            if ja and ja.strip():
                                texts.append(ja)
                continue
            if isinstance(ent, dict):
                ja = ent.get("ja")
                if ja and ja.strip():
                    texts.append(ja)
    for jf in sorted(CHAR_DIR.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        for sec in (data.get("sections") or {}).values():
            for row in sec.get("rows", []):
                for cell in row:
                    t = cell.get("t", "")
                    if t and t.strip():
                        texts.append(t)
    return texts


# ----------------------------------------------------------------- 分词过滤
_KEEP_NOUN_SUBTYPES = {
    "一般", "固有名詞", "サ変接続", "形容動詞語幹", "ナイ形容詞語幹",
    "形容詞語幹", "副詞可能", "感動詞", "組織", "地域", "人名", "姓",
}
_DROP_NOUN_SUBTYPES = {"数", "代名詞", "非自立", "接尾", "接頭", "助数詞", "未知"}


def _keep_token(surface: str, pos: str, exclude: set) -> bool:
    if not surface or not surface.strip():
        return False
    if _FULLWIDTH_ASCII_RE.match(surface) or _NUM_RE.match(surface) or _PUNCT_RE.match(surface):
        return False
    if _PURE_SYMBOL_RE.match(surface):
        return False
    if surface in WIKI_UI:
        return False
    if surface in exclude:
        return False
    if _is_same_shape(surface):
        return False  # 同形词不进 high_freq
    if _HIRA_RE.match(surface):
        return False  # 纯平假名功能词
    # 纯片假名短碎片（长度≤1 或全为长音/促音 ー/ッ/ャ 等）→ 排除，避免 ダメ/ー 之类词干噪声
    if _KANA_RE.fullmatch(surface) and (len(surface) <= 1 or set(surface) <= {"ー", "ッ", "ャ", "ュ", "ョ", "ァ", "ィ", "ゥ", "ェ", "ォ"}):
        return False
    top = pos.split(",")[0]
    if top == "名詞":
        sub = pos.split(",")[1] if len(pos.split(",")) > 1 else ""
        if sub in _DROP_NOUN_SUBTYPES:
            return False
        if sub not in _KEEP_NOUN_SUBTYPES and not _KANA_RE.search(surface):
            if not _HAN_RE.search(surface):
                return False
        return True
    if top == "未知語":
        return True
    return False


def scan() -> tuple[Counter, set[str]]:
    """返回 (候选频次 Counter, 被排除同形词集合)。"""
    exclude = _glossary_exclude()
    texts = _collect_ja()
    print(f"[info] glossary 已译专名排除：{len(exclude)}，收集日语文案段：{len(texts)}", file=sys.stderr)
    tok = Tokenizer()
    cnt: Counter = Counter()
    n_tok = 0
    for i, t in enumerate(texts):
        # 符号剥离预处理：把 [出撃設定] 这类核心词释放出来参与分词
        cleaned = _strip_decor(t)
        for tk in tok.tokenize(cleaned):
            n_tok += 1
            surf = tk.surface
            if not _keep_token(surf, tk.part_of_speech, exclude):
                continue
            cnt[surf] += 1
        if (i + 1) % 2000 == 0:
            print(f"[progress] {i+1}/{len(texts)} 段, 当前词种 {len(cnt)}", file=sys.stderr)
    print(f"[info] 分词总数 {n_tok}, 候选词种 {len(cnt)}", file=sys.stderr)
    return cnt, exclude


def _load_old_raw() -> dict:
    """读旧 high_freq.yaml 全量（含 _precise 等辅助段，供原样保留）。"""
    if not HF_FILE.exists():
        return {}
    try:
        return yaml.safe_load(HF_FILE.read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"[warn] 读取旧 high_freq.yaml 失败：{e}", file=sys.stderr)
        return {}


def _load_old_hf() -> dict[str, str]:
    return (_load_old_raw().get("high_freq", {}) or {})


def merge_entries(candidates: "dict[str, int]",
                  old: "dict[str, str]") -> "tuple[dict[str, str], int, int]":
    """把「本轮候选」与「旧表条目」合并为新的 high_freq（**只增不删**）。

    返回 (merged, reused, kept)。

    为什么必须只增不删（2026-09-25 实测教训）：
      扫描器靠 janome 分词产出**词级**候选，且 `_is_same_shape` 把纯汉字词全部排除，
      于是两类旧条目**永远成不了候选** ——
        ① 词组/句子级条目（人工/AI 积累，如「ゴールデンハニー戦ではサブ装備に」）；
        ② 中日同形条目（k==v，如 巫女/限定/防御力）。
      旧实现写盘时只写 candidates，实测会把 3552 条里的 2567 条（含 2501 条已有译文 +
      全部 66 条同形条目）**静默删掉**（`tools/_dev/hf_rescan_risk.py` 可复现），
      页面术语随之回退日文、待译清单里那些词全部回灌。
      因此合并语义定为：候选只负责**新增/补充**，任何情况下都不删除已有条目。
    """
    merged: dict[str, str] = {}
    reused = 0
    for w in candidates:
        zh = old.get(w, "")
        if zh:
            reused += 1
        merged[w] = zh          # 命中候选：沿用旧译文；没有则留空待补
    kept = 0
    for w, zh in old.items():
        if w in merged:
            continue
        if not zh:
            continue            # 旧条目本身就没有译文（历史占位）→ 不必留着占位
        merged.setdefault(w, zh)   # ← 非候选但**有译文/同形标记**的条目：一律保留
        kept += 1
    return merged, reused, kept


def main() -> None:
    ap = argparse.ArgumentParser(description="按新规则扫描并**补充** high_freq.yaml（只增不删）")
    ap.add_argument("--dry", action="store_true", help="仅打印统计，不写文件")
    args = ap.parse_args()

    cnt, _ = scan()
    candidates = {w: c for w, c in cnt.items() if c >= THRESHOLD}
    print(f"[info] 频次≥{THRESHOLD} 候选：{len(candidates)}", file=sys.stderr)

    raw = _load_old_raw()
    old = raw.get("high_freq", {}) or {}
    merged, reused, kept = merge_entries(candidates, old)
    new_pending = sum(1 for w, zh in merged.items() if not zh)
    print(f"[info] 复用旧译文 {reused} 条，新待译 {new_pending} 条，"
          f"保留非候选旧条目 {kept} 条（只增不删，不再按频次丢弃）", file=sys.stderr)

    if args.dry:
        items = sorted(candidates.items(), key=lambda kv: kv[1], reverse=True)
        print(f"[dry] 候选数 {len(items)}；合并后总条目 {len(merged)}（保留非候选 {kept}）；前 40：")
        for w, c in items[:40]:
            print(f"  {c}\t{w}\t{merged.get(w, '')}")
        return

    pairs = sorted(merged.items(), key=lambda kv: len(kv[0]), reverse=True)  # 长词优先
    header = (
        "# ============================================================================\n"
        "# 全站高频游戏术语（日 → 中），render-time / inject 子串最高优先级覆盖\n"
        "# ----------------------------------------------------------------------------\n"
        "# 生成：pipeline/escah_pipeline/glossary_scan.py（**补充式**：只新增/补译，绝不删条目）\n"
        "# 规则(2026-08-19)：频次≥3、长度不限、符号剥离、纯符号排除、同形词排除（同形由 inject 层处理）\n"
        "# 应用：i18n.py 三级 inject 第 4 级（high_freq）；仅 zh 站；ja 站不受影响。\n"
        "# 维护：重跑 glossary_scan.py 只做补充；zh 留空者由 inject/人工补全。\n"
        "# ⚠ 历史上本文件是「按候选全量重写」，会丢掉分词产不出的词组级条目与同形条目\n"
        "#   （实测 3552 条里会丢 2567 条，见 tools/_dev/hf_rescan_risk.py）；\n"
        "#   2026-09-25 起改为合并语义。整串/块级译文请放 glossary/phrases.yaml，\n"
        "#   「保留原文」名单放 glossary/retain_ja.yaml（两者都不被本脚本触碰）。\n"
        "# ============================================================================\n"
    )
    # 辅助段（_precise 等）原样保留，避免"重扫一次白名单也没了"
    extra = {k: v for k, v in raw.items() if k != "high_freq"}
    body = yaml.safe_dump(
        {"high_freq": {ja: zh for ja, zh in pairs}, **extra},
        allow_unicode=True, sort_keys=False, default_flow_style=False,
    )
    HF_FILE.write_text(header + body, encoding="utf-8")
    print(f"[done] glossary/high_freq.yaml：{len(pairs)} 条"
          f"（复用旧译 {reused}，待译 {new_pending}，保留非候选旧条目 {kept}）")


if __name__ == "__main__":
    main()
