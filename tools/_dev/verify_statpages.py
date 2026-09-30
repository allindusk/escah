# -*- coding: utf-8 -*-
"""只验证「统计数据页」这一条链路（不跑整站 sync-site，秒级 ✓）。

验证四件事：
  ① 页面渲染：5 页 × 2 语言都能产出非空 HTML
  ② 落盘：md + frag JSON 写到正确位置，且 frag 里确实有 `escah-tbl` 表格 ✓
  ③ 侧栏：`sidebar.{ja,zh}.json` 里出现「数据统计 / データ調査」分组及其 4 个子项 ✓
  ④ 表格规模：统计总行数，确认数据没丢 ✓

用法：python tools/_dev/verify_statpages.py [--write]
      不带 --write 时只渲染不落盘（纯检查 ✓）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from escah_pipeline import config, sitegen, statpages  # noqa: E402


def main() -> int:
    write = "--write" in sys.argv
    dirs = {"ja": config.SITE_JA_DIR, "zh": config.SITE_ZH_DIR}

    # ① 渲染
    labels = statpages.load_labels()
    print(f"词表条目 {len(labels)} 条")
    total_rows = 0
    for page in statpages.PAGES:
        for loc in ("ja", "zh"):
            frag = statpages.render_page(page, labels, loc)
            if not frag:
                print(f"!! {page['slug']}[{loc}] 渲染为空")
                continue
            n_tbl = frag.count('class="escah-tbl"')
            n_tr = frag.count("<tr>")
            total_rows += n_tr
            print(f"   {page['slug']:<22}[{loc}] {len(frag):>7} 字｜表 {n_tbl} 张｜行 {n_tr}")
    print(f"\n全部页面表格行合计 {total_rows}")

    if write:
        n = statpages.write_pages(sitegen._write_md, dirs)
        print(f"已落盘 {n} 个 md")
        # ② frag 检查
        for slug in [p["slug"] for p in statpages.PAGES[:2]]:
            f = config.SITE_DIR / ".vitepress" / "frag" / f"{slug}.zh.json"
            ok = f.exists() and 'escah-tbl' in f.read_text(encoding="utf-8")
            print(f"   frag {slug}.zh.json: {'✓ 有表格' if ok else '✗ 缺失/无表格'}")
        # ③ 侧栏
        sitegen._write_sidebars(sitegen.load_registry())
        for loc in ("ja", "zh"):
            p = config.SITE_DIR / ".vitepress" / "generated" / f"sidebar.{loc}.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            hit = None
            for grp in data:
                for it in grp.get("items", []):
                    if it.get("link", "").endswith(f"/{loc}/statistics.html"):
                        hit = (grp["text"], it["text"], len(it.get("items", [])))
            print(f"   侧栏[{loc}] 数据统计分组: {hit if hit else '✗ 未找到'}")
    # ④ 完整性：非空单元格数必须 **JSON == 页面**
    #    （"信息展示全不全"的硬指标 ✓：清理空列/空行只允许丢空单元格 ✓，
    #      漏一行/一列都会被这个数字抓到 ✓）
    import re as _re

    # ⚠️ 数单元格**不要用正则** ✗（2026-09-30 两度踩坑：`<t[dh][^>]*>` 会把 `<thead>`
    # 也算成单元格 → 虚增 ✗；改成 `<t[dh][\s>]...` 又漏掉别的 ✓ 反复对不上 ✗）。
    # 改用 **lxml 真解析**（项目本来就依赖 ✓）：`//td|//th` 取元素、只数非空的 ✓，精确且不脆 ✓。
    import lxml.html as _lxml_html

    def count_nonempty(html: str) -> int:
        try:
            root = _lxml_html.fragment_fromstring(html, create_parent="div")
        except Exception:  # noqa: BLE001
            return 0
        return sum(1 for el in root.xpath("//td|//th")
                   if (el.text_content() or "").strip())

    total_json = total_html = 0
    for page in statpages.PAGES:
        if not page.get("package"):
            continue
        data = statpages._pkg(page["package"])
        if not data:
            continue
        for sheet in statpages._pick_sheets(data, page.get("sheets") or []):
            for t in sheet["tables"]:
                for r in (t.get("header") or []) + (t.get("rows") or []):
                    total_json += sum(1 for c in r if (c.get("t") or "").strip())
        html = statpages.render_page(page, labels, "zh")
        total_html += count_nonempty(html)
    ok = total_json == total_html
    print(f"非空单元格：JSON {total_json} vs 页面 {total_html} → {'✓ 一致（信息未丢）' if ok else '✗ 不一致！'}")
    if not ok:
        # 逐页/逐表定位多出来（或少了）的单元格 ✓
        for page in statpages.PAGES:
            if not page.get("package"):
                continue
            data = statpages._pkg(page["package"])
            if not data:
                continue
            pj = ph = 0
            per_table = []
            for sheet in statpages._pick_sheets(data, page.get("sheets") or []):
                for t in sheet["tables"]:
                    j = sum(1 for r in (t.get("header") or []) + (t.get("rows") or [])
                            for c in r if (c.get("t") or "").strip())
                    h = count_nonempty(statpages.render_table(t, labels, "zh"))
                    pj += j
                    ph += h
                    if j != h:
                        per_table.append((sheet["name"], t.get("nrows"), j, h))
            print(f"   {page['slug']}: JSON {pj} vs 页面 {ph}")
            for name, nrows, j, h in per_table:
                print(f"        不一致 [{name}] {nrows}行: JSON {j} → 页面 {h}")
    return 0 if ok else 2



if __name__ == "__main__":
    raise SystemExit(main())
