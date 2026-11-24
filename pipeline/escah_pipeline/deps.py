# -*- coding: utf-8 -*-
"""内容来源页（`テーブル/xxx` 或任意内容页）与**宿主页**的绑定索引。

为什么需要它（2026-10-19 实测，用户反馈「list-ssr/sr/r 没跟着 characters 一起更新」）：
  · 原站大量列表页（`SSR` / `SR` / `R` / `キャラクター一覧` / `サポーター` / `装備一覧` …）
    的表格数据存在子页 `テーブル/xxx` 里，由 `#table(テーブル/xxx, …)` 插件**渲染进宿主页正文**；
  · 于是「子页被编辑」只改子页的时间戳，**宿主页自己的「最終更新日時」根本不动** ——
    时间戳比对（`sync-stale` / `sync-recent`）对这类页**永久判 unchanged** ✗；
  · `テーブル/*` 本身是排除页（不进镜像、不进侧栏），也没有它自己的快照可比。
  实测：`list-ssr` 的 raw 停在 2026-07-22，而 `テーブル/SSR` 2026-10-07 就改过；
  `SSR` 页的「最終更新日時」从 2022-10-06 起就没再变过。

对策：把宿主页认出来，对这些页**忽略时间戳、直接比正文 sha256**。
`updater._probe_and_save` 本来就把正文下载下来了，多算一次哈希 = 零额外请求。

索引**从 data/raw 现算**（宿主页正文里带着 `cmd=table_edit&…&page=テーブル/xxx` 的编辑链接），
随抓取自动更新，不需要人工维护一张依赖表。

2026-11-25 扩展：`#table()` 的来源**不一定是 `テーブル/*` 子页**，也可以是**普通内容页**。
实测 `装備一覧` 的表来自 `装備リスト`（编辑链接 `page=装備リスト`），于是：
  · 改的是 `装備リスト`，`装備一覧` 自己的时间戳仍是 2026-09-22 → 判 unchanged；
  · 而 `装備一覧` 又不在旧版 `table_dep_hosts()` 里（它只认 `テーブル/` 前缀）→ 永远不重探；
  · 结果 raw 冻在 2026-09-27，`装備リスト` 里新增的装备行在 `装備一覧` 上永远显示不出来。
因此判据放宽为「**任意** `page=X`（X ≠ 自己）」：X 是内容来源，宿主页跟着重探。
"""
from __future__ import annotations

import json
import re
import urllib.parse

from . import config

# `page=` 参数值（PukiWiki 的表单/编辑链接都是 URL 编码或裸页名，字符集足够窄）
_PAGE_PARAM_RE = re.compile(r"page=([A-Za-z0-9%._~:%+\-]+)")
# 只认「表格行的编辑链接」：`cmd=table_edit&…&page=X`。
# 用 `<a href="…">` 整体匹配而不是全页扫 `page=`，避免把附件/其它插件的 page= 误当依赖。
_TABLE_EDIT_ANCHOR_RE = re.compile(r'<a\s[^>]*href="([^"]*cmd=table_edit[^"]*)"')

_index: "dict[str, list[str]] | None" = None


def _file_to_name() -> "dict[str, str]":
    """raw 文件名（去扩展名）→ 页面名。长页名会以哈希命名落盘，必须靠 manifest 反查。"""
    try:
        man = json.loads((config.DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out: "dict[str, str]" = {}
    for name, e in (man.get("pages") or {}).items():
        f = (e or {}).get("file") or ""
        if f.startswith("raw/") and f.endswith(".html"):
            out[f[4:-5]] = name
    return out


def scan_hosts() -> "dict[str, list[str]]":
    """扫描 data/raw → {内容来源页名: [宿主页名, …]}（进程内缓存一次）。

    来源页两类：
      ① `テーブル/xxx` 表格子页 —— 宿主页正文里带 `cmd=edit&page=テーブル/…`
         或 `cmd=table_edit&…&page=テーブル/…`（前者是页面底部「別衣装」等表的编辑链接）；
      ② **普通内容页**被 `#table()` 内嵌 —— 只能从 `cmd=table_edit&…&page=X` 认（如
         `装備一覧` ← `装備リスト`）。宿主页自己给自己打的编辑链接不算依赖。
    """
    global _index
    if _index is not None:
        return _index
    hosts: "dict[str, list[str]]" = {}
    raw = config.RAW_DIR
    if not raw.exists():
        _index = hosts
        return hosts
    name_by_stem = _file_to_name()
    for path in raw.glob("*.html"):
        try:
            text = path.read_bytes().decode("utf-8", "ignore")
        except OSError:
            continue
        # 便宜的预筛：绝大多数页面没有任何表格编辑链接
        if "cmd=table_edit" not in text and "cmd=edit" not in text:
            continue
        host = name_by_stem.get(path.stem) or urllib.parse.unquote(path.stem)

        def _add(owner: str) -> None:
            if not owner or owner == host:
                return            # 本页自己表格行上的编辑链接 ≠ 依赖
            lst = hosts.setdefault(owner, [])
            if host not in lst:
                lst.append(host)

        # ① 沿用旧判据：全页任意 `page=テーブル/…`（cmd=edit 与 table_edit 都算）
        for m in _PAGE_PARAM_RE.finditer(text):
            owner = urllib.parse.unquote(m.group(1))
            if owner.startswith("テーブル/"):
                _add(owner)
        # ② 新增：任意 `cmd=table_edit&…&page=X`（X 可以是普通内容页）
        for m in _TABLE_EDIT_ANCHOR_RE.finditer(text):
            pm = _PAGE_PARAM_RE.search(m.group(1))
            if pm is None:
                continue
            owner = urllib.parse.unquote(pm.group(1))
            if not owner.startswith("テーブル/"):
                _add(owner)
    _index = hosts
    return hosts


def table_dep_hosts() -> "set[str]":
    """所有「内容绑定在别的页」的宿主页名集合。

    这些页的「最終更新日時」不可信 —— 变更检测必须走 sha256。
    """
    return {h for v in scan_hosts().values() for h in v}


def owner_pages() -> "set[str]":
    """被别的页内嵌内容的来源页名集合（命中更新履历时用来连带宿主页）。"""
    return set(scan_hosts().keys())


def hosts_of(table_name: str) -> "list[str]":
    """指定来源页的宿主页名列表（`テーブル/xxx` 或普通内容页都适用）。"""
    return list(scan_hosts().get(table_name, []))


def reset_cache() -> None:
    """丢弃缓存（测试/长驻进程重扫 raw 时用）。"""
    global _index
    _index = None
