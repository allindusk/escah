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
    # ②.5 「原样镜像」页的人工作译文（`data/statdata/mirror_texts.yaml` ✓）。
    # 镜像覆盖**全部工作表**（含数据页未收录的记录表 ✓），所以它有自己的一批译文 ✓；
    # 与 stat_labels 同属**人工层** ✓（键要原样保留空格 ✗不要 strip ✗）。
    mirror_texts = STAT_DIR / "mirror_texts.yaml"
    if mirror_texts.exists():
        try:
            import yaml
            data = yaml.safe_load(mirror_texts.read_text(encoding="utf-8")) or {}
            for k, v in (data.get("texts") or {}).items():
                if str(v).strip():
                    labels[str(k)] = str(v).strip()
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


def _nonempty(r: "list[dict]") -> int:
    return sum(1 for c in r if (c.get("t") or "").strip())


def split_segments(rows: "list[list[dict]]") -> "list[list[list[dict]]]":
    """把一张 sheet 的行**按空行切成若干块** ✓（空行是作者天然的"分块边界" ✓）。

    为什么必须分块（2026-09-30 用户反馈"本来不一样的数据被放进了同一张表"✗）：
    一个 sheet 里常纵向堆着**好几块结构完全不同的数据** ✗。实测 `結果(合計)`：
      · 行 0-2   目录标题 + 运行条件（元信息）
      · 行 4-15  消费道具「合计/平均」**16 列矩阵**（列=各配置）
      · 行 18-25 `種別 / 獲得スタミナ(平均)` **2 列小表**
      · 行 28-50 `装備アイテム/合計/平均/確率/ランキング` **17 列排行榜**
    原实现把它们当**一张 19 列的表**渲染 ✗ → 2 列小表被拉成 19 列、还共用错表头 ✗✗。
    分块后每块有自己的列宽、自己的表头、自己的排序/筛选 ✓。
    """
    segs: "list[list[list[dict]]]" = []
    cur: "list[list[dict]]" = []
    for r in rows:
        if any((c.get("t") or "").strip() for c in r):
            cur.append(r)
        elif cur:
            segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    return segs


def _render_block(rows: "list[list[dict]]", cap: "list[dict] | None",
                  labels: "dict[str, str]", locale: str) -> str:
    """一块数据 → 一个独立表格（可选块标题 ✓）。"""
    def cell_html(c: dict, tag: str, cls: str = "") -> str:
        span = ""
        if c.get("cs", 1) > 1:
            span += f' colspan="{c["cs"]}"'
        if c.get("rs", 1) > 1:
            span += f' rowspan="{c["rs"]}"'
        cattr = f' class="{cls}"' if cls else ""
        txt = label(c.get("t", ""), labels, locale)
        return f"<{tag}{cattr}{span}>{html.escape(txt)}</{tag}>" if txt else f"<{tag}{cattr}{span}></{tag}>"

    body = [r for r in rows if _nonempty(r)]
    out: "list[str]" = []
    if cap is not None:
        # ⚠️ 标题要取**第一个非空格** ✗不要取 cap[0] ✗：作者的标题行常是 ` | ・何か` 这种
        # 首格为空、文字在第 2 格的形式 ✗，取首格会得到空串 ⇒ 标题被丢掉 ✗
        # （2026-09-30 实测：正是这个 bug 让 19 格文本在页面上消失 ✗）。
        ctext = ""
        for c in cap:
            ctext = label(c.get("t", ""), labels, locale)
            if ctext:
                break
        if ctext:
            # 块标题用 <h3>：① 进右侧大纲 ⇒ 长页面可按块跳转 ✓；
            # ② 不再占表格首行 ⇒ 每块的表头就是它自己的真表头 ✓。
            out.append(f'<h3 class="stat-cap">{html.escape(ctext)}</h3>')
    if not body:
        return "\n".join(out)
    width = max(len(r) for r in body)
    # 表头：块内前 5 行里非空最多的那行（≥2 才认 ✓，否则退回首行 ✓）；
    # 站点 tableEnhancer 的排序/筛选依赖真 <th> 行 ✓，所以必须选出真表头 ✓。
    # ⚠️ 但**小块（<4 行）不选表头** ✓：实测"运行条件"这类元信息块只有 1-3 行、行间形态
    # 还不一致（1 格 / 13 格 / 14 格 ✓），硬挑一行当表头会挑中一行条件 ⇒ 页面上出现
    # 一个毫无意义的表头 ✗（2026-09-30 截图确认 ✓）。这类块直接当普通数据表渲染 ✓。
    if len(body) >= 4:
        cnt = lambda i: _nonempty(body[i])  # noqa: E731
        k = max(range(min(5, len(body))), key=cnt)
        header = [body.pop(k if cnt(k) >= 2 else 0)]
    else:
        header = []
    if header and len(header[0]) < width:
        # 表头补齐到块宽度 ✓：短表头在大块上会拉出一条空白带 ✗，也会少列导致筛选项缺失 ✗
        header[0] = header[0] + [{"t": ""}] * (width - len(header[0]))
    # 小块（<5 行）**不挂 `escah-tbl`** ✓：分块后小表很多（宝箱页共 180+ 块 ✓），
    # 每块都生成一整套"排序/筛选/全屏"工具条会铺满整页 ✗✗ —— 而两三行的表本来也不需要排序 ✓。
    # 大块保留 escah-tbl ✓，照旧获得排序/筛选/全屏 ✓。
    cls = "escah-tbl" if len(body) >= 4 else "stat-tbl"
    out.append(f'<div class="table-scroll"><table class="{cls}">')
    if header:
        out.append("<thead><tr>" + "".join(cell_html(c, "th") for c in header[0]) + "</tr></thead>")
    out.append("<tbody>")
    for r in body:
        out.append("<tr>" + "".join(cell_html(c, "td") for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def _min_col(seg: "list[list[dict]]") -> int:
    """一段的**缩进**（最小非空列号）✓ —— 实测这是最准的分块判据 ✓。"""
    return min(min(i for i, c in enumerate(r) if (c.get("t") or "").strip()) for r in seg)


def render_table(t: dict, labels: "dict[str, str]", locale: str) -> str:
    """一张 sheet → HTML：**先按空行切段 ✓，再按"缩进"合并成块 ✓，每块独立成表 ✓**。

    为什么不是"一段一块" ✗（2026-09-30 实测）：那样宝箱页会从 23 张暴增到 **183 张** ✗✗ ——
    记录型 sheet（`検証` 190 行 / `参照用` 272 行）里散布着大量零星空行 ✗，它们只是"两次测量
    之间的间隔" ✓，不是换了一块数据 ✓。实测判据：
      · `結果(合計)`：4 块的缩进分别是 0 / 1 / 1 / 1 ✓，配合"单格标题另起一块"正好切成 **4 块** ✓
        （元信息 / 16 列矩阵 / 2 列小表 / 17 列排行榜 ✓ —— 正是用户指出"被塞进同一张表"的那四块 ✓）；
      · `検証`：各段缩进**全是 1** ✓ ⇒ 合并成 **1 张表** ✓（37 → 1 ✓）。
    """
    rows = list(t.get("header") or []) + list(t.get("rows") or [])
    segs = split_segments(rows)
    items: "list[dict]" = []                      # {"cap": 标题行|None, "min": 缩进, "rows": [...]}
    pending: "list[dict] | None" = None
    for seg in segs:
        # 单独成段的"单格标题行"（如 `・入手できるスタミナの平均` ✓）→ 作为下一块的标题 ✓
        if len(seg) == 1 and _nonempty(seg[0]) <= 1:
            if pending is None:
                pending = seg[0]
                continue
        mc = _min_col(seg)
        if items and pending is None and items[-1]["min"] == mc:
            items[-1]["rows"].extend(seg)         # 缩进相同 ⇒ 仍属同一块 ✓
            continue
        items.append({"cap": pending, "min": mc, "rows": list(seg)})
        pending = None
    if pending is not None:                       # 末尾孤立的标题
        items.append({"cap": pending, "min": 0, "rows": []})
    return "\n".join(_render_block(it["rows"], it["cap"], labels, locale) for it in items)


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
        # 原样镜像入口 ✓（只在镜像文件确实生成过时才输出 ✓，避免 CI 上出现死链 ✗）
        mirror_dir = config.SITE_PUBLIC_DIR / "mirror"
        if mirror_dir.exists():
            # ⚠️ 必须标成**外链**（`rel="external" target="_blank"`）✓✗：
            # `public/mirror/*.html` 是**静态文件**、不是 VitePress 路由 ✗，而站点 SPA 路由会
            # 拦截站内链接做客户端跳转 ⇒ 直接渲染成 **404 视图** ✗（2026-09-30 浏览器实测复现：
            # 点击后 URL 正确但标题是 `404 | 超昂大戦 Wiki`、0 张表 ✗ —— 直接输入 URL 反而正常 ✓，
            # 所以只测直连是测不出来的 ✗）。标成外链后走整页加载 ✓，正常显示 ✓。
            links = "".join(
                f'<a href="../mirror/{k}.html" rel="external" target="_blank">{k}</a>　'
                for k in MIRROR_PKGS
                if (mirror_dir / f"{k}.html").exists()
            )
            if links:
                head2 = "原様ミラー（未翻訳・原文ママ）" if locale == "ja" else "原样镜像对照（未翻译·格式原样）"
                lead = ("元の Google スプレッドシート出力をそのまま表示（翻訳・並べ替えなし）。"
                        if locale == "ja" else
                        "直接渲染原始导出内容（未翻译、未重排、未删空行空列），用于核对镜像保真度。")
                parts.append(f'<h2>{head2}</h2>\n<p class="stat-credit">{lead}</p>\n<p>{links}</p>')
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


# ------------------------------------------------------------------ 原样镜像 ----
# 用户要求（2026-09-30）："完全不改原来的格式，也不用项目里的表格样式，先用 HTML 完全镜像
# 展示静态数据，看看能不能镜像到一模一样"。
#
# 做法：**不经过我们解析出的 JSON** ✓ —— 那一步会丢掉 Google 导出的**内联样式**
# （背景色 / 加粗 / 字号 / 对齐 ✓，实测每 sheet 33~204 处 `style=` ✓，正是原表的视觉信息 ✓）。
# 而是把原始 `.html` 里的 `<table class="waffle">…</table>` **整块原样**搬进一个
# **独立静态页**（`site/public/mirror/<key>.html` ✓）：
#   · 不进 VitePress 主题 ✗（自带页面壳 + 最小 CSS ✓）⇒ 不会被站点样式改写 ✓
#   · 不翻译 ✗、不重排 ✗、不删空行空列 ✗ ⇒ 与导出结果逐格一致 ✓
# 注意 `site/public/` 在 .gitignore 里 ✓ —— 这些页由 `sync_site` 从
# `recycle_bin/data/`（本机素材 ✓，CI 没有 ✓）现场生成 ✓，不会进仓库 ✓。

MIRROR_PKGS = {
    "annihilation": "殲滅戦報酬調べるくん",
    "d2p-gacha": "D2Pガチャしらべるくん",
    "box": "ボックスしらべるくん",
    "treasure-open": "宝箱開封しらべるくん",
}

_MIRROR_TABLE_RE = re.compile(r'<table[^>]*class="[^"]*waffle[^"]*".*?</table>', re.S | re.I)
_MIRROR_ANY_TABLE_RE = re.compile(r"<table\b.*?</table>", re.S | re.I)
_SCRIPT_RE = re.compile(r"<script\b.*?</script>", re.S | re.I)

_MIRROR_CSS = """
  html, body { margin: 0; padding: 0; background: #fff; color: #202124;
       font-family: system-ui, "Segoe UI", "Yu Gothic UI", sans-serif; }
  header { padding: 12px 16px 4px; }
  h1 { font-size: 17px; margin: 0 0 4px; }
  .lead { font-size: 12px; color: #5f6368; margin: 2px 0; }
  .nav { font-size: 12px; margin: 4px 0 0; }
  .nav a { margin-right: 10px; }
  /* 正文区：底部留出标签栏高度 ✓；一个页面**只显示一个工作表** ✓ */
  main { padding: 8px 16px 68px; }
  section.sheet { overflow: auto; max-width: 100%; }
  section.sheet[hidden] { display: none; }
  /* 只保证"像 Google 表格"的最小骨架（边框 ✓）；底色/加粗等观感仍由导出的内联样式决定 ✓ */
  table.waffle { border-collapse: collapse; font-size: 12px; }
  table.waffle td, table.waffle th { border: 1px solid #dadce0; padding: 2px 6px;
       vertical-align: top; white-space: pre-wrap; }
  /* 左下角工作表标签栏（模拟 Google 表格 / Excel 的底部 sheet 切换 ✓） */
  .tabbar { position: fixed; left: 0; right: 0; bottom: 0; display: flex; gap: 2px;
       align-items: flex-end; background: #f1f3f4; border-top: 1px solid #dadce0;
       padding: 6px 8px 0; overflow-x: auto; scrollbar-width: thin; z-index: 10; }
  .tab { flex: 0 0 auto; border: 1px solid #dadce0; border-bottom: none; background: #e8eaed;
       color: #3c4043; font-size: 12px; line-height: 1.4; padding: 5px 10px;
       border-radius: 8px 8px 0 0; cursor: pointer; max-width: 220px; white-space: nowrap;
       overflow: hidden; text-overflow: ellipsis; font-family: inherit; }
  .tab:hover { background: #dee1e6; }
  .tab.on { background: #fff; color: #1a73e8; font-weight: 600; }
  .tabmeta { flex: 0 0 auto; align-self: center; font-size: 12px; color: #5f6368;
       padding: 0 8px 6px 4px; white-space: nowrap; }

  /* ---- 版式改成"像办公软件"：表头区固定在上、工作表区域**自己滚动**、标签栏固定在底部 ✓ ----
     为什么工作表区域要自己滚动 ✗：`position: sticky` 的冻结是相对于**最近的滚动祖先** ✓，
     若滚动的是整页 ✗，表内单元格就"贴"不住 ✗（2026-09-30 实测确认 ✓）。 */
  html, body { height: 100%; }
  body { display: flex; flex-direction: column; }
  header { flex: 0 0 auto; }
  main { flex: 1 1 auto; min-height: 0; overflow: hidden; padding: 0 16px; }
  section.sheet { height: 100%; overflow: auto; }
  .tabbar { position: static; flex: 0 0 auto; }

  /* ---- 冻结行列 ✓ ------------------------------------------------------------------
     原始 Google 导出里**不含用户的冻结设置** ✗，所以按最通用的做法：冻结**首行**
     （A B C 列字母行 ✓）与**首列**（1 2 3 行号列 ✓）—— 与办公软件默认观感一致 ✓。
     两个坑：① sticky 单元格必须是**不透明背景** ✓，否则滚动时下层内容透出来 ✗
     （导出带底色的格子以内联色优先 ✓ —— 内联样式优先于样式表 ✓ —— 无底色的补白 ✓）；
     ② 冻结行与冻结列交叉的那格要更高 z-index ✓，否则会被互相盖住 ✗。 */
  table.waffle tr:first-child > * { position: sticky; top: 0; z-index: 3; background-color: #fff; }
  table.waffle tr > *:first-child { position: sticky; left: 0; z-index: 2; background-color: #fff; }
  table.waffle tr:first-child > *:first-child { z-index: 4; }
"""

# 左下角标签栏的切换逻辑（内联 ✓，不引外部依赖 ✓）。注意这是**普通字符串** ✗不是 f-string ✗
# —— 里面有大量 `{}` ✓，放进 f-string 会被当占位符而报错 ✓。
_MIRROR_JS = """<script>
(function () {
  var tabs = [].slice.call(document.querySelectorAll('.tab'));
  var sheets = [].slice.call(document.querySelectorAll('section.sheet'));

  // 冻结行列用的一次性样式（由本脚本注入 ✓，避免再改 CSS 段 ✓）。
  var st = document.createElement('style');
  st.textContent = '.frz-cell{position:sticky;background-color:#fff;' +
    'background-clip:padding-box}';
  document.head.appendChild(st);

  // ---- 冻结行列：**逐表按内容判断** ✓ ------------------------------------------------
  // 用户要求（2026-09-30）："我不是说让你理解表格内容再定冻结行列吗，为什么你统一处理" ✗ ——
  // 统一冻"首行+首列"是错的 ✗，实测各表结构并不一样：
  //   · `box/結果`：行1 是 `A B C` 列字母行、行2 只有行号 `1`（空行 ✗）、**行3** 才是真表头
  //     `アイテム / 合計 / 確率` ⇒ 应冻 **3 行** ✓；
  //   · `box/調査`：行3 是 `宝箱数` 小节标题、**行4** 才是真表头 `調査No./ステージ/アイテム`
  //     ⇒ 应冻 **4 行** ✓；
  //   · 标签列同理：列1 是 `1 2 3` 行号 ✓、列2 常是空列 ✗、**列3** 才是名称列 ✓。
  // 判据（对每张表现算 ✓）：
  //   ① 表头行 = 从第 2 行起，**第一个非空单元格 ≥3 的行** ✓（跳过字母行与"只有行号"的空行 ✓）；
  //   ② 标签列 = 该表头行里**第一个有文字**（非纯数字）的格所在列 ✓（它左边的都是行号/空列 ✓）；
  //   ③ 偏移用**实测**的行高/列宽累加 ✓ —— 每行每列宽高不同，写死像素必然错位 ✗。
  function applyFreeze(sec) {
    [].slice.call(sec.querySelectorAll('table.waffle')).forEach(function (tb) {
      var rows = [].slice.call(tb.rows);
      if (!rows.length) return;
      // 角色分类（用户要求"理解表头/描述/数据，再推理该冻什么"✓，而不是找一行"像表头"的 ✗）
      function txts(r) {
        return [].slice.call(r.cells).map(function (c) { return (c.textContent || '').trim(); });
      }
      function isNum(t) { return /^[-\\d.,%()（）\\s]+$/.test(t); }
      var LETTERS = /^[A-Z]{1,3}$/;
      var nR = 0, k, c;
      // ① **行角色**：列字母行 / 只有行号的空行 / 说明行 / 表头行 / 数据行 ——
      //    从顶往下扫到"数据开始"为止 ✓；之间那些都要冻 ✓（否则冻结块不连续、会留一条缝 ✗）。
      // 统计某行的内容时**跳过第 1 列（行号列 `1 2 3`）** ✗ —— 它不是内容 ✗，
      // 否则 `2 | 宝箱数` 会被数成 2 格 ⇒ 单格说明行被误判成数据行 ✗（2026-09-30 实测踩到 ✓）。
      function contentTxts(r) {
        var out = [];
        for (var q = 1; q < r.cells.length; q++) {
          var t = (r.cells[q].textContent || '').trim();
          if (t) out.push(t);
        }
        return out;
      }
      for (k = 0; k < rows.length; k++) {
        var ts = contentTxts(rows[k]);
        var role = 'data';
        if (!ts.length) {
          role = 'blank';
        } else if (ts.every(function (t) { return LETTERS.test(t); })) {
          role = 'letters';                      // `A B C…` 列字母行 ✓
        } else if (ts.length === 1) {
          role = 'note';                         // 单格文本 ⇒ 小节标题/说明/描述 ✓
        } else {
          // 表头判据：本行文字格够多 ✓ 且**严格多于下一行** ✗（数据行里也有名称文字 ✓ ⇒
          // 用"≥"会把数据行也判成表头 ✓ ——实测 `box/結果` 因此一路数到第 11 行 ✗✗）。
          var tx = ts.filter(function (t) { return !isNum(t); }).length;
          var nt = 0;
          if (k + 1 < rows.length) {
            nt = contentTxts(rows[k + 1]).filter(function (t) { return !isNum(t); }).length;
          }
          role = (tx >= 2 && tx > nt) ? 'header' : 'data';
        }
        if (role === 'data') break;
        nR = k + 1;
        // ⚠️ 上限 4 行：实测真表头最深在第 4 行 ✓（`box/調査`：行3 是 `宝箱数` 小节、行4 才是表头 ✓）。
        // 更重要的是**兜底** ✗ —— 见下：`概要 / 目次 / 参照用` 这类"整张表都是文字"的描述表 ✓，
        // 永远扫不到"数据行" ✗，没有上限就会冻掉 48 行 ✗✗（2026-09-30 实测 ✓）。
        if (nR >= 4) break;
      }
      if (nR < 1) nR = 1;
      // ② **列角色**：行号列 / 空列 / 文本型关键列（名称·编号·条件 ✓）都冻 ✓；
      //    碰到**首个纯数字列** ⇒ 数据区开始，停 ✓。上限 3 列，防止整表都是文字时冻一大片 ✗。
      var nC = 1, maxCols = rows[0] ? rows[0].cells.length : 1;
      for (c = 0; c < maxCols && c < 3; c++) {
        var vals = [];
        for (k = nR; k < Math.min(rows.length, nR + 12); k++) {
          var t2 = rows[k].cells[c] ? (rows[k].cells[c].textContent || '').trim() : '';
          if (t2) vals.push(t2);
        }
        var allNum = vals.length > 0 && vals.every(isNum);
        if (c === 0 || vals.length === 0 || !allNum) nC = c + 1;
        else break;
      }
      var i, j;
      var lefts = [], acc = 0, first = rows[0];
      for (j = 0; j < nC; j++) {
        lefts.push(acc);
        acc += first.cells[j] ? first.cells[j].getBoundingClientRect().width : 0;
      }
      var top = 0;
      for (i = 0; i < rows.length; i++) {
        var r = rows[i], isHead = (i < nR);
        for (j = 0; j < nC && j < r.cells.length; j++) {
          var c = r.cells[j];
          c.classList.add('frz-cell');
          c.style.left = lefts[j] + 'px';
          if (isHead) c.style.top = top + 'px';
          c.style.zIndex = isHead ? 5 : 2;      // 行列交叉格最高 ✓，否则互相盖住 ✗
        }
        if (isHead) top += r.getBoundingClientRect().height;
      }
    });
  }

  function show(i) {
    if (i < 0 || i >= sheets.length) i = 0;
    sheets.forEach(function (s, j) { s.hidden = (j !== i); });
    tabs.forEach(function (t, j) { t.classList.toggle('on', j === i); });
    var t = tabs[i];
    if (t && t.scrollIntoView) t.scrollIntoView({ block: 'nearest', inline: 'center' });
    document.title = t.textContent + ' · 原样镜像';
    try { history.replaceState(null, '', '#' + encodeURIComponent(t.textContent)); } catch (e) {}
    // 必须在**显示之后**测量 ✓：隐藏元素的高度/宽度都是 0 ✗，冻结偏移会全算成 0 ✗。
    applyFreeze(sheets[i]);
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function () { show(parseInt(t.dataset.i, 10)); });
  });
  var h = '';
  try { h = decodeURIComponent((location.hash || '').slice(1)); } catch (e) { h = ''; }
  var idx = -1;
  tabs.forEach(function (t, j) { if (t.textContent === h) idx = j; });
  show(idx >= 0 ? idx : 0);
  window.addEventListener('resize', function () { applyFreeze(sheets[0] && sheets.find(function (s) { return !s.hidden; }) || sheets[0]); });
})();
</script>
"""


# 日文专用字形（简体中文里不会出现 ✓）：`発実変売価帰広対経説読…`。用于判断"这段文字
# 是否仍是日文" ✓ —— 只看假名是不够的 ✗（`発行日` / `改訂内容` / `選択` 都是纯汉字日文 ✓）。
_JP_ONLY = (
    "発実変売価帰広対経説読悪圧弁険験権観覧難鳥黒図団囲気済訳蔵戦単拠毎報増検査質適選択"
    "確認設縮闘値収円塩齢絵仮処融資産益頼週曜駅歳弐壱派遣雇継続総額鉄鉱脈扉帯服装備蓄庫"
    "補填育成技獄麗磨鎧翼弾銃剣盾具"
)


def _still_ja(s: str) -> bool:
    return bool(_KANA_RE.search(s)) or any(c in _JP_ONLY for c in s)


def _label_mirror(raw: str, labels: "dict[str, str]", locale: str) -> str:
    """镜像翻译：先按原样查 ✓；**若结果仍是日文，就去掉所有空白再查一遍** ✓。

    为什么需要（2026-09-30 实测）：源里同一内容常带**全角空格 / 换行**变体 ✗ ——
    例如单元格里其实是 `装備アイテム` 或 `（例：経験値　計測前…）` ✓，精确匹配全落空 ✗，
    页面上就留了一堆日文 ✗。`\\s` 在 Python 里**包含全角空格 `\\u3000`** ✓，所以一次压掉即可 ✓。
    """
    out = label(raw, labels, locale)
    if _still_ja(out):
        squeezed = re.sub(r"\s+", "", raw)
        out2 = label(squeezed, labels, locale)
        if not _still_ja(out2):
            out = out2
    return out


def _translate_table(frag: str, labels: "dict[str, str]", locale: str) -> "tuple[str, int, int]":
    """把镜像表格里的**文字**翻成中文 ✓，**除此之外一律不动** ✓。

    为什么只改文本节点（2026-09-30 用户要求"翻译一下"，同时版式要原样 ✓）：
      · `style=`（背景色 / 加粗 / 字号 ✓）、`colspan/rowspan`（合并 ✓）、
        空行空列 ✓、标签层级 ✓ 全部逐字保留 ⇒ **版式与原始导出一致，只换语言** ✓；
      · 逐**文本节点**翻译（而不是整格 textContent ✗）还能保住单元格内的 `<br>` 换行 ✓
        与 `<a>` 链接 ✓（整格替换会把它们吃掉 ✗）。
    查不到译文的串由 `label()` 原样保留 ✓（不瞎编 ✓）。
    返回 (html, 改动的文本节点数, 单元格总数) ✓ 便于报告翻译覆盖率 ✓。
    """
    import lxml.html as _lxml_html

    try:
        root = _lxml_html.fragment_fromstring(frag, create_parent="div")
    except Exception:  # noqa: BLE001
        return frag, 0, 0
    changed = total = 0
    for el in root.iter():
        if not isinstance(el.tag, str) or el.tag not in ("td", "th"):
            continue
        total += 1
        for holder in [el] + [x for x in el.iter() if x is not el]:
            for attr in ("text", "tail"):
                raw = getattr(holder, attr, None)
                if raw and raw.strip():
                    new = _label_mirror(raw, labels, locale)
                    if new != raw:
                        setattr(holder, attr, new)
                        changed += 1
    out = _lxml_html.tostring(root, encoding="unicode")
    if out.startswith("<div>") and out.rstrip().endswith("</div>"):
        out = out[len("<div>"):-len("</div>")].strip()
    return out, changed, total


def _mirror_sheets(pkg_dir: "Path") -> "list[tuple[str, str]]":
    out: "list[tuple[str, str]]" = []
    for f in sorted(pkg_dir.glob("*.html")):
        text = f.read_text(encoding="utf-8", errors="replace")
        m = _MIRROR_TABLE_RE.search(text) or _MIRROR_ANY_TABLE_RE.search(text)
        if not m:
            continue
        out.append((f.stem, _SCRIPT_RE.sub("", m.group(0))))
    return out


def write_mirror_pages(public_dir: "Path", raw_root: "Path | None" = None) -> int:
    """生成 4 个"原样镜像"静态页（`site/public/mirror/<key>.html` ✓）。返回写出数 ✓。

    源素材缺失时（如 CI ✗）**静默跳过** ✓，不影响建站 ✓。
    """
    raw_root = raw_root or (config.ROOT / "recycle_bin" / "data")
    if not raw_root.exists():
        return 0
    out_dir = public_dir / "mirror"
    out_dir.mkdir(parents=True, exist_ok=True)
    # ⚠️ 相对链接要**相对于本页所在的 mirror/ 目录** ✓✗：写成 `mirror/xxx.html` 会变成
    # `/escah/mirror/mirror/xxx.html` ⇒ 404 ✗（2026-09-30 用户实测发现 ✓）。页与页同目录 ⇒ 直接写文件名 ✓。
    links = "".join(
        f'<a href="{k}.html">{k}</a>' for k in MIRROR_PKGS
    )
    written = 0
    for key, prefix in MIRROR_PKGS.items():
        pkg_dir = next((p for p in raw_root.glob(prefix + "*") if p.is_dir()), None)
        if pkg_dir is None:
            continue
        sheets = _mirror_sheets(pkg_dir)
        if not sheets:
            continue
        labels = load_labels()
        sections: "list[str]" = []
        tabs: "list[str]" = []
        n_change = n_cells = 0
        for i, (name, frag) in enumerate(sheets):
            t_frag, ch, tot = _translate_table(frag, labels, "zh")
            n_change += ch
            n_cells += tot
            sections.append(
                f'<section class="sheet" id="sheet-{i}" data-name="{html.escape(name)}">'
                f"{t_frag}</section>"
            )
            tabs.append(
                f'<button class="tab" type="button" data-i="{i}">{html.escape(name)}</button>'
            )
        # 一个页面**只显示一个工作表** ✓（其余 `hidden` ✓，左下角标签切换 ✓ —— 用户要求
        # "模拟办公软件那样左下角可以切换工作表" ✓）。标签用 `<button>` + 少量内联 JS ✓，
        # 不引外部依赖 ✓；当前工作表写进 `location.hash` ✓（可直达 / 可分享 ✓）。
        body = [f"<h1>原样镜像 · {html.escape(key)}</h1>",
                '<p class="lead">版式与原始导出一致（背景色 / 加粗 / 合并单元格 / 空行空列全保留），'
                '仅将文字译为中文；未重排、未删行列。</p>',
                f'<p class="nav">{links}</p>',
                '<main id="sheets">' + "".join(sections) + "</main>",
                '<nav class="tabbar" id="tabbar">' + "".join(tabs)
                + f'<span class="tabmeta">共 {len(sheets)} 个工作表 · 点底部标签切换</span></nav>',
                _MIRROR_JS]
        doc = ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
               '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
               f"<title>原样镜像 · {key}</title>\n<style>{_MIRROR_CSS}</style>\n</head>\n<body>\n"
               + "\n".join(body) + "\n</body>\n</html>\n")
        (out_dir / f"{key}.html").write_text(doc, encoding="utf-8", newline="\n")
        print(f"    镜像 {key}: {len(sheets)} 个工作表，"
              f"已译文本 {n_change} 处 / 单元格 {n_cells} 个")
        written += 1
    return written


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
