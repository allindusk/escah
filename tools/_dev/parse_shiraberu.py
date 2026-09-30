# -*- coding: utf-8 -*-
"""把攻略作者提供的 4 套「しらべるくん」HTML 解析成**干净 JSON**，供站点生成器使用。

为什么要有这一步（2026-09-28）：
  · 原始素材是 **Google スプレッドシート的 HTML 导出**：数据硬编码在
    `<table class="waffle">` 里，每个包还带一份 **4MB 的 `resources/sheet.css`**，
    整行被压成超长单行、列头靠绝对定位 → **不适合直接嵌入站点** ✗（样式污染 + 体积 + 移动端崩）。
  · 而且源目录 `recycle_bin/` 已被 .gitignore ✗ → CI 拿不到素材 ✗。
  ⇒ 解析成 JSON（`data/statdata/*.json`）并入库 ✓，站点生成器只读 JSON ✓（可复现 ✓）。

解析要点：
  · `colspan/rowspan` 会记录下来 ✓（合并表头在渲染时要还原）
  · `softmerge-inner` 包装层要去掉 ✓（Google 用它做软合并）
  · 末尾空行/空列裁掉 ✓
  · 单元格数 > 阈值的表标 `raw: true` ✓（如 8 张上万格的原始开箱明细 ✗，站点不渲染，只作下载）

用法：
  python tools/_dev/parse_shiraberu.py               # dry-run：报告各包解析概况
  python tools/_dev/parse_shiraberu.py --apply       # 写出 data/statdata/*.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "recycle_bin" / "data"
OUT = ROOT / "data" / "statdata"
# 超过这么多单元格的表视为「原始明细」（不渲染，只作下载）。
# 2026-09-28 调参：原 2000 会把「ボックス 調査」（150 行×多列=2726 格）也标成 raw ✗，
# 而它是**有用的逐次调查记录**（表格增强器能轻松吃下 150 行 ✓）→ 提到 5000，
# 这样只有真正巨大的（`集計(*)` 上万格、`結果(グラフ)` 67×110）才走 raw ✓。
RAW_CELL_LIMIT = 5000

PACKAGES = [
    ("treasure-open", "宝箱開封しらべるくんv2.12"),
    ("annihilation", "殲滅戦報酬調べるくんv1.1"),
    ("d2p-gacha", "D2Pガチャしらべるくんv1.3"),
    ("box", "ボックスしらべるくん"),
]


def _text(cell) -> str:
    """取单元格文本：剥掉 softmerge 包装层，压缩空白。"""
    for inner in cell.select(".softmerge-inner"):
        inner.unwrap()
    t = cell.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", t).strip()


_COL_LETTER_RE = re.compile(r"^[A-Z]{1,3}$")


def _strip_sheet_chrome(header_rows, body_rows):
    """剥掉 Google 表格导出自带的「列字母表头行(A B C…)」与「行号列(1 2 3…)」。

    实测（殲滅戦報酬）：每张表首行是 A..J 的列字母行、每行第 0 格是行号 ✗，
    真实内容自第 2 行第 2 列起。不剥掉的话：页面上多一层噪声、且表头行数/列数
    与真实结构不符（后续按表头做中文化会错位 ✗）。
    """
    # ② 行号列：正文 ≥80% 行首格是 th 且为纯数字 ⇒ 整列都是行号（先剥，见下注释）
    if body_rows:
        numbered = sum(
            1 for r in body_rows
            if r and r[0].get("h") and r[0].get("t", "").strip().isdigit()
        )
        if numbered >= max(1, int(len(body_rows) * 0.8)):
            header_rows = [r[1:] for r in header_rows]
            body_rows = [r[1:] for r in body_rows]

    # ① 列字母行：**必须放在剥行号之后** ✗ —— 未剥时该行首格是空的行号格，
    #    于是 texts=[\"\", \"A\", \"B\", …] 全字母判定失败、字母行残留 ✗（实测踩过）。
    #    判定时**忽略空单元格**，并要求非空的都是 A..Z/AA 且按字典序。
    def is_letters(r) -> bool:
        if not r:
            return False
        nonempty = [c for c in r if c.get("t", "").strip()]
        if len(nonempty) < 2 or not all(c.get("h") for c in nonempty):
            return False
        texts = [c.get("t", "").strip() for c in nonempty]
        if not all(_COL_LETTER_RE.match(t) for t in texts):
            return False
        return texts == sorted(texts)

    header_rows = [r for r in header_rows if not is_letters(r)]

    # ③ 去掉**所有**「整列为空」的列（不只是前导列 ✗）与「整行为空」的前导行。
    #    为什么：作者的表里有大量装饰性**空列**（如 結果(合計) 那张宽矩阵），
    #    只清前导列 ✗ → 页面上是一大片空白列 ✗（2026-09-30 浏览器实测所见）。
    #    判定：表头+正文里该列**所有**单元格都为空**且无合并** ⇒ 该列无信息，可去 ✓。
    all_rows = header_rows + body_rows
    width = max((len(r) for r in all_rows), default=0)
    used = [False] * width
    for r in all_rows:
        for i, c in enumerate(r):
            if c.get("t", "").strip() or c.get("cs", 1) > 1 or c.get("rs", 1) > 1:
                used[i] = True
    if used and not all(used):
        keep = [i for i in range(width) if used[i]]
        header_rows = [[r[i] for i in keep if i < len(r)] for r in header_rows]
        body_rows = [[r[i] for i in keep if i < len(r)] for r in body_rows]
    while header_rows and not any(c.get("t", "").strip() for c in header_rows[0]):
        header_rows.pop(0)
    while body_rows and not any(c.get("t", "").strip() for c in body_rows[0]):
        body_rows.pop(0)
    return header_rows, body_rows


def parse_table(tbl) -> dict:
    header_rows: "list[list[dict]]" = []
    body_rows: "list[list[dict]]" = []
    for tr in tbl.find_all("tr", recursive=True):
        cells = tr.find_all(["td", "th"], recursive=False)
        if not cells:
            continue
        entry = []
        for c in cells:
            # 紧凑编码（2026-09-28）：默认值不写 ✓ —— 每个单元格都带 cs/rs/th 时
            # treasure-open.json 到 1.17MB ✗；只写非默认后体积降一个量级 ✓。
            # 约定：t=文本；cs=colspan(>1 才写)；rs=rowspan(>1 才写)；h=1 表示表头格
            cell = {"t": _text(c)}
            cs = int(c.get("colspan") or 1)
            rs = int(c.get("rowspan") or 1)
            if cs > 1:
                cell["cs"] = cs
            if rs > 1:
                cell["rs"] = rs
            if c.name == "th":
                cell["h"] = 1
            entry.append(cell)
        # 整行是 th（或首行）→ 表头行（注意紧凑编码里表头标记是 "h" ✓）
        if (entry and all(e.get("h") for e in entry)) or (
            not header_rows and entry and entry[0].get("h")
        ):
            header_rows.append(entry)
        else:
            body_rows.append(entry)
    # 裁掉尾部整行空 + 行内尾部空列
    def _blank(e) -> bool:
        return all(not x["t"] for x in e)

    while body_rows and _blank(body_rows[-1]):
        body_rows.pop()
    width = 0
    for e in header_rows + body_rows:
        w = sum(x.get("cs", 1) for x in e)      # 紧凑编码：cs 缺省为 1 ✓
        width = max(width, w)
    # 尾部空列：从后往前看，若某列在所有行都空则去掉（保留 colspan 语义）
    def _trim_row(e):
        while e and _blank([e[-1]]):
            e.pop()
        return e

    header_rows = [_trim_row(e) for e in header_rows]
    body_rows = [_trim_row(e) for e in body_rows]
    header_rows, body_rows = _strip_sheet_chrome(header_rows, body_rows)
    n_cells = sum(len(e) for e in header_rows + body_rows)
    return {
        "header": header_rows,
        "rows": body_rows,
        "nrows": len(body_rows),
        "ncols": width,
        "raw": n_cells > RAW_CELL_LIMIT,
    }


def parse_package(key: str, dirname: str) -> dict:
    d = SRC / dirname
    sheets = []
    if not d.exists():
        return {"key": key, "dir": dirname, "sheets": [], "missing": True}
    for html in sorted(d.glob("*.html")):
        raw = html.read_text(encoding="utf-8", errors="replace")
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            print("!! 需要 beautifulsoup4（pip install beautifulsoup4）")
            raise SystemExit(2)
        soup = BeautifulSoup(raw, "html.parser")
        tables = []
        raw_meta = []
        for tbl in soup.find_all("table", class_=lambda c: c and "waffle" in c):
            t = parse_table(tbl)
            if not (t["nrows"] or t["header"]):
                continue
            if t["raw"]:
                # ⚠️ 原始明细**不收录数据**（只留规模）：实测收录后 treasure-open.json 会到 4MB ✗，
                #    而站点根本不渲染它们（上万格）→ 只记 nrows/ncols 供页面如实说明 ✓。
                raw_meta.append({"nrows": t["nrows"], "ncols": t["ncols"]})
                continue
            tables.append(t)
        sheets.append({
            "file": html.name,
            "name": html.stem,
            "tables": tables,
            "rawTables": raw_meta,
            "cells": sum(sum(len(e) for e in t["header"] + t["rows"]) for t in tables),
        })
    return {"key": key, "dir": dirname, "sheets": sheets}


def main() -> int:
    apply = "--apply" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    total_cells = 0
    for key, dirname in PACKAGES:
        data = parse_package(key, dirname)
        if data.get("missing"):
            print(f"[{key}] 目录不存在：{dirname}")
            continue
        cells = sum(s["cells"] for s in data["sheets"])
        total_cells += cells
        big = [s["name"] for s in data["sheets"] if any(t["raw"] for t in s["tables"])]
        print(f"\n[{key}] {dirname}")
        print(f"    页面 {len(data['sheets'])} 个｜单元格 {cells}")
        print(f"    原始明细页（不渲染，仅下载）：{big if big else '无'}")
        for s in data["sheets"][:60]:
            if any(t["raw"] for t in s["tables"]):
                continue
            desc = "、".join(f"表{i + 1}({t['nrows']}行×{t['ncols']}列)" for i, t in enumerate(s["tables"]))
            print(f"      · {s['name']}: {desc}")
        if apply:
            p = OUT / f"{key}.json"
            p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                         encoding="utf-8", newline="\n")
            print(f"    → 写出 {p.relative_to(ROOT)}（{p.stat().st_size / 1024:.1f} KB）")
    print(f"\n合计单元格 {total_cells}")
    if not apply:
        print("（dry-run；加 --apply 写出 data/statdata/*.json）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
