"""生成 VitePress 站点内容：双语 .md、数据 JSON、侧边栏、图片同步。

数据流：data/parsed/ja（日文片段）+ data/parsed/zh（中文片段/人工覆盖）
      → site/ja、site/zh（生成的 .md，不手工编辑）+ site/public（数据与图片）
"""
from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import shutil
from urllib.parse import urljoin

import yaml
from bs4 import BeautifulSoup
from lxml import html as lxml_html

from . import config
from .logutil import get_logger
from .parser_puki import safe_id
from .registry import RARITY_SECTIONS, load_registry
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
_HEADING_RE = re.compile(r"^h[1-6]$", re.I)
_IMG_EXT_RE = re.compile(r"\.([a-zA-Z0-9]+)$")
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


def _img_local_name(src: str) -> str:
    abs_url = urljoin(config.SOURCE_BASE, src)
    digest = hashlib.sha256(abs_url.encode()).hexdigest()[:16]
    m = _IMG_EXT_RE.search(src.rsplit("/", 1)[-1])
    ext = (m.group(1).lower() if m else "png")
    ext = re.sub(r"[^a-z0-9]", "", ext)[:5] or "png"
    return f"{digest}.{ext}"


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
    """读取片段：zh 优先人工覆盖 → data/parsed/zh → data/parsed/ja。返回 (html, translated, reviewed)。"""
    if locale == "zh":
        override = config.OVERRIDES_ZH_DIR / f"{slug}.html"
        if override.exists():
            return override.read_text(encoding="utf-8"), True, True
        zh_path = config.DATA_DIR / "parsed" / "zh" / f"{slug}.html"
        if zh_path.exists():
            return zh_path.read_text(encoding="utf-8"), True, False
    ja_path = config.PARSED_JA_DIR / f"{slug}.html"
    if ja_path.exists():
        return ja_path.read_text(encoding="utf-8"), locale == "ja", False
    return "", False, False


def _write_md(path, title: str, fragment: str, from_slug: str, source_url: str, source_updated: str, synced: str, reviewed: bool, translated: bool) -> None:
    # 原始 HTML 片段以 JSON 形式单独落盘，生成时用 import 导入并由 MirrorContent
    # 以 v-html 在 SSR/客户端渲染。选用 JSON 而非 ?raw：VitePress 的 SSR 构建
    # 不会转换 ?raw 导入（导致预渲染内容为空），但会可靠转换 JSON 导入。
    site_root = config.ROOT / "site"
    frag_dir = site_root / ".vitepress" / "frag"
    frag_dir.mkdir(parents=True, exist_ok=True)
    frag_file = frag_dir / f"{from_slug}.json"
    frag_file.parent.mkdir(parents=True, exist_ok=True)
    frag_file.write_text(
        json.dumps({"html": _sanitize_html(_localize_routes(fragment, from_slug))}, ensure_ascii=False),
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
    path.write_text(body, encoding="utf-8")


def _extract_charlist(entries_by_name: dict[str, dict]) -> list[dict]:
    """从キャラクター一覧 raw 页提取角色卡片数据（含筛选元数据）。"""
    raw_path = config.RAW_DIR / page_filename(config.CHARLIST_PAGE)
    if not raw_path.exists():
        log.warning("キャラクター一覧 快照不存在，角色卡片数据为空")
        return []
    soup = BeautifulSoup(raw_path.read_text(encoding="utf-8", errors="replace"), "lxml")
    content = soup.select_one("#body") or soup
    chars: list[dict] = []
    rarity: str | None = None
    for el in content.descendants:
        tag = getattr(el, "name", None)
        if tag and _HEADING_RE.match(tag):
            text = re.sub(r"[^A-Za-z]", "", el.get_text(strip=True)).replace("edit", "")
            rarity = text if text in RARITY_SECTIONS else None
        elif tag == "tr" and rarity:
            img_link = el.find("a", href=True)
            if img_link is None or img_link.find("img") is None:
                continue
            name = img_link.get("title") or img_link.find("img").get("alt", "").replace("_icon.png", "")
            if not name or name not in entries_by_name:
                continue
            img = img_link.find("img")
            # 提取行单元格 → 表头映射（表头为该表第一行）
            table = el.find_parent("table")
            headers: list[str] = []
            if table:
                first = table.find("tr")
                if first:
                    headers = [c.get_text(strip=True) for c in first.find_all(["th", "td"], recursive=False)]
            cells = [c.get_text(" ", strip=True) for c in el.find_all(["th", "td"], recursive=False)]
            meta: dict[str, str] = {}
            for i, val in enumerate(cells):
                if i < len(headers):
                    key = headers[i].strip()
                    # 只保留类别型列（值短且非纯数字），作为筛选项
                    if key and val and len(val) <= 8 and not val.isdigit() and key not in ("名前", "アイコン"):
                        meta[key] = val
            chars.append({
                "name": name,
                "rarity": entries_by_name[name].get("rarity", rarity),
                "icon": "img/" + _img_local_name(img.get("src", "")),
                "meta": meta,
            })
    return chars


def sync_site() -> None:
    config.ensure_dirs()
    entries = load_registry()
    manifest = Manifest()
    now = manifest.data.get("last_update_run") or ""
    by_name = {e["name"]: e for e in entries}

    # ---- 1. 镜像页 .md（ja/zh）----
    written = 0
    for e in entries:
        name, slug = e["name"], e["slug"]
        route_slug = "characters-mirror" if slug == "characters" else slug
        synced = (manifest.page(name) or {}).get("fetched_at", "")[:10]
        source_url = (manifest.page(name) or {}).get("url") or f"{config.SOURCE_BASE}?{name}"
        source_updated = _source_mtime(name)
        for locale, site_dir in (("ja", config.SITE_JA_DIR), ("zh", config.SITE_ZH_DIR)):
            fragment, translated, reviewed = _read_fragment(slug, locale, name)
            if not fragment:
                continue
            md_path = site_dir / f"{route_slug}.md"
            _write_md(md_path, name, fragment, route_slug, source_url, source_updated, synced, reviewed, translated)
            written += 1

    # ---- 2. 特殊页：角色一览（重构）/ 首页 / 索引 / 术语 / 更新记录 ----
    special = {
        "characters": "<CharList />",
        "sitemap": "<SiteMap />",
        "updates": "<UpdatesLog />",
        # 注意：不能用 "glossary"——该 slug 已被 WIKI 镜像页「用語集」占用，
        # 同名会覆盖镜像 md 导致用語集页面在站点上不可见。
        "term-map": "<GlossaryTable />",
    }
    special_titles = {
        "characters": {"ja": "キャラクター一覧", "zh": "角色一览"},
        "sitemap": {"ja": "全ページ一覧", "zh": "全部页面"},
        "updates": {"ja": "更新履歴", "zh": "更新记录"},
        "term-map": {"ja": "日中用語対照表", "zh": "日中术语对照表"},
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
    chars = _extract_charlist(by_name)
    (public_data / "characters.json").write_text(
        json.dumps(chars, ensure_ascii=False), encoding="utf-8"
    )
    char_out = public_data / "char"
    char_out.mkdir(exist_ok=True)
    copied = 0
    for f in config.PARSED_CHAR_DIR.glob("*.json"):
        shutil.copy2(f, char_out / f.name)
        copied += 1
    glossary = yaml.safe_load(config.GLOSSARY_FILE.read_text(encoding="utf-8")) or []
    (public_data / "glossary.json").write_text(
        json.dumps(glossary, ensure_ascii=False), encoding="utf-8"
    )
    (public_data / "updates.json").write_text(
        json.dumps(_updates_data(entries, manifest), ensure_ascii=False), encoding="utf-8"
    )
    (public_data / "sitemap.json").write_text(
        json.dumps(_sitemap_data(entries, manifest), ensure_ascii=False), encoding="utf-8"
    )

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
        "onMounted(() => { location.replace('./ja/') })\n"
        '</script>\n',
        encoding="utf-8",
    )
    log.info(
        "站点内容生成完成：md %d 页，角色卡 %d，角色数据 %d，图片 %d",
        written, len(chars), copied, img_count,
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


def _sitemap_data(entries: list[dict], manifest: Manifest) -> dict:
    cats: dict[str, list[dict]] = {}
    for e in entries:
        cat = e.get("category", "misc")
        m = manifest.page(e["name"])
        cats.setdefault(cat, []).append({
            "title": e["name"],
            "slug": "characters-mirror" if e["slug"] == "characters" else e["slug"],
            "synced": (m or {}).get("fetched_at", "")[:10],
        })
    out = []
    for key in CATEGORY_ORDER + ["character-detail"]:
        if key in cats:
            out.append({
                "key": key,
                "label_ja": CATEGORY_LABELS[key]["ja"],
                "label_zh": CATEGORY_LABELS[key]["zh"],
                "pages": sorted(cats[key], key=lambda p: p["title"]),
            })
    return {"categories": out}


def _write_sidebars(entries: list[dict]) -> None:
    gen_dir = config.SITE_DIR / ".vitepress" / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)
    for locale in ("ja", "zh"):
        sections: dict[str, list[dict]] = {}
        for e in entries:
            cat = e.get("category", "misc")
            if cat == "character-detail":
                continue
            route_slug = "characters-mirror" if e["slug"] == "characters" else e["slug"]
            sections.setdefault(cat, []).append({
                "text": e["name"],
                "link": f"/{locale}/{route_slug}",
            })
        sidebar = [
            {"text": CATEGORY_LABELS["character"][locale], "collapsed": False,
             "items": [{"text": "キャラクター一覧" if locale == "ja" else "角色一览", "link": f"/{locale}/characters"}]}
        ]
        for key in CATEGORY_ORDER:
            if key in sections:
                sidebar.append({
                    "text": CATEGORY_LABELS[key][locale],
                    "collapsed": True,
                    "items": sections[key],
                })
        sidebar.append({
            "text": "その他" if locale == "ja" else "站点",
            "collapsed": True,
            "items": [
                {"text": "全ページ一覧" if locale == "ja" else "全部页面", "link": f"/{locale}/sitemap"},
                {"text": "日中用語対照表" if locale == "ja" else "日中术语对照表", "link": f"/{locale}/term-map"},
                {"text": "更新履歴" if locale == "ja" else "更新记录", "link": f"/{locale}/updates"},
            ],
        })
        (gen_dir / f"sidebar.{locale}.json").write_text(
            json.dumps(sidebar, ensure_ascii=False, indent=1), encoding="utf-8"
        )
