# -*- coding: utf-8 -*-
"""原站「更新履歴ページ」解析 —— 变更检测的**廉价前置通道**。

为什么需要它（2026-09-27 评估）：
  现有两条检测通道都不理想：
    · `update`（RSS `?cmd=rss`）：只与 registry 里 `mode == watch` 的 49 页求交集，
      静态页/角色页的更新**根本不在覆盖范围内**；
    · `sync-stale`（全站并行比对 `最終更新日時`）：覆盖全 ✓，但要 **675 次请求**
      （实测 ~1 分钟，对原站是礼貌上限附近）。想每天跑就太重了。
  原站有个 PukiWiki 的 `#recent` 插件页面「更新履歴ページ」，**一次请求**就能拿到
  「最新 100 条 = 日期 + 页面名」的清单（实测单页 markup 稳定、按页面去重、严格倒序），
  正好用来把候选集从 675 页缩到几十页。

本模块只负责**解析**（纯函数，便于离线验证），网络与落盘在 `updater.sync_recent_pages`。

页面实际标记（2026-09-27 实测，URL `?更新履歴ページ`）：
  <h2 class="content_1_0">wikiページ更新履歴 †</h2>
  <h5>最新の100件</h5>
  <div>
    <h5>5分以内に更新</h5>
    <ul class="recent_list"><li><a href="?<enc>" title="コメント/… ">コメント/…</a></li></ul>
    <h5>2日以内に更新</h5>
    <ul class="recent_list"></ul><strong>2026-09-26</strong>
    <ul class="recent_list"><li><a ...>テーブル/…</a></li>…</ul>
  要点：
    · 相对分组（`n日以内に更新`）给出"多久以内"，分组内再用 `<strong>YYYY-MM-DD</strong>`
      给出**精确日期**；因此绝大多数条目都有确切日期，少数（今日刚改）只有相对范围。
    · 页面**按页面名去重**（同一页今天改 5 次也只出现一次）——对"是否要重抓"恰好够用。
    · 单区块硬上限 100 条（另有「最新の30件」区块，是其子集），超出需「もっとみる」。
      → 条目数触顶意味着窗口可能被截断，调用方必须据此升级为全量比对（见 updater）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import config
from .fetcher import PoliteFetcher, page_url
from .registry import href_to_page_name

# 原站页面名（PukiWiki 中文档名就是它，URL = SOURCE_BASE + "?" + quote(name)）
# 定义在 config 里（与其它"原站入口页"常量放一起，如 MENUBAR_PAGE / CHARLIST_PAGE）。
RECENT_HISTORY_PAGE = config.RECENT_HISTORY_PAGE

# `#recent` 插件的区块上限。「最新の100件」是本模块使用的区块。
RECENT_LIMIT = 100

_BUCKET_RE = re.compile(r"^(\d+)\s*(分|時間|日|週間|週)以内に更新$")
_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_SECTION_RE = re.compile(r"最新の\s*(\d+)\s*件")

# 相对分组 → 折算天数（用于判断"窗口是否够深"）
_UNIT_DAYS = {"分": 0, "時間": 0, "日": 1, "週間": 7, "週": 7}


@dataclass(frozen=True)
class RecentEntry:
    """一条更新记录（页面名 + 尽可能精确的日期）。"""

    name: str
    date: str | None          # 'YYYY-MM-DD'；仅相对分组给出时可为 None
    within_days: int | None   # 「n日以内に更新」折算天数；无分组信息则 None
    section: str              # '最新の100件' / '最新の30件' / ''


@dataclass
class RecentHistory:
    """解析结果 + 供调用方做 HA 决策的元信息。"""

    entries: list[RecentEntry] = field(default_factory=list)
    sections: dict[str, int] = field(default_factory=dict)   # 区块名 → 条目数
    truncated: bool = False      # 有条目数触及该区块上限（窗口可能被截断）

    @property
    def names(self) -> set[str]:
        return {e.name for e in self.entries}

    @property
    def oldest_date(self) -> str | None:
        """带日期的条目里最早的那天（用于判断窗口是否覆盖到上次同步）。"""
        dates = [e.date for e in self.entries if e.date]
        return min(dates) if dates else None

    @property
    def newest_date(self) -> str | None:
        dates = [e.date for e in self.entries if e.date]
        return max(dates) if dates else None


def parse_recent_history(html: str) -> RecentHistory:
    """解析「更新履歴ページ」HTML。**纯函数**：不联网、不落盘，便于离线核对。"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("div", id="body") or soup.body
    hist = RecentHistory()
    if body is None:
        return hist

    section = ""
    date: str | None = None
    within: int | None = None
    seen: set[str] = set()

    # 按文档顺序扫「分组标题 / 日期 / 条目列表」，用一个状态机串起来。
    # 只关心这四类节点：h2/h5（区块或相对分组标题）、strong（精确日期）、ul.recent_list。
    for el in body.find_all(["h2", "h5", "strong", "ul"]):
        if el.name in ("h2", "h5"):
            text = el.get_text(" ", strip=True)
            m_sec = _SECTION_RE.search(text)
            if m_sec:
                section = text
                date, within = None, None
                continue
            m_b = _BUCKET_RE.match(text)
            if m_b:
                within = int(m_b.group(1)) * _UNIT_DAYS.get(m_b.group(2), 0)
                date = None      # 进入新分组，清掉上一个分组的日期
                continue
            # 其它 h2/h5（页面标题 / 「更新履歴」等）不改变状态
            continue

        if el.name == "strong":
            text = el.get_text(" ", strip=True)
            m_d = _DATE_RE.match(text)
            if m_d:
                date = text
            continue

        # ul.recent_list：本组条目
        cls = el.get("class") or []
        if "recent_list" not in cls:
            continue
        for li in el.find_all("li"):
            a = li.find("a")
            if a is None:
                # 没有链接的条目（极少数）退化为取文本
                raw = li.get_text(" ", strip=True)
                name = raw or ""
            else:
                # title 属性最稳（实测形如 "コメント/雑談掲示板 "，带尾随空格）；
                # 退化时从 href 反解，复用 registry 的 PukiWiki 链接解析。
                name = (a.get("title") or "").strip() or (
                    href_to_page_name(a.get("href") or "") or ""
                ) or a.get_text(" ", strip=True)
            name = name.strip()
            if not name or name in seen:
                continue          # 按页面去重（保留最先出现 = 最新的一条）
            seen.add(name)
            hist.entries.append(
                RecentEntry(name=name, date=date, within_days=within, section=section)
            )

    for name, count in _count_sections(hist).items():
        hist.sections[name] = count
    hist.truncated = any(
        count >= limit for name, count, limit in _section_limits(hist)
    )
    return hist


def _count_sections(hist: RecentHistory) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in hist.entries:
        out[e.section] = out.get(e.section, 0) + 1
    return out


def _section_limits(hist: RecentHistory) -> "list[tuple[str, int, int]]":
    """[(区块名, 条目数, 该区块声明的上限)]，用于判断是否触顶。"""
    out: list[tuple[str, int, int]] = []
    for name, count in hist.sections.items():
        m = _SECTION_RE.search(name)
        limit = int(m.group(1)) if m else RECENT_LIMIT
        out.append((name, count, limit))
    return out


def fetch_recent_history(fetcher: "PoliteFetcher | None" = None) -> RecentHistory:
    """抓取并解析「更新履歴ページ」（走 PoliteFetcher：限速 + 退避重试）。

    只发 **1 个** 请求 —— 这正是本通道相对全量比对（675 次）的价值所在。
    """
    url = page_url(RECENT_HISTORY_PAGE)
    if fetcher is not None:
        return parse_recent_history(fetcher.get(url).text)
    with PoliteFetcher() as f:
        return parse_recent_history(f.get(url).text)


def _main() -> int:
    """自检：抓一次真实页面，打印解析结果概况（离线核对用）。

    用法：python -m escah_pipeline.recent [--limit 30]
    """
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows 控制台默认 GBK
    limit = 30
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    hist = fetch_recent_history()
    print(f"页面：{RECENT_HISTORY_PAGE}")
    print(f"解析条目：{len(hist.entries)} ｜ 区块：{hist.sections}")
    print(f"窗口：最旧 {hist.oldest_date} → 最新 {hist.newest_date}"
          f" ｜ 触顶截断：{hist.truncated}")
    no_date = [e for e in hist.entries if not e.date]
    print(f"无精确日期（仅相对分组）：{len(no_date)} 条")
    print(f"\n前 {limit} 条：")
    for e in hist.entries[:limit]:
        print(f"   {e.date or '(今)'}  within={e.within_days}  {e.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
