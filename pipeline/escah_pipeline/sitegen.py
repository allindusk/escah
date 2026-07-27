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
_MTIME_RE = re.compile(r"Last-modified:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}[^<\n]*)")

MD_TEMPLATE = """---
title: "{title}"
layout: doc
outline: [2, 3]
meta:
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

    # ---- 页内目录（wiki .contents）锚点修正：PukiWiki 的 TOC 链接指向内层
    #      anchor(<a id="y4f8fac5">) 的哈希，而该内层 anchor 已被 _strip_nav_links
    #      剥离（仅保留 <hX id="content_1_0">）。导致页内目录点击无反应。这里按
    #      文本匹配把 TOC 链接重指向真实存在的标题 id，恢复页内跳转。----
    _relink_toc(frag)

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


def _strip_nav_links(frag) -> None:
    """删除 wiki 的导航/工具超链接，保留其内部结构（角色头像/纯文本）。

    - jumpmenu：回到顶部导航箭头
    - anchor_super：章节编辑锚点（† / 铅笔）
    - internal-link：去掉 <a> 外衣、保留内部内容（避免整站死链，角色卡头像与
      交叉引用文本得以保留；悬停浮窗仍由头像/角色名触发）
    """
    for el in frag.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' jumpmenu ')]"):
        el.drop_tree()
    for el in frag.xpath(".//a[contains(concat(' ', normalize-space(@class), ' '), ' anchor_super ')]"):
        el.drop_tree()
    for a in frag.xpath(".//a[contains(concat(' ', normalize-space(@class), ' '), ' internal-link ')]"):
        # 拆解保留内部内容：去掉跳转链接，但保留其中的文字/图片。
        # 纯文本保存在 a.text、尾文本在 a.tail（均非「元素子节点」），必须把二者
        # 一并提升到父节点，否则纯文本链接（如表格/列表里的角色名、分类页 ・ 列表）
        # 文字会被整体删除 → 表现为表格角色名列空白、分类页只剩小黑点。
        parent = a.getparent()
        if parent is None:
            a.drop_tree()
            continue
        prev = a.getprevious()
        if a.text:
            if prev is not None:
                prev.tail = (prev.tail or "") + a.text
            else:
                parent.text = (parent.text or "") + a.text
        for child in list(a):
            parent.insert(parent.index(a), child)
        last = a.getprevious()
        if a.tail:
            if last is not None:
                last.tail = (last.tail or "") + a.tail
            elif prev is not None:
                prev.tail = (prev.tail or "") + a.tail
            else:
                parent.text = (parent.text or "") + a.tail
        parent.remove(a)


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
        txt = re.sub(r"\s+", "", h.text_content() or "")
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


def _write_md(path, title: str, fragment: str, from_slug: str, source_url: str, source_updated: str, synced: str, reviewed: bool, translated: bool, locale: str, pre_sanitized: bool = False) -> None:
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
    sanitized = fragment if pre_sanitized else _sanitize_html(_localize_routes(fragment, from_slug))
    frag_file.write_text(
        json.dumps({"html": sanitized}, ensure_ascii=False),
        encoding="utf-8",
    )
    rel = os.path.relpath(frag_file, path.parent).replace(os.sep, "/")
    path.parent.mkdir(parents=True, exist_ok=True)
    body = MD_TEMPLATE.format(
        title=title.replace('"', "'"),
        source_url=source_url,
        source_updated=source_updated,
        synced=synced,
        reviewed=str(reviewed).lower(),
        translated=str(translated).lower(),
        rel=rel,
    )
    # 注入正文文本（隐藏块），供 VitePress 本地搜索索引；否则 md 仅含组件、索引无内容
    try:
        _tree = lxml_html.fragment_fromstring(sanitized, create_parent="div")
        _raw = re.sub(r"\s+", " ", _tree.text_content()).strip()
        if _raw:
            body += '\n\n<div class="search-index" style="display:none" aria-hidden="true">{}</div>\n'.format(
                _html.escape(_raw, quote=False)
            )
    except Exception:
        pass
    path.write_text(body, encoding="utf-8")




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
        source_url = (manifest.page(name) or {}).get("url") or f"{config.SOURCE_BASE}?{name}"
        source_updated = _source_mtime(name)
        use_i18n = i18n.has_i18n(slug)
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
            md_path = site_dir / f"{route_slug}.md"
            _write_md(md_path, _page_title_ja2zh(name, locale), fragment, route_slug, source_url, source_updated, synced, reviewed, translated, locale, pre_sanitized=use_i18n)
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
        hero_title, hero_tag, recent = "超昂大战 Escalation Heroines", "攻略 Wiki 中日双语镜像站", "最近更新"
        pages_label, chars_label = "镜像页面", "收录角色"
    else:
        hero_title, hero_tag, recent = "超昂大戦エスカレーションヒロインズ", "攻略 Wiki 日中バイリンガルミラー", "最近の更新"
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

<RecentUpdates />
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


def _write_sidebars(entries: list[dict]) -> None:
    gen_dir = config.SITE_DIR / ".vitepress" / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)
    for locale in ("ja", "zh"):
        sections: dict[str, list[dict]] = {}
        for e in entries:
            cat = e.get("category", "misc")
            if cat == "character-detail":
                continue
            route_slug = e["slug"]
            sections.setdefault(cat, []).append({
                "text": _page_title_ja2zh(e["name"], locale),
                "link": f"/{locale}/{route_slug}.html",
            })
        # キャラクター一覧分组：wiki「キャラクター一覧」页（/characters，含 369 角色列表）为父节点，
        # SSR/SR/R 作为其子节点（树状）；其余角色相关页（必杀技一覧/原画別索引…）并列。
        char_pages = sections.get("character", [])
        # 注意：链接统一带 .html 后缀（cleanUrls:false），判断须匹配 .html，
        # 否则 wiki_char/rarity 全部落空 → 生成空「角色一览」父节点 + 所有页平铺（重复项）。
        wiki_char = next(
            (it for it in char_pages if it["link"].endswith(("/characters", "/characters.html"))),
            None,
        )
        _RARITY_SUF = ("/list-ssr", "/list-sr", "/list-r",
                       "/list-ssr.html", "/list-sr.html", "/list-r.html")
        rarity = [it for it in char_pages if it["link"].endswith(_RARITY_SUF)]
        others = [it for it in char_pages if it is not wiki_char and it not in rarity]
        char_items: list[dict] = []
        if wiki_char is not None:
            wiki_char = dict(wiki_char)
            wiki_char["text"] = _page_title_ja2zh(wiki_char["text"], locale)
            wiki_char["collapsed"] = False
            wiki_char["items"] = rarity
            char_items.append(wiki_char)
        else:
            char_items.append({
                "text": "キャラクター一覧" if locale == "ja" else "角色一览",
                "collapsed": False,
                "items": rarity,
            })
        char_items.extend(others)
        sidebar = [
            {"text": "キャラクター" if locale == "ja" else "角色", "collapsed": False, "items": char_items}
        ]
        for key in CATEGORY_ORDER:
            # character 已并入「キャラクター一覧」；misc 并入下方「その他」，避免重复分组
            if key in ("character", "misc"):
                continue
            if key in sections:
                sidebar.append({
                    "text": CATEGORY_LABELS[key][locale],
                    "collapsed": True,
                    "items": sections[key],
                })
        # その他：分类为 misc 的页面 + 站点栏目（全ページ一覧/更新履歴），合并去重
        misc_items = list(sections.get("misc", []))
        misc_items.append(
            {"text": "更新履歴" if locale == "ja" else "更新记录", "link": f"/{locale}/updates.html"}
        )
        sidebar.append({
            "text": CATEGORY_LABELS["misc"][locale],
            "collapsed": True,
            "items": misc_items,
        })
        (gen_dir / f"sidebar.{locale}.json").write_text(
            json.dumps(sidebar, ensure_ascii=False, indent=1), encoding="utf-8"
        )
