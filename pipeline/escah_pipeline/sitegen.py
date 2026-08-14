"""生成 VitePress 站点内容：双语 .md、数据 JSON、侧边栏、图片同步。

数据流：data/parsed/ja（日文片段）+ data/parsed/zh（中文片段/人工覆盖）
      → site/ja、site/zh（生成的 .md，不手工编辑）+ site/public（数据与图片）
"""
from __future__ import annotations

import hashlib
import html as _html
import json
import os
import posixpath
import re
import shutil
from urllib.parse import urljoin, unquote
import yaml

from bs4 import BeautifulSoup
from lxml import etree
from lxml import html as lxml_html

from . import config
from . import i18n
from .logutil import get_logger
from .parser_puki import safe_id
from .registry import load_registry
from .snapshot import Manifest, page_filename

log = get_logger()

CATEGORY_LABELS = {
    "guide": {"ja": "ゲームガイド", "zh": "游戏指南"},
    "character": {"ja": "キャラクター", "zh": "角色"},
    "system": {"ja": "システム", "zh": "系统"},
    "equipment": {"ja": "装備・アイテム", "zh": "装备与道具"},
    "quest": {"ja": "クエスト・ミッション", "zh": "任务与使命"},
    "misc": {"ja": "その他", "zh": "其他"},
    "character-detail": {"ja": "キャラクター詳細", "zh": "角色详情"},
}
CATEGORY_ORDER = ["guide", "character", "system", "equipment", "quest", "misc"]

# ---- 侧边栏显式结构（slug 驱动；顺序即展示顺序）----
# 顶层组 cat 对应 CATEGORY_LABELS；中间节点 slug 既是页也是容器（展开看子项）；
# _SB_DIV 为视觉分隔符。zh 站点部分页需改名（去活动编号 / 加 VIP 说明），见 _SB_OVERRIDE_ZH。
_SB_DIV = "__SB_DIV__"
_SB_OVERRIDE_ZH = {
    "wide-battle": "广域战",
    "annihilation": "歼灭战",
    "shop": "商店（VIP等级）",
}
SIDEBAR_TREE = [
    {"cat": "character", "items": [
        {"slug": "characters", "items": [
            {"slug": "rarity-links", "combined": ["list-ssr", "list-sr", "list-r"], "sep": " | "},
        ]},
        {"slug": "list-supporter"},
        {"slug": "list-npc"},
        _SB_DIV,
        {"slug": "skills"},
        {"slug": "unique-effects"},
        {"slug": "special-attributes"},
        _SB_DIV,
        {"slug": "bedroom-scenes"},
        {"slug": "artists"},
        {"slug": "voice-actors"},
        {"slug": "release-history"},
    ]},
    {"cat": "guide", "flat": True, "collapsed": True},
    {"cat": "system", "collapsed": True, "items": [
        {"slug": "battle", "items": [
            {"slug": "raid", "items": [
                {"slug": "raid-recommended"},
                {"slug": "raid-buff-debuff"},
                {"slug": "raid-formations"},
            ]},
        {"slug": "b-universe"},
        {"slug": "wide-battle", "items": [{"slug": "map-list"}]},
        {"slug": "annihilation"},
        ]},
        _SB_DIV,
        {"slug": "limit-break"},
        {"slug": "awakening"},
        {"slug": "level-cap"},
        _SB_DIV,
        {"slug": "treasure-box"},
        {"slug": "exchange"},
        {"slug": "character-exchange"},
        {"slug": "collection"},
        _SB_DIV,
        {"slug": "shop"},
    ]},
    {"cat": "equipment", "collapsed": True, "items": [
        {"slug": "equipment", "items": [{"slug": "super-equipment"}]},
        {"slug": "items", "items": [{"slug": "item-value-guide"}]},
    ]},
    {"cat": "quest", "collapsed": True, "items": [
        {"slug": "main-story", "items": [{"slug": "scenario-order"}]},
        {"slug": "main-quest"},
        {"slug": "daily-quest"},
        {"slug": "missions"},
        _SB_DIV,
        {"slug": "events"},
    ]},
    {"cat": "misc", "flat": True, "collapsed": True},
]
_MTIME_RE = re.compile(r"Last-modified:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}[^<\n]*)")

MD_TEMPLATE = """---
title: "{title}"
layout: doc
{prevnext}meta:
  sourceUrl: "{source_url}"
  sourceUpdated: "{source_updated}"
  synced: "{synced}"
  reviewed: {reviewed}
  translated: {translated}
---

<script setup>
import frag from "{rel}"
</script>

<MirrorContent :html="frag.html" />
"""


# lxml.html 会把属性名规范为小写，这里把 SVG 等需要大小写的属性还原回去
_SVG_ATTRS = {
    "viewbox": "viewBox",
    "preserveaspectratio": "preserveAspectRatio",
    "gradientunits": "gradientUnits",
    "gradienttransform": "gradientTransform",
    "clippathunits": "clipPathUnits",
    "clippath": "clipPath",
}


def _sanitize_html(html: str) -> str:
    """规范化 PukiWiki 原始 HTML 片段，使其可被 VitePress/Vue 安全解析。

    PukiWiki 产出的 HTML 常有嵌套错乱/未闭合标签（如 TOC 的 li/ul 层级错位、
    plugin-spoiler 未闭合的 span）与内联事件处理器（onclick）。前者会让 Vue
    模板编译器报 “Element is missing end tag”（其解析器比浏览器严格，不接受
    html.parser 的“修复”结果），后者依赖原站 JS（tglRgn 等）而无意义。

    这里用 lxml.html 以整树方式重新平衡所有标签，输出天然合法的 HTML；
    只做呈现层清洗，不改动 data/parsed 下忠实保留的解析数据。
    """
    if not html:
        return html
    try:
        frag = lxml_html.fragment_fromstring(html, create_parent="div")
    except Exception:
        frag = lxml_html.fromstring(f"<div>{html}</div>")
    for el in frag.iter():
        if not isinstance(el.tag, str):  # 注释/处理指令等
            continue
        for attr in list(el.attrib):
            if attr.lower().startswith("on"):
                del el.attrib[attr]

    # ---- 清理导航/工具类超链接（用户要求：已有目录，不必保留这些导航）----
    _strip_nav_links(frag)

    # ---- 角色链接保留（不再去链接化）----
    # 角色详情页（/zh/characters/名.html，370+ 个）真实存在，站内链接可直接跳转不
    # 会 404。保留正文内「<a href=characters/名.html>」后：i18n 的「句末【链接】」
    # 方案会把它提取到句末【角色名】（统一全站超链接行为）；客户端 tagCharLinks
    # 对其打 data-char，浮窗 hover/点击固定窗照常。不再改写成 <span data-char>，
    # 以免译文被注入替换（用户要求：正文不做注入）。
    _neutralize_char_links(frag)

    # ---- 页内目录（wiki .contents）锚点修正：PukiWiki 的 TOC 链接指向内层
    #      anchor(<a id="y4f8fac5">) 的哈希，而该内层 anchor 已被 _strip_nav_links
    #      剥离（仅保留 <hX id="content_1_0">）。导致页内目录点击无反应。这里按
    #      文本匹配把 TOC 链接重指向真实存在的标题 id，恢复页内跳转。----
    _relink_toc(frag)

    # ---- 剥离 PukiWiki 行署名编辑戳（--[page]YYYY-MM-DD(周X)HH:MM:SS）----
    # 这是 wiki 元数据（谁在何时编辑该行），任何语言页都不应显示，且会污染译文
    # （LLM 把「角色名+编辑戳」整行当句子翻译，导致角色名被错译）。在解析期就删掉。
    _strip_edit_stamps(frag)

    # ---- 表格：去空白表 + 外包横向滚动容器（多列属性/对比表可横滑，避免裁切）----
    for tbl in frag.xpath(".//table"):
        if not (tbl.text_content() or "").strip() and not tbl.xpath(".//img"):
            tbl.drop_tree()
    for tbl in frag.xpath(".//table"):
        wrapper = etree.Element("div", attrib={"class": "table-scroll"})
        tbl.addprevious(wrapper)
        wrapper.append(tbl)

    out = lxml_html.tostring(frag, method="html", encoding="unicode")
    # 去掉为平衡而包的最外层 <div>…</div>
    if out.startswith("<div>") and out.rstrip().endswith("</div>"):
        out = out[len("<div>"):-len("</div>")]
    for low, cam in _SVG_ATTRS.items():
        out = re.sub(rf'\b{low}=', f"{cam}=", out, flags=re.I)
    # 折叠属性值内的换行/多余空白：PukiWiki 会把 style 等属性格式化到多行，
    # 而 Vue 的 HTML 词法分析器无法在带换行的属性值上正确闭合标签，
    # 会误报 “Element is missing end tag”
    out = re.sub(
        r'="([^"]*?)"',
        lambda m: '="{}"'.format(re.sub(r"\s+", " ", m.group(1))),
        out,
    )
    return out


_EDIT_STAMP_RE = re.compile(
    r"--\[[^\]]*\][0-9]{4}-[0-9]{2}-[0-9]{2}\([^)]*\)[0-9]{2}:[0-9]{2}:[0-9]{2}"
)


def _strip_edit_stamps(frag) -> None:
    """删除 PukiWiki 行署名编辑戳（--[编辑者]YYYY-MM-DD(周X)HH:MM:SS）。

    这是 wiki 元数据，正文不应显示，且会污染译文（LLM 易把「角色名+编辑戳」整行
    当成句子翻译，导致角色名被错译成「已经删掉了——--[...]」之类）。解析期剥离。
    """
    for el in frag.iter():
        if not isinstance(el.tag, str):
            continue
        if el.text:
            new = _EDIT_STAMP_RE.sub("", el.text)
            if new != el.text:
                el.text = new
        if el.tail:
            new = _EDIT_STAMP_RE.sub("", el.tail)
            if new != el.tail:
                el.tail = new


def _strip_nav_links(frag) -> None:
    """删除 wiki 的导航/工具超链接，保留交叉引用链接与内部结构。

    - jumpmenu：回到顶部导航箭头
    - anchor_super：章节编辑锚点（† / 铅笔）
    - internal-link：**保留**（站内交叉引用，如「参考リンク：寝室シーンの開き方」
      指向 faq）。全站扫描确认所有 internal-link 目标均在 registry 内（无死链），
      直接保留 <a> + href + title 即可恢复正文引用超链接；文本仍由 i18n 翻译。
    """
    for el in frag.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' jumpmenu ')]"):
        el.drop_tree()
    for el in frag.xpath(".//a[contains(concat(' ', normalize-space(@class), ' '), ' anchor_super ')]"):
        aid = el.get("id")
        parent = el.getparent()
        if parent is None:
            el.drop_tree()
            continue
        if aid:
            # 保留章节跳转锚点：PukiWiki 的 anchor_super(<a id="...">†</a>) 是正文里
            # #id 链接（如 #drop_list）的唯一真实目标；直接 drop 会让这些跳转失效。
            # 改为占位 <span id="..."> 落回原父元素内（保留锚点，去掉无意义 † 图标）。
            span = etree.Element("span", attrib={"id": aid})
            parent.insert(parent.index(el), span)
        el.drop_tree()


def _neutralize_char_links(frag) -> None:
    """正文内指向角色详情页的 <a href="characters/名.html"> 保留原样。

    角色详情页（/zh/characters/名.html，共 370+ 个）真实存在，站内链接可直接跳转，
    不会 404。保留 <a> 后：
      - i18n「句末【链接】」方案会把句中角色名提取到句末【角色名】（绑定该 href），
        统一全站超链接行为（左键业内跳转、中键新标签）；
      - 客户端 tagCharLinks 对「<a href=characters/名.html>」打 data-char，
        浮窗 hover / 点击固定窗照常生效；
      - 不再把正文角色名改写成 <span data-char>（即「注入替换」），避免译文被改写。
    内联头像（<img>）由 tagAvatars 另行打 data-char，与此无关。
    """
    # 保留 <a>，不做去链接化。此处留空函数以维持调用点稳定（历史去链接化逻辑已废弃）。
    return


def _neutralize_char_links_html(html: str) -> str:
    """HTML 字符串版去链接化：供 pre_sanitized（i18n）页面在 sync-site 落盘前补跑。
    幂等：若已无 a[href*=characters/] 则原样返回。"""
    try:
        tree = lxml_html.fragment_fromstring(html, create_parent="div")
    except Exception:
        return html
    _neutralize_char_links(tree)
    out = lxml_html.tostring(tree, encoding="unicode")
    if out.startswith("<div>") and out.endswith("</div>"):
        out = out[5:-6]
    return out


def _relink_toc(frag) -> None:
    """把 wiki 页内目录(.contents)的锚点链接重指向真实存在的标题 id。

    PukiWiki 的 TOC 项形如 `<a href="#y4f8fac5">标题</a>`，而该哈希来自标题内层
    被剥离的 anchor；真实标题元素为 `<hX id="content_1_0">`。按「链接文本 == 标题
    文本(去空白)」匹配，将 href 改写为 `#content_1_0`，使点击可正确跳转。
    """
    # 建立 去空白标题文本 -> 标题 id 映射（只取带 id 的标题，避免冲突覆盖）
    head_map: dict[str, str] = {}
    for h in frag.xpath(
        ".//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]"
    ):
        hid = h.get("id")
        if not hid:
            continue
        # 标题 text 可能含 anchor_super 残留符号（如 †），剥除非 CJK/字母数字符号再
        # 去空白，使其与 TOC 纯文本项（"概要"）匹配，否则 relink 失败、目录仍指向旧 hash。
        txt = re.sub(r"\s+", "", h.text_content() or "")
        txt = re.sub(r"[^\w\u3000-\u9fff\u3040-\u30ff]", "", txt)
        if txt:
            head_map.setdefault(txt, hid)
    if not head_map:
        return
    for block in frag.xpath(
        ".//div[contains(concat(' ', normalize-space(@class), ' '), ' contents ')]"
    ):
        for a in block.xpath(".//a[@href]"):
            href = a.get("href", "")
            if not href.startswith("#"):
                continue
            txt = re.sub(r"\s+", "", a.text_content() or "")
            target = head_map.get(txt)
            if target:
                a.set("href", "#" + target)


def _rel(from_slug: str, to_slug: str) -> str:
    from_dir = posixpath.dirname(from_slug)
    return posixpath.relpath(to_slug + ".html", from_dir or ".")


def _localize_routes(html: str, from_slug: str) -> str:
    def repl(m: re.Match) -> str:
        target = m.group(1)
        anchor = m.group(3) or ""
        return f'href="{_rel(from_slug, target)}{anchor}"'

    return re.sub(r'href="__ROUTE__/([^"#]+?)(\.html)(#[^"]*)?"', repl, html)


def _source_mtime(name: str) -> str:
    raw_path = config.RAW_DIR / page_filename(name)
    if not raw_path.exists():
        return ""
    text = raw_path.read_text(encoding="utf-8", errors="replace")
    m = _MTIME_RE.search(text)
    return m.group(1).strip() if m else ""


def _read_fragment(slug: str, locale: str, name: str) -> tuple[str, bool, bool]:
    """读取片段：data/parsed/zh → data/parsed/ja。返回 (html, translated, reviewed)。"""
    if locale == "zh":
        zh_path = config.DATA_DIR / "parsed" / "zh" / f"{slug}.html"
        if zh_path.exists():
            return zh_path.read_text(encoding="utf-8"), True, False
    ja_path = config.PARSED_JA_DIR / f"{slug}.html"
    if ja_path.exists():
        return ja_path.read_text(encoding="utf-8"), locale == "ja", False
    return "", False, False


# ---- 站点词汇表（日→中）：仅作用于 zh 站点；角色名按约定保留日文 ----
_GLOSSARY: dict | None = None


def _load_glossary() -> dict:
    """读取根目录 glossary/terms.yaml（AI 维护的日→中词汇表）。

    仅含站点 UI 文案（页面标题、侧栏链接文字、角色悬浮窗分段标题），
    不含页面正文（正文由用户手工翻译工作流处理）。
    """
    global _GLOSSARY
    if _GLOSSARY is not None:
        return _GLOSSARY
    data: dict = {}
    path = config.GLOSSARY_FILE
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:  # noqa: BLE001
            log.warning("词汇表读取失败，zh 站点将回退为日文原文：%s", exc)
            data = {}
    else:
        log.info("未找到词汇表 %s，zh 站点将保留日文标题", path)
    _GLOSSARY = data
    return data


def _page_title_ja2zh(name: str, locale: str) -> str:
    """zh 站点把 WIKI 日文页名翻译成中文；ja 或词表缺条目则保留日文原文。"""
    if locale != "zh":
        return name
    return _load_glossary().get("page_titles", {}).get(name, name)


def _write_md(path, title: str, fragment: str, from_slug: str, source_url: str, source_updated: str, synced: str, reviewed: bool, translated: bool, locale: str, pre_sanitized: bool = False, no_prevnext: bool = False) -> None:
    # 原始 HTML 片段以 JSON 形式单独落盘，生成时用 import 导入并由 MirrorContent
    # 以 v-html 在 SSR/客户端渲染。选用 JSON 而非 ?raw：VitePress 的 SSR 构建
    # 不会转换 ?raw 导入（导致预渲染内容为空），但会可靠转换 JSON 导入。
    # ⚠️ frag 必须按 locale 分文件（{slug}.ja.json / {slug}.zh.json）：ja 与 zh 的
    # .md 各自 import 自己的那份，否则后生成的 locale 会覆盖共享文件，导致日语页
    # 渲染出中文（或反之）。见 2026-07-25 修复。
    site_root = config.ROOT / "site"
    frag_dir = site_root / ".vitepress" / "frag"
    frag_dir.mkdir(parents=True, exist_ok=True)
    frag_file = frag_dir / f"{from_slug}.{locale}.json"
    frag_file.parent.mkdir(parents=True, exist_ok=True)
    # key 化 i18n 页面（pre_sanitized=True）在 parse/i18n build 阶段已完成
    # 净化+路由改写，此处直接落盘，免去每次 sync-site 的 lxml 重处理。
    # 但角色链接去链接化需再补一次（i18n 模板可能早于该逻辑生成、或正文为
    # 角色详情页内部互链），故 pre_sanitized 也跑轻量的 _neutralize_char_links。
    if pre_sanitized:
        sanitized = _neutralize_char_links_html(fragment)
    else:
        sanitized = _sanitize_html(_localize_routes(fragment, from_slug))
    frag_file.write_text(
        json.dumps({"html": sanitized}, ensure_ascii=False),
        encoding="utf-8",
    )
    rel = os.path.relpath(frag_file, path.parent).replace(os.sep, "/")
    path.parent.mkdir(parents=True, exist_ok=True)
    # 角色详情页禁用 VitePress 文档页脚 prev/next：其上一/下一篇是相邻角色，
    # 等价于「角色名跳转到角色页」——站点已有浮窗，无需此类跳转（也避免 ja 站
    # 生成 /escah/ja/characters/名.html 互链）。其他页保留上/下页导航。
    prevnext = "prev: false\nnext: false\n" if no_prevnext else ""
    body = MD_TEMPLATE.format(
        title=title.replace('"', "'"),
        source_url=source_url,
        source_updated=source_updated,
        synced=synced,
        reviewed=str(reviewed).lower(),
        translated=str(translated).lower(),
        rel=rel,
        prevnext=prevnext,
    )
    # 注入正文文本（隐藏块），供 VitePress 本地搜索索引；否则 md 仅含组件、索引无内容
    try:
        _tree = lxml_html.fragment_fromstring(sanitized, create_parent="div")
        _raw = re.sub(r"\s+", " ", _tree.text_content()).strip()
        if _raw:
            # 前置 <h1>页面标题</h1>：让 VitePress 搜索索引（_splitIntoSections）能切出
            # 带页面标题的上下文面包屑（titles），否则平铺纯文本会被切成 titles:[] 的大块，
            # 搜索结果列表不显示任何上下文/页面标题。
            body += '\n\n<div class="search-index" style="display:none" aria-hidden="true"><h1>{}</h1>{}</div>\n'.format(
                _html.escape(title, quote=False),
                _html.escape(_raw, quote=False),
            )
    except Exception:
        pass
    path.write_text(body, encoding="utf-8")




# 假名范围：用于判定文本是否仍含日文（需在中文标题后补原词）
_TERM_KANA_RE = re.compile(
    r"[\u3040-\u309F\u30A0-\u30FF\u31F0-\u31FF\uFF65-\uFF9F]"
)
_TAG_RE = re.compile(r"<[^>]+>")


def _has_kana(s: str) -> bool:
    return bool(_TERM_KANA_RE.search(s or ""))


def _augment_term_originals(zh_html: str, ja_html: str) -> str:
    """术语/俗语类页面：在 zh 的 <dt> 中文标题后补上原日文（中文（日文））。

    仅对含 <dl class="list1 list-indent1"> 的词条列表生效；按文档顺序把 zh 与 ja
    的同序 <dt> 配对，若 zh 标题尚未含日文则追加「（日文）」（包一层 .term-ja
    便于弱化样式），已含（如俗语集译者已手写日文）则跳过，保证幂等且不重复。
    """
    if (
        "list1 list-indent1" not in zh_html
        or "list1 list-indent1" not in ja_html
    ):
        return zh_html
    zh_dts = re.findall(r"<dt>(.*?)</dt>", zh_html, re.S)
    ja_dts = re.findall(r"<dt>(.*?)</dt>", ja_html, re.S)
    if len(zh_dts) != len(ja_dts) or not zh_dts:
        return zh_html
    ja_iter = iter(ja_dts)

    def repl(m: "re.Match") -> str:
        zh_txt = m.group(1)
        ja_txt = _TAG_RE.sub("", next(ja_iter, "")).strip()
        if ja_txt and not _has_kana(zh_txt) and _has_kana(ja_txt):
            return (
                f'<dt>{zh_txt}<span class="term-ja">（{ja_txt}）</span></dt>'
            )
        return m.group(0)

    return re.sub(r"<dt>(.*?)</dt>", repl, zh_html, flags=re.S)


def sync_site() -> None:
    config.ensure_dirs()
    entries = load_registry()
    manifest = Manifest()
    now = manifest.data.get("last_update_run") or ""

    # ---- 1. 镜像页 .md（ja/zh）----
    written = 0
    for e in entries:
        name, slug = e["name"], e["slug"]
        route_slug = slug
        synced = (manifest.page(name) or {}).get("fetched_at", "")[:10]
        # 原网页链接优先级：registry(pages.yaml) 显式 url > manifest 抓取 url > SOURCE_BASE 兜底
        source_url = (
            e.get("url")
            or (manifest.page(name) or {}).get("url")
            or f"{config.SOURCE_BASE}?{name}"
        )
        source_updated = _source_mtime(name)
        use_i18n = i18n.has_i18n(slug)
        # 预取 ja 片段，供 zh 词条标题补原日文（术语/俗语页）配对使用
        ja_fragment = None
        if use_i18n:
            ja_fragment = i18n.render_locale(slug, "ja")
        else:
            ja_fragment, _, _ = _read_fragment(slug, "ja", name)
        for locale, site_dir in (("ja", config.SITE_JA_DIR), ("zh", config.SITE_ZH_DIR)):
            if use_i18n:
                # key 化 i18n：模板 {{keyN}} → 语言文本（查表，零正则），已预净化
                fragment = i18n.render_locale(slug, locale)
                translated = locale == "zh" and i18n.zh_ratio(slug) > 0
                reviewed = False
            else:
                fragment, translated, reviewed = _read_fragment(slug, locale, name)
            if not fragment:
                continue
            # 术语/俗语类页面：zh 标题补原日文（ja 片段配对，已含则跳过）
            if locale == "zh" and ja_fragment and "list1 list-indent1" in fragment:
                fragment = _augment_term_originals(fragment, ja_fragment)
            md_path = site_dir / f"{route_slug}.md"
            _write_md(md_path, _page_title_ja2zh(name, locale), fragment, route_slug, source_url, source_updated, synced, reviewed, translated, locale, pre_sanitized=use_i18n, no_prevnext=(e.get("category") == "character-detail"))
            written += 1

    # ---- 2. 特殊页：首页 / 更新记录 ----
    special = {
        "updates": "<UpdateRecord />",
    }
    special_titles = {
        "updates": {"ja": "更新履歴", "zh": "更新记录"},
    }
    for slug_key, component in special.items():
        for locale, site_dir in (("ja", config.SITE_JA_DIR), ("zh", config.SITE_ZH_DIR)):
            title = special_titles[slug_key][locale]
            body = f'---\ntitle: "{title}"\nlayout: doc\n---\n\n{component}\n'
            (site_dir / f"{slug_key}.md").write_text(body, encoding="utf-8")

    # ---- 3. 首页门户 ----
    stats = _compute_stats(entries)
    for locale, site_dir in (("ja", config.SITE_JA_DIR), ("zh", config.SITE_ZH_DIR)):
        (site_dir / "index.md").write_text(_home_md(locale, stats), encoding="utf-8")

    # ---- 4. 数据 JSON ----
    public_data = config.SITE_PUBLIC_DIR / "data"
    public_data.mkdir(parents=True, exist_ok=True)
    # 同时写入 theme/.gen-data：供前端组件在 SSR 阶段 import（消除首屏空白、利于 SEO）。
    # 组件原本用 onMounted fetch(public/data/*)，SSR 时 onMounted 不执行会导致首屏真空白；
    # 改为 import 静态数据后，SSR 与 CSR 都能直接渲染内容。
    gen_data = config.SITE_DIR / ".vitepress" / "theme" / ".gen-data"
    gen_data.mkdir(parents=True, exist_ok=True)

    def _dump(name: str, obj):
        text = json.dumps(obj, ensure_ascii=False)
        (public_data / name).write_text(text, encoding="utf-8")
        (gen_data / name).write_text(text, encoding="utf-8")

    char_out = public_data / "char"
    char_out.mkdir(exist_ok=True)
    # 浮窗 JSON 的 zh 必须由「角色自己页面的 i18n 词典」回填（节点级 keyN + 整句块
    # 回退 blkN），与详情页 render_locale 用同一数据源。否则 extract_all_characters
    # 只做了 glossary 精确匹配（无块级回退），浮窗会比详情页少译大量技能/效果文本。
    i18n.char_fill_all()
    copied = 0
    for f in config.PARSED_CHAR_DIR.glob("*.json"):
        shutil.copy2(f, char_out / f.name)
        copied += 1
    _dump("updates.json", _updates_data(entries, manifest))
    _dump("page-times.json", _page_times_data(entries, manifest))
    _dump("site-terms.json", {"char_sections": _load_glossary().get("char_sections", {})})

    # ---- 5. 图片同步 ----
    img_out = config.SITE_PUBLIC_DIR / "img"
    img_out.mkdir(exist_ok=True)
    img_count = 0
    for f in config.ASSETS_IMG_DIR.iterdir():
        if f.is_file():
            shutil.copy2(f, img_out / f.name)
            img_count += 1

    # ---- 6. 侧边栏 ----
    _write_sidebars(entries)

    # ---- 7. 根跳转页 ----
    # 注意：location 在 SSR 渲染时不可用，必须放到 onMounted 中仅客户端执行，
    # 否则 `vitepress build` 会因 ReferenceError: location is not defined 而失败。
    (config.SITE_DIR / "index.md").write_text(
        '---\nlayout: page\n---\n'
        '<script setup>\n'
        "import { onMounted } from 'vue'\n"
        "onMounted(() => { location.replace('./zh/') })\n"
        '</script>\n',
        encoding="utf-8",
    )
    log.info(
        "站点内容生成完成：md %d 页，角色 %d，角色数据 %d，图片 %d",
        written, sum(1 for e in entries if e.get("category") == "character-detail"), copied, img_count,
    )


def _compute_stats(entries: list[dict]) -> dict:
    watch = sum(1 for e in entries if e.get("mode") == "watch")
    chars = sum(1 for e in entries if e.get("category") == "character-detail")
    return {"pages": len(entries), "watch": watch, "chars": chars}


def _home_md(locale: str, stats: dict) -> str:
    if locale == "zh":
        hero_title, hero_tag, recent = "超昂大战 Escalation Heroines", "攻略 Wiki 中日双语镜像站", "镜像站更新记录"
        pages_label, chars_label = "镜像页面", "收录角色"
    else:
        hero_title, hero_tag, recent = "超昂大戦エスカレーションヒロインズ", "攻略 Wiki 日中バイリンガルミラー", "ミラーサイト更新履歴"
        pages_label, chars_label = "ミラーページ", "収録キャラクター"
    return f"""---
title: "{hero_title}"
layout: doc
---

<div class="home-hero">
  <h1>{hero_title}</h1>
  <p>{hero_tag}</p>
  <div class="home-stats">
    <div class="stat"><b>{stats['pages']}</b><span>{pages_label}</span></div>
    <div class="stat"><b>{stats['chars']}</b><span>{chars_label}</span></div>
  </div>
</div>

<CategoryCards />

## {recent}

<MirrorChangelog />
"""


def _updates_data(entries: list[dict], manifest: Manifest) -> dict:
    by_date: dict[str, list[dict]] = {}
    for e in entries:
        m = manifest.page(e["name"])
        if not m or m.get("status") != "ok":
            continue
        date = (m.get("fetched_at") or "")[:10]
        if not date:
            continue
        by_date.setdefault(date, []).append({
            "name": e["name"], "slug": e["slug"], "status": m["status"],
        })
    changed = [
        {"date": d, "pages": sorted(ps, key=lambda p: p["name"])}
        for d, ps in sorted(by_date.items(), reverse=True)
    ][:14]
    return {
        "lastRun": manifest.data.get("last_update_run"),
        "watchCount": sum(1 for e in entries if e.get("mode") == "watch"),
        "changed": changed,
    }


def _page_times_data(entries: list[dict], manifest: "Manifest") -> dict:
    """更新记录页数据：按「攻略 / 角色」分两组，每组四列
    （日文名 / 中文名 / 原WIKI最后编辑时间 / 镜像站点更新时间）。

    - 日文名与中文名固定展示，不随中日站点切换翻译。
    - 攻略组按导航栏默认顺序（分类序 + 名称）排序。
    - 角色组按「キャラクター一覧」页表格的固有顺序排序（SSR→SR→R→…）。
    - 时间取自 manifest：wiki_last_modified（原站）、fetched_at（镜像）。
    """
    # 角色 canonical 顺序：解析 キャラクター一覧 页表格里 characters/名.html 的出现顺序
    order: dict[str, int] = {}
    try:
        chtml = (config.PARSED_JA_DIR / "characters.html").read_text(
            encoding="utf-8", errors="replace"
        )
        for i, m in enumerate(re.finditer(r"characters/([^ \"#'?]+\.html)", chtml)):
            nm = unquote(m.group(1))[:-5]  # 去掉 .html
            order.setdefault(nm, i)
    except Exception:
        pass

    guide_rows: list[tuple[int, dict]] = []
    char_rows: list[tuple[int, dict]] = []
    for e in entries:
        name = e["name"]
        cat = e.get("category", "misc")
        m = manifest.page(name) or {}
        wiki = (m.get("wiki_last_modified") or "")[:16].replace("T", " ")
        mirror = (m.get("fetched_at") or "")[:16].replace("T", " ")
        row = {
            "ja": name,
            "zh": _page_title_ja2zh(name, "zh"),
            "wiki": wiki,
            "mirror": mirror,
        }
        if cat == "character-detail":
            char_rows.append((order.get(name, 10 ** 9), row))
        else:
            ci = CATEGORY_ORDER.index(cat) if cat in CATEGORY_ORDER else len(CATEGORY_ORDER)
            guide_rows.append((ci, row))
    guide_rows.sort(key=lambda t: (t[0], t[1]["ja"]))
    char_rows.sort(key=lambda t: t[0])
    return {
        "guide": [t[1] for t in guide_rows],
        "characters": [t[1] for t in char_rows],
    }


def _sb_combined_node(node, locale: str, slug_index: dict, explicit: set) -> dict | None:
    """合并多个列表页为一个侧边栏文本节点，内含多个链接：例如 "SSR | SR | R"。"""
    parts = []
    for s in node["combined"]:
        e = slug_index.get(s)
        if e is None:
            return None
        explicit.add(s)
        label = (_SB_OVERRIDE_ZH[s] if locale == "zh" and s in _SB_OVERRIDE_ZH
                 else _page_title_ja2zh(e["name"], locale))
        parts.append(f'<a href="/{locale}/{s}.html">{label}</a>')
    return {
        "text": node.get("sep", " | ").join(parts),
        "collapsible": False,
    }


def _sb_node(node, locale: str, slug_index: dict, explicit: set) -> dict | None:
    """把 SIDEBAR_TREE 的一个节点递归展开成 VitePress sidebar item。"""
    if node == _SB_DIV:
        # 视觉分隔符：VitePress 会丢弃「纯 hash 链接」(#xxx) 的 sidebar item（客户端渲染
        # 时直接跳过），所以这里用「一个真实存在页面 + #__SB_DIV__ 锚点」作为 link，
        # 确保渲染出 <a href="...#__SB_DIV__">。custom.css 隐藏文字、用 border-top 画实线。
        return {"text": "—", "link": f"/{locale}/characters.html#__SB_DIV__"}
    if isinstance(node, dict) and node.get("combined"):
        return _sb_combined_node(node, locale, slug_index, explicit)
    slug = node["slug"]
    explicit.add(slug)
    e = slug_index.get(slug)
    if e is None:
        return None
    text = (_SB_OVERRIDE_ZH[slug] if locale == "zh" and slug in _SB_OVERRIDE_ZH
            else _page_title_ja2zh(e["name"], locale))
    item = {"text": text, "link": f"/{locale}/{slug}.html"}
    kids = node.get("items")
    if kids:
        sub = []
        for k in kids:
            n = _sb_node(k, locale, slug_index, explicit)
            if n is not None:
                sub.append(n)
        # 中间节点不折叠（用户要求全部展开，不要可折叠/展开）。
        item["items"] = sub
    return item


def _write_sidebars(entries: list[dict]) -> None:
    gen_dir = config.SITE_DIR / ".vitepress" / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)
    # slug -> entry 索引（跳过角色详情页与子页面，不进侧边栏）
    slug_index: dict[str, dict] = {}
    for e in entries:
        if e.get("category") in ("character-detail", "subpage"):
            continue
        slug_index[e["slug"]] = e
    for locale in ("ja", "zh"):
        sidebar: list[dict] = []
        explicit: set[str] = set()
        for grp in SIDEBAR_TREE:
            cat = grp["cat"]
            label = CATEGORY_LABELS[cat][locale]
            if grp.get("flat"):
                # 游戏指南 / 其他：保持 registry 原顺序平铺
                items = [{
                    "text": _page_title_ja2zh(e["name"], locale),
                    "link": f"/{locale}/{e['slug']}.html",
                } for e in entries
                    if e.get("category") == cat and e.get("category") not in ("character-detail", "subpage")]
            else:
                items = []
                for node in grp["items"]:
                    if isinstance(node, dict) and node.get("combined"):
                        n = _sb_combined_node(node, locale, slug_index, explicit)
                        if n is not None:
                            items.append(n)
                        continue
                    n = _sb_node(node, locale, slug_index, explicit)
                    if n is not None:
                        items.append(n)
                # fallback：该分类下未显式列出的页面（含未来新增）追加到组末尾
                for s, e in slug_index.items():
                    if e.get("category") == cat and s not in explicit:
                        items.append({
                            "text": _page_title_ja2zh(e["name"], locale),
                            "link": f"/{locale}/{s}.html",
                        })
            if cat == "misc":
                # 站点栏目：更新记录（非 registry 条目）
                items.append({
                    "text": "更新履歴" if locale == "ja" else "更新记录",
                    "link": f"/{locale}/updates.html",
                })
            sidebar.append({
                "text": label,
                "collapsed": bool(grp.get("collapsed", False)),
                "items": items,
            })
        (gen_dir / f"sidebar.{locale}.json").write_text(
            json.dumps(sidebar, ensure_ascii=False, indent=1), encoding="utf-8"
        )
