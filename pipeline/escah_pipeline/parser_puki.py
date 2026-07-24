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

from bs4 import BeautifulSoup, Comment

from . import config
from .logutil import get_logger
from .registry import href_to_page_name, load_registry
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


def safe_id(name: str) -> str:
    """页面名 → 文件安全 ID（保留日文可读性）。"""
    return name.translate(_INVALID_FILENAME)


def needs_translation(text: str) -> bool:
    return bool(_JA_RE.search(text))


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
    _remove_chrome(body)
    _rewrite_links(body, slug_by_name)
    _rewrite_images(body, pending_assets)
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
    workers = max(1, min(os.cpu_count() or 4, 16))
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
