"""全站一致性扫描：核对原站快照(data/raw) 与镜像片段(data/parsed/ja) 的内容保真度。

重点：
1. 评论镜像：每页 raw #body 与 parsed 片段中的 li.pcmt 数量是否一致（评论是否全镜像）。
2. 正文保真：独立从 raw 抽取“读者可见文本”（去掉脚本/样式/导航/尾注/广告/评论提交表单/
   死链，但保留评论），与 parsed 片段文本做 difflib 相似度，标记明显内容缺失的页面。

输出：控制台摘要 + tools/_verify_report.txt
用法：python tools/verify_consistency.py
"""
from __future__ import annotations

import os
import sys
import unicodedata
import urllib.parse
import difflib
from pathlib import Path

from bs4 import BeautifulSoup
import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PARSED_JA = ROOT / "data" / "parsed" / "ja"
REGISTRY = ROOT / "data" / "registry" / "pages.yaml"

CHROME_SELECTORS = ".navi, .lastmodified, .rss, .toolbar, #navigator, #footer, .comment_form, #body > .plugin_comment"


def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return " ".join(s.split())


def raw_visible_text(raw_html: str) -> str:
    """从原站快照抽取读者可见文本（独立实现，保留评论）。"""
    soup = BeautifulSoup(raw_html, "lxml")
    body = soup.find("div", id="body")
    if body is None:
        return ""
    for sel in ("script", "style", "noscript", "iframe"):
        for t in body.find_all(sel):
            t.decompose()
    for t in body.select(CHROME_SELECTORS):
        t.decompose()
    # 评论区：先把评论 <ul> 从 form 中解救出来（与解析器 _keep_pcomments 一致），
    # 再删除提交表单/死链/包裹评论的 form/表单 CSS。否则评论会随 form 被删。
    # 注意：部分页面评论区在 #body 之外（孤立），需在整文档层面救援并移入 #body。
    for div in soup.find_all("div", class_="pcomment"):
        for form in list(div.find_all("form")):
            ul = form.find("ul")
            if ul is not None and ul.find("li", class_="pcmt") is not None:
                form.insert_before(ul)
            form.decompose()
        pf = div.find("div", id="pcomment-form")
        if pf is not None:
            pf.decompose()
        for p in div.find_all("p"):
            if "最新の20件" in (p.get_text() or ""):
                p.decompose()
        for st in div.find_all("style"):
            st.decompose()
    # 把 #body 之外的评论区移入 #body（与解析器 parse_page_html 一致）
    if body is not None:
        for pc in list(soup.find_all("div", class_="pcomment")):
            if pc.find_parent(id="body") is None:
                body.append(pc)
    # 其它残留 form（不应含正文内容）
    if body is not None:
        for f in body.find_all("form"):
            f.decompose()
    return norm_text(body.get_text(" ", strip=True))


def count_pcmt(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")
    return len(soup.find_all("li", class_="pcmt"))


def main() -> int:
    reg = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    pages = reg.get("pages", [])

    total = 0
    comment_mismatch = []      # (slug, raw_n, parsed_n)
    low_ratio = []             # (slug, ratio)
    no_raw = []
    no_parsed = []
    raw_comments = 0
    parsed_comments = 0
    ratio_sum = 0.0

    for entry in pages:
        name = entry.get("name", "")
        slug = entry.get("slug", "")
        is_char = slug.startswith("characters/")
        total += 1

        raw_path = RAW_DIR / (urllib.parse.quote(name, safe="") + ".html")
        parsed_path = PARSED_JA / (slug + ".html")
        if not raw_path.exists():
            no_raw.append(slug)
            continue
        if not parsed_path.exists():
            no_parsed.append(slug)
            continue

        raw_html = raw_path.read_text(encoding="utf-8")
        parsed_html = parsed_path.read_text(encoding="utf-8")

        rn = count_pcmt(raw_html)
        pn = count_pcmt(parsed_html)
        raw_comments += rn
        parsed_comments += pn
        if rn != pn:
            comment_mismatch.append((slug, rn, pn, "char" if is_char else "main"))

        golden = raw_visible_text(raw_html)
        parsed_text = norm_text(BeautifulSoup(parsed_html, "lxml").get_text(" ", strip=True))
        if golden and parsed_text:
            ratio = difflib.SequenceMatcher(None, golden, parsed_text).ratio()
        else:
            ratio = 0.0
        ratio_sum += ratio
        if ratio < 0.9:
            low_ratio.append((slug, round(ratio, 3), "char" if is_char else "main"))

    avg_ratio = ratio_sum / total if total else 0.0

    lines = []
    lines.append("=" * 70)
    lines.append("全站一致性扫描报告 (raw data/raw  vs  mirror data/parsed/ja)")
    lines.append("=" * 70)
    lines.append(f"注册表页面总数        : {total}")
    lines.append(f"raw 缺失(未抓取)      : {len(no_raw)}  -> {no_raw}")
    lines.append(f"parsed 缺失           : {len(no_parsed)}  -> {no_parsed}")
    lines.append(f"原站评论总数(raw)     : {raw_comments}")
    lines.append(f"镜像评论总数(parsed)  : {parsed_comments}")
    lines.append(f"评论数量不一致的页面  : {len(comment_mismatch)}")
    for slug, rn, pn, kind in comment_mismatch:
        lines.append(f"   - [{kind}] {slug}: raw={rn} parsed={pn}")
    lines.append(f"正文平均相似度        : {avg_ratio:.3f}")
    lines.append(f"相似度<0.9 的页面     : {len(low_ratio)}")
    for slug, r, kind in low_ratio:
        lines.append(f"   - [{kind}] {slug}: ratio={r}")
    lines.append("=" * 70)
    report = "\n".join(lines)
    print(report)

    out = ROOT / "tools" / "_verify_report.txt"
    out.write_text(report + "\n", encoding="utf-8")
    print(f"\n报告已写入 {out}")

    # 退出码：评论全镜像且无内容缺失 -> 0；否则 1
    return 0 if (not comment_mismatch and not low_ratio) else 1


if __name__ == "__main__":
    sys.exit(main())
