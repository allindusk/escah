"""图片资源下载：pending_assets.json 中的 URL → data/assets/img/<hash>.<ext>（去重、断点续传）。"""
from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import config
from .fetcher import FetchError, PoliteFetcher, is_challenge_page
from .logutil import get_logger
from .snapshot import Manifest, sha256_bytes

log = get_logger()

# 镜像自身的本地化图片路径（parse 把正文 <img src> 改写成它）
_MIRROR_SRC_RE = re.compile(r"/img/([0-9a-f]{8,}\.[a-z0-9]+)$")


def _is_self_referential(url: str) -> bool:
    """源地址是不是「镜像自己的本地化图片路径」（`…/img/<hash>.<ext>`）。

    `/img/` 是**镜像的命名空间**（parse 把正文 <img src> 改写成它），源站没有这个路径，
    请求必然 404。这类记录来自 `urljoin(SOURCE_BASE, "/img/x.png")`，而 pending_assets.json
    只增不删 → 会永久残留、每次同步重试一遍（实测 172 条常驻、刷 172 行 ERROR、多花约 35s）。

    安全性核查（tools/_dev/diag_assets_refs.py）：这 172 个目标文件名在
    data/parsed/i18n 模板、data/parsed/ja 片段、site md 里**零引用**，
    图片本体也已在本地（早期命名是 `sha256(原始URL)[:16]`，与现在的记录名不同）→ 可安全清理。
    """
    return bool(_MIRROR_SRC_RE.search(url))


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

    # ① 先剔除「永远下不下来」的陈旧记录并落盘（必须在下面的 early-return 之前，
    #    否则当没有新图要下时，清理结果不会写回去，下次仍然重试 → 永久残留）。
    stale = [u for u in pending if _is_self_referential(u)]
    if stale and not force:
        for u in stale:
            pending.pop(u, None)
        pending_path.write_text(json.dumps(pending, ensure_ascii=False, indent=1), encoding="utf-8")
        log.warning("清理 %d 条陈旧记录：源地址是镜像自身 /img/ 路径（永远 404，图片本地已有）", len(stale))

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
