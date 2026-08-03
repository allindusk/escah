"""PukiWiki 解析器：raw 快照 → 净化 HTML 片段（日文忠实原文）+ 翻译文本块清单。

设计说明：
- 中间层用 HTML 片段而非 Markdown——原网页大量 colspan/rowspan 复杂表格，
  HTML 片段可保证镜像排版与原网页完全一致；文本块清单（chunks）供翻译使用。
- 日文忠实原则：只移除 wiki 管理控件（编辑链接、投稿表单、脚本），不改动任何正文文本；
  站内链接与图片引用仅做"指向"改写，不改显示文本。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from concurrent.futures import ProcessPoolExecutor
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup, Comment, Tag

from . import config
from .logutil import get_logger
from .registry import extract_characters, href_to_page_name, load_registry
from .snapshot import Manifest, page_filename

log = get_logger()

# 需要当作翻译块的内层块级标签
BLOCK_TAGS = ("p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "dt", "dd", "caption", "blockquote")
# 块内内容保持原样不翻译的标签
SKIP_TRANSLATE_TAGS = ("pre", "code", "script", "style")
# 需要翻译的日文字符
_JA_RE = re.compile(r"[ぁ-んァ-ヶ一-龯々〆ヵヶ]")
# Windows 文件名非法字符 → 全角替代
_INVALID_FILENAME = str.maketrans({"/": "／", "\\": "＼", ":": "：", "*": "＊", "?": "？", '"': "″", "<": "＜", ">": "＞", "|": "｜"})

CHROME_LINK_RE = re.compile(r"[?&]cmd=(edit|guiedit|freeze|diff|backup)")
CHROME_IMG_RE = re.compile(r"(guiedit|paraedit|edit)\.png")

# 上游 wiki 用 [添付:名_icon.png] 引用角色头像；若该附件未上传，wiki 会渲染出
# “File not found: "名_icon.png" at page "img"[添付]” 文本。下游镜像据此替换为角色已知头像。
_CHAR_ICON_MAP: dict[str, str] | None = None
_FILE_NOT_FOUND_RE = re.compile(
    r'File not found:.*?([^"\s&]+?)_icon\.png.*?at page.*?img.*?\[添付\]'
)


def _char_icon_map() -> dict[str, str]:
    """名(日文) → 本地头像 hash(不含 img/ 前缀)，取自「キャラクター一覧」快照。

    与 chara.py 同源(extract_characters)，hash 与 data/parsed/characters/*.json 的 icon 一致；
    取快照而非已提取 JSON，可避免“先 parse 后提取”顺序下新角色首次 parse 时映射缺失。
    """
    global _CHAR_ICON_MAP
    if _CHAR_ICON_MAP is not None:
        return _CHAR_ICON_MAP
    m: dict[str, str] = {}
    try:
        raw = config.RAW_DIR / page_filename(config.CHARLIST_PAGE)
        if raw.exists():
            for c in extract_characters(raw.read_text(encoding="utf-8", errors="replace")):
                icon = c.get("icon") or ""
                if icon.startswith("img/"):
                    m[c["name"]] = icon.split("/", 1)[-1]
    except Exception as err:  # noqa: BLE001
        log.warning("构建角色头像映射失败：%s", err)
    _CHAR_ICON_MAP = m
    return m


def _fix_missing_char_icons(soup: BeautifulSoup, body: Tag) -> None:
    """把上游 wiki 未上传附件导致的“File not found”角色头像单元格替换为已知头像 <img>。"""
    icon_map = _char_icon_map()
    if not icon_map:
        return
    for a in list(body.find_all("a")):
        mm = _FILE_NOT_FOUND_RE.search(a.get_text(strip=True))
        if not mm:
            continue
        name = mm.group(1)
        if name not in icon_map:
            continue
        img = soup.new_tag("img", src=f"/img/{icon_map[name]}")
        img["alt"] = f"{name}_icon.png"
        img["title"] = f"{name}_icon.png"
        img["height"] = "100"
        img["width"] = "100"
        img["loading"] = "lazy"
        a.replace_with(img)


def safe_id(name: str) -> str:
    """页面名 → 文件安全 ID（保留日文可读性）。"""
    return name.translate(_INVALID_FILENAME)


def needs_translation(text: str) -> bool:
    return bool(_JA_RE.search(text))


def _keep_pcomments(body: BeautifulSoup) -> None:
    """保留 pcomment 插件的网友评论（含 [发送ID] 与 comment_date 时间），从被删的 form 中解救。

    PukiWiki 的 pcomment 把评论 <ul class="list1">（含 li.pcmt 与嵌套回复 ul.list2/3）
    整体嵌在 <form> 内，原 _remove_chrome 会随 form 一并 decompose 掉。这里在通用
    form 删除之前先把评论 ul 移出 form，并清理回复单选框 / 空“新帖”标记 / 提交表单 /
    死链提示“最新の20件を表示しています”。评论正文、[发送ID]、时间均保留。
    """
    for div in body.find_all("div", class_="pcomment"):
        for form in list(div.find_all("form")):
            ul = form.find("ul")
            if ul is not None and ul.find("li", class_="pcmt") is not None:
                form.insert_before(ul)
            form.decompose()
        pf = div.find("div", id="pcomment-form")
        if pf is not None:
            pf.decompose()
        for st in list(div.find_all("style")):
            st.decompose()
        for p in list(div.find_all("p")):
            if "最新の20件" in (p.get_text() or ""):
                p.decompose()
        # 统一清理评论项的回复单选框与空“新帖”标记（同时覆盖评论不在 form 内的情况）
        for li in div.find_all("li", class_="pcmt"):
            inp = li.find("input", class_="pcmt")
            if inp is not None:
                inp.decompose()
            for ns in li.find_all("span", class_="__plugin_new"):
                ns.decompose()


def _remove_chrome(body: BeautifulSoup) -> None:
    """移除 wiki 管理控件：编辑链接、锚点标记、脚本、表单控件（不碰正文文本）。"""
    for tag in body.find_all(["script", "style", "noscript", "iframe"]):
        tag.decompose()
    for tag in body.find_all(["form", "input", "button", "select", "textarea"]):
        tag.decompose()
    for a in list(body.find_all("a", href=True)):
        href = a["href"]
        # 附件"查看大图"链接：正文内容图常被此类链接包裹。
        # 若含 <img> 则解包（保留图片、去掉链接）；否则视为纯管理链接删除。
        if "plugin=attach" in href:
            if a.find("img") is not None:
                a.unwrap()
            else:
                a.decompose()
            continue
        # 编辑/管理链接
        if CHROME_LINK_RE.search(href) or "plugin=newpage" in href:
            a.decompose()
            continue
        # 空锚点标记（#xxx 且无文本）
        if href.startswith("#") and not a.get_text(strip=True) and a.find("img") is None:
            a.decompose()
    for img in list(body.find_all("img", src=True)):
        if CHROME_IMG_RE.search(img["src"]):
            img.decompose()
    for c in body.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()


# 站方皮肤自动注入的「板の利用ルール」通知（PukiWiki region 插件块 rgn-container）：
# 每页重复出现、非页面正文，不应镜像也不应翻译。按内容唯一标识，
# 避免误删页面作者用 region 插件写的正经折叠内容。
_RULES_MARKERS = ("板を利用する前にルールを必ずお読みください", "ルールについて")


def _remove_rules_region(body: BeautifulSoup) -> None:
    """删除每页自动附加的「利用規約/板の利用ルール」通知区域。"""
    for div in list(body.find_all("div", class_="rgn-container")):
        txt = div.get_text(" ", strip=True) or ""
        if any(m in txt for m in _RULES_MARKERS):
            div.decompose()


def _rewrite_links(body: BeautifulSoup, slug_by_name: dict[str, str]) -> None:
    """站内链接 → 本站路由；未登记页面 → 源站绝对链接（新窗口）。"""
    for a in body.find_all("a", href=True):
        href = a["href"]
        name = href_to_page_name(href)
        if name is None:
            if href.startswith("http"):
                a["target"] = "_blank"
                a["rel"] = "noopener"
            continue
        anchor = ""
        if "#" in href:
            anchor = "#" + href.split("#", 1)[1]
        slug = slug_by_name.get(name)
        if slug:
            a["href"] = "__ROUTE__/" + quote(slug) + ".html" + anchor
            a["class"] = (a.get("class") or []) + ["internal-link"]
        else:
            # 未登记的页面（活动页、NPC 等）→ 源站
            a["href"] = f"{config.SOURCE_BASE}?{quote(name)}" + anchor
            a["target"] = "_blank"
            a["rel"] = "noopener"
            a["class"] = (a.get("class") or []) + ["source-link"]


def _rewrite_images(body: BeautifulSoup, pending_assets: dict[str, str]) -> None:
    """图片 → 本地 /img/<hash>.<ext>；源 URL 登记进 pending_assets 供下载。"""
    for img in body.find_all("img", src=True):
        src = img["src"].strip()
        if src.startswith("data:"):
            continue
        abs_url = urljoin(config.SOURCE_BASE, src)
        digest = hashlib.sha256(abs_url.encode("utf-8")).hexdigest()[:16]
        ext = src.rsplit(".", 1)[-1].lower() if "." in src.rsplit("/", 1)[-1] else "png"
        ext = re.sub(r"[^a-z0-9]", "", ext)[:5] or "png"
        local = f"{digest}.{ext}"
        pending_assets[abs_url] = local
        img["src"] = "/img/" + local
        img["loading"] = "lazy"
        # 原网页宽高属性保留（排版一致），不额外处理


def iter_chunk_elements(root) -> list:
    """统一的翻译块元素选择器（parser 与 translator 共用，保证顺序与数量一致）。"""
    out = []
    for el in root.find_all(BLOCK_TAGS):
        if el.find(BLOCK_TAGS):
            continue  # 只取最内层块
        if any(p.name in SKIP_TRANSLATE_TAGS for p in el.parents):
            continue
        if not el.decode_contents().strip():
            continue
        out.append(el)
    return out


def _extract_chunks(body: BeautifulSoup) -> list[dict]:
    """抽取最内层块级元素作为翻译块（含内联标签的 inner HTML）。"""
    chunks: list[dict] = []
    for el in iter_chunk_elements(body):
        inner = el.decode_contents().strip()
        text = el.get_text(" ", strip=True)
        chunks.append({
            "i": len(chunks),
            "tag": el.name,
            "html": inner,
            "text": text,
            "translate": needs_translation(text),
        })
    return chunks


def parse_page_html(name: str, raw_html: str, slug_by_name: dict[str, str], pending_assets: dict[str, str]) -> tuple[str, list[dict]]:
    """解析单页：返回 (净化片段 HTML, 翻译块清单)。"""
    soup = BeautifulSoup(raw_html, "lxml")
    body = soup.select_one("#body")
    if body is None:
        log.warning("%s：未找到 #body，整页作为正文", name)
        body = soup.body or soup
    # 评论救援必须在整文档层面做：部分页面的 pcomment 被原站渲染在 #body 之外
    # （如嵌于错位表格后，lxml 把评论推出 #body），仅处理 #body 会漏掉它们。
    _keep_pcomments(soup)
    _remove_chrome(body)
    _remove_rules_region(body)
    # 把 #body 之外的评论区移入 #body，确保进入片段（救援已在上面完成）。
    for pc in list(soup.find_all("div", class_="pcomment")):
        if pc.find_parent(id="body") is None:
            body.append(pc)
    _rewrite_links(body, slug_by_name)
    _rewrite_images(body, pending_assets)
    _fix_missing_char_icons(soup, body)
    chunks = _extract_chunks(body)
    fragment = body.decode_contents()
    return fragment, chunks


def _parsed_paths(entry: dict) -> tuple[str, str]:
    slug = entry["slug"]
    return f"{slug}.html", f"{slug}.chunks.json"


def _parse_one(args: tuple) -> tuple:
    """单页解析（可在独立进程运行，无共享可变状态）。

    返回 (name, ok, err, frag_rel, chunks_rel, fragment, chunks, index_entry, pending_delta)。
    """
    name, raw_path, e, slug_by_name = args
    local_pending: dict[str, str] = {}
    try:
        raw_text = raw_path.read_text(encoding="utf-8", errors="replace")
        fragment, chunks = parse_page_html(name, raw_text, slug_by_name, local_pending)
    except Exception as err:  # noqa: BLE001 - 单页失败不阻塞全局
        return (name, False, str(err), None, None, None, None, None, None)
    frag_rel, chunks_rel = _parsed_paths(e)
    index_entry = {
        "name": name,
        "slug": e["slug"],
        "category": e.get("category"),
        "mode": e.get("mode"),
        "rarity": e.get("rarity"),
        "fragment": frag_rel,
        "chunks": chunks_rel,
        "chunk_count": len(chunks),
        "translate_count": sum(1 for c in chunks if c["translate"]),
    }
    return (name, True, None, frag_rel, chunks_rel, fragment, chunks, index_entry, local_pending)


def parse_all(pages: list[str] | None = None, force: bool = False) -> None:
    """解析全部快照 → data/parsed/ja/ 片段与文本块；更新 parsed 索引。"""
    config.ensure_dirs()
    entries = load_registry()
    if pages:
        wanted = set(pages)
        entries = [e for e in entries if e["name"] in wanted]
    slug_by_name = {e["name"]: e["slug"] for e in load_registry()}
    # 246 个正文子页面（装备/讨伐/世界观/主线）已建镜像，链接应指向本站而非原 wiki。
    # subpage_name_slug.json: {日文页名: {slug, subgroup}}，合并进 slug_by_name 让
    # _rewrite_links 自动把原 wiki 查看链接改写为站内 internal-link。
    _subpage_map = config.ROOT / "tools" / "subpage_name_slug.json"
    if _subpage_map.exists():
        for _nm, _info in json.loads(_subpage_map.read_text(encoding="utf-8")).items():
            _sl = _info.get("slug") if isinstance(_info, dict) else _info
            if _sl and _nm not in slug_by_name:
                slug_by_name[_nm] = _sl
    manifest = Manifest()
    pending_assets: dict[str, str] = {}
    if (config.DATA_DIR / "pending_assets.json").exists():
        pending_assets = json.loads((config.DATA_DIR / "pending_assets.json").read_text(encoding="utf-8"))

    index_path = config.DATA_DIR / "parsed" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}

    # 断点续解析：筛出需要处理的页（跳过不存在/已解析且未变更者），并预建目录防并发竞态
    targets = []
    skipped = 0
    for e in entries:
        name = e["name"]
        raw_path = config.RAW_DIR / page_filename(name)
        if not raw_path.exists():
            continue
        m = manifest.page(name)
        frag_rel, _ = _parsed_paths(e)
        frag_path = config.PARSED_JA_DIR / frag_rel
        if frag_path.exists() and not force and m and m.get("parsed_sha256") == m.get("sha256"):
            skipped += 1
            continue
        targets.append((name, raw_path, e, slug_by_name))
        frag_path.parent.mkdir(parents=True, exist_ok=True)

    ok = failed = 0
    workers = max(1, round((os.cpu_count() or 4) * 0.8))  # 留约 20% CPU 不占满
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for name, ok_flag, err, frag_rel, chunks_rel, fragment, chunks, index_entry, local_pending in ex.map(_parse_one, targets):
            if not ok_flag:
                failed += 1
                log.error("解析失败 %s：%s", name, err)
                continue
            frag_path = config.PARSED_JA_DIR / frag_rel
            frag_path.write_text(fragment, encoding="utf-8")
            chunks_path = config.PARSED_JA_DIR / chunks_rel
            chunks_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=1), encoding="utf-8")
            index[name] = index_entry
            pending_assets.update(local_pending)
            m = manifest.page(name)
            if m:
                m["parsed_sha256"] = m.get("sha256")
                manifest.data["pages"][name] = m
            ok += 1
            if ok % 50 == 0:
                log.info("已解析 %d 页…", ok)
    (config.DATA_DIR / "pending_assets.json").write_text(
        json.dumps(pending_assets, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    manifest.save()
    log.info("解析完成：成功 %d，跳过 %d，失败 %d；待下载图片 %d（进程池 workers=%d）", ok, skipped, failed, len(pending_assets), workers)
