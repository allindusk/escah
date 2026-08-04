"""提取「需要加超链接的跨页/外链句子」到 glossary/link_terms.todo.yaml。

口径（2026-08-04 收紧，避免噪声）：
- 只处理**外链**（http:// / https://）的 <a> 与**跨页 .html 跳转**的 <a>。
  站内跳转（internal-link / 页内 #锚点 / 面包屑 / 目录 div.contents）已由渲染管线自动
  加 target=_blank 处理，无需配置，排除。
- 排除噪声：cmd=table_edit、File not found、div.contents 目录容器内的链接。
- 主内容：只取非 div.contents 容器内的 <a>（正文），避免把目录页内锚点算进来。

分流逻辑（「已在词表翻好的直接进真值，不进 todo」）：
- 对每条 linkable <a>，取其链接文本 ja、该页实际译文 zh、href。
- 跨 ≥2 页重复的 (zh, href) → 归并到全局 "*" 条目（只精修一次即全站生效）。
- 单页且已翻译（zh ≠ ja）→ 直接归并真值（单页条目）。
- 单页且未翻译（zh == ja，纯英文/数字/URL 等无日文）→ 直接固化真值。
- 单页且未翻译（含日文假名/汉字）→ 进 todo（reason=untranslated）。

「译名不统一导致精准配置失效」检测（2026-08-04 新增，用户明确诉求）：
- link_terms.yaml 是「词级精确子串匹配」唯一真值：配置 links[].zh 必须与该页实际
  译文里的链接词**逐字一致**才能命中。
- 若某链接词 ja 已在 link_terms 配了 zh（slug 级或全局 *），但**该页实际译文 zh
  不在配置的 zh 集合内**（且 zh ≠ ja，即已翻译但译名和配置不一致，如配置「常见问题」
  实际译「常见问题汇总」/「FAQ」）→ 精准匹配必然失效，进 todo（reason=mismatch）。
- 这类条目附 expected_zh（link_terms 期望的统一译名），方便用户把各页 ja/zh 键值
  统一后，重跑本脚本即可清 todo、进真值。
- 用户拍板：ja→zh 译名不统一的页面不直接进真值（会污染配置、无法精准覆盖），
  必须人工统一译名后再由脚本接管。

输出：
- glossary/link_terms.todo.yaml : 待处理的条目（slug 分组，含整句 ja/zh 上下文 + reason）
- 直接增量合并进 glossary/link_terms.yaml : 词表已覆盖/译名一致的 linkable 条目（去重）

依赖：lxml、yaml；复用 i18n 的 _norm 归一化（NFC+折叠空白+去 PukiWiki 标题尾部 †）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from lxml import html as lxml_html

ROOT = Path(__file__).resolve().parent.parent
I18N_DIR = ROOT / "data" / "parsed" / "i18n"
GLOSSARY_DIR = ROOT / "glossary"
TODO_FILE = GLOSSARY_DIR / "link_terms.todo.yaml"
TRUTH_FILE = GLOSSARY_DIR / "link_terms.yaml"

# 归一化（与 i18n._norm 一致）
_TITLE_TAIL_RE = re.compile(r"[†*]\s*$")


def _norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"\s+", "", s)
    s = _TITLE_TAIL_RE.sub("", s)
    return s


def _norm_ns(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"\s+", "", s)
    return s


# ---------------- 词表加载（判断「链接文本已在词表翻好」）----------------
def _load_glossary_map() -> dict[str, str]:
    """返回 names/terms/skills/high_freq 四份词表的「归一化 ja -> 中文 zh」映射。

    用途（2026-08-04 用户定，自动化核心）：若某链接词的原文 ja 已在这四份词表
    里有中文翻译（ja != zh），则渲染期会被 _name_override / high_freq 覆盖成该
    中文词，链接 <a> 壳保留、精准命中必然成功——这类词无需进 todo 待精修，
    直接在分流时按 (ja, zh=该中文词, href) 格式归并 link_terms.yaml 真值即可。

    合并优先级（后者覆盖前者，越具体的专名越优先）：
        high_freq < terms < skills < names
    中日同形条目（ja == zh）不纳入（它们不是「翻译」，链接直接用原文即可）。
    """
    merged: dict[str, str] = {}
    # 顺序：先低优先 high_freq/terms/skills，最后 names（专名权威最高）
    files = [
        ("high_freq.yaml", "high_freq"),
        ("terms.yaml", None),       # terms 顶层即各子段（page_titles/char_sections/...），整文件递归展开
        ("skills.yaml", "skills"),
        ("names.yaml", "names"),
    ]

    def _ingest(section) -> None:
        """把一段（可能嵌套 dict）里的 ja:zh 扁平映射并入 merged。"""
        if not isinstance(section, dict):
            return
        for k, v in section.items():
            if isinstance(v, dict):
                # 嵌套段（如 terms 的各子段），递归展开
                _ingest(v)
                continue
            if not (isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip()):
                continue
            if _norm_ns(k) == _norm_ns(v):
                continue  # 中日同形，不算翻译，跳过
            merged[_norm_ns(k)] = v

    for fname, top in files:
        p = GLOSSARY_DIR / fname
        if not p.exists():
            continue
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception as e:
            print(f"[warn] 词表 {fname} 加载失败：{e}", file=sys.stderr)
            continue
        if not isinstance(data, dict):
            continue
        if top is None:
            _ingest(data)
        else:
            _ingest(data.get(top, {}))
    return merged


# ---------------- 模板解析 ----------------
_KEY_RE = re.compile(r"\{\{key(\d+)\}\}")
_EXCLUDE_CONTAINER_CLASSES = {"contents"}  # 目录：全是页内 #锚点，排除
_JA_RE = re.compile(r"[ぁ-んァ-ヶ一-龯]")  # 含日文假名/汉字 → 需 LLM 精修


def _needs_review(text: str) -> bool:
    """未翻译文本（zh==ja）是否需要 LLM 精修。

    纯英文/数字/URL/标点（无日文）→ 原文 <a> 已正确，直接固化真值，不需审。
    含日文假名/汉字 → 可能需要定中文词，进 todo。
    """
    return bool(_JA_RE.search(text or ""))


def _strip_nav_links(html: str) -> str:
    """去掉导航/页脚链接（与渲染管线一致），只保留正文链接。

    这里主要排除 div.contents（目录）；面包屑/页内锚点由 is_linkable 直接过滤。
    """
    try:
        frag = lxml_html.fragment_fromstring(html, create_parent="div")
    except Exception:
        return html
    for cls in _EXCLUDE_CONTAINER_CLASSES:
        for el in frag.xpath(f".//div[contains(concat(' ', normalize-space(@class), ' '), ' {cls} ')]"):
            el.getparent().remove(el)
    out = lxml_html.tostring(frag, method="html", encoding="unicode")
    if out.startswith("<div>") and out.rstrip().endswith("</div>"):
        out = out[len("<div>"):-len("</div>")]
    return out


# 同站域名（本站镜像源站，站内跳转，渲染时已自带 <a>，无需 link_terms 配置，排除）
_SAME_SITE_HOSTS = {"escalationheroines.wikiru.jp"}


def is_linkable(href: str, slug: str = "") -> bool:
    """抽取「需要 link_terms 配置的链接」：外链 + 跨页 .html 跳转（跨页复用）。

    排除：
    - 空 / 纯页内 #锚点（目录、回顶）
    - 指向「当前页自身」的 .html#锚点（同页章节跳转，如 annihilation.html#k0a52a12）
    - cmd=table_edit（编辑按钮）
    - File not found（图片缺失噪声）
    - 同站 wikiru 跳转（源站站内导航，渲染管线已处理）
    - div.contents 目录（由 _strip_nav_links 剥离）
    跨页 .html 跳转（如 faq.html / limit-break.html）纳入：跨多页重复的中文词
    会归并进全局 '*' 条目，只精修一次即对全站生效。
    """
    if not href:
        return False
    if href.startswith("#"):
        return False
    low = href.lower()
    if "cmd=table_edit" in low:
        return False
    if "file not found" in low or "filenotfound" in low:
        return False
    from urllib.parse import urlparse
    host = (urlparse(href).netloc or "").lower()
    if host in _SAME_SITE_HOSTS:
        return False
    # 外链
    if href.startswith("http://") or href.startswith("https://"):
        return True
    # 站内相对跳转（.html，可能带 #锚点）
    if ".html" in low:
        # 去掉锚点后的页面名
        page = low.split("#", 1)[0]
        if page in ("", f"{slug.lower()}.html"):
            # 指向当前页自身的章节锚点（如 annihilation.html#xxx）→ 排除
            return False
        return True
    return False


def _load_json(slug: str) -> dict:
    p = I18N_DIR / f"{slug}.json"
    if not p.exists():
        return {}
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _load_truth_config() -> tuple[dict, dict]:
    """读 link_terms.yaml，返回 (slug_config, global_config)。

    slug_config: slug -> { ja_norm: set(zh) }    单页条目
    global_config: { ja_norm: set(zh) }           全局 "*" 条目
    用于在「译名不统一」检测里判断：某链接词 ja 已配置哪些 zh，
    以及该页实际译文 zh 是否落在配置集合内（否则精准匹配失效）。
    """
    slug_config: dict[str, dict[str, set]] = {}
    global_config: dict[str, set] = {}
    data = _read_truth(TRUTH_FILE)
    for e in data:
        sl = e.get("slug")
        links = e.get("links") or []
        for ln in links:
            ja = (ln.get("ja") or "").strip()
            zh = (ln.get("zh") or "").strip()
            if not ja or not zh:
                continue
            jn = _norm_ns(ja)
            if sl == "*":
                global_config.setdefault(jn, set()).add(zh)
            else:
                slug_config.setdefault(sl, {}).setdefault(jn, set()).add(zh)
    return slug_config, global_config


def _restore_text(text_with_keys: str, jd: dict) -> tuple[str, str]:
    """把含 {{keyN}} 占位符的纯文本，替换为 (ja 整句, zh 整句)。

    zh 缺译时回退 ja。返回 (ja_ctx, zh_ctx) 均为纯文本（无 HTML 标签）。
    """
    def repl(m, locale):
        key = f"key{m.group(1)}"
        ent = jd.get(key) or {}
        if locale == "zh":
            return ent.get("zh") or ent.get("ja", "") or ""
        return ent.get("ja", "") or ""
    ja_ctx = _KEY_RE.sub(lambda m: repl(m, "ja"), text_with_keys)
    zh_ctx = _KEY_RE.sub(lambda m: repl(m, "zh"), text_with_keys)
    return ja_ctx.strip(), zh_ctx.strip()


def q(s: str) -> str:
    """安全转义为 YAML 双引号标量（处理内部双引号/冒号等）。"""
    return yaml.safe_dump(s, allow_unicode=True, default_style='"').strip()


# 整句上下文缓存：(slug, zh, href) -> (ja_ctx, zh_ctx, link_ja)
_CTX: dict[tuple, tuple] = {}


def _page_zh_text(slug: str, jd: dict) -> str:
    """汇总该页中文全文文本（节点级 zh 还原 + 所有 blk.zh），用于 link_terms 命中校验。

    关键修复（2026-08-04）：原脚本只靠模板 <a> 内文本还原，对「节点级 key 全空、
    靠 blk 整句译文」的块完全失效（link_zh 回退成日文，与 link_terms 日文 zh 一致，
    误判已处理）。这里用 blk.zh 真实中文整句参与校验。
    """
    parts: list[str] = []
    for key, ent in jd.items():
        if not (isinstance(key, str) and key.startswith("key")):
            continue
        zh = (ent.get("zh") or "").strip()
        if zh:
            parts.append(zh)
    for bk, ent in jd.get("blocks", {}).items():
        if isinstance(ent, dict):
            bzh = (ent.get("zh") or "").strip()
            if bzh:
                parts.append(bzh)
    return "\n".join(parts)


_KATAKANA_RE = re.compile(r"[ァ-ヶ]")


def _zh_is_japanese(term_zh: str) -> bool:
    """link_terms 的 zh 字段是否仍是日文（含片假名/平假名即判为日文，需改中文）。"""
    return bool(_KATAKANA_RE.search(term_zh)) or bool(re.search(r"[ぁ-ん]", term_zh))


# 不翻译、不进待精修的页面：原画索引(artists) 与 声优一览(voice-actors)。
# 这两个页面的带链接文本块按项目规则保持原文（日文），不参与链接词精修。
SKIP_SLUGS = {"artists", "voice-actors"}


def main() -> None:
    glossary_map = _load_glossary_map()
    slug_config, global_config = _load_truth_config()
    # 收集所有 linkable 链接：slug -> [(link_ja, link_zh, href), ...]
    all_by_slug: dict[str, list[tuple[str, str, str]]] = {}
    # 每页中文全文（节点级 zh + blk.zh），用于命中校验
    page_zh: dict[str, str] = {}

    tpl_files = sorted(I18N_DIR.glob("*.template.html"))
    print(f"[info] 扫描 {len(tpl_files)} 个模板文件")
    skipped = 0
    for tpl in tpl_files:
        slug = tpl.name[: -len(".template.html")]
        if slug in SKIP_SLUGS:
            continue
        jd = _load_json(slug)
        if not jd:
            skipped += 1
            continue
        page_zh[slug] = _page_zh_text(slug, jd)
        html = tpl.read_text(encoding="utf-8")
        html = _strip_nav_links(html)
        try:
            frag = lxml_html.fragment_fromstring(html, create_parent="div")
        except Exception:
            skipped += 1
            continue

        # 收集所有 linkable <a>
        for a in frag.xpath(".//a"):
            href = (a.get("href") or "").strip()
            if not is_linkable(href, slug):
                continue
            link_ja = (a.text_content() or "").strip()
            if not link_ja:
                continue
            # 整句 ja / zh 上下文（含此 <a> 的最小句子容器）
            sent_el = a
            for _ in range(6):
                if sent_el.getparent() is None:
                    break
                p = sent_el.getparent()
                txt_nodes = [c for c in p.iter() if c.text and c.text.strip()]
                if len(txt_nodes) >= 1:
                    sent_el = p
                    break
                sent_el = p
            ja_ctx, zh_ctx = _restore_text(sent_el.text_content(), jd)
            link_zh = _restore_text(a.text_content(), jd)[1] or link_ja
            # 若链接词 ja 已在 glossary 四份词表里有中文翻译，则用该中文词作为
            # 有效 zh（渲染期会被覆盖成此中文，链接壳保留、精准命中必然成功）。
            # 这类词直接归真值，不进 todo。
            gzh = glossary_map.get(_norm_ns(link_ja), link_zh)

            all_by_slug.setdefault(slug, []).append((link_ja, link_zh, gzh, href))
            # 同时记录整句上下文，供 todo 使用（按 (slug,link_ja,link_zh,href) 索引）
            _ctx_key = (slug, link_ja, link_zh, href)
            _CTX[_ctx_key] = (ja_ctx, zh_ctx, link_ja, link_zh)

    # ---- 分流 ----
    # 统计每个 (有效zh, href) 出现的 slug 集合（跨页重复判定）。有效 zh 优先取
    # glossary 已翻译的中文词（gzh），否则取该页实际译文 link_zh。
    pair_slugs: dict[tuple[str, str], set[str]] = {}
    # (slug, link_ja, link_zh, href) -> (ja_ctx, zh_ctx) 上下文
    for sl, pairs in all_by_slug.items():
        for ja, zh, gzh, href in pairs:
            pair_slugs.setdefault((gzh, href), set()).add(sl)

    global_pairs: set[tuple[str, str]] = set()   # 跨 ≥2 页 → 全局 *
    single_pairs: dict[str, list[tuple[str, str]]] = {}
    # todo 条目：带 reason。 (slug, link_ja, link_zh, href) -> reason
    todo_map: dict[tuple[str, str, str, str], str] = {}

    for (zh, href), sls in pair_slugs.items():
        if len(sls) >= 2:
            global_pairs.add((zh, href))
            continue
        sl = next(iter(sls))
        # 取该 (slug,zh,href) 下任一条记录的 ja 与翻译标志（用 gzh 判定）
        recs = [r for r in all_by_slug[sl] if r[2] == zh and r[3] == href]
        link_ja = recs[0][0] if recs else zh
        translated = _norm_ns(zh) != _norm_ns(link_ja) and bool(zh)
        if translated:
            # 已翻译：先判「译名不统一导致精准配置失效」
            reason = _mismatch_reason(sl, link_ja, zh, slug_config, global_config)
            if reason:
                todo_map[(sl, link_ja, zh, href)] = reason
            else:
                single_pairs.setdefault(sl, []).append((zh, href))
        else:
            # 未翻译（zh==ja）：纯英文/数字/URL 等无需 LLM 精修的，直接固化真值；
            # 仅含日文（假名/汉字）的未译文本才进 todo 待 LLM 处理。
            if _needs_review(zh):
                todo_map[(sl, link_ja, zh, href)] = "untranslated"
            else:
                single_pairs.setdefault(sl, []).append((zh, href))

    # ---- 全局命中校验（治本）：link_terms 的 zh 必须在对应页中文全文里能命中 ----
    # 对每条已配置链接，检测 links[].zh 是否真能在「该页中文全文（含 blk.zh）」里
    # 精确子串命中。命中不了且 zh 仍是日文（含片假名/平假名）→ reason=zh_japanese，
    # 这些条目在中文译文里永远包不上链接，需把 zh 改成实际中文词。
    # 全局 '*' 条目：任一页中文全文命中即视为有效（跨页复用）。
    # 特例（2026-08-04 用户定）：若 term_ja 在 glossary 四份词表里已有中文翻译，
    # 则直接把该条 zh 改成 glossary 的中文词（渲染期会被覆盖成此词、链接壳保留、
    # 精准命中必然成功），就地修正真值、不进 todo。
    truth_data = _read_truth(TRUTH_FILE)
    truth_modified = False
    for e in truth_data:
        sl = e.get("slug")
        if sl in SKIP_SLUGS:
            continue
        links = e.get("links") or []
        for ln in links:
            term_zh = (ln.get("zh") or "").strip()
            term_ja = (ln.get("ja") or "").strip()
            href = (ln.get("href") or "").strip()
            if not term_zh or not href:
                continue
            if sl == "*":
                hits = any(_norm_ns(term_zh) in _norm_ns(page_zh[s])
                           for s in page_zh)
            else:
                hits = _norm_ns(term_zh) in _norm_ns(page_zh.get(sl, ""))
            if hits:
                continue
            # 未命中：若 zh 仍是日文（非中日同形）→ 必然失效
            if _zh_is_japanese(term_zh):
                # 优先查 glossary 是否已有该 ja 的中文翻译：有则就地修正 zh，不进 todo
                gzh = glossary_map.get(_norm_ns(term_ja))
                if gzh:
                    ln["zh"] = gzh
                    truth_modified = True
                    continue
                reason = "zh_japanese"
                # 注意：zh_japanese 类的中文译文里本就没有该词（zh 是日文），
                # 故不塞整页全文作上下文（否则 ja 短、zh 一长串，且撑爆 todo）。
                # 优先复用前面 <a> 收集阶段已写的整句上下文（若有）；
                # 没有则 ja_ctx/zh_ctx 留空，todo 里只给链接词本身。
                if (sl, term_ja, term_zh, href) not in _CTX:
                    _CTX[(sl, term_ja, term_zh, href)] = (term_ja, "", term_ja, term_zh)
                todo_map[(sl, term_ja, term_zh, href)] = reason

    # 若 truth 有就地修正（glossary 已翻译的词），先回写再合并避免被读回覆盖
    if truth_modified:
        TRUTH_FILE.write_text(_dump_yaml(truth_data), encoding="utf-8")

    _merge_into_truth(TRUTH_FILE, single_pairs, global_pairs)

    # ---- 写 todo（附整句上下文 + reason + expected_zh）----
    todo_entries = []
    for (sl, link_ja, zh, href), reason in todo_map.items():
        ja_ctx, zh_ctx, _, _ = _CTX.get(
            (sl, link_ja, zh, href), ("", "", link_ja, zh))
        expected = _expected_zh(sl, link_ja, slug_config, global_config)
        todo_entries.append({
            "slug": sl,
            "reason": reason,
            "ja_full": ja_ctx,
            "zh_full": zh_ctx,
            "link": {
                "ja": link_ja,
                "zh": zh,                       # 该页实际译文（与配置不一致）
                "expected_zh": expected,        # link_terms 期望的统一译名（可能为空）
                "href": href,
            },
        })
    _write_todo(TODO_FILE, todo_entries)

    n_truth = len(global_pairs) + sum(len(v) for v in single_pairs.values())
    n_mismatch = sum(1 for r in todo_map.values() if r == "mismatch")
    n_untrans = sum(1 for r in todo_map.values() if r == "untranslated")
    n_zhja = sum(1 for r in todo_map.values() if r == "zh_japanese")
    print(f"[done] 直接归并真值: {n_truth} 条（全局* {len(global_pairs)} / 单页 {n_truth - len(global_pairs)}）")
    print(f"[done] 待处理 todo: {len(todo_entries)} 条 → {TODO_FILE.name} "
          f"（译名不一致 {n_mismatch} / 未翻译 {n_untrans} / zh为日文 {n_zhja}）")


def _mismatch_reason(slug: str, link_ja: str, link_zh: str,
                     slug_config: dict, global_config: dict) -> str | None:
    """译名不统一检测：该链接词 ja 已在 link_terms 配置，但该页实际译文 zh
    不在配置 zh 集合内（且已翻译）→ 返回 'mismatch'，否则 None。

    含义：link_terms 用精确子串匹配 links[].zh 命中译文；若实际译文与配置 zh
    逐字不一致，精准链接必然失效，需人工统一译名后再由脚本接管。
    """
    jn = _norm_ns(link_ja)
    if not link_zh or link_zh == link_ja:
        return None  # 未翻译不算 mismatch
    cfg = global_config.get(jn)
    sc = slug_config.get(slug, {}).get(jn)
    if cfg is None and sc is None:
        return None  # 该 ja 未在任何配置里 → 不算失效
    allowed = (cfg or set()) | (sc or set())
    if link_zh in allowed:
        return None  # 实际译文与某配置 zh 一致 → 能精准命中，不进 todo
    return "mismatch"


def _expected_zh(slug: str, link_ja: str,
                 slug_config: dict, global_config: dict) -> str:
    """该链接词 ja 在 link_terms 里配置的统一译名（取首个），供 todo 提示用。"""
    jn = _norm_ns(link_ja)
    sc = slug_config.get(slug, {}).get(jn)
    if sc:
        return next(iter(sc))
    gc = global_config.get(jn)
    if gc:
        return next(iter(gc))
    return ""


def _read_truth(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        return [e for e in data if isinstance(e, dict)]
    except Exception as e:
        print(f"[warn] 读取真值文件失败：{e}", file=sys.stderr)
        return []


def _merge_into_truth(path: Path, single_pairs: dict[str, list], global_pairs: set) -> None:
    """增量合并：保留既有条目，追加新的单页/全局条目（按 (slug,zh,href) 去重）。"""
    existing = _read_truth(path)
    seen: set[tuple] = set()
    for e in existing:
        sl = e.get("slug")
        for ln in (e.get("links") or []):
            seen.add((sl, (ln.get("zh") or "").strip(), (ln.get("href") or "").strip()))
    # 重组：existing 保留 + 新增（按 slug 聚合，避免同 slug 拆成多条）
    out = list(existing)
    # 先统计各 slug 下已有的 (zh,href)，用于去重
    for sl, pairs in single_pairs.items():
        agg: list[dict] = []
        for zh, href in pairs:
            if (sl, zh, href) in seen:
                continue
            seen.add((sl, zh, href))
            agg.append({"ja": zh, "zh": zh, "href": href})
        if agg:
            out.append({"slug": sl, "links": agg})
    if global_pairs:
        agg_g: list[dict] = []
        for zh, href in global_pairs:
            if ("*", zh, href) in seen:
                continue
            seen.add(("*", zh, href))
            agg_g.append({"ja": zh, "zh": zh, "href": href})
        if agg_g:
            out.append({"slug": "*", "links": agg_g})
    path.write_text(_dump_yaml(out), encoding="utf-8")


def _write_todo(path: Path, entries: list[dict]) -> None:
    if not entries:
        if path.exists():
            path.unlink()
        return
    lines: list[str] = []
    lines.append("# link_terms 待办：由 tools/_extract_link_todo.py 生成")
    lines.append("# 每条含整句 ja/zh 上下文（校对用）+ link（ja/zh/expected_zh/href）。")
    lines.append("# reason:")
    lines.append("#   mismatch    = 该链接词 ja 已在 link_terms 配了 zh，但本页译文 zh 与配置不一致")
    lines.append("#                 （译名不统一，精准子串匹配必然失效）。请先把本页 ja/zh 键值统一成")
    lines.append("#                 expected_zh（或反之更新 link_terms 配置），再重跑本脚本即清 todo。")
    lines.append("#   untranslated = 链接词尚未翻译（含日文），需先翻再配置。")
    lines.append("#   zh_japanese  = link_terms 该条 zh 仍是日文原文（含片假名/平假名），")
    lines.append("#                 在中文译文（含 blk 整句译文）里精确匹配必然失败，链接丢失。")
    lines.append("#                 请把 links[].zh 改成中文译文里实际出现的词（如 ステータス→属性），")
    lines.append("#                 再跑 _merge_link_terms.py 合并。注意：中日同形词（強化/中毒等）不在此列。")
    lines.append("# 处理完跑 tools/_merge_link_terms.py 合并进 link_terms.yaml 并删除本文件。")
    lines.append("")
    for e in entries:
        ln = e["link"]
        lines.append(f"- slug: {e['slug']}")
        lines.append(f"  reason: {e.get('reason', '')}")
        # 整句上下文用块标量（|），直接写纯文本，不套 q()（q() 会加引号破坏块）
        lines.append("  ja: |")
        for bl in (e.get("ja_full") or "").split("\n"):
            lines.append(f"    {bl}")
        lines.append("  zh: |")
        for bl in (e.get("zh_full") or "").split("\n"):
            lines.append(f"    {bl}")
        lines.append("  link:")
        lines.append(f"    ja: {q(ln['ja'])}")
        lines.append(f"    zh: {q(ln['zh'])}")
        if ln.get("expected_zh"):
            lines.append(f"    expected_zh: {q(ln['expected_zh'])}")
        lines.append(f"    href: {q(ln['href'])}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _dump_yaml(entries: list[dict]) -> str:
    """手写 YAML（保持可读性，ja==zh 时省略 ja）。"""
    lines: list[str] = []
    lines.append("# 中文译文「指定词汇 → 超链接」配置（render-time 由 i18n._apply_config_links 应用）。")
    lines.append("#")
    lines.append("# 结构：每个条目 { slug, links:[{ja, zh, href}] }。")
    lines.append("# - slug 为页面 slug（如 annihilation）；slug: '*' 表示对所有页面生效（全局条目）。")
    lines.append("# - links[].zh 为要在中文译文里包裹成 <a> 的词（精确子串匹配，长词优先）。")
    lines.append("# - links[].ja 为原文词（仅 LLM 理解/审计用，不参与渲染匹配）。")
    lines.append("# - href：外链写完整 http(s)://；站内写 'faq.html' 由代码归一成 /zh/faq.html 并 target=_blank。")
    lines.append("#")
    lines.append("# 给大语言模型（LLM）的说明：")
    lines.append("# 1. 本文件是「词级精确链接包裹」的唯一真值。渲染管线不会自动加链接，必须在此配置。")
    lines.append("# 2. 给页面增译/更新译文后，运行 tools/_extract_link_todo.py 提取待配置句子 → 本文件 *.todo.yaml。")
    lines.append("# 3. 你（LLM）在对话里逐条处理 todo：把 links[].zh 设为目标中文词、href 设跳转地址。")
    lines.append("# 4. 跑 tools/_merge_link_terms.py 把 todo 合并进本文件（按 slug+zh 去重），并删除 todo。")
    lines.append("# 5. 同一个词跨多页出现时，优先用全局 '*' 条目，只精修一次即对全站生效。")
    lines.append("")
    for e in entries:
        sl = e.get("slug", "")
        links = e.get("links") or []
        if not links:
            continue
        lines.append(f"- slug: {q(sl)}")
        lines.append("  links:")
        for ln in links:
            ja = (ln.get("ja") or "").strip()
            zh = (ln.get("zh") or "").strip()
            href = (ln.get("href") or "").strip()
            lines.append(f"    - ja: {q(ja)}")
            lines.append(f"      zh: {q(zh)}")
            lines.append(f"      href: {q(href)}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
