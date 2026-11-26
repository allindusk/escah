# -*- coding: utf-8 -*-
"""表格子页「同源」：同一张 `テーブル/xxx` 的多个宿主页只保留一份数据与一份译文。

原站机制（这正是源 WIKI 的做法）：
  `#table(テーブル/SSR, …)` 插件把**子页**里存的表格渲染进**多个宿主页** ——
    · `SSR` / `SR` / `R` / `NPC` 页（数据页）
    · `キャラクター一覧` 聚合页（把上面四张表拼成一页）
  子页只有一份实际数据，所以源站天然「改一处、处处同步」。

镜像站此前的做法（有 bug）：
  每个宿主页各自抓一份 raw、各自 parse、各自 i18n build →
  同一张表在库里存在 2 份 HTML 副本 + 2 份译文，两边会漂移
  （译文维护还要 characters.json / list-npc.json 各改一次）。

本模块把「同一 テーブル 子页的多个宿主页」认成同源组：
  ① 解析层 `sync_parsed()`：组内选**最完整**的表当权威，整表覆盖其它宿主页的
     `data/parsed/ja/<slug>.html`，并给每张表打 `data-tbl-id="テーブル/xxx"`；
     —— 于是 `chara.py`（実装日）、`sitegen`（角色顺序）读到的永远是最新数据。
  ② i18n 层：聚合页（`AGGREGATORS`）build 时把同源表整块挖掉、留
     `<div class="escah-embed-tbl" data-embed="テーブル/xxx">` 占位；
     渲染期再由 `render_table()` 把 provider 页渲染出的**同一张表**塞回去。
     —— 译文只有 provider 页（list-ssr 等）那一份，改一处两处同步。

不纳入的组：宿主全是角色详情页（`characters/*`）的「テーブル/キャラ/別衣装_XXX」等
（那是角色页内部同一张形态一览表，影响面 400+ 页，另行评估）。
"""
from __future__ import annotations

import re
import urllib.parse

from . import config
from .logutil import get_logger

log = get_logger()

# 聚合页：其表格整块来自 provider 页（数据 + 译文都不自己维护）
AGGREGATORS: "frozenset[str]" = frozenset({"characters"})
CHAR_SLUG_PREFIX = "characters/"

_TABLE_RE = re.compile(r"<table\b([^>]*)>(.*?)</table>", re.S | re.I)
_PAGE_PARAM_RE = re.compile(r"page=([A-Za-z0-9%._~:%+\-]+)")
_TR_RE = re.compile(r"<tr\b", re.I)
_CELL_RE = re.compile(r"<t[hd]\b", re.I)
_ID_RE = re.compile(r'\sid="([^"]*)"')
_TBL_ID_ATTR = "data-tbl-id"

_groups_cache: "dict[str, list[str]] | None" = None
_slug_cache: "dict[str, str] | None" = None


# ------------------------------------------------------------------ 基础信息 --


def _slug_by_name() -> "dict[str, str]":
    global _slug_cache
    if _slug_cache is None:
        from .registry import load_registry

        _slug_cache = {e["name"]: e["slug"] for e in load_registry()}
    return _slug_cache


def groups() -> "dict[str, list[str]]":
    """{テーブル子页: [宿主页名, …]}，只保留需要同源的组（≥2 宿主、非角色详情页内部）。"""
    global _groups_cache
    if _groups_cache is not None:
        return _groups_cache
    from . import deps

    slugs = _slug_by_name()
    out: "dict[str, list[str]]" = {}
    for tid, names in deps.scan_hosts().items():
        # 2026-11-25：deps 的键已扩展到「被 #table() 内嵌的普通内容页」（如 装備リスト），
        # 同源表格机制只认 `テーブル/xxx` 编号表 —— 内容页表不参与合并，否则会去找一个
        # 不存在的 `テーブル/装備リスト`，白白报警告。
        if not tid.startswith("テーブル/"):
            continue
        if len(names) < 2:
            continue
        page_slugs = [slugs.get(n, "") for n in names]
        if all(s.startswith(CHAR_SLUG_PREFIX) for s in page_slugs):
            continue  # 角色详情页内部的形态表：另有评估，不在此处动
        out[tid] = list(names)
    _groups_cache = out
    return out


def provider_name(tid: str) -> "str | None":
    """该表的权威宿主页名。

    规则（2026-11-13）：① 排除聚合页（它的表格本来就是拼来的）；
    ② 其余成员中取**行数最多**者（wiki 表格只会增行，最多通常即最新）；
    ③ 并列/无 parsed 产物时按 registry 顺序取第一个。
    """
    names = groups().get(tid) or []
    if not names:
        return None
    slugs = _slug_by_name()
    cands = [n for n in names if slugs.get(n) not in AGGREGATORS] or list(names)
    best, best_rows = cands[0], -1
    for n in cands:
        rows = _rows_in_parsed(n, tid)
        if rows > best_rows:
            best, best_rows = n, rows
    return best


def provider_slug(tid: str) -> "str | None":
    n = provider_name(tid)
    return _slug_by_name().get(n) if n else None


def embed_targets() -> "set[str]":
    """需要把同源表**挖空、改由 provider 页供给**的页 slug（各组里非权威成员）。

    2026-11-26 扩展（用户要求「≥2 宿主的都处理」）：
      此前只挖 `AGGREGATORS`（characters）一页，于是 `raid` / `raid-buff-debuff`
      那 3 张「3 宿主」表仍各存一份 HTML + 一份译文（重复约 786 条），改一处要改三处。
      现在任何同源组里只要不是该表的权威 provider，一律挖空 —— 数据与译文都只留
      provider 页那一份。

    安全性：
      · provider 自己永不挖（否则 `inject_embeds` 取不到表，页面会缺表）；
      · 组内找不到可用 provider 时整组不挖（宁可保留副本，也不生成空占位）；
      · 一页可同时是「A 表的 provider + B 表的成员」，挖空只针对它是成员的 tid。
    """
    slugs = _slug_by_name()
    out: "set[str]" = set()
    for tid, names in groups().items():
        prov_slug = slugs.get(provider_name(tid) or "")
        if not prov_slug:
            continue
        for n in names:
            s = slugs.get(n)
            if s and s != prov_slug:
                out.add(s)
    return out


def should_embed(slug: str, tid: str) -> bool:
    """该页的这张表是否应挖空、改由 provider 供给（逐表判定，页级判据不够用）。

    为什么必须逐表（2026-11-26 实测）：一页里可能同时有
      · 属于多宿主组、且本页是非权威成员的表 → 该挖；
      · 来自单宿主来源页的表（如 raid-buff-debuff 的 10 张专属表）→ **不能挖**，
        因为 `groups()` 不含它，`provider_slug()` 返回 None，挖了就没有任何页面能供给
        （inject 时被替换成空串，表直接消失）。
    首版按页判据把 raid-buff-debuff 的 25 张表全挖了，正是这个坑。
    """
    names = groups().get(tid) or []
    if len(names) < 2:
        return False
    slugs = _slug_by_name()
    prov = provider_name(tid)
    if not prov:
        return False
    prov_slug = slugs.get(prov)
    return bool(prov_slug) and slug != prov_slug and slug in {slugs.get(n) for n in names}


def aggregator_deps() -> "dict[str, list[str]]":
    """{聚合页 slug: [provider slug, …]} —— 变更检测/重建联动用。"""
    slugs = _slug_by_name()
    out: "dict[str, list[str]]" = {}
    for tid, names in groups().items():
        prov = provider_name(tid)
        if not prov:
            continue
        for n in names:
            s = slugs.get(n)
            if s in AGGREGATORS and s != slugs.get(prov):
                out.setdefault(s, []).append(slugs.get(prov, ""))
    return {k: [p for p in v if p] for k, v in out.items()}


# ---------------------------------------------------------------- 表定位解析 --


class _Table:
    __slots__ = ("start", "end", "attrs", "body", "tid", "el_id", "nrows", "ncols")

    def __init__(self, start: int, end: int, attrs: str, body: str):
        self.start = start
        self.end = end
        self.attrs = attrs
        self.body = body
        self.tid = _table_id(attrs + body)
        m = _ID_RE.search(attrs)
        self.el_id = m.group(1) if m else ""
        self.nrows = len(_TR_RE.findall(body)) + 1
        row1 = re.search(r"<tr\b[^>]*>(.*?)</tr>", body, re.S | re.I)
        self.ncols = len(_CELL_RE.findall(row1.group(1) if row1 else body)) or 1

    @property
    def html(self) -> str:
        return f"<table{self.attrs}>{self.body}</table>"

    @property
    def fingerprint(self) -> str:
        """忽略 `from=` / `id=` 的内容指纹（判断两页的同源表是否真的一致）。"""
        s = re.sub(r'from=[^&"]*', "from=", self.html)
        s = re.sub(r'\sid="[^"]*"', "", s)
        return s


def _table_id(text: str) -> "str | None":
    for m in _PAGE_PARAM_RE.finditer(text):
        name = urllib.parse.unquote(m.group(1))
        if name.startswith("テーブル/"):
            return name
    return None


def _scan(text: str) -> "list[_Table]":
    return [_Table(m.start(), m.end(), m.group(1), m.group(2))
            for m in _TABLE_RE.finditer(text)]


def _add_tbl_id(attrs: str, tid: str) -> str:
    if _TBL_ID_ATTR in attrs:
        return attrs
    return f' {_TBL_ID_ATTR}="{tid}"' + attrs


def _ensure_tbl_id(table_html: str, tid: str) -> str:
    """整表 HTML 上保证带 data-tbl-id（已在则不动）。"""
    if _TBL_ID_ATTR in table_html[:400]:
        return table_html
    return re.sub(r"<table\b", f'<table {_TBL_ID_ATTR}="{tid}"', table_html, count=1)


_rows_cache: "dict[tuple[str, str], int]" = {}


def _rows_in_parsed(page_name: str, tid: str) -> int:
    """该宿主页 parsed 产物里这张表的行数（无产物 / 找不到 → -1）。"""
    key = (page_name, tid)
    if key in _rows_cache:
        return _rows_cache[key]
    slug = _slug_by_name().get(page_name)
    rows = -1
    path = config.PARSED_JA_DIR / f"{slug}.html" if slug else None
    if path is not None and path.exists():
        try:
            for t in _scan(path.read_text(encoding="utf-8")):
                if t.tid == tid:
                    rows = t.nrows
                    break
        except OSError:
            pass
    _rows_cache[key] = rows
    return rows


# ---------------------------------------------------- 来源页 → 宿主页锚点 ----
# 正文里常把表格子页写成外链（如 `?テーブル/レイド/呪縛対策…`）。这些表本站其实
# 已经镜像进某个宿主页，链接应改指站内锚点，而不是把读者送出站。锚点取
# 「该表之前最近一个带 id 的标题」，即它所在的小节。
_h_heading_cache: "dict[str, dict[str, str]]" = {}
_parsed_text_cache: "dict[str, dict[str, str]]" = {}
_raw_head_cache: "dict[str, dict[str, str]]" = {}
_link_cache: "dict[str, list[tuple[str, str]]] | None" = None
_H_TAG_RE = re.compile(r"^h[1-6]$")


def _table_headings(slug: str) -> "dict[str, str]":
    """该页 parsed 里 {data-tbl-id: 表前最近标题的 id}（进程内缓存）。"""
    if slug in _h_heading_cache:
        return _h_heading_cache[slug]
    out: "dict[str, str]" = {}
    path = config.PARSED_JA_DIR / f"{slug}.html"
    if path.exists():
        try:
            from lxml import html as lxml_html

            doc = lxml_html.fromstring(path.read_text(encoding="utf-8", errors="replace"))
            last = ""
            for el in doc.iter():
                if not isinstance(el.tag, str):
                    continue
                tag = el.tag.lower()
                if _H_TAG_RE.match(tag):
                    if el.get("id"):
                        last = el.get("id")
                elif tag == "table":
                    tid = el.get(_TBL_ID_ATTR)
                    if tid and tid not in out:
                        out[tid] = last
        except Exception as e:  # noqa: BLE001 单页解析失败不影响出站
            log.warning("[table-sync] 解析 %s 失败：%s", slug, e)
    _h_heading_cache[slug] = out
    return out


def _norm_heading(text: str) -> str:
    return re.sub(r"\s+", "", text or "").replace("†", "")


def _parsed_heading_ids(slug: str) -> "dict[str, str]":
    """{归一化标题文本: id}（parsed 侧，把 raw 里的标题文本映射成锚点 id）。"""
    if slug in _parsed_text_cache:
        return _parsed_text_cache[slug]
    out: "dict[str, str]" = {}
    path = config.PARSED_JA_DIR / f"{slug}.html"
    if path.exists():
        try:
            from lxml import html as lxml_html

            doc = lxml_html.fromstring(path.read_text(encoding="utf-8", errors="replace"))
            for el in doc.iter():
                if isinstance(el.tag, str) and _H_TAG_RE.match(el.tag.lower()):
                    hid = el.get("id")
                    key = _norm_heading(el.text_content())
                    if hid and key and key not in out:
                        out[key] = hid
        except Exception as e:  # noqa: BLE001
            log.warning("[table-sync] 解析 %s 标题失败：%s", slug, e)
    _parsed_text_cache[slug] = out
    return out


def _raw_heading_text(slug: str, tid: str) -> "str | None":
    """raw 里该表之前最近标题的**文本**（parsed 已剥离 `page=` 链接，只能从 raw 认）。

    返回 "" 表示表在第一个标题之前（页首）；None 表示 raw 里找不到这张表。
    """
    from .snapshot import page_filename

    if slug not in _raw_head_cache:
        mapping: "dict[str, str]" = {}
        name = next((n for n, s in _slug_by_name().items() if s == slug), None)
        path = config.RAW_DIR / page_filename(name) if name else None
        if path is not None and path.exists():
            try:
                from lxml import html as lxml_html

                doc = lxml_html.fromstring(path.read_bytes().decode("utf-8", "ignore"))
                last = ""
                for el in doc.iter():
                    if not isinstance(el.tag, str):
                        continue
                    tag = el.tag.lower()
                    if _H_TAG_RE.match(tag):
                        last = el.text_content()
                        continue
                    if tag == "table":
                        blob = lxml_html.tostring(el, encoding="unicode")
                        for m in _PAGE_PARAM_RE.finditer(blob):
                            who = urllib.parse.unquote(m.group(1))
                            if who.startswith("テーブル/") and who not in mapping:
                                mapping[who] = _norm_heading(last)
            except Exception as e:  # noqa: BLE001
                log.warning("[table-sync] 解析 raw %s 失败：%s", slug, e)
        _raw_head_cache[slug] = mapping
    return _raw_head_cache[slug].get(tid)


def link_targets() -> "dict[str, list[tuple[str, str]]]":
    """{来源页名: [(宿主页 slug, 锚点 id), …]} —— 正文外链改站内锚点用。

    provider 排最前（内容权威），其余按 registry 顺序；调用方通常优先取
    「链接所在页自己」这个宿主（留在本页），没有才退到 provider。
    某来源页的所有宿主都没打 `data-tbl-id` 时不出现在结果里（调用方保持外链）。
    """
    global _link_cache
    if _link_cache is not None:
        return _link_cache
    from . import deps

    slugs = _slug_by_name()
    out: "dict[str, list[tuple[str, str]]]" = {}
    for tid, names in deps.scan_hosts().items():
        if not tid.startswith("テーブル/"):
            continue
        prov = slugs.get(provider_name(tid) or "")
        cands: "list[tuple[str, str]]" = []
        for n in names:
            slug = slugs.get(n)
            if not slug:
                continue
            hid = _table_headings(slug).get(tid)      # 解析期已打 data-tbl-id 的页
            if hid is None:                           # 没打标 → 用 raw 的标题文本回查
                htext = _raw_heading_text(slug, tid)
                if htext is None:
                    continue
                hid = _parsed_heading_ids(slug).get(htext, "")
            cands.append((slug, hid))
        if not cands:
            continue
        cands.sort(key=lambda x: x[0] != prov)   # provider 优先，其余保持原序
        out[tid] = cands
    _link_cache = out
    return out


def reset_link_cache() -> None:
    global _link_cache
    _link_cache = None
    _h_heading_cache.clear()
    _parsed_text_cache.clear()
    _raw_head_cache.clear()


# ------------------------------------------------------------------ 解析层 --


def sync_parsed(dry_run: bool = False) -> dict:
    """把同源组的表格统一到权威表，并给每张表打 `data-tbl-id`。

    返回报告：{"groups": {tid: {provider: 页名, members: [...]}},
                "patched": {slug: [tid…]}, "skipped": [(slug, tid, 原因)…]}
    """
    rep: dict = {"groups": {}, "patched": {}, "skipped": []}
    _rows_cache.clear()
    grp = groups()
    if not grp:
        return rep
    slugs = _slug_by_name()
    name_by_slug = {v: k for k, v in slugs.items()}

    # 收集所有成员页的表
    # ⚠️ 只扫组成员：parsed 里的表格**已剥离 `page=` 编辑链接**，非成员宿主页的表
    # 无法反查 tid（2026-11-26 实测：扩大扫描范围也打不上标，纯属白耗解析）。
    # 正文里指向「单宿主来源页」的链接改走 `link_targets()` 的 raw 回查路径。
    texts: "dict[str, str]" = {}
    scanned: "dict[str, list[_Table]]" = {}
    for names in grp.values():
        for n in names:
            slug = slugs.get(n)
            if not slug or slug in scanned:
                continue
            path = config.PARSED_JA_DIR / f"{slug}.html"
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            texts[slug] = text
            scanned[slug] = _scan(text)

    for tid, names in grp.items():
        prov_name = provider_name(tid)
        prov_slug = slugs.get(prov_name or "")
        members = [slugs.get(n, "") for n in names]
        rep["groups"][tid] = {"provider": prov_name, "members": names}
        if not prov_slug or prov_slug not in scanned:
            rep["skipped"].append((prov_slug or "?", tid, "权威页无 parsed 产物"))
            continue
        auth = next((t for t in scanned[prov_slug] if t.tid == tid), None)
        if auth is None:
            rep["skipped"].append((prov_slug, tid, "权威页找不到该表"))
            continue
        for slug in members:
            if slug == prov_slug or slug not in scanned:
                continue
            tgt = next((t for t in scanned[slug] if t.tid == tid), None)
            if tgt is None:
                rep["skipped"].append((slug, tid, "目标页找不到该表"))
                continue
            if tgt.ncols != auth.ncols:
                rep["skipped"].append(
                    (slug, tid, f"列数不同（{tgt.ncols}≠{auth.ncols}），视为该页自行裁剪，不覆盖"))
                continue
            if auth.nrows < tgt.nrows:
                rep["skipped"].append(
                    (slug, tid, f"权威表行数更少（{auth.nrows}<{tgt.nrows}），不用较少数据覆盖"))
                continue
            if tgt.fingerprint == auth.fingerprint:
                continue  # 内容已一致（仅 from/id 不同）
            rep["patched"].setdefault(slug, []).append(tid)

    if dry_run:
        return rep

    # 逐页重写：先打标，再按 start 降序替换为目标表
    for slug, tbs in scanned.items():
        text = texts[slug]
        repl: "list[tuple[int, int, str]]" = []
        patched_tids = set(rep["patched"].get(slug, []))
        for t in tbs:
            if not t.tid:
                continue
            new_attrs = _add_tbl_id(t.attrs, t.tid)
            if t.tid in patched_tids:
                prov_slug = slugs.get(provider_name(t.tid) or "")
                auth = next((x for x in scanned.get(prov_slug, []) if x.tid == t.tid), None)
                if auth is None:
                    continue
                html = _remap(auth.html, from_page=name_by_slug.get(prov_slug, ""),
                              to_page=name_by_slug.get(slug, ""), el_id=t.el_id)
                repl.append((t.start, t.end, _ensure_tbl_id(html, t.tid)))
            elif new_attrs != t.attrs:
                repl.append((t.start, t.end, f"<table{new_attrs}>{t.body}</table>"))
        if not repl:
            continue
        for start, end, new in sorted(repl, key=lambda r: -r[0]):
            text = text[:start] + new + text[end:]
        if not dry_run:
            (config.PARSED_JA_DIR / f"{slug}.html").write_text(text, encoding="utf-8")
    return rep


def _remap(table_html: str, from_page: str, to_page: str, el_id: str) -> str:
    """权威表 → 目标页语境：改 `from=` 参数与表 id（避免同页重复 id）。"""
    if from_page and to_page and from_page != to_page:
        to_enc = urllib.parse.quote(to_page, safe="")

        def _from(m: "re.Match") -> str:
            val = m.group(1)
            return "from=" + to_enc if urllib.parse.unquote(val) == from_page else m.group(0)

        table_html = re.sub(r'from=([^&"\s]*)', _from, table_html)
    if el_id:
        table_html = re.sub(r'(<table\b[^>]*?)\sid="[^"]*"',
                            lambda m: f'{m.group(1)} id="{el_id}"', table_html, count=1)
    return table_html


# ------------------------------------------------------------------- 渲染层 --


_EMBED_RE = re.compile(r'<div class="escah-embed-tbl" data-embed="([^"]*)"></div>\s*')
_guard: "set[str]" = set()


def render_table(slug: str, tid: str, locale: str) -> "str | None":
    """渲染 provider 页并从结果里抽出指定同源表的 HTML。"""
    from . import i18n

    if slug in _guard:
        log.warning("[table-sync] 检测到自引用/循环嵌入：%s / %s", slug, tid)
        return None
    _guard.add(slug)
    try:
        page = i18n.render_locale(slug, locale)
    finally:
        _guard.discard(slug)
    if not page:
        return None
    pat = re.compile(r'<table\b[^>]*%s="%s"[^>]*>.*?</table>' % (_TBL_ID_ATTR, re.escape(tid)),
                     re.S | re.I)
    m = pat.search(page)
    if not m:
        log.error("[table-sync] %s 的 %s 渲染结果里找不到该表（locale=%s）", slug, tid, locale)
        return None
    return m.group(0)


def inject_embeds(html: str, slug: str, locale: str) -> str:
    """把 `<div class="escah-embed-tbl" data-embed="…">` 换成 provider 页的同名表。"""
    if "escah-embed-tbl" not in html:
        return html
    seq = [0]

    def _one(m: "re.Match") -> str:
        tid = m.group(1)
        prov = provider_slug(tid)
        if not prov or prov == slug:
            log.error("[table-sync] %s 的嵌入表 %s 无可用 provider", slug, tid)
            return ""
        out = render_table(prov, tid, locale)
        if not out:
            return ""
        seq[0] += 1
        # 同页多表嵌入 → 重排 id，避免重复 id（js/锚点行为可预期）
        return re.sub(r'(<table\b[^>]*?)\sid="[^"]*"',
                      lambda mm: f'{mm.group(1)} id="sortabletable{seq[0]}"', out, count=1)

    return _EMBED_RE.sub(_one, html)


def reset_cache() -> None:
    global _groups_cache, _slug_cache
    _groups_cache = None
    _slug_cache = None
