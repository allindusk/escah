# -*- coding: utf-8 -*-
"""原站「更新履歴ページ」**周存档** —— CI 每周跑一次 → 落盘入库 → 本地增量更新直接读它。

为什么要有这个（2026-10-19 用户决定）：
  原先有一条 CI 工作流做"CI 自动镜像+解析+建站"，用户改为**全部本地更新并推送**；
  但本地要知道"这周原站动了哪些页"，要么全量爬取比对（675 次请求），要么有个存档。
  原站「更新履歴ページ」（PukiWiki `#recent`）**1 次请求**就能拿到最新 100 条
  「日期 + 页面名」，按它生成存档即可 —— 本地拉 `data/upstream/latest.json` 就知道
  哪些页是**新增**、哪些页**已更新**、哪些**不用动**。

产物（全部入库）：
  data/upstream/latest.json              最新一份（本地更新时读这个）
  data/upstream/weekly/<ISO周>.json      按周存档，留历史
  data/upstream/weekly/<ISO周>.md        人类可读摘要（CI 日志/直接翻看）
  data/upstream/history-<ISO周年>.ndjson 累积流水，**按年分文件**；每行 = **一个页条目**
                                         （week + 页名 + status…），可查"某页哪周动过"
  data/upstream/history.bad.ndjson       解析失败的坏行留档（从主文件移出，避免永久残留）

为什么按年分文件（2026-11-13）：
  单文件流水每周 +100 行、约 1.9 MB/年，且写入是"读全文→按周去重→整文件重写"；
  拆成 history-<ISO周年>.ndjson 后单文件上限约 1.9 MB、跨年自动新建，写入只需读写
  当年那一份。这些文件**没有代码读者**（`show`/`names` 只读 latest.json，历史只供
  grep/翻看），所以拆分不影响任何代码路径。

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


# 路径一律在**调用时**从 ARCHIVE_DIR 现算（不再固化成 import 期常量）：
#   ① 年文件要先知道是哪一年，import 期算不出来；
#   ② 测试可以把 ARCHIVE_DIR 换成临时目录，不必逐个改常量。
def _weekly_dir() -> Path:
    return ARCHIVE_DIR / "weekly"


def _latest_file() -> Path:
    return ARCHIVE_DIR / "latest.json"


def _year_history_file(year: str) -> Path:
    return ARCHIVE_DIR / f"history-{year}.ndjson"


def _history_file(week: str) -> Path:
    """某个 ISO 周所属的流水文件：history-<ISO周年>.ndjson（跨年自动新建）。

    用 week 的前 4 位（即 ISO 周年 `%G`，不是日历年）：2026-12-29 属于 2027-W01，
    落在 2027 文件里，与 week 键自身一致。
    """
    return _year_history_file(week[:4])


def _legacy_history_file() -> Path:
    """旧版单文件流水（迁移前）。存在即自动拆分并入年文件后删除。"""
    return ARCHIVE_DIR / "history.ndjson"


def _bad_file() -> Path:
    """坏行留档：解析失败的原始行，从主文件移出后存这里。"""
    return ARCHIVE_DIR / "history.bad.ndjson"


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
    """落盘：latest.json + weekly/<周>.json/.md + 追加 history-<ISO周年>.ndjson。"""
    _migrate_legacy_history()
    week = snap["iso_week"]
    weekly_dir = _weekly_dir()
    weekly_dir.mkdir(parents=True, exist_ok=True)
    weekly = weekly_dir / f"{week}.json"
    weekly_md = weekly_dir / f"{week}.md"
    latest = _latest_file()
    hist = _history_file(week)

    def _dump(p: Path) -> None:
        p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")

    _dump(weekly)
    _dump(latest)

    # 累积流水：一个页条目一行。同周重跑 → 先滤掉该周旧行（跨周历史不受影响）；
    # 解析不了的坏行移出主文件（否则它永远留在里面、也永远不参与按周去重）。
    lines: "list[str]" = []
    bad: "list[str]" = []
    if hist.exists():
        for ln in hist.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                obj = json.loads(ln)
            except Exception:  # noqa: BLE001 - 坏行不阻断本周存档
                bad.append(ln)
                continue
            if obj.get("week") == week:
                continue
            lines.append(ln)
    for it in snap["items"]:
        lines.append(json.dumps({"week": week, **it}, ensure_ascii=False))
    hist.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if bad:
        _append_bad(bad)

    weekly_md.write_text(_to_markdown(snap), encoding="utf-8")
    return {"weekly": str(weekly), "latest": str(latest),
            "md": str(weekly_md), "history": str(hist)}


def _append_bad(lines: "list[str]") -> None:
    """坏行留档（去重后追加）。"""
    p = _bad_file()
    known = set(p.read_text(encoding="utf-8").splitlines()) if p.exists() else set()
    fresh = [ln for ln in lines if ln not in known]
    if not fresh:
        return
    with p.open("a", encoding="utf-8") as fh:
        for ln in fresh:
            fh.write(ln + "\n")


def _migrate_legacy_history() -> None:
    """把旧版单文件 `history.ndjson` 按 ISO 周年拆进 `history-<年>.ndjson`。

    幂等：迁移完删除旧文件；旧文件不存在时立即返回（每次 save 调一次，开销可忽略）。
    同一个 week 在两边都出现时以旧文件为准（它是更新的一方），保证「同周只有一份」。
    """
    legacy = _legacy_history_file()
    if not legacy.exists():
        return
    by_year: "dict[str, list[str]]" = {}
    bad: "list[str]" = []
    for ln in legacy.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        try:
            obj = json.loads(ln)
        except Exception:  # noqa: BLE001 - 坏行进留档，不阻断迁移
            bad.append(ln)
            continue
        week = str(obj.get("week") or "")
        by_year.setdefault(week[:4] or "unknown", []).append(ln)
    for year, incoming in by_year.items():
        target = _year_history_file(year)
        weeks = {json.loads(ln).get("week") for ln in incoming}
        kept: "list[str]" = []
        if target.exists():
            for ln in target.read_text(encoding="utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    if json.loads(ln).get("week") in weeks:
                        continue
                except Exception:  # noqa: BLE001
                    pass
                kept.append(ln)
        kept.extend(incoming)
        target.write_text("\n".join(kept) + "\n", encoding="utf-8")
    if bad:
        _append_bad(bad)
    legacy.unlink()


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
    p = _latest_file()
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def actionable_names(snap: "dict | None" = None, statuses=ACTIONABLE) -> "list[str]":
    """存档里需要处理的页面名（statuses=None 表示全部条目的页面名）。"""
    snap = snap or latest()
    if not snap:
        return []
    if statuses is None:
        return [it["name"] for it in snap["items"]]
    return [it["name"] for it in snap["items"] if it["status"] in statuses]
