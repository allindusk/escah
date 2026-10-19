# -*- coding: utf-8 -*-
"""表格子页（`テーブル/xxx`）与**宿主页**的绑定索引。

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
"""
from __future__ import annotations

import re
import urllib.parse

from . import config

# 编码形态：`page=%E3%83%86%E3%83%BC%E3%83%96%E3%83%AB%2FSSR`
_TBL_PREFIX_ENC = urllib.parse.quote("テーブル/", safe="")
# `page=` 参数值（PukiWiki 的表单/编辑链接都是 URL 编码或裸页名，字符集足够窄）
_PAGE_PARAM_RE = re.compile(r"page=([A-Za-z0-9%._~:%+\-]+)")

_index: "dict[str, list[str]] | None" = None


def scan_hosts() -> "dict[str, list[str]]":
    """扫描 data/raw → {テーブル子页名: [宿主页名, …]}（进程内缓存一次）。"""
    global _index
    if _index is not None:
        return _index
    hosts: "dict[str, list[str]]" = {}
    raw = config.RAW_DIR
    if not raw.exists():
        _index = hosts
        return hosts
    for path in raw.glob("*.html"):
        try:
            text = path.read_bytes().decode("utf-8", "ignore")
        except OSError:
            continue
        # 便宜的预筛：绝大多数页面根本不引用 テーブル 子页
        if _TBL_PREFIX_ENC not in text and "テーブル/" not in text:
            continue
        host = urllib.parse.unquote(path.stem)
        for m in _PAGE_PARAM_RE.finditer(text):
            tbl = urllib.parse.unquote(m.group(1))
            if not tbl.startswith("テーブル/"):
                continue
            lst = hosts.setdefault(tbl, [])
            if host not in lst:
                lst.append(host)
    _index = hosts
    return hosts


def table_dep_hosts() -> "set[str]":
    """所有「内容绑定在 テーブル 子页」的宿主页名集合。

    这些页的「最終更新日時」不可信 —— 变更检测必须走 sha256。
    """
    return {h for v in scan_hosts().values() for h in v}


def hosts_of(table_name: str) -> "list[str]":
    """指定 `テーブル/xxx` 的宿主页名列表。"""
    return list(scan_hosts().get(table_name, []))


def reset_cache() -> None:
    """丢弃缓存（测试/长驻进程重扫 raw 时用）。"""
    global _index
    _index = None
