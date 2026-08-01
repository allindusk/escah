#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站高频词汇分析：抽取日语文案 → janome 分词 → 统计词频(>阈值) → 排除 glossary 已译词与噪声。

输出：tools/_todo_translate/high_freq_terms_<date>.txt
格式：每行 `出现次数<TAB>日文`（按频率降序），供译者精翻后并入 glossary。

噪声过滤：
  - glossary 已译 JA（精确匹配）
  - 角色/专有名词子串碎片（如「昂」「閃忍」来自「超昂閃忍」分词）
  - 纯假名语法/功能词（游戏术语均为汉字/片假名）
  - wiki/UI 通用词（編集/完了/コンテンツ/ゲーム 等 MediaWiki 导航词）
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import yaml
from janome.tokenizer import Tokenizer

ROOT = Path(__file__).resolve().parent.parent
PARSED = ROOT / "data" / "parsed"
I18N_DIR = PARSED / "i18n"
CHAR_DIR = PARSED / "characters"
GLOSSARY = ROOT / "glossary"
TODO_DIR = ROOT / "tools" / "_todo_translate"
TODO_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLD = 20

# wiki / UI 通用词（MediaWiki 导航与界面词，非游戏术语，不应进入 glossary）
WIKI_UI = {
    "編集", "閲覧", "差分", "履歴", "削除", "追加", "保存", "移動", "表示", "ページ",
    "利用", "案内", "検索", "完了", "設定", "変更", "更新", "読み込み", "読込",
    "読み", "戻る", "進む", "トップ", "ヘルプ", "ログイン", "アカウント", "メニュー",
    "リンク", "タグ", "カテゴリ", "カテゴリー", "一覧", "確認", "開始", "終了",
    "コンテンツ", "ゲーム", "サイト", "ノート", "トーク", "特殊", "通常",
}


def _glossary_data() -> tuple[set[str], list[str]]:
    """返回 (glossary 已译 JA 精确集合, 专有/角色全名列表)。

    - gloss：names/skills/terms 三处所有 JA key 的精确匹配排除集合。
    - names：仅 names.yaml 的日文名 + 中文名，用于「角色名分词碎片」子串排除
      （绝不包含 skills/terms 的长句条目，否则会把 必殺/攻撃 等常见词误删）。
    """
    gloss: set[str] = set()
    names: list[str] = []
    # 1) 三处 glossary 的 JA key 全部进入精确排除
    for fn in ("names.yaml", "skills.yaml", "terms.yaml"):
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
                            gloss.add(k)
    # 2) 仅 names.yaml 用于角色名碎片子串排除
    np = GLOSSARY / "names.yaml"
    if np.exists():
        try:
            data = yaml.safe_load(np.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, dict):
                    for k, val in v.items():
                        if isinstance(k, str) and k.strip():
                            names.append(k)
                        if isinstance(val, str) and val.strip():
                            names.append(val)
    return gloss, names


# ---------- 2) 收集全站日语文案 ----------
_ASCII_RE = re.compile(r"^[\x00-\x7f]+$")
_NUM_RE = re.compile(r"^[\d.,，。%＋+／/()（）\s\-]+$")
_PUNCT_RE = re.compile(r"^[\s\W_]+$")
_HIRA_RE = re.compile(r"^[\u3040-\u309f]+$")          # 纯平假名
_KANA_RE = re.compile(r"^[\u3040-\u30ff\u31f0-\u31ff]+$")


def _collect_ja() -> list[str]:
    texts: list[str] = []
    for jf in sorted(I18N_DIR.rglob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
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


# ---------- 3) 分词 + 过滤 ----------
_KEEP_NOUN_SUBTYPES = {
    "一般", "固有名詞", "サ変接続", "形容動詞語幹", "ナイ形容詞語幹",
    "形容詞語幹", "副詞可能", "感動詞", "組織", "地域", "人名", "姓",
}
_DROP_NOUN_SUBTYPES = {"数", "代名詞", "非自立", "接尾", "接頭", "助数詞", "未知"}


def _keep_token(surface: str, pos: str, gloss: set, names: list) -> bool:
    if not surface or not surface.strip():
        return False
    if _ASCII_RE.match(surface) or _NUM_RE.match(surface) or _PUNCT_RE.match(surface):
        return False
    if surface in WIKI_UI:
        return False
    if surface in gloss:
        return False
    # 纯平假名 = 语法/功能词，游戏术语均为汉字/片假名 → 排除
    if _HIRA_RE.match(surface):
        return False
    top = pos.split(",")[0]
    if top == "名詞":
        sub = pos.split(",")[1] if len(pos.split(",")) > 1 else ""
        if sub in _DROP_NOUN_SUBTYPES:
            return False
        if sub not in _KEEP_NOUN_SUBTYPES and not _KANA_RE.match(surface):
            # 未知名词子类且非片假名 → 仅保留含汉字者
            if not re.search(r"[\u4e00-\u9fff]", surface):
                return False
        # 仅对【单字】做角色名子串排除（昂/神/連/木/月 等分词碎片）。
        # 绝不排除多字游戏词（攻撃/必殺/防御…即便其恰为某装备/BOSS 名子串），
        # 否则会误删真正的高频词汇。
        if len(surface) == 1 and any(surface in nm for nm in names):
            return False
        if _KANA_RE.match(surface) and len(surface) < 2:
            return False
        return True
    if top == "未知語":
        return True
    return False


def main() -> None:
    gloss, names = _glossary_data()
    print(f"[info] glossary 已译 JA：{len(gloss)}，专有/角色名：{len(names)}", file=sys.stderr)
    texts = _collect_ja()
    print(f"[info] 收集日语文案段：{len(texts)}", file=sys.stderr)

    tok = Tokenizer()
    cnt: Counter = Counter()
    n_tok = 0
    for i, t in enumerate(texts):
        for tk in tok.tokenize(t):
            n_tok += 1
            surf = tk.surface
            if not _keep_token(surf, tk.part_of_speech, gloss, names):
                continue
            cnt[surf] += 1
        if (i + 1) % 2000 == 0:
            print(f"[progress] {i+1}/{len(texts)} 段, 当前词种 {len(cnt)}", file=sys.stderr)

    print(f"[info] 分词总数 {n_tok}, 候选词种 {len(cnt)}", file=sys.stderr)
    items = [(c, w) for w, c in cnt.items() if c > THRESHOLD]
    items.sort(reverse=True)
    print(f"[info] 频率>{THRESHOLD} 的词汇：{len(items)}", file=sys.stderr)

    out = TODO_DIR / f"high_freq_terms_{date.today():%Y%m%d}.txt"
    with out.open("w", encoding="utf-8") as f:
        f.write(f"# 全站高频词汇（出现次数>{THRESHOLD}，已排除 glossary 已译词/角色名碎片/wiki-UI 词）\n")
        f.write(f"# 生成：tools/_analyze_freq.py  | 词种总数 {len(cnt)} | 命中 {len(items)}\n")
        f.write("# 格式：出现次数<TAB>日文\n")
        for c, w in items:
            f.write(f"{c}\t{w}\n")
    print(f"[done] 写出：{out}", file=sys.stderr)


if __name__ == "__main__":
    main()
