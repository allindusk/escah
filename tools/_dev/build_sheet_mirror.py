# -*- coding: utf-8 -*-
"""把攻略作者导出的 Google 表格**原样**取出来做保真镜像（不改结构、不改样式、不翻译）。

用户要求（2026-09-30）："完全不改原来的格式，也不用项目里的表格样式，先用 HTML 完全镜像
展示静态数据，看看能不能镜像到一模一样"。

做法：每个 sheet 的原始 `.html` 里都有一个 `<table class="waffle">…</table>` ✓ ——
它的**内联样式**（背景色、加粗、字号、对齐）承载了原表的视觉信息 ✓，而解析成 JSON 时
这些样式会被丢掉 ✗。所以保真镜像**不经过 JSON** ✓，直接把这个 table 元素原样搬过来 ✓。

产物：`data/statdata/mirror/<包key>.json` = {"sheets":[{"name":..., "html":...}]} ✓（入库 ✓）。

用法：
  python tools/_dev/build_sheet_mirror.py                 # 只体检：列出各包各 sheet 的体积
  python tools/_dev/build_sheet_mirror.py --apply         # 写出镜像 JSON
"""

from __future__ import annotations

import html as _html
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "recycle_bin" / "data"
OUT = ROOT / "data" / "statdata" / "mirror"

# 包 key → 原始目录名前缀（与 statpages.PAGES 一致 ✓）
PKGS = {
    "annihilation": "殲滅戦報酬調べるくん",
    "d2p-gacha": "D2Pガチャしらべるくん",
    "box": "ボックスしらべるくん",
    "treasure-open": "宝箱開封しらべるくん",
}

_SCRIPT_RE = re.compile(r"<script\b.*?</script>", re.S | re.I)


def extract_table(path: Path) -> str:
    """取原始 html 里的第一个 `<table class="waffle">…</table>`（原样，含内联样式 ✓）。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'<table[^>]*class="[^"]*waffle[^"]*".*?</table>', text, re.S | re.I)
    if not m:
        m = re.search(r"<table\b.*?</table>", text, re.S | re.I)
    if not m:
        return ""
    frag = m.group(0)
    # Google 导出里 table 内部不会有 script ✗，但保险起见清一下 ✓
    return _SCRIPT_RE.sub("", frag)


def verify() -> int:
    """结构校验：镜像页必须与源文件**结构逐格一致** ✓，只允许文字不同（已翻译 ✓）。

    判据（2026-09-30 改：翻译后"逐字节一致"不再适用 ✓）：
      · 工作表数量与顺序一致 ✓
      · 每张表的**单元格数**一致 ✓
      · 每个单元格的 `tag / colspan / rowspan / style` 指纹一致 ✓
        ⇒ 版式（底色 / 加粗 / 合并 / 空行空列）一格没动 ✓，只有文字变成了中文 ✓
    """
    import lxml.html as LH

    page_dir = ROOT / "site" / "public" / "mirror"
    bad = 0
    for key, prefix in PKGS.items():
        page = page_dir / f"{key}.html"
        if not page.exists():
            print(f"!! {page.name} 不存在（先跑 verify_statpages.py --write ✓）")
            bad += 1
            continue
        proot = LH.fragment_fromstring(page.read_text(encoding="utf-8", errors="replace"),
                                      create_parent="div")
        secs = proot.xpath("//section[contains(@class,'sheet')]")
        d = next((p for p in RAW.glob(prefix + "*") if p.is_dir()), None)
        if d is None:
            continue
        src = [(f.stem, extract_table(f)) for f in sorted(d.glob("*.html"))]
        src = [(n, g) for n, g in src if g]
        n_ok = n_bad = 0
        if len(src) != len(secs):
            print(f"   ✗ [{key}] 工作表数不一致：源 {len(src)} vs 页面 {len(secs)}")
            bad += 1
            continue
        for (name, frag), sec in zip(src, secs):
            a = LH.fragment_fromstring(frag, create_parent="div").xpath("//td|//th")
            b = sec.xpath(".//td|.//th")
            fa = [(c.tag, c.get("colspan"), c.get("rowspan"), c.get("style")) for c in a]
            fb = [(c.tag, c.get("colspan"), c.get("rowspan"), c.get("style")) for c in b]
            if fa == fb:
                n_ok += 1
            else:
                n_bad += 1
                print(f"   ✗ [{key}] {name} 结构对不上"
                      f"（单元格 {len(a)} vs {len(b)} ✓ 指纹差异 "
                      f"{sum(1 for x, y in zip(fa, fb) if x != y)} 处）")
        print(f"{key:<16} 结构一致 {n_ok} / 不一致 {n_bad}")
        bad += n_bad
    print("✓ 结构与原始导出逐格一致（仅文字已译）" if bad == 0 else f"✗ 有 {bad} 个工作表对不上")
    return 0 if bad == 0 else 2


def main() -> int:
    if "--verify" in sys.argv:
        return verify()
    apply = "--apply" in sys.argv
    total = 0
    for key, prefix in PKGS.items():
        d = next((p for p in RAW.glob(prefix + "*") if p.is_dir()), None)
        if d is None:
            print(f"!! 找不到 {prefix}*")
            continue
        sheets = []
        pkg_size = 0
        for f in sorted(d.glob("*.html")):
            frag = extract_table(f)
            if not frag:
                continue
            sheets.append({"name": f.stem, "html": frag})
            pkg_size += len(frag.encode("utf-8"))
        total += pkg_size
        print(f"{key:<16} {len(sheets):>2} sheet  镜像 {pkg_size / 1024:>8.1f} KB")
        # 抽查一条：确认内联样式在 ✓（保真镜像的关键 ✓）
        if sheets:
            sample = sheets[0]["html"]
            n_style = sample.count("style=")
            print(f"   例 [{sheets[0]['name']}] 长度 {len(sample)} 字符，含 style= {n_style} 处")
        if apply:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / f"{key}.json").write_text(
                json.dumps({"sheets": sheets}, ensure_ascii=False), encoding="utf-8", newline="\n"
            )
    print(f"\n四包合计镜像体积 {total / 1024 / 1024:.2f} MB")
    if apply:
        print(f"已写出到 {OUT.relative_to(ROOT)}")
    else:
        print("（dry-run；加 --apply 写出 ✓）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
