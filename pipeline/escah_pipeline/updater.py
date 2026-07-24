"""自动更新：处理 planned 镜像 → 依"最后编辑时间"(RSS/--full)检测变更 → 重抓/重解析/zh_patch → 刷新计划。

翻译统一走 tools/zh_patch.py（词典确定性替换）。
"""
from __future__ import annotations

import os
import subprocess
import sys

from . import config
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
from .registry import load_registry, save_registry
from .sitegen import sync_site
from .snapshot import Manifest, save_snapshot, utcnow_iso

log = get_logger()


def _run_zh_patch() -> None:
    """以子进程运行 tools/zh_patch.py（词典确定性替换）。"""
    cmd = [sys.executable, str(config.ROOT / "tools" / "zh_patch.py")]
    log.info("运行 zh_patch 生成中文镜像页…")
    subprocess.run(
        cmd,
        cwd=str(config.ROOT),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        check=False,
    )


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


def _process_planned(by_name: dict) -> list[str]:
    """处理 mirror_plan.yaml 中的 planned 条目：镜像+注册+翻译，成功后移入 mirrored。

    返回本次成功处理的页名列表（需重解析/重翻译）。
    """
    plan = load_mirror_plan()
    planned = plan.get("planned", [])
    if not planned:
        return []
    remaining = []
    processed: list[str] = []
    with PoliteFetcher() as f:
        manifest = Manifest()
        for item in planned:
            name, group = _normalize_planned(item)
            if not name:
                remaining.append(item)
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

    if processed:
        save_registry(list(by_name.values()))
        new_plan = load_mirror_plan()
        new_plan["planned"] = remaining
        save_mirror_plan(new_plan)
        sync_plan()  # 重建 mirrored，使新页落入对应分组
        log.info("planned 处理完成 %d 页，剩余 %d 页待处理", len(processed), len(remaining))
    return processed


def run_update(no_translate: bool = False, full: bool = False) -> None:
    """自动更新主流程。

    1) 处理 planned；2) 检测变更（默认 RSS 近期变更，--full 逐页最后编辑时间）；
    3) 仅重处理变更页（重抓→重解析→重抽角色→zh_patch）；4) 补图→sync-site→刷新计划→写 manifest。
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
            # 仅检查 mode=watch 且在册非缺失/非挑战页
            for i, e in enumerate(registry, 1):
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
                log.info("[%d/%d] 最后编辑时间变更 %s", i, len(registry), name)
        else:
            log.info("增量模式：依据 RSS 近期变更页检测…")
            recent = fetch_recent_changes(f)
            if recent:
                watch_names = {
                    e["name"] for e in registry if e.get("mode") == "watch"
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
        if not no_translate:
            _run_zh_patch()
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
