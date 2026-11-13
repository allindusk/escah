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
