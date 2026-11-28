"""自动更新：处理 planned 镜像 → 依"最后编辑时间"(RSS/--full)检测变更 → 重抓/重解析/zh_patch → 刷新计划。

翻译统一走 tools/zh_patch.py（词典确定性替换）。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor

from . import config, deps
from .chara import extract_all_characters
from .fetcher import (
    FetchError,
    PoliteFetcher,
    is_challenge_page,
    is_missing_page,
    page_url,
    parse_wiki_lastmod,
)
from .logutil import get_logger
from .parser_puki import parse_all
from .plan import (
    _group_to_entry,
    _normalize_planned,
    fetch_recent_changes,
    load_mirror_plan,
    save_mirror_plan,
    sync_plan,
)
from .registry import (
    AUTO_UPDATE_FLAG,
    auto_update_entries,
    is_auto_update,
    load_registry,
    save_registry,
)
from .sitegen import SIDEBAR_FLAT_CATEGORIES, sync_site
from .snapshot import Manifest, save_snapshot, utcnow_iso

log = get_logger()


def _gtrans_todo_files(paths: "list[str] | None") -> None:
    """用谷歌免费机翻把指定待译清单翻成 `*_translated.txt`，供后续 fill 回填。

    ⚠️ 只处理**显式传入**的文件，绝不调用 `gtrans.translate_todo_dir(TODO_DIR)`
    扫整个待译目录：全站未译残留量仍很大（2026-08-31 实测：待译条目约 3.7 万、
    假名约 13.7 万），一旦扫目录就会把历史积压全部重翻，update 跑到失控。
    同名的 `*_translated.txt` 已存在则跳过（同一天重复 update 不浪费配额）。
    机翻失败只告警、不阻断：后续 fill 仍会回填已有译文。
    """
    from pathlib import Path

    from . import gtrans

    for p in paths or []:
        try:
            src = Path(p)
            out = src.with_name(f"{src.stem}_translated.txt")
            if out.exists():
                log.info("[gtrans] 已有译文，跳过：%s", out.name)
                continue
            got = gtrans.translate_todo_file(src)
            log.info("[gtrans] 机翻完成：%s → %s", src.name, Path(got).name)
        except Exception as err:  # noqa: BLE001 机翻失败不应阻断整轮更新
            log.warning("[gtrans] 机翻失败（跳过，fill 仍会用已有译文）：%s：%s", p, err)


def _run_zh_patch(pages: list[str] | None = None,
                  todo_files: "list[str] | None" = None,
                  use_gtrans: bool = True) -> None:
    """key 化 i18n 流程（2026-07-27 取代 zh_patch 正则替换，函数名保留兼容）。

    build（重 parse 页面重建模板+JSON，按 ja 文本回贴已有 zh）→ 应用翻译
    （migrate 旧 [N] 存量迁移 + 回填 _todo_translate 最新待译清单中的 [N] 中文）
    → char-fill（角色数据 JSON）。全程查表，无正则。

    `use_gtrans=True` 时在 fill 之前先用谷歌免费机翻把 `todo_files` 翻成译文文件
    （见 _gtrans_todo_files），使本地 update 与 CI（sync-fetch.yml）一样闭环出中文，
    不必再手工补 `gtrans` 一步。
    """
    from . import i18n

    log.info("运行 key 化 i18n（build → %s→ fill → char-fill）…",
             "gtrans " if use_gtrans and todo_files else "")
    i18n.build_all(slugs=pages)
    i18n.migrate_all(slugs=pages)        # 旧版 _translated_texts/<slug>.txt 的 [N] 存量迁移（幂等）
    if use_gtrans:
        _gtrans_todo_files(todo_files)
    # 统一走 v2 按页模式（[keyN]/[blkN] 按 id 精确写回）。
    # 旧的 fill_latest_todo 按位置序号 [N] 对齐：extract→fill 之间待译集合一旦变动
    # （glossary-fill / apply-dedup / 部分条目已译）就会整体错位且无报错，故废弃。
    i18n.fill_todo_per_page(slugs=pages)
    # 机翻留档：把本轮由谷歌机翻**真正落库**的条目单独存进 data/mt/（入库），
    # 供后续用别的方式精翻（`mt export` → 改译文 → `mt apply --write`，见 mt.py 顶部说明）。
    # 只扫显式送翻过的清单产物，`--no-gtrans` 或无译文卷时是空操作。
    if use_gtrans:
        from . import mt

        mt.record()
    i18n.char_fill_all()


def _write_todo_for_changed(changed_pages: list[str], by_name: dict) -> "list[str]":
    """更新脚本：对本次新增/变更的页面，生成 v2 按页待译清单
    tools/_todo_translate/<slug>_<YYYYMMDD>.txt + <slug>_<YYYYMMDD>_index.json
    （i18n.extract_todo_per_page，条目直接是 [keyN]/[blkN] 真 id）。

    ⚠️ 必须用 v2 按页格式：`fill_todo_per_page` 只消费 `<slug>_<date>*_translated.txt` +
    `_index.json`；旧 `extract_todo` 的 `new_translation_<date>.txt` 集中式清单
    （# MAP + [N] 序号）与之不匹配，fill 会静默空转（历史 bug：本地 update 的
    extract→fill 从没真正回填过）。此改动同时与 CI（i18n extract --per-page）对齐。

    返回本次产出的清单文件路径列表（无 i18n 页/无待译时为空列表），供 _run_zh_patch
    定向机翻——避免整目录扫描带来的失控开销。
    """
    from . import i18n

    slugs = []
    for name in changed_pages:
        entry = by_name.get(name, {})
        is_char = entry.get("category") == "character-detail"
        slug = f"characters/{name}" if is_char else entry.get("slug", name)
        if i18n.has_i18n(slug):
            slugs.append(slug)
    if not slugs:
        return []
    generated = i18n.extract_todo_per_page(slugs=slugs)
    if generated:
        log.info("待译清单已更新：%d 个文件", len(generated))
    return generated


# 单轮最多串行"礼貌重试"多少页。并行阶段大面积失败说明是原站限流/反爬（不是单页偶发），
# 逐页 2–4 秒重试只会把封禁做实 —— 大失败直接不重试（见 _probe_and_save 末尾）。
SERIAL_RETRY_LIMIT = 40


def _probe_and_save(
    candidates: "list[dict]",
    dry_run: bool,
    workers: int,
    tag: str,
    retry_serial: bool = True,
    force_hash: "set[str] | None" = None,
) -> "tuple[list[str], list[str]]":
    """并行探测候选页的「最終更新日時」，对漂移页落快照。

    返回 (变更页名列表, 探测失败/无时间戳的页名列表)。

    `force_hash`：**忽略时间戳、直接比正文 sha256** 的页名集合。用于两类时间戳不可信的页
    （详见 `deps.py` 与本节末尾注释）：
      · 表格绑定页（`テーブル/xxx` 渲染进正文，宿主页自身时间戳不动）；
      · 出现在「更新履歴」里的页（履歴比页面自己的 `Last-modified` 权威，实测原站有
        114 页共享 `2022-12-22 10:04:23` 这个冻结时间戳）。
    正文本来就已经 GET 下来了，多算一次哈希零额外请求。

    由 `sync_stale_pages`（全量 675 页）与 `sync_recent_pages`（更新履歴驱动的候选择）
    **共用**：两条通道的"判定口径 + 落盘动作"必须逐字一致 —— 否则 `sync-recent --verify`
    的交叉校验就没有意义（两边的差异会混入实现差异，而非真实的漏检）。

    为什么是并行裸 httpx 而非 PoliteFetcher：检测本身只是每页一个 GET，13 线程全站
    ~1 分钟（实测原站正常响应、未被限流）；走 PoliteFetcher 的 2–4 秒随机 sleep 则要
    34 分钟以上。检测时**已经拿到正文**，直接写快照，省掉对变更页的第二次抓取。

    ⚠️ `retry_serial=True`（默认）：并行阶段的失败页会用 `PoliteFetcher` **串行重试一遍**
    —— 失败**不等于**未变更，而并行通道为速度牺牲了重试（裸 httpx、无退避），实测偶发
    `peer closed connection without sending complete message body` 这类瞬时断连
    （2026-09-27 一轮里出现 2 页）。不重试的话这些页会被静默跳过：本轮漏、下轮才补，
    若长期不稳定就永远漏掉，且**在报告里完全看不出来**。
    重试有**两道闸**（失败达半数直接放弃、其余最多 `SERIAL_RETRY_LIMIT` 页），
    详见函数末尾 —— 大失败＝原站在拦我们，此时重试等于加速被封。
    """
    import threading

    import httpx

    from .fetcher import LASTMOD_RE, page_url, parse_wiki_lastmod
    from .snapshot import Manifest, sha256_bytes

    manifest = Manifest()
    force = set(force_hash or ())
    lock = threading.Lock()
    local = threading.local()
    failed: "list[str]" = []

    def _client() -> "httpx.Client":
        c = getattr(local, "client", None)
        if c is None:
            c = httpx.Client(
                timeout=config.FETCH_TIMEOUT, follow_redirects=True,
                headers={"User-Agent": config.USER_AGENT,
                         "Accept-Language": "ja,en;q=0.8"})
            local.client = c
        return c

    def _judge(name: str, resp) -> "tuple[str, tuple | None]":
        """时间戳口径判定，返回 **(状态, 载荷)** 三态：

          ('changed',   (name, resp, remote, old))  → 需要落快照
          ('unchanged', None)                       → 时间戳一致，跳过
          ('unknown',   None)                       → 解析不出时间戳（结构变/挑战页）

        ⚠️ 必须是三态：曾用 "None 同时表示 unchanged 与 unknown"，结果**每一页未变更的页
        都被记成"失败"** → 触发一轮无意义的串行重试（实测 38 页全被误判、白跑 ~110 秒），
        而真正的失败又淹没在假失败里看不出来。失败≠未变更，两者不能共用一个哨兵值。
        """
        text = resp.text
        remote = parse_wiki_lastmod(text)
        # ⚠️ 时间戳解析不出来的页（反爬挑战页 / 结构变化）**必须先拦掉**，
        #    哪怕它在 force 集合里 —— 否则「哈希不同」会把挑战页正文当成新快照写进
        #    data/raw，一次就把镜像好的页面污染成「One moment, please…」✗
        if not remote or not LASTMOD_RE.search(text):
            return "unknown", None
        old_entry = manifest.page(name) or {}
        old = old_entry.get("wiki_last_modified")
        if name in force:
            # 时间戳不可信（表格绑定页 / 更新履歴已确认改过的页）→ 内容哈希才是判据。
            # 哈希相同 = 真的没变（不写盘，避免无意义的 git churn）。
            if old_entry.get("sha256") == sha256_bytes(resp.content):
                return "unchanged", None
            return "changed", (name, resp, remote, old)
        if old == remote:
            return "unchanged", None
        return "changed", (name, resp, remote, old)

    def _probe(e: dict):
        name = e["name"]
        try:
            resp = _client().get(page_url(name))
            if resp.status_code != 200:
                failed.append(name)
                return None
        except Exception as err:  # noqa: BLE001 单页失败不阻断
            log.warning("[%s] %s 抓取失败：%s", tag, name, err)
            failed.append(name)
            return None
        state, payload = _judge(name, resp)
        if state == "unknown":
            failed.append(name)
            return None
        return payload          # 'unchanged' → None（主循环里被跳过）

    def _commit(name: str, resp, remote: str, old) -> None:
        if dry_run:
            log.info("[%s] 需要更新 %s（%s → %s）", tag, name, old, remote)
            return
        with lock:
            save_snapshot(name, resp.content)
            manifest.record_page(
                name, page_url(name), resp.content, status="ok",
                http_last_modified=resp.headers.get("last-modified"),
                wiki_last_modified=remote)
            log.info("[%s] 已更新快照 %s（%s → %s）", tag, name, old, remote)

    changed: "list[str]" = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(_probe, candidates):
            if not res:
                continue
            name, resp, remote, old = res
            changed.append(name)
            _commit(name, resp, remote, old)

    # 失败页串行礼貌重试（限速 + 退避）。仍失败者保留在 failed 里（报告可见）。
    #
    # ⚠️ 两道闸（2026-11-28 用户反馈"每次探太多会被封"）：
    #   ① **半数以上同时失败 ⇒ 判定为原站已在限流/反爬，本轮完全不重试**。
    #      实测日志：768 页并行探测全部失败后，又对 768 页逐页"礼貌重试"
    #      （每页 2–4 秒 + 最多 3 次退避）—— 那不是重试，是把封禁做实。
    #   ② 其余情况最多重试 SERIAL_RETRY_LIMIT 页，超出的写进失败报告留到下一轮
    #      （候选页都来自更新履歴窗口，窗口有 9~20 天深，下一轮自然还会被选中）。
    if failed and retry_serial:
        retry_names = list(dict.fromkeys(failed))
        if len(retry_names) >= max(20, len(candidates) // 2):
            log.warning("[%s] %d/%d 页并行探测失败（≥半数）→ 判定为原站限流/反爬，"
                        "本轮**不**串行重试（避免把封禁做实）；这些页留到下一轮",
                        tag, len(retry_names), len(candidates))
            failed = retry_names
        else:
            if len(retry_names) > SERIAL_RETRY_LIMIT:
                log.warning("[%s] 失败页 %d 个，超过单轮串行重试上限 %d（其余留到下一轮）",
                            tag, len(retry_names), SERIAL_RETRY_LIMIT)
                retry_names = retry_names[:SERIAL_RETRY_LIMIT]
            failed = []
            log.info("[%s] %d 页并行探测失败，改用礼貌重试：%s",
                     tag, len(retry_names), "、".join(retry_names[:5]))
            with PoliteFetcher() as f:
                for name in retry_names:
                    try:
                        resp = f.get(page_url(name))
                    except Exception as err:  # noqa: BLE001
                        log.warning("[%s] %s 重试仍失败：%s", tag, name, err)
                        failed.append(name)
                        continue
                    state, payload = _judge(name, resp)
                    if state == "unknown":
                        failed.append(name)
                        continue
                    if state == "unchanged":
                        continue
                    assert payload is not None
                    if name not in changed:
                        changed.append(name)
                    _commit(name, payload[1], payload[2], payload[3])
            if failed:
                log.warning("[%s] %d 页重试后仍失败（本次未确认状态）：%s",
                            tag, len(failed), "、".join(failed[:5]))

    if not dry_run:
        manifest.save()
    return changed, failed


def _recent_names_safe(tag: str) -> "set[str]":
    """容错地取「更新履歴」里的页名集合；失败只告警（退回纯时间戳判定）。"""
    from . import recent as recent_mod

    try:
        hist = recent_mod.fetch_recent_history()
    except Exception as err:  # noqa: BLE001 更新履歴挂了不该让同步停摆
        log.warning("[%s] 更新履歴不可用，本轮只能按时间戳判定：%s", tag, err)
        return set()
    return set(hist.names)


def _force_hash_names(hist_names: "set[str]", known: "set[str]") -> "set[str]":
    """需要**忽略时间戳、按正文 sha256 判定**的页名集合（只取注册表内的页）。

    两类页的时间戳不可信：
      ① 表格绑定页：`#table(テーブル/xxx)` 渲染进正文，子页改动不动宿主页时间戳；
      ② 更新履歴里出现的页：履歴比页面自己的 `Last-modified` 权威 —— 实测原站有 114 页
         共享 `2022-12-22 10:04:23` 这个冻死的时间戳（装备页、原画別索引都在其中），
         而它们在更新履歴里分别标着 2026-10-08 / 10-10 / 10-14，属于「明明改了、时间戳不变」。
    """
    table_hosts = deps.table_dep_hosts() & known
    hist_hit = hist_names & known
    return table_hosts | hist_hit


def _source_hosts(name: str, known: "set[str]") -> "list[str]":
    """更新履歴里的一个页名 → 它会影响的**已镜像宿主页**。

      · `コメント/X`：pcomment 插件把评论区**渲染进宿主页 X 的正文**（实测 203 个页面带
        这种区块），所以评论一改，X 的正文就变了 —— 宿主就是 X 本身；
      · `テーブル/X`（以及被 `#table()` 内嵌的普通内容页，如 `装備リスト`）：一个来源页可能
        被多个宿主页内嵌（`テーブル/SSR` → `SSR`・`list-ssr`・`characters`…），由 `deps` 反查；
      · 其余页名（角色页/导航页）不是内容来源，返回空。

    这两类来源的改动都**不动宿主页自己的「最終更新日時」** —— 履歴里的这条记录就是唯一信号，
    因此也没必要每轮把宿主页再无条件探一遍（2026-11-28 用户反馈的正是这个）。
    """
    if name.startswith("コメント/"):
        host = name[len("コメント/"):]
        return [host] if host in known else []
    return [h for h in deps.hosts_of(name) if h in known]


def sync_stale_pages(
    dry_run: bool = False,
    workers: int = 13,
    report: "dict | None" = None,
) -> list[str]:
    """**并行全量**检测原站「最終更新日時」漂移，只对变更页落快照（`update --full` 的快版）。

    为什么需要它（2026-09-27 实测）：
      · 原站没有批量列出各页更新时间的入口，HTTP `Last-Modified` 又不可用（近乎常量），
        所以「这一页更新了没有」只能逐页抓一次正文、读页面里的「最終更新日時」文本；
      · `update --full` 走 `PoliteFetcher`（随机 sleep 2–4 秒、**串行**）→ 675 页要
        **至少 34 分钟**；而检测本身只是每页一个 GET，并行 13 线程全站扫完 ~1 分钟
        （实测原站正常响应、未被限流）；
      · 检测时**已经拿到正文**，直接写快照即可，省掉对变更页的第二次抓取。

    与 `update --full` 的关系：语义相同（比对 wiki_last_modified → 变更页落快照），
    只是把「检测」与「礼貌抓取」解耦。落盘后 `parse` 会因 sha256 变化自动重解析。

    这是**权威通道**（覆盖全站每一页），代价是 675 次请求；日常增量请用
    `sync_recent_pages`（1 次请求），本通道作为每周兜底与交叉校验继续保留。

    `report`（可选）：由 `sync_recent_pages` 的回退分支传入，用来把失败页一并写进它的
    报告 —— 否则回退轮里"有页没探成"会对外不可见，`last_ok` 也可能被误推进。
    返回：本次落盘的页名列表（dry_run 时只返回"将被落盘"的页）。
    """
    config.ensure_dirs()
    all_pages = load_registry()
    registry = auto_update_entries(all_pages)
    excluded = [e["name"] for e in all_pages if not is_auto_update(e)]
    if excluded:
        log.info("[sync-stale] 自动更新排除 %d 页（%s）：%s",
                 len(excluded), AUTO_UPDATE_FLAG, "、".join(excluded))
    known = {e["name"] for e in registry}
    table_hosts = deps.table_dep_hosts() & known
    hist_hit = _recent_names_safe("sync-stale") & known
    force = table_hosts | hist_hit
    if force:
        log.info("[sync-stale] %d 页改用内容 sha256 判定（时间戳不可信）："
                 "表格绑定 %d 页 + 更新履歴 %d 页", len(force), len(table_hosts), len(hist_hit))
    changed, failed = _probe_and_save(registry, dry_run, workers, "sync-stale", force_hash=force)
    if report is not None:
        report["failed"] = failed
    return changed


# 更新履歴通道的状态文件（随提交入库：用来算"上次同步到哪一天"，判断窗口是否够深）
RECENT_STATE_FILE = config.MANIFEST_FILE.parent / "recent_state.json"


def _is_namespaced(name: str) -> bool:
    """是否属**原站内部页**（不在镜像范围）。

    判定：带命名空间前缀（`SandBox/…`・`イベント一覧/…`・`広域戦マップ/…`）或事件编号页
    （`イベント91_…`）。这类页既不在 `NAV_CATEGORIES` 的导航清单里，也不是角色一览里的页，
    镜像范围之外 —— 归入「范围外」而不是「疑似漏登记」，避免报告里混入噪声。
    不用正则：`updater` 模块本身不 import `re`，字符串判断足够且更直白。
    """
    return "/" in name or name.startswith("イベント")


def _is_nav_like(name: str) -> bool:
    """是否属**已知的导航/系统页**（`SLUG_MAP` 有路由，或列在 `NAV_CATEGORIES` 里）。

    这类页未出现在注册表，是**有意为之**：它们若登记就会进左侧导航栏，而导航栏新增
    必须人工确认（用户约束，见 `registry.NAV_CATEGORIES` 注释）。所以它们要单独成类，
    既不能混进"疑似该新增"（会诱导自动登记 ✗），也不该被当成脏数据丢掉（人工可能要开）。
    """
    from .registry import NAV_CATEGORIES, SLUG_MAP

    if name in SLUG_MAP:
        return True
    return any(name in names for names in NAV_CATEGORIES.values())


def _shift_date(day: str, delta: int) -> str:
    from datetime import date, timedelta

    y, m, d = (int(x) for x in day.split("-"))
    return (date(y, m, d) + timedelta(days=delta)).isoformat()


def _last_sync_date(manifest: "Manifest") -> "str | None":
    """manifest 里最晚的一次抓取日期（'YYYY-MM-DD'）—— 代表"上次同步到哪一天"。"""
    stamps = [
        (p.get("fetched_at") or "")[:10]
        for p in manifest.data.get("pages", {}).values()
    ]
    stamps = [s for s in stamps if len(s) == 10]
    return max(stamps) if stamps else None


def _last_ok_date() -> "str | None":
    """上次**成功枚举完整个更新履歴窗口**的日期（`recent_state.json` 的 `last_ok`）。

    与 `_last_sync_date` 的区别很关键：manifest 那个只有"某页真的变了"才推进，安静期会
    一直停在几周前 —— 于是窗口余量判定会**误判成窗口不够深**、白白回退一次 675 页全量。
    `last_ok` 记的是"上次确认过窗口覆盖到哪一天"，才是余量判定的正确基准。
    """
    try:
        state = json.loads(RECENT_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    day = str(state.get("last_ok") or "")[:10]
    return day if len(day) == 10 else None


def sync_recent_pages(
    dry_run: bool = False,
    workers: int = 13,
    fallback: bool = True,
    margin_days: int = 1,
) -> dict:
    """**更新履歴驱动的增量检测**：1 次请求缩小候选集，只对候选页做时间戳比对。

    为什么再开一条通道（2026-09-27）：
      · 原站「更新履歴ページ」（PukiWiki `#recent`）**一次请求**就能拿到"最新 100 条 =
        精确日期 + 页面名"（实测窗口约 21 天），按页面去重、严格倒序；
      · 全量 `sync_stale_pages` 虽准，但要 675 次请求（~1 分钟），想每天跑偏重；
      · RSS（`update` 默认路径）只与 49 个 `mode == watch` 页求交集 —— 静态页/角色页
        的更新根本不在覆盖范围内，因此不能单独依赖它。

    **高可用设计**（本函数的重点，不是"更快的 sync-stale"）：
      ① 双通道：本通道（廉价、每天可跑）+ `sync-stale`（权威、每周兜底）；
      ② 交叉校验：`--verify` 会把两条通道的变更集会做差集并报告 —— 若全量通道发现了
         本通道**没发现**的页，说明窗口不够深或解析退化，是可观测的信号；
      ③ **窗口饱和度回退**：更新履历是"最新 100 条"的**截断**列表，条目数触顶是常态
         （实测恒为 True），所以**不能用触顶做判据**；真正要紧的是"窗口最旧的日期是否
         仍覆盖得上我们上次成功枚举窗口的日期"。若覆盖不上、或整页解析为空/无日期 → 自动升级为
         全量比对（`fallback=True` 时），宁慢不错；
      ④ 盲区可观测：把"更新履历里出现、但 registry 未登记且未被排除规则排除"的页面名
         单独报出来 —— 这类页若真是可镜像页，说明 `discover` 漏登记了（历史上正是
         "注册表有记录却没有快照/i18n"那类静默缺口）；
      ⑤ 宿主页**只按履歴连带**，不再每轮全探（2026-11-28）：履歴里的 `テーブル/X` 与
         `コメント/X` 就是"哪个宿主页的正文会变"的完整信号（见 `_source_hosts`）。
         之前每轮无条件探 201 个宿主页，叠加回退全量后单轮近千次请求，会招来限流/封禁；
      ⑥ **通道本身不可用 → 本轮直接跳过**（抓取失败 / 反爬挑战页），绝不回退全量：
         原站已经在拦我们的时候再发几百个请求，只会把封禁做实。跳过时不推进 `last_ok`，
         连续失败若干轮后窗口自然覆盖不上，那时才会尝试一次全量。

    落盘：变更页快照 + `data/recent_state.json`（状态，随提交入库）。
    返回：本次运行的报告 dict（CI 直接打印，便于事后追查）。
    """
    from . import recent as recent_mod
    from .registry import _is_excluded
    from .snapshot import Manifest

    config.ensure_dirs()
    manifest = Manifest()
    report: dict = {
        "page": recent_mod.RECENT_HISTORY_PAGE,
        "entries": 0,
        "window": [None, None],
        "truncated": False,
        "candidates": 0,
        "sources": 0,            # 命中内容来源页（コメント/…・テーブル/…）且宿主已镜像的条数
        "from_sources": 0,       # 由内容来源页连带引入的宿主页数
        "always_probe": 0,       # pages.yaml 手工点名「时间戳冻死」的必探页数
        "hash_forced": 0,        # 按正文 sha256 判定（忽略时间戳）的页数
        "changed": [],
        "failed": [],
        "unregistered": [],      # 未登记、且非导航类 → 多为新增角色页（允许自动登记的那类）
        "known_nav": [],         # 已知导航/系统页但未镜像 → 有意为之，需人工确认
        "frozen": [],            # no_auto_update：已镜像但永远读不出更新时刻，不参与自动更新
        "out_of_scope": 0,
        "fell_back": False,
        "skipped": False,        # 被反爬挑战页拦住 → 本轮整体跳过（不回退全量）
        "reason": "",
    }

    def _dump_state() -> None:
        """写 `data/recent_state.json`（dry_run 不写）。

        `last_ok` 只在"本轮确实把该查的都查干净了"时推进：跳过、被拦、或存在探测失败的页
        时保持原值 —— 它是下次判断窗口够不够深的基准，往前挪会静默漏检。
        """
        if dry_run:
            return
        advanced = not report["skipped"] and not report["failed"]
        state = {
            "fetched_at": utcnow_iso(),
            "last_ok": utcnow_iso()[:10] if advanced else _last_ok_date(),
            "entries": report["entries"],
            "window": report["window"],
            "truncated": report["truncated"],
            "candidates": report["candidates"],
            "sources": report["sources"],
            "from_sources": report["from_sources"],
            "always_probe": report["always_probe"],
            "hash_forced": report["hash_forced"],
            "changed": report["changed"],
            "failed": report["failed"],
            "fell_back": report["fell_back"],
            "skipped": report["skipped"],
            "reason": report["reason"],
            "unregistered": report["unregistered"],
            "known_nav": report["known_nav"],
            "frozen": report["frozen"],
        }
        RECENT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        RECENT_STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---- ① 抓 + 解析 ----
    # ⚠️ 抓取本身失败（HTTP 403/429/503、SSL、DNS…）时**本轮直接跳过，不回退全量**：
    #    2026-11-28 实测日志里的一轮 —— 履歴拿不到 → 回退 768 页全量 → 768 页全部失败
    #    → 又对这 768 页逐页"礼貌重试"（每页 2–4 秒）。那是自己申请封禁。
    #    不推进 `last_ok` ⇒ 连续失败若干轮后窗口自然覆盖不上，才会尝试一次全量，
    #    这样"少抓一轮"最多让镜像晚一周，而不会把出口 IP 打死。
    try:
        hist = recent_mod.fetch_recent_history()
    except Exception as err:  # noqa: BLE001 网络/结构异常都不该让同步停摆
        log.warning("[sync-recent] 更新履歴抓取/解析失败：%s", err)
        hist = recent_mod.RecentHistory()
        report["skipped"] = True
        report["reason"] = f"更新履歴不可用：{err}"
    report["entries"] = len(hist.entries)
    report["window"] = [hist.oldest_date, hist.newest_date]
    report["truncated"] = hist.truncated

    # 反爬挑战页也是 HTTP 200，只是内容全是"请稍候"：这时**立即收工**，连候选都不该算。
    # 原站既然在拦我们，再按"解析为空 → 回退全量"跑 675 次请求就是自己申请封禁。
    if hist.challenged:
        report["skipped"] = True
        report["reason"] = "更新履歴被反爬挑战页拦截"
    if report["skipped"]:
        log.warning("[sync-recent] %s → 本轮跳过（**不回退全量**；下一轮再试，"
                    "窗口真覆盖不上时才会升级全量）", report["reason"])
        _dump_state()
        return report

    # ---- ② 页面名 → registry 条目（不在镜像范围内的只统计，供观测）----
    registry = load_registry()
    by_name = {e["name"]: e for e in registry}
    known = set(by_name)
    candidates: "list[dict]" = []
    seen: set[str] = set()

    def _add_candidate(name: str) -> bool:
        """收进候选；`no_auto_update` 的页只记进 frozen，不探测。返回是否真的入列。"""
        if name in seen:
            return False
        seen.add(name)
        if not is_auto_update(by_name[name]):
            # no_auto_update（如反爬挑战页「公式ヘルプ」）：内容已镜像完成、站点照常渲染，
            # 只是永远读不出更新时刻 → 不探测，否则每轮都报一次假失败。
            report["frozen"].append(name)
            return False
        candidates.append(by_name[name])
        return True

    # 宿主页名 → 命中它的内容来源页（`コメント/…` ・ `テーブル/…` ・被内嵌的普通内容页）
    source_hits: "dict[str, list[str]]" = {}
    for name in hist.names:
        # 先看它是不是"给别人供内容"的来源页：这与它自己是否镜像无关
        # （`テーブル/全ストーリー実装順` 既自己镜像、又被 `メインストーリー` 内嵌）。
        hosts = _source_hosts(name, known)
        for host in hosts:
            source_hits.setdefault(host, []).append(name)
        if name in by_name:
            _add_candidate(name)
        elif hosts:
            # 内容来源页（`コメント/…`・`テーブル/…`）：自己不镜像，只用来连带宿主页。
            report["sources"] += 1
        elif _is_excluded(name) or _is_namespaced(name):
            # 掲示板（排除规则）；以及带命名空间前缀或事件编号的原站内部页
            # （イベント一覧/… ・広域戦マップ/… ・SandBox/… ・イベント91_…）——都属镜像范围外。
            report["out_of_scope"] += 1
        elif _is_nav_like(name):
            # 已知导航/系统页但我们没镜像：**有意为之**（登记会进左侧栏，需人工确认）。
            report["known_nav"].append(name)
        else:
            # 无命名空间的页面名：多为**角色页**这类"不进左侧导航栏"的页，
            # 正是允许自动新增的那一类（由 discover Phase 2 从「キャラクター一覧」登记）。
            # 本通道只做**提示**，绝不自行登记。
            report["unregistered"].append(name)

    # ---- ②b 内容来源页 → 连带宿主页 ----
    # `テーブル/xxx` 由 `#table()` 渲染进宿主页正文；`コメント/X` 由 pcomment 插件把评论区
    # 渲染进 X 的正文（实测 203 个页面带这种区块）。两者的改动**都不动宿主页自己的
    # 「最終更新日時」**，所以宿主页只靠自己的时间戳永远判 unchanged
    # （用户反馈的正是这个：list-ssr/sr/r 的 raw 停在 2026-07-22，而 `テーブル/SSR` 10-07 就改过）。
    # 更新履歴里的这两类记录就是**唯一需要的信号** —— 命中哪个，就连带它的宿主页。
    #
    # ⚠️ 2026-11-28 用户反馈：这里曾一度"表格宿主页每轮无条件全探"（约 201 页/轮），
    #    理由是"子页改动被挤出 100 条窗口就永久丢失"。但窗口是按时间连续截断的：
    #    某个改动被挤出窗口，意味着之后有 100 个不同的页被改过，那窗口最旧日期必然晚于
    #    该改动 —— ③ 的"窗口是否覆盖上次同步"判定会直接回退全量。所以每轮全探纯属冗余，
    #    单轮 201 页 + 回退 768 页的请求量已经会被原站限流/封禁。
    added = [h for h in sorted(source_hits) if _add_candidate(h)]
    report["from_sources"] = len(added)
    if source_hits:
        log.info("[sync-recent] 更新履歴命中 %d 个内容来源页（コメント/・テーブル/…）"
                 " → 连带重抓宿主页 %d 个：%s",
                 len({s for v in source_hits.values() for s in v}), len(added),
                 "、".join(sorted(source_hits)[:8]))

    # ---- ②c 时间戳冻死页（注册表手工点名，2026-11-25 补）----
    # 只剩这一类无法从履歴/依赖索引推导：**内容不来自别处、但自己的「最終更新日時」停更**
    # （实测 `メインクエスト` 停在 2026-05-15，而正文 8 月后仍在追加 Area 页），
    # 只能在 `data/registry/pages.yaml` 打 `always_probe: true` 手工点名。
    flagged = sorted(n for n in known if (by_name[n] or {}).get("always_probe"))
    always = [n for n in flagged if _add_candidate(n)]
    if always:
        log.info("[sync-recent] 必探（%s: true）%d 页：%s",
                 "always_probe", len(always), "、".join(always[:8]))
    report["always_probe"] = len(always)
    # 本轮所有候选一律按正文 sha256 判定（更新履歴里出现的页同样不信时间戳：
    # 实测原站有 114 页共享 2022-12-22 这个冻死的时间戳，装备页/原画別索引都在其中）
    force = {e["name"] for e in candidates}
    report["hash_forced"] = len(force)
    report["candidates"] = len(candidates)
    if report["unregistered"]:
        log.info(
            "[sync-recent] 更新履歴里有 %d 个页面尚未登记（多为新增角色页，"
            "由 discover 从角色一览自动登记；**不会**新增任何导航页）：%s",
            len(report["unregistered"]), "、".join(report["unregistered"][:8]))
    if report["known_nav"]:
        log.info(
            "[sync-recent] 另有 %d 个**已知导航/系统页**未镜像（有意为之，需人工确认才登记）：%s",
            len(report["known_nav"]), "、".join(report["known_nav"][:8]))

    # ---- ③ 饱和/失效判定 → 决定是否升级为全量 ----
    # ⚠️ 走到这里说明**履歴页本身是好的**（拿到了真页面），只是窗口不够用：
    #    「什么都没发现」不等于「什么都没变」—— 解析为空/无日期/窗口太浅时必须升级全量 ✗。
    #    （抓取失败与反爬挑战页已在 ① 直接跳过，不再走到这里。）
    # 基准用 `last_ok`（上次**成功枚举完窗口**的日期）而不是 manifest 的最晚抓取日：
    # 后者在安静期会停在几周前，把"窗口够深"误判成"不够深"，白白全量一次 675 页。
    last_sync = _last_ok_date() or _last_sync_date(manifest)
    need_full = False
    if not hist.entries:
        need_full, report["reason"] = True, "更新履歴解析为空（页面结构可能已变）"
    elif not hist.oldest_date:
        need_full, report["reason"] = True, "更新履歴无任何精确日期"
    elif hist.oldest_date and last_sync:
        floor = _shift_date(last_sync, -max(0, margin_days))
        if hist.oldest_date > floor:
            need_full = True
            report["reason"] = (
                f"窗口最旧 {hist.oldest_date} 未覆盖上次同步 {last_sync}"
                f"（差 {margin_days} 天余量）"
            )

    if need_full and fallback:
        log.warning("[sync-recent] %s → 回退全量比对（sync-stale）", report["reason"])
        changed = sync_stale_pages(dry_run=dry_run, workers=workers, report=report)
        report.update(fell_back=True, changed=changed)
    else:
        if need_full and not fallback:
            log.warning("[sync-recent] %s（--no-fallback：仅报告）", report["reason"])
        changed, failed = _probe_and_save(
            candidates, dry_run, workers, "sync-recent", force_hash=force)
        report.update(changed=changed, failed=failed)

    # ---- ④ 状态落盘（供下次算窗口余量；dry_run 不写）----
    _dump_state()

    log.info(
        "[sync-recent] 窗口 %s→%s（%d 条，触顶=%s）｜候选 %d 页"
        "（履歴直接命中 %d ＋ 来源页连带 %d ＋ 必探 %d；均按内容哈希判定）｜"
        "%s %d 页｜回退=%s｜跳过=%s｜自动更新排除命中 %d 页",
        report["window"][0], report["window"][1], report["entries"], report["truncated"],
        report["candidates"],
        report["candidates"] - report["from_sources"] - report["always_probe"],
        report["from_sources"], report["always_probe"], "将更新" if dry_run else "已更新",
        len(report["changed"]), report["fell_back"], report["skipped"],
        len(report["frozen"]),
    )
    return report


def verify_recent_vs_stale(workers: int = 13) -> dict:
    """**交叉校验**：两条通道各跑一次「只检测不落盘」，比对变更集。

    用法只在需要体检时（CI 里不必每次跑，因为它本身就是一次全量）。
    返回 {'recent': [...], 'stale': [...], 'missed_by_recent': [...], 'extra_by_recent': [...]}
      · missed_by_recent 非空 = 更新履歴窗口不够深/解析退化 → 需要排查（这是唯一的危险信号）；
      · extra_by_recent 非空 = 候选页与全量口径的差异（一般应在容错范围内）。
    """
    from . import recent as recent_mod

    registry = auto_update_entries()      # 两侧口径一致：都排除 no_auto_update 的页
    by_name = {e["name"]: e for e in registry}
    try:
        hist = recent_mod.fetch_recent_history()
    except Exception as err:  # noqa: BLE001
        log.warning("[verify] 更新履歴不可用：%s", err)
        hist = recent_mod.RecentHistory()
    known = set(by_name)
    if hist.challenged:
        log.warning("[verify] 更新履歴返回反爬挑战页，本次交叉校验无意义（两边都会是空/全量）")
    force = _force_hash_names(set(hist.names), known)
    # 候选口径必须与 `sync_recent_pages` **完全一致**（履歴直命中 + 内容来源页连带宿主页），
    # 否则比对出来的差异是实现差异，而不是真实漏检。
    cand_names = [n for n in hist.names if n in by_name]
    for name in hist.names:
        for host in _source_hosts(name, known):
            if host not in cand_names:
                cand_names.append(host)
    cand = [by_name[n] for n in cand_names]

    r1, _ = _probe_and_save(cand, True, workers, "verify-recent", force_hash=force)
    r2, _ = _probe_and_save(registry, True, workers, "verify-stale", force_hash=force)
    s1, s2 = set(r1), set(r2)
    return {
        "recent": sorted(s1),
        "stale": sorted(s2),
        "missed_by_recent": sorted(s2 - s1),
        "extra_by_recent": sorted(s1 - s2),
    }


def _fetch_and_record(
    fetcher: PoliteFetcher,
    manifest: Manifest,
    name: str,
) -> bool:
    """抓取单页并写快照/记录 manifest（含 wiki_last_modified）。返回是否成功入册。

    挑战页/抓取失败返回 False；缺失页(status=missing)仍返回 True（已记录，便于清理）。
    """
    url = page_url(name)
    try:
        resp = fetcher.get(url)
    except FetchError as err:
        log.error("抓取失败 %s：%s", name, err)
        manifest.record_page(name, url, b"", status="error", error=str(err))
        manifest.save()
        return False
    content = resp.content
    text = content.decode(resp.encoding or "utf-8", errors="replace")
    if is_challenge_page(text):
        log.warning("触发海外验证，跳过 %s（需人工在浏览器完成一次验证）", name)
        manifest.record_page(name, url, b"", status="challenged")
        manifest.save()
        return False
    save_snapshot(name, content)
    status = "missing" if is_missing_page(text) else "ok"
    if status == "missing":
        log.warning("页面不存在 %s", name)
    manifest.record_page(
        name, url, content, status=status,
        http_last_modified=resp.headers.get("last-modified"),
        wiki_last_modified=parse_wiki_lastmod(text),
    )
    return True


def planned_grows_sidebar(name: str, group: "str | None", by_name: dict) -> bool:
    """该 planned 项若注册，是否会让**左侧导航栏新增一项**（需人工确认）。

    判定依据：它会落到"平铺分类"（`guide` / `misc`，见 `sitegen.SIDEBAR_FLAT_CATEGORIES`）
    —— 这两类由 `_write_sidebars` 按 registry 原顺序全量列出，注册即上栏 ✗。
    其它分类（system / equipment / quest / character-detail）在侧栏里是**显式 slug** 列举的，
    新页拿的是哈希兜底 slug，不会自动上栏 ✓。
    已登记的页返回 False（只刷新、不新增，无妨）。
    """
    if name in by_name:
        return False
    return _group_to_entry(name, group).get("category") in SIDEBAR_FLAT_CATEGORIES


def _process_planned(by_name: dict) -> list[str]:
    """处理 mirror_plan.yaml 中的 planned 条目：镜像+注册+翻译，成功后移入 mirrored。

    返回本次成功处理的页名列表（需重解析/重翻译）。

    ⚠️ 用户约束（2026-09-27）：**左侧导航栏不允许新增镜像页**。`planned` 里若出现
    `guide` / `misc` 这类"平铺进侧栏"的页，注册进去就等于往导航栏加一项 ✗
    —— 这里**在抓取之前**就跳过，并把它**移出 planned**（否则每轮都会重试、白耗请求），
    同时打 WARNING 交人工决定（要镜像就手工写进 pages.yaml）。
    """
    plan = load_mirror_plan()
    planned = plan.get("planned", [])
    if not planned:
        return []
    remaining = []
    processed: list[str] = []
    skipped_nav: list[str] = []
    with PoliteFetcher() as f:
        manifest = Manifest()
        for item in planned:
            name, group = _normalize_planned(item)
            if not name:
                remaining.append(item)
                continue
            if planned_grows_sidebar(name, group, by_name):
                skipped_nav.append(name)
                log.warning(
                    "planned 的 %s（分组=%s）属**导航类**，注册会让左侧栏新增 ✗"
                    " → 已跳过并移出 planned；确需镜像请人工写入 %s",
                    name, group, config.REGISTRY_FILE.name,
                )
                continue
            if not _fetch_and_record(f, manifest, name):
                remaining.append(item)
                continue
            # 注册 / 更新 registry 条目
            if group and name not in by_name:
                entry = _group_to_entry(name, group)
            else:
                entry = by_name.get(name) or _group_to_entry(name, group)
            by_name[name] = entry
            processed.append(name)
            log.info("planned 已镜像并注册 %s（分组=%s）", name, group)
        manifest.save()

    # 注意：skipped_nav 非空时**也要**改写计划文件 —— 否则那些导航类项会一直留在 planned 里，
    # 每轮重复告警（虽然已在抓取前跳过、不耗请求，但噪声会掩盖真正需要注意的项）。
    if processed or skipped_nav:
        if processed:
            save_registry(list(by_name.values()))
        new_plan = load_mirror_plan()
        new_plan["planned"] = remaining
        save_mirror_plan(new_plan)
        sync_plan()  # 重建 mirrored，使新页落入对应分组
        if processed:
            log.info("planned 处理完成 %d 页，剩余 %d 页待处理", len(processed), len(remaining))
        if skipped_nav:
            log.warning(
                "planned 剔除**导航类** %d 项（不镜像、不上栏，需人工确认才登记）：%s",
                len(skipped_nav), "、".join(skipped_nav[:8]),
            )
    return processed


def run_update(no_translate: bool = False, full: bool = False,
               no_gtrans: bool = True) -> None:
    """自动更新主流程。

    1) 处理 planned；2) 检测变更（默认 RSS 近期变更，--full 逐页最后编辑时间）；
    3) 仅重处理变更页（重抓→重解析→重抽角色→zh_patch）；4) 补图→sync-site→刷新计划→写 manifest。

    ⚠️ 2026-09-28 方针变更（用户决定）：**`no_gtrans` 默认 True（不再机翻）** ✓ ——
    免费谷歌端点质量不可控（实测旧"预替换"路径 chrF3 0.175、术语命中 37.8%，且会产出
    「抗眩光低血糖症列表」这类乱译 ✗✗），改为人工精翻。要临时开启：CLI `update --gtrans`
    或显式传 `no_gtrans=False`。防御性地把默认值也设成"不机翻"，避免其它调用方误触发 ✗。
    """
    config.ensure_dirs()
    registry = load_registry()
    by_name = {e["name"]: e for e in registry}
    if not registry:
        log.warning("注册表为空，请先运行 discover 与 fetch")
        return

    # 1) planned
    planned_processed = _process_planned(by_name)

    # 2) 变更检测
    changed: list[str] = []
    with PoliteFetcher() as f:
        manifest = Manifest()
        if full:
            log.info("全量模式：逐页比对 WIKI 最后编辑时间…")
            # 仅检查 mode=watch 且在册非缺失/非挑战页；`no_auto_update` 的页（如反爬挑战页
            # 「公式ヘルプ」）一律跳过 —— 见 registry.AUTO_UPDATE_FLAG。
            full_targets = auto_update_entries(registry)
            for i, e in enumerate(full_targets, 1):
                name = e["name"]
                old = manifest.page(name)
                if old and old.get("status") in ("missing", "challenged", "error"):
                    continue
                if not _fetch_and_record(f, manifest, name):
                    continue
                new = manifest.page(name)
                if old and old.get("wiki_last_modified") == new.get("wiki_last_modified"):
                    continue
                changed.append(name)
                log.info("[%d/%d] 最后编辑时间变更 %s", i, len(full_targets), name)
        else:
            log.info("增量模式：依据 RSS 近期变更页检测…")
            recent = fetch_recent_changes(f)
            if recent:
                watch_names = {
                    e["name"] for e in auto_update_entries(registry)
                    if e.get("mode") == "watch"
                }
                for name in recent & watch_names:
                    old = manifest.page(name)
                    if old and old.get("status") in ("missing", "challenged", "error"):
                        continue
                    if not _fetch_and_record(f, manifest, name):
                        continue
                    new = manifest.page(name)
                    if old and old.get("wiki_last_modified") == new.get("wiki_last_modified"):
                        continue
                    changed.append(name)
                    log.info("RSS 变更页 %s", name)

    reprocess = sorted(set(planned_processed) | set(changed))
    if not reprocess:
        log.info("本轮无变更页面")
    else:
        log.info("检测到需重处理页面 %d 个", len(reprocess))
        parse_all(pages=reprocess, force=True)
        if any(e.get("category") == "character-detail" for e in registry if e["name"] in set(reprocess)):
            extract_all_characters(force=True)
        else:
            extract_all_characters()
        todo_files = _write_todo_for_changed(reprocess, by_name)
        if not no_translate:
            # 只把「本次变更页产出的那些清单」送去机翻，绝不扫整个待译目录。
            _run_zh_patch(todo_files=todo_files or None,
                          use_gtrans=not no_gtrans)
        else:
            log.info("已跳过翻译（--no-translate）")

    # 4) 补图 + 重新生成站点 + 刷新计划
    from .assets import download_assets
    download_assets()
    sync_site()
    sync_plan()  # 任意 registry 变化后保持 mirrored 同步

    manifest.data["last_update_run"] = utcnow_iso()
    manifest.save()
    log.info("自动更新完成：重处理 %d 页，站点已重新生成", len(reprocess))
