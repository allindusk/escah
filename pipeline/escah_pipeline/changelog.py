# -*- coding: utf-8 -*-
"""原站「更新履歴ページ」**周存档** —— CI 每周跑一次 → 落盘入库 → 本地增量更新直接读它。

为什么要有这个（2026-10-19 用户决定）：
  原先 `sync-cron.yml` 是"CI 自动镜像+解析+建站"，用户改为**全部本地更新并推送**；
  但本地要知道"这周原站动了哪些页"，要么全量爬取比对（675 次请求），要么有个存档。
  原站「更新履歴ページ」（PukiWiki `#recent`）**1 次请求**就能拿到最新 100 条
  「日期 + 页面名」，按它生成存档即可 —— 本地拉 `data/upstream/latest.json` 就知道
  哪些页是**新增**、哪些页**已更新**、哪些**不用动**。

产物（全部入库）：
  data/upstream/latest.json          最新一份（本地更新时读这个）
  data/upstream/weekly/<ISO周>.json  按周存档，留历史
  data/upstream/weekly/<ISO周>.md    人类可读摘要（CI 日志/直接翻看）
  data/upstream/history.ndjson       累积流水（每行 = 一周一条目），可查"某页哪周动过"

条目 status 语义：
  new        原站有、registry 未登记 → 需本地 `discover` 登记 + 抓取（新增页）
  update     已登记，且原站日期新于本地快照 → 需重抓
  unchanged  已登记，本地快照已覆盖该日期 → 不用动
  excluded   命中 registry 排除规则（`EXCLUDE_PATTERNS`）→ 不**单独**建页：
             MenuBar/SideBar/ヘッダ/フッタ 等 wiki 系统·导航页、練習/雛形 模板页，
             以及 `コメント/`·掲示板 等独立页。
             ⚠️ 注意区分：本项目的**评论区是页面正文的一部分**（每个页面底部都有），
             随所属页面一起镜像；这里说的是 PukiWiki 的**独立评论页**，不是评论区。
  frozen     `no_auto_update`（如反爬的公式ヘルプ）：站点照常渲染，不自动更新

用法：
  python -m escah_pipeline.cli changelog fetch   # 抓取并落盘
  python -m escah_pipeline.cli changelog show    # 打印最新存档摘要
  python -m escah_pipeline.cli changelog names   # 只打印「需要处理」的页面名（一行一个）
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
from pathlib import Path

from . import config
from . import recent as recent_mod
from .fetcher import PoliteFetcher, page_url
from .registry import _is_excluded, is_auto_update, load_registry
from .snapshot import Manifest
from .updater import _is_namespaced

ARCHIVE_DIR = config.DATA_DIR / "upstream"
WEEKLY_DIR = ARCHIVE_DIR / "weekly"
LATEST_FILE = ARCHIVE_DIR / "latest.json"
HISTORY_FILE = ARCHIVE_DIR / "history.ndjson"

# 需要本地"做点什么"的状态
ACTIONABLE = ("new", "update")


def _iso_week(day: "dt.date | None" = None) -> str:
    d = day or dt.date.today()
    return d.strftime("%G-W%V")


# 原站反爬验证页（`is_challenge_page` 的同款特征，此处再列一遍是为了在**本模块内**
# 独立判定，避免依赖 fetcher 的调用时序）：
#   · 日文旧版「少々お待ちください…」
#   · 2026-10-19 起的 Cloudflare 无感 JS 挑战「One moment, please...」
# 两者都是 HTTP 200 + 5 秒后 JS reload，不执行 JS 就永远拿不到正文。
_CHALLENGE_RE = re.compile(
    r"少々お待ちください|One moment, please|window\.location\.reload"
    r"|request is being verified"
)


def _looks_like_content(text: str) -> bool:
    return bool(text) and not _CHALLENGE_RE.search(text) and (
        "recent_list" in text or 'id="body"' in text or "<body" in text
    )


def _http_get_text(url: str, cookie: "str | None" = None) -> str:
    headers = {"Cookie": cookie} if cookie else None
    with PoliteFetcher() as f:
        return f.get(url, headers=headers).text


def _browser_get_text(url: str, timeout: float = 45.0, cookie: "str | None" = None) -> str:
    """用真实浏览器取 HTML（能执行 JS，Cloudflare 的无感挑战通常会在 reload 后放行）。

    需要 playwright + chromium（可选依赖；未安装时抛 ImportError，由调用方降级处理）。
    """
    from playwright.sync_api import sync_playwright  # noqa: PLC0415 可选依赖

    with sync_playwright() as p:
        try:
            b = p.chromium.launch(headless=True, args=["--no-sandbox"])
        except Exception:
            b = p.chromium.launch(headless=True, channel="msedge", args=["--no-sandbox"])
        ctx = b.new_context(locale="ja-JP", timezone_id="Asia/Tokyo")
        if cookie:
            from urllib.parse import urlparse  # noqa: PLC0415

            host = urlparse(url).netloc
            for part in cookie.split(";"):
                if "=" not in part:
                    continue
                k, v = part.split("=", 1)
                ctx.add_cookies([{"name": k.strip(), "value": v.strip(),
                                  "domain": host, "path": "/"}])
        pg = ctx.new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            html = pg.content()
            if _looks_like_content(html):
                b.close()
                return html
            time.sleep(2)
        html = pg.content()
        b.close()
    return html


def fetch_history(
    attempts: int = 3,
    wait: float = 6.0,
    html: "str | None" = None,
    cookie: "str | None" = None,
    browser: bool = False,
):
    """抓取并解析更新履歴；命中反爬验证页就退避重试 / 回退真实浏览器。

    三条通道（按成本递增）：
      ① `html`   —— 完全离线：解析给定 HTML（浏览器另存/其它途径拿到的页面）
      ② HTTP     —— 1 次请求；带 `cookie` 时注入（可传浏览器里的 cf_clearance）
      ③ `browser`—— 真实浏览器执行 JS，等 Cloudflare 无感挑战放行后取 HTML
    """
    if html is not None:
        return recent_mod.parse_recent_history(html)
    url = page_url(recent_mod.RECENT_HISTORY_PAGE)
    last = ""
    for i in range(attempts):
        last = _http_get_text(url, cookie=cookie)
        if _looks_like_content(last):
            return recent_mod.parse_recent_history(last)
        if i < attempts - 1:
            time.sleep(wait * (i + 1))
    if browser:
        last = _browser_get_text(url, cookie=cookie)
        if _looks_like_content(last):
            return recent_mod.parse_recent_history(last)
    raise RuntimeError(
        f"更新履歴页 {attempts} 次 HTTP 均返回验证页"
        f"{'（浏览器回退也失败）' if browser else ''}，末次 {len(last)} 字节"
    )


def build(html: "str | None" = None, cookie: "str | None" = None,
          browser: bool = False) -> dict:
    """抓取原站更新履歴 → 与本地 registry/manifest 对照 → 返回存档 dict（不落盘）。"""
    hist = fetch_history(html=html, cookie=cookie, browser=browser)
    registry = load_registry()
    by_name = {e["name"]: e for e in registry}
    manifest = Manifest()

    items: "list[dict]" = []
    for e in hist.entries:
        ent = by_name.get(e.name)
        slug = None
        local = None
        if ent is None:
            status = "excluded" if (_is_excluded(e.name) or _is_namespaced(e.name)) else "new"
        else:
            slug = ent.get("slug") or None
            m = manifest.page(e.name) or {}
            local = (m.get("wiki_last_modified") or "")[:10] or None
            if not is_auto_update(ent):
                status = "frozen"
            elif e.date and (local is None or local < e.date):
                status = "update"
            else:
                status = "unchanged"
        items.append({
            "name": e.name,
            "url": page_url(e.name),
            "date": e.date,
            "within_days": e.within_days,
            "section": e.section,
            "slug": slug,
            "status": status,
            "local_updated": local,
            "needs_update": status in ACTIONABLE,
        })

    counts: "dict[str, int]" = {}
    for it in items:
        counts[it["status"]] = counts.get(it["status"], 0) + 1

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "iso_week": _iso_week(),
        "source": page_url(recent_mod.RECENT_HISTORY_PAGE),
        "window": [hist.oldest_date, hist.newest_date],
        "truncated": hist.truncated,
        "counts": counts,
        "items": items,
    }


def save(snap: dict) -> "dict[str, str]":
    """落盘：latest.json + weekly/<周>.json + weekly/<周>.md + 追加 history.ndjson。"""
    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
    week = snap["iso_week"]
    weekly = WEEKLY_DIR / f"{week}.json"
    weekly_md = WEEKLY_DIR / f"{week}.md"

    def _dump(p: Path) -> None:
        p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")

    _dump(weekly)
    _dump(LATEST_FILE)

    # 累积流水：一周一条目一行（覆盖同周重跑 → 先滤掉本周旧行）
    lines = []
    if HISTORY_FILE.exists():
        for ln in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                if json.loads(ln).get("week") == week:
                    continue
            except Exception:
                pass
            lines.append(ln)
    for it in snap["items"]:
        lines.append(json.dumps({"week": week, **it}, ensure_ascii=False))
    HISTORY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    weekly_md.write_text(_to_markdown(snap), encoding="utf-8")
    return {"weekly": str(weekly), "latest": str(LATEST_FILE),
            "md": str(weekly_md), "history": str(HISTORY_FILE)}


def _to_markdown(snap: dict) -> str:
    c = snap["counts"]
    out = [
        f"# 原站更新履歴存档 {snap['iso_week']}",
        "",
        f"- 生成时间：{snap['generated_at']}",
        f"- 来源：{snap['source']}",
        f"- 窗口：{snap['window'][0]} ~ {snap['window'][1]}（truncated={snap['truncated']}）",
        f"- 条目：新增 {c.get('new', 0)} / 需更新 {c.get('update', 0)} / "
        f"无变化 {c.get('unchanged', 0)} / 排除 {c.get('excluded', 0)} / 冻结 {c.get('frozen', 0)}",
        "",
        "## 需要处理（新增 + 已更新）",
        "",
        "| 页面 | 状态 | 原站日期 | 本地快照 | slug |",
        "|---|---|---|---|---|",
    ]
    for it in snap["items"]:
        if it["status"] not in ACTIONABLE:
            continue
        out.append(f"| {it['name']} | {it['status']} | {it['date'] or '-'} | "
                   f"{it['local_updated'] or '-'} | {it['slug'] or '-'} |")
    out += ["", "<details><summary>全部条目</summary>", "",
            "| 页面 | 状态 | 原站日期 | 本地快照 |", "|---|---|---|---|"]
    for it in snap["items"]:
        out.append(f"| {it['name']} | {it['status']} | {it['date'] or '-'} | {it['local_updated'] or '-'} |")
    out += ["", "</details>", ""]
    return "\n".join(out)


def latest() -> "dict | None":
    if not LATEST_FILE.exists():
        return None
    return json.loads(LATEST_FILE.read_text(encoding="utf-8"))


def actionable_names(snap: "dict | None" = None, statuses=ACTIONABLE) -> "list[str]":
    """存档里需要处理的页面名（statuses=None 表示全部条目的页面名）。"""
    snap = snap or latest()
    if not snap:
        return []
    if statuses is None:
        return [it["name"] for it in snap["items"]]
    return [it["name"] for it in snap["items"] if it["status"] in statuses]
