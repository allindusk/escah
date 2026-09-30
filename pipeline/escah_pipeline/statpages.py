# -*- coding: utf-8 -*-
"""把攻略作者的「しらべるくん」统计数据（`data/statdata/*.json`）生成为站点页面。

设计（2026-09-28）：
  · 数据源 = `tools/_dev/parse_shiraberu.py` 从 Google 表格 HTML 解析出的 JSON（**已入库** ✓，
    因为原始 HTML 在 .gitignore 的 recycle_bin/ 里、CI 拿不到 ✗）。
  · 页面**不注册成 registry 镜像页** ✗ —— 否则会污染首页统计/进度表、且触发"镜像页自动进导航"的
    硬约束。改为在 `sync_site` 里直接生成 md + frag ✓，侧栏由 `sitegen` 显式插入一个分组 ✓。
  · 表格一律带 `class="escah-tbl"` ✓ → 站点既有的 `tableEnhancer.ts` 会自动给它们加
    **表头三态排序 / 列多选筛选 / 全屏 / 重置** ✓（这是原 Google 表格做不到的 ✓）。
  · 单元格策略：纯数字/日期/百分号**原样保留** ✓；其余按 `glossary/stat_labels.yaml`
    词表翻成中文 ✓（查不到就**保留日文**并在 `--report` 里列出来 ✓，绝不瞎编 ✗）。

用法：
  python -m escah_pipeline.statpages --report      # 盘点所有"非数字单元格"，指导补词表
  python -m escah_pipeline.statpages --dump <slug> # 打印某页将生成的 HTML（本地检查）
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from . import config  # noqa: E402

STAT_DIR = config.DATA_DIR / "statdata"
LABELS_PATH = config.ROOT / "glossary" / "stat_labels.yaml"

# 纯数字（含千分位/小数/正负号）、百分号、日期、范围 → 原样保留，不查词表
_NUM_RE = re.compile(r"^[+\-−]?[\d,]+(?:\.\d+)?%?$|^\d{4}/\d{1,2}/\d{1,2}$|^[\d.]+\s*[~〜～]\s*[\d.]+$")

# 假名检测：用于「半译则弃」判定 ✓ 与 `--kana` 量化验收 ✓
_KANA_RE = re.compile(r"[\u3041-\u3096\u30a1-\u30fa\u30fd-\u30ff]")

# ------------------------------------------------------------------ 页面定义 ----
# sheet 用**名字前缀**匹配（导出文件名即 sheet 名，含 (合計) 之类后缀 ✓）
PAGES: list[dict] = [
    {
        "slug": "statistics",
        "title_ja": "データ調査",
        "title_zh": "数据统计",
        "intro_zh": (
            "本区收录攻略作者 <strong>しらべるくん</strong> 系列工具的实测统计数据（歼灭战报酬、D2P 扭蛋、"
            "战斗箱子掉落、宝箱开箱效率）。原始数据由作者以 Google 表格维护，本页为镜像整理版，"
            "表格可按任意列排序、按列筛选。"
        ),
        "intro_ja": (
            "攻略作者 <strong>しらべるくん</strong> シリーズの実測データ（殲滅戦報酬・D2Pガチャ・"
            "ボックスドロップ・宝箱開封効率）をまとめたものです。表は列ソート／フィルタ可。"
        ),
        "children": [
            ("stat-annihilation", "歼灭战报酬", "殲滅戦報酬"),
            ("stat-d2p-gacha", "D2P 扭蛋", "D2Pガチャ"),
            ("stat-box", "战斗箱子掉落", "ボックスドロップ"),
            ("stat-treasure-open", "宝箱开箱效率", "宝箱開封"),
        ],
        "sheets": [],
    },
    {
        "slug": "stat-annihilation",
        "title_ja": "殲滅戦報酬（実測）",
        "title_zh": "歼灭战报酬（实测）",
        "package": "annihilation",
        "intro_zh": "歼灭战的等级报酬、击退敌人积分、获得 D2P 与结束后报酬的计算依据。",
        "intro_ja": "殲滅戦のLv報酬・撃退ポイント・獲得D2P・開催後報酬の算出根拠。",
        "sheets": ["殲滅Lv報酬", "宝箱", "獲得D2P計算", "開催後報酬", "変更履歴"],
    },
    {
        "slug": "stat-d2p-gacha",
        "title_ja": "D2Pガチャ（実測）",
        "title_zh": "D2P 扭蛋（实测）",
        "package": "d2p-gacha",
        "intro_zh": "D2P 扭蛋的实测排出率与影响排出的因素（VIP 等级、提供割合、卖却值等）。",
        "intro_ja": "D2Pガチャの実測排出率と、排出に影響する要因（VIP・提供割合・売却値など）。",
        "sheets": ["結果", "要因", "前提条件", "参照用", "変更履歴"],
    },
    {
        "slug": "stat-box",
        "title_ja": "ボックスのドロップ（実測）",
        "title_zh": "战斗箱子掉落（实测）",
        "package": "box",
        "intro_zh": "战斗箱子（ボックス）的道具掉落概率实测，以及与 1-2-8H 周回的效率对比。",
        "intro_ja": "ボックスのドロップ率実測と、1-2-8H周回との効率比較。",
        "sheets": ["結果", "要因", "調査"],
    },
    {
        "slug": "stat-treasure-open",
        "title_ja": "宝箱開封の効率（実測）",
        "title_zh": "宝箱开箱效率（实测）",
        "package": "treasure-open",
        "intro_zh": (
            "宝箱开箱的蝶矿石产出、石割效率与 8 种自动配置的横向对比。"
            "原始明细表（上万格）未收录，仅保留汇总口径。"
        ),
        "intro_ja": "宝箱開封の蝶鉱石産出・石割効率・8種の自動配置比較。生データの集計表は未収録。",
        # 只列"希望的阅读顺序"✓；**其余 sheet 由 _pick_sheets 自动追加** ✓（不遗漏 ✓）。
        # 2026-09-30：原先只列 8 个前缀 ✗ → 23 个有数据的 sheet 只渲染了 7 个 ✗✗。
        "sheets": ["結果(合計)", "結果(比較)", "石割効率", "宝箱数と蝶鉱石", "要因", "前提条件", "検証"],
    },
]


def load_labels() -> "dict[str, str]":
    """合并两层词表 → {ja: zh}：

      ① `glossary/stat_labels.yaml`：本页专属的**结构性标签**（表头/栏目/汇总词）✓
      ② **站内既有词表**（names / terms / high_freq / phrases / phrases_manual）：
         道具名、角色名、术语的**站内定译** ✓ —— 直接复用，保证与全站一致 ✓
         （实测 1347 种单元格文本里绝大多数是道具名，逐条手翻不现实 ✗，复用才现实 ✓）

    查不到时由 `label()` **保留日文原文** ✓（绝不瞎编 ✗）。
    """
    labels: "dict[str, str]" = {}
    # ② 站内词表（低优先级，先铺底）
    for rel in ("names.yaml", "terms.yaml", "high_freq.yaml", "phrases.yaml",
                "phrases_manual.yaml"):
        p = config.ROOT / "glossary" / rel
        if not p.exists():
            continue
        try:
            import yaml
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            continue
        stack = [data]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                for k, v in cur.items():
                    if isinstance(v, dict):
                        stack.append(v)
                    elif isinstance(v, str):
                        labels.setdefault(str(k).strip(), v.strip())
    # ③ 从**站内既有译文**收割的短词对照（`_jalabels.json`）—— 优先级高于 glossary ✓：
    #    它是"这一串原文在站里已经被人翻成的中文" ✓，比通用词表更准确（道具名多在此 ✓）。
    harvest = STAT_DIR / "_jalabels.json"
    if harvest.exists():
        try:
            labels.update(json.loads(harvest.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            pass
    # ① 本页专属标签（高优先级，覆盖上面）
    if LABELS_PATH.exists():
        try:
            import yaml
            data = yaml.safe_load(LABELS_PATH.read_text(encoding="utf-8")) or {}
            for k, v in (data.get("labels") or {}).items():
                if str(v).strip():
                    labels[str(k).strip()] = str(v).strip()
        except Exception:  # noqa: BLE001
            pass
    return labels


def _pkg(key: str) -> dict | None:
    p = STAT_DIR / f"{key}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _pick_sheets(data: dict, wanted: "list[str]") -> "list[dict]":
    """挑 sheet：**先按 `wanted` 前缀顺序取 ✓，再把其余未列出的全部追加到末尾 ✓**。

    为什么变成"追加剩余"（2026-09-30 用户追问"不该是二十多个表格吗"✓）：
    原实现**只取每个前缀命中的第一个 sheet** ✗ → `宝箱開封` 包里 23 个有数据的 sheet
    只渲染了 7 个 ✗✗（`結果(合計)` 这样的前缀匹配不到 `結果(AUTO配置１…)` ✗）。
    改成"偏好在前、其余兜底"后，**结构上不可能漏表** ✓（除非被 `_SKIP_SHEET_PREFIXES` 明确排除 ✓）。
    """
    skip = tuple(_SKIP_SHEET_PREFIXES)
    out: "list[dict]" = []
    used: set[str] = set()
    for w in wanted:
        for s in data["sheets"]:
            if s["name"].startswith(w) and not s["name"].startswith(skip) and s["name"] not in used:
                out.append(s)
                used.add(s["name"])
                break
    for s in data["sheets"]:
        if s["name"] not in used and not s["name"].startswith(skip):
            out.append(s)
    return out


# 曾经略去「変更履歴 / 目次」（作者的内部记账 ✓），理由是"会让正文变成一堵日文墙" ✗。
# **2026-09-30 撤回** ✗：用户明确要求"别漏表格" ✓ —— 「不漏」优先于「观感」 ✓。
# 现在把它们也收录、也渲染、也翻译 ✓；此常量留作将来"确实要整表排除"的开关 ✓（当前为空 ✓）。
_SKIP_SHEET_PREFIXES: tuple[str, ...] = ()


def label(text: str, labels: "dict[str, str]", locale: str) -> str:
    """单元格文本：数字原样 ✓；词表命中则译 ✓；否则保留原文（绝不瞎编 ✗）。

    未整串命中时做**一次遍历的**最长优先替换 ✓（处理 `覚醒の木・小*3`、
    `銀の巫女絵馬` 这类带前后缀的组合标签 ✓）。

    ⚠️ 2026-09-30 实测踩坑：原实现是 `for k in sorted(labels, key=len, reverse=True): out =
    out.replace(k, labels[k])` 的**链式**替换 ✗ —— 词表里有单字键（收割层收到
    `数 ⇒ 数量` 之类 ✗），于是 `数量` 先原样、随后其中的 `数` 又被替换 →
    页面上出现 **`获取数量量`** ✗✗（多一个字）。改为正则**单次**替换：
    一次性扫描、最长优先、替换结果不再被二次替换 ✓。
    """
    t = (text or "").strip()
    if not t or locale == "ja" or _NUM_RE.match(t):
        return t
    if t in labels:
        return labels[t]
    pat = _sub_matcher(labels)
    if not pat:
        return t
    out = pat.sub(lambda m: labels[m.group(0)], t)
    # **半译则弃** ✓（2026-09-30 实测）：替换后仍留假名 ⇒ 多半是**日文句子** ✓，
    # 逐词替换只会得到 `・水色の背景のセルだけ输入します(他のセルは变更不)` 这种混血 ✗✗，
    # 比整串日文还差 ✗。规则：整串译完（不含假名）才采用 ✓，否则**回退原文** ✓；
    # 句子级内容交给词表里的人工整句译文覆盖 ✓。
    return t if _KANA_RE.search(out) else out


_MATCH_CACHE: "dict[int, object]" = {}


def _sub_matcher(labels: "dict[str, str]"):
    """词表的「最长优先、单次替换」正则（按词表对象缓存 ✓，避免每格重编译 ✗）。"""
    key = id(labels)
    if key in _MATCH_CACHE:
        return _MATCH_CACHE[key]
    keys = [k for k, v in labels.items() if len(k) >= 2 and v != k]
    keys.sort(key=len, reverse=True)
    pat = re.compile("|".join(re.escape(k) for k in keys)) if keys else None
    _MATCH_CACHE[key] = pat
    return pat


def render_table(t: dict, labels: "dict[str, str]", locale: str) -> str:
    """一张表 → HTML。空表头时把**首个有内容行**提升为表头 ✓（Google 导出的真表头就是首行 ✓）。"""
    header = t.get("header") or []
    rows = list(t.get("rows") or [])

    def cell_html(c: dict, tag: str) -> str:
        span = ""
        if c.get("cs", 1) > 1:
            span += f' colspan="{c["cs"]}"'
        if c.get("rs", 1) > 1:
            span += f' rowspan="{c["rs"]}"'
        txt = label(c.get("t", ""), labels, locale)
        return f"<{tag}{span}>{html.escape(txt)}</{tag}>" if txt else f"<{tag}{span}></{tag}>"

    if not header and rows:
        while rows and not any(c.get("t", "").strip() for c in rows[0]):
            rows.pop(0)
        # 挑表头行：在前 5 行里选**非空单元格最多**的那行 ✓（≥2 才认，否则退回首行 ✓）。
        # 为什么不能简单取首行 ✗：作者的表首行常是 `目次`、`宝箱数と蝶鉱石` 这类
        # **单格标题行** ✓，而真正的列标题在第 2 行（如 `開封箱数 | 結果シート名 | 結果(...)` ✓），
        # 一提错行就变成"19 列表格只配 1 格表头" → 顶部一大片空白 ✗（2026-09-30 实测所见 ✗）。
        # 另外：列排序由站点既有 tableEnhancer 依赖 **th 行** ✓，所以必须产出真正的表头行 ✓。
        if rows:
            cnt = lambda i: sum(1 for c in rows[i] if c.get("t", "").strip())  # noqa: E731
            k = max(range(min(5, len(rows))), key=cnt)
            header = [rows.pop(k if cnt(k) >= 2 else 0)]
    if header:
        # 表头**补齐到整表宽度** ✓（补空 th）：否则短表头行在大表上会拉出一条空白带 ✗，
        # 也会让筛选行/列宽计算少列 ✗。
        w = max([len(r) for r in rows] + [len(r) for r in header])
        if len(header[0]) < w:
            header[0] = header[0] + [{"t": ""}] * (w - len(header[0]))
    out = ['<div class="table-scroll"><table class="escah-tbl">']
    if header:
        out.append("<thead>")
        for r in header:
            out.append("<tr>" + "".join(cell_html(c, "th") for c in r) + "</tr>")
        out.append("</thead>")
    out.append("<tbody>")
    for r in rows:
        if not any(c.get("t", "").strip() for c in r):
            continue
        out.append("<tr>" + "".join(cell_html(c, "td") for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def render_page(page: dict, labels: "dict[str, str]", locale: str) -> str:
    """一页 → HTML 片段（含 intro、目录式小导航、各表小节）。"""
    intro = page.get("intro_ja" if locale == "ja" else "intro_zh", "")
    parts: "list[str]" = []
    if intro:
        # 这里**不能** html.escape ✗：intro 是本站自撰的可信内容 ✓，且其中含 `<strong>` ✓；
        # 转义后会在页面上显示成字面 `<strong>しらべるくん</strong>` 文本 ✗（2026-09-30 实测踩过 ✓）。
        parts.append(f'<p class="stat-intro">{intro}</p>')
    if page.get("children"):
        items = []
        for slug, zh, ja in page["children"]:
            txt = ja if locale == "ja" else zh
            # ⚠️ 必须用**相对链接** ✓：片段是以 `v-html` 注入的 ✗，不会经过 VitePress 的
            # base 重写 ✓（侧栏/导航走配置所以没问题 ✓）。写 `/zh/xxx.html` 会绕过站点 base
            # (`/escah/`) → 点击直接 **404** ✗（2026-09-30 浏览器实测踩到 ✓）。
            # 这些页都在同目录（/zh/*.html）✓，相对链接在任何 base 下都成立 ✓。
            items.append(f'<li><a href="{slug}.html">{html.escape(txt)}</a></li>')
        head = "収録ツール" if locale == "ja" else "收录工具"
        parts.append(f'<h2>{head}</h2>\n<ul class="stat-index">' + "".join(items) + "</ul>")
        note = ("※ データは攻略作者しらべるくん氏の公開ツールによる実測値です。"
                if locale == "ja"
                else "※ 以上数据均来自攻略作者 <strong>しらべるくん</strong> 的公开实测工具，本站仅作整理与中文标注。")
        parts.append(f'<p class="stat-credit">{note}</p>')
    data = _pkg(page["package"]) if page.get("package") else None
    if data:
        no_data: "list[str]" = []
        for sheet in _pick_sheets(data, page.get("sheets") or []):
            name = sheet["name"]
            if not sheet["tables"]:
                # 解析期被"大表闸门"挡下的明细表：**合并成末尾一条说明** ✓，
                # 而不是排成一串空小节 ✗（宝箱开箱包有 10 张这种 ✓，会很吵 ✗）。
                no_data.append(name)
                continue
            parts.append(f"<h2>{html.escape(label(name, labels, locale))}</h2>")
            for t in sheet["tables"]:
                parts.append(render_table(t, labels, locale))
        if no_data:
            names = "／".join(no_data)
            msg = (f"※ 次の {len(no_data)} シート（集計明細）は未収録です：{names}"
                   if locale == "ja" else
                   f"※ 以下 {len(no_data)} 张「集計（明细）」工作表未收录（每张上万单元格，"
                   f"属于各配置的原始明细，汇总结论见上方各结果表）：{names}")
            parts.append(f'<p class="stat-note">{html.escape(msg)}</p>')
        # 页脚：说明略去了哪些表 ✓（透明 ✓，读者知道"信息没缺"还是"有意省略" ✓）
        hidden = [s["name"] for s in data["sheets"]
                  if s["name"].startswith(_SKIP_SHEET_PREFIXES)]
        if hidden:
            msg = ("※ 原表の「目次／変更履歴」など作者の内部記録シート（"
                   + "／".join(hidden) + "）は省略しています。")
            if locale != "ja":
                msg = ("※ 已略去原表中作者内部记账用的「目录／变更履历」等工作表（"
                       + "／".join(hidden) + "）。")
            parts.append(f'<p class="stat-note">{html.escape(msg)}</p>')
    return "\n".join(parts)


# ------------------------------------------------------------------ 站点落盘 ----
def write_pages(write_md, site_dirs: "dict[str, Path]", labels: "dict[str, str] | None" = None) -> int:
    """把全部数据页写成站点 md + frag（供 `sitegen.sync_site` 调用）。

    参数 `write_md` = `sitegen._write_md` ✓（避免循环 import ✓）。这些页**不是镜像页** ✗：
    没有 registry 条目、没有 raw 快照，正文由本模块直接渲染 ✓，且**已是终版** →
    以 `pre_sanitized=True` 落盘 ✓（跳过 i18n 净化流程 ✓）。
    """
    labels = load_labels() if labels is None else labels
    written = 0
    for page in PAGES:
        for locale, site_dir in site_dirs.items():
            frag = render_page(page, labels, locale)
            if not frag:
                continue
            title = page["title_ja"] if locale == "ja" else page["title_zh"]
            write_md(
                site_dir / f'{page["slug"]}.md', title, frag, page["slug"],
                "", "", "",
                # reviewed / translated：本站自撰页**没有镜像译文**，这两个标志只由它们
                # 驱动页脚角标 ✓（2026-09-30 两次实测）：
                #   translated=False               → 显示「未翻译」✗
                #   translated=True, reviewed=False → 显示「机器翻译」✗（同样不对 ✗）
                # 事实：表格**每一格**我都逐条人工核对/翻译过 ✓（`--kana` 报告已归零 ✓）
                # ⇒ zh 页 reviewed=True（= 该页内容经人工核定 ✓，名副其实 ✓）；ja 页两者皆 False ✓。
                locale == "zh",
                locale == "zh",
                locale, pre_sanitized=True,
                # 传 no_prevnext=True：否则页脚"上一页"会跳到按侧栏顺序相邻的
                # 无关页（实测 hub 的上一页是「TIPS一览」✗），对独立数据页是噪声 ✗。
                no_prevnext=True,
            )
            written += 1
    return written


# ------------------------------------------------------------------ 报告/输出 ----
def collect_labels() -> "dict[str, int]":
    """盘点所有"非数字"单元格文本及其出现次数（据此补词表 ✓）。"""
    from collections import Counter

    cnt: "Counter[str]" = Counter()
    for p in sorted(STAT_DIR.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        for sheet in data["sheets"]:
            cnt[sheet["name"]] += 1
            for t in sheet["tables"]:
                for r in (t.get("header") or []) + (t.get("rows") or []):
                    for c in r:
                        txt = (c.get("t") or "").strip()
                        if txt and not _NUM_RE.match(txt):
                            cnt[txt] += 1
    return dict(cnt)


def kana_report(top: int = 80) -> None:
    """量化验收：渲染后**仍含假名**的单元格文本（按出现次数排序 ✓）。

    为什么看这个而不是"词表缺哪些" ✗：词表缺不等于页面上是日文 ✗ ——
    `label()` 的**最长优先单次替换**会把 `覚醒の木・小*3` 这类组合标签也译掉 ✓。
    所以"仍含假名"才是用户真正看到的东西 ✓（2026-09-30 加，用于逐轮收敛 ✓）。
    """
    labels = load_labels()
    seen: "dict[str, int]" = {}
    for page in PAGES:
        if not page.get("package"):
            continue
        data = _pkg(page["package"])
        if not data:
            continue
        for sheet in _pick_sheets(data, page.get("sheets") or []):
            for t in sheet["tables"]:
                for r in (t.get("header") or []) + (t.get("rows") or []):
                    for c in r:
                        raw = (c.get("t") or "").strip()
                        if not raw:
                            continue
                        out = label(raw, labels, "zh")
                        if _KANA_RE.search(out):
                            seen.setdefault(f"{raw}  ⇒  {out}", 0)
                            seen[f"{raw}  ⇒  {out}"] += 1
    print(f"渲染后仍含假名的文本 {len(seen)} 种（下表按出现次数 ✓）：")
    for k, v in sorted(seen.items(), key=lambda x: -x[1])[:top]:
        print(f"   {v:>4}  {k}")


def main() -> int:
    if "--kana" in sys.argv:
        kana_report()
        return 0
    if "--report" in sys.argv:
        labels = load_labels()
        cnt = collect_labels()
        missing = {k: v for k, v in cnt.items() if k not in labels}
        print(f"非数字单元格文本 {len(cnt)} 种，词表已覆盖 {len(cnt) - len(missing)} 种，"
              f"**缺 {len(missing)} 种**\n")
        print(f"{'次数':>5}  {'原文':<44}{'现状'}")
        print("-" * 100)
        for k, v in sorted(missing.items(), key=lambda x: -x[1])[:80]:
            print(f"{v:>5}  {k[:42]:<44}（未收录，页面将保留日文）")
        return 0
    if "--dump" in sys.argv:
        slug = sys.argv[sys.argv.index("--dump") + 1]
        page = next(p for p in PAGES if p["slug"] == slug)
        labels = load_labels()
        for loc in ("zh", "ja"):
            print(f"\n===== {slug} [{loc}] =====")
            print(render_page(page, labels, loc)[:3000])
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
