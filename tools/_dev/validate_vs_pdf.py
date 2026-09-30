# -*- coding: utf-8 -*-
"""**交叉校验**：作者的 PDF 发布稿 ⇄ 我从 HTML 网格导出解析出的 `data/statdata/*.json`。

为什么要有这个（2026-09-30 用户明确的原需求 ✓）：同一样东西作者给了**两种文件** ——
  ① `recycle_bin/data/*.html`：Google 表格的**网格导出** ✓（我据此建的站 ✓，结构完整但只是原始网格 ✓）
  ② `recycle_bin/data/*.pdf` ：作者的**最终发布稿** ✓（排版/配色/图表是终版 ✓，但机器取用不如网格 ✓）
两种独立来源互为对照 ⇒ 才能查出"**我漏了什么 / 我解析错什么**" ✓（自己跟自己比是没有意义的 ✗）。

校验三层：
  ① **工作表集合**：PDF 目次页列出的 sheet 名 ⇄ JSON 里收录的 sheet 名（查"漏表"✓）
  ② **数值多重集**：PDF 全部数字 token ⇄ JSON 全部数字 token（查"漏数/多数/精度对不上"✓）
  ③ **文本 token**：PDF 行内文字 ⇄ JSON 单元格文字（辅助定位，取样本人工看 ✓）

用法：
  python tools/_dev/validate_vs_pdf.py            # 全部包
  python tools/_dev/validate_vs_pdf.py d2p-gacha  # 单个包
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
STAT = ROOT / "data" / "statdata"
RAWD = ROOT / "recycle_bin" / "data"

# key → PDF 文件名（PDF 是"发布稿"，未必收录该包全部 sheet ✗，如 box 只发布了「要因」1 页 ✓）
PDFS = {
    "annihilation": "殲滅戦報酬調べるくんv1.1.pdf",
    "d2p-gacha": "D2Pガチャしらべるくんv1.3.pdf",
    "box": "ボックスしらべるくん - 要因.pdf",
    "treasure-open": "宝箱開封しらべるくんv2.12.pdf",
}

_NUM_RE = re.compile(r"(?<![\d.])\d[\d,]*(?:\.\d+)?")
_DOT_RE = re.compile(r"^[・•·]\s*")


def norm_num(tok: str) -> str:
    """数字 token 归一化：去千分位 ✓、浮点保留 2 位 ✓（PDF 显示值就是 2 位 ✓）。"""
    s = tok.replace(",", "")
    try:
        f = float(s)
    except ValueError:
        return s
    if f == int(f):
        return str(int(f))
    return f"{f:.2f}"


def json_nums(data: dict) -> "collections.Counter[str]":
    out: "collections.Counter[str]" = collections.Counter()
    for sheet in data["sheets"]:
        for t in sheet["tables"]:
            for r in (t.get("header") or []) + (t.get("rows") or []):
                for c in r:
                    for m in _NUM_RE.finditer(c.get("t") or ""):
                        out[norm_num(m.group(0))] += 1
    return out


def json_sheets(data: dict) -> "list[str]":
    return [s["name"] for s in data["sheets"]]


def pdf_pages_text(pdf: Path) -> "list[str]":
    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    return [" ".join((p.extract_text() or "").split()) for p in reader.pages]


def pdf_toc_names(pages: "list[str]") -> "list[str]":
    """目次/集計シート一覧 页里 `・名前` 形式的 sheet 名 ✓。"""
    out: "list[str]" = []
    for txt in pages:
        for part in re.split(r"\s(?=・)", txt):
            m = _DOT_RE.match(part.strip())
            if m:
                name = part.strip()[m.end():].strip()
                if name and len(name) < 60 and not name[0].isdigit():
                    out.append(name)
    return out


def main() -> int:
    keys = sys.argv[1:] or list(PDFS)
    grand = 0
    for key in keys:
        jp = STAT / f"{key}.json"
        pp = RAWD / PDFS.get(key, "")
        if not jp.exists() or not pp.exists():
            print(f"\n===== {key}：缺文件（json={jp.exists()} pdf={pp.exists()}）✗")
            continue
        data = json.loads(jp.read_text(encoding="utf-8"))
        pages = pdf_pages_text(pp)
        ptext = " ".join(pages)
        # ① 工作表集合
        jsheets = json_sheets(data)
        toc = pdf_toc_names(pages)
        toc_set, jset = set(toc), set(jsheets)
        print(f"\n===== {key}")
        print(f"  ① 工作表：JSON {len(jsheets)} 个 ⇄ PDF 目次 {len(set(toc))} 个"
              f"｜两边都有 {len(toc_set & jset)}")
        only_pdf = [n for n in toc if n not in jset]
        only_json = [n for n in jsheets if n not in toc_set]
        if only_pdf:
            print(f"     ⚠ PDF 有、JSON 无（{len(only_pdf)}）: {only_pdf[:8]}")
        if only_json:
            print(f"     ⚠ JSON 有、PDF 目次无（{len(only_json)}）: {only_json[:8]}")
        # ② 数值多重集
        jn = json_nums(data)
        pn: "collections.Counter[str]" = collections.Counter()
        pn_page: "dict[str, int]" = {}
        for i, txt in enumerate(pages):
            for m in _NUM_RE.finditer(txt):
                v = norm_num(m.group(0))
                pn[v] += 1
                pn_page.setdefault(v, i + 1)
        miss = pn - jn              # PDF 有、JSON 里数量不足 ⇒ 疑似漏数 ✗
        extra = jn - pn             # JSON 有、PDF 里没有 ⇒ 疑似解析噪声/重复 ✗
        print(f"  ② 数值：PDF {sum(pn.values())} 个 token（{len(pn)} 种）"
              f" ⇄ JSON {sum(jn.values())} 个（{len(jn)} 种）")
        print(f"     PDF 有而 JSON 不足的 {sum(miss.values())} 个 / {len(miss)} 种")
        for v, n in list(miss.items())[:12]:
            print(f"        {v:>16}  差 {n} 个   （PDF 首次出现 p{pn_page.get(v)}）")
        print(f"     JSON 有而 PDF 没有的 {sum(extra.values())} 个 / {len(extra)} 种")
        for v, n in list(extra.items())[:8]:
            print(f"        {v:>16}  多 {n} 个")
        grand += sum(miss.values())
    print(f"\n总计：PDF 有而 JSON 不足的数值 token = {grand} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
