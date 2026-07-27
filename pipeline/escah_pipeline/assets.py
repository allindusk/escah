"""图片资源下载：pending_assets.json 中的 URL → data/assets/img/<hash>.<ext>（去重、断点续传）。"""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import config
from .fetcher import FetchError, PoliteFetcher, is_challenge_page
from .logutil import get_logger
from .snapshot import Manifest, sha256_bytes

log = get_logger()


def _download_one(url: str, filename: str, path) -> tuple:
    """下载单张图片（可在独立线程运行）。返回 (url, filename, sha_or_None, ok, err)。"""
    try:
        with PoliteFetcher() as f:
            resp = f.get(url)
    except FetchError as err:
        return (url, filename, None, False, str(err))
    ctype = resp.headers.get("content-type", "")
    if "image" not in ctype and len(resp.content) < 1024:
        text = resp.content.decode(resp.encoding or "utf-8", errors="replace")
        if is_challenge_page(text):
            return (url, filename, None, False, "challenge")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    return (url, filename, sha256_bytes(resp.content), True, None)


def download_assets(force: bool = False) -> None:
    config.ensure_dirs()
    pending_path = config.DATA_DIR / "pending_assets.json"
    if not pending_path.exists():
        log.warning("没有待下载图片（先运行 parse）")
        return
    pending: dict[str, str] = json.loads(pending_path.read_text(encoding="utf-8"))

    todo = []
    for url, filename in pending.items():
        path = config.ASSETS_IMG_DIR / filename
        if path.exists() and not force:
            continue
        todo.append((url, filename, path))
    log.info("待下载图片 %d / %d", len(todo), len(pending))
    if not todo:
        return

    manifest = Manifest()
    ok = failed = 0
    workers = max(4, round((os.cpu_count() or 4) * 0.8))  # 留约 20% CPU 不占满
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_download_one, url, filename, path) for (url, filename, path) in todo]
        for fut in as_completed(futures):
            url, filename, sha, success, err = fut.result()
            if not success:
                failed += 1
                log.error("图片下载失败 %s：%s", url, err)
                continue
            manifest.record_asset(url, sha, filename)
            ok += 1
            if ok % 50 == 0:
                log.info("已下载 %d 张…", ok)
                manifest.save()
    manifest.save()
    log.info("图片下载完成：成功 %d，失败 %d（线程池 workers=%d）", ok, failed, workers)
