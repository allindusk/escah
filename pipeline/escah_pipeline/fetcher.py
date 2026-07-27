"""礼貌抓取器：限速 + 随机抖动、自定义 UA、429/5xx 指数退避（10/20/40 秒）、断点续抓。"""
from __future__ import annotations

import random
import re
import time
from urllib.parse import quote

import httpx

from . import config
from .logutil import get_logger

log = get_logger()


class FetchError(Exception):
    """抓取最终失败（重试耗尽或不可重试的状态码）。"""


def is_challenge_page(text: str) -> bool:
    """检测 Cloudflare Turnstile 海外验证页（不自动提交，标记后跳过）。"""
    return "cf-turnstile" in text or "海外からのアクセス" in text


def is_missing_page(text: str) -> bool:
    """检测 PukiWiki 页面不存在（限 #body 区域且内容极短，避免正文含相同短语的误报）。"""
    m = re.search(r'<div id="body">(.*?)<hr class="full_hr"', text, re.S)
    if not m:
        return False
    body = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    if len(body) > 300:
        return False
    return "ページが見つかりません" in body or "は存在しません" in body


def page_url(name: str) -> str:
    return f"{config.SOURCE_BASE}?{quote(name)}"


# WIKI 自身的"最后编辑时间"，存在于两处：
#   - <meta name="description" content="最終更新日時:YYYY-MM-DD (曜) HH:MM:SS...">
#   - <div id="lastmodified">Last-modified: YYYY-MM-DD (曜) HH:MM:SS<span ...>
# 两种形式都解析（兼容有无空格 / 是否含秒），保证全站覆盖。
LASTMOD_RE = re.compile(
    r"(?:最終更新日時|Last-modified):\s*"
    r"(\d{4}-\d{2}-\d{2})\s*\(.\d?\)\s*"
    r"(\d{1,2}:\d{2}(?::\d{2})?)"
)


def parse_wiki_lastmod(text: str) -> str | None:
    """从页面 HTML 提取 WIKI 最后编辑时间，返回 'YYYY-MM-DD HH:MM:SS' 或 None。"""
    m = LASTMOD_RE.search(text)
    if not m:
        return None
    return f"{m.group(1)} {m.group(2)}"


class PoliteFetcher:
    """带限速与退避重试的 HTTP 客户端。"""

    def __init__(self) -> None:
        self._client = httpx.Client(
            headers={
                "User-Agent": config.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,image/*;q=0.8,*/*;q=0.5",
                "Accept-Language": "ja,en;q=0.8",
            },
            follow_redirects=True,
            timeout=config.FETCH_TIMEOUT,
        )
        self._last_ts = 0.0

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PoliteFetcher":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _throttle(self) -> None:
        wait = random.uniform(config.FETCH_MIN_INTERVAL, config.FETCH_MAX_INTERVAL)
        delta = time.monotonic() - self._last_ts
        if delta < wait:
            time.sleep(wait - delta)
        self._last_ts = time.monotonic()

    def get(self, url: str) -> httpx.Response:
        last_err: Exception | None = None
        for attempt in range(config.FETCH_MAX_RETRIES + 1):
            self._throttle()
            try:
                resp = self._client.get(url)
            except httpx.HTTPError as e:
                last_err = e
                wait = config.FETCH_BACKOFF_SECONDS[
                    min(attempt, len(config.FETCH_BACKOFF_SECONDS) - 1)
                ]
                log.warning("请求异常 %s（%s），%d 秒后重试…", url, e, wait)
                time.sleep(wait)
                continue
            if resp.status_code == 200:
                return resp
            if resp.status_code in (429, 500, 502, 503, 504):
                wait = config.FETCH_BACKOFF_SECONDS[
                    min(attempt, len(config.FETCH_BACKOFF_SECONDS) - 1)
                ]
                log.warning(
                    "HTTP %d %s，%d 秒后重试（第 %d 次）…",
                    resp.status_code, url, wait, attempt + 1,
                )
                time.sleep(wait)
                last_err = FetchError(f"HTTP {resp.status_code}")
                continue
            raise FetchError(f"HTTP {resp.status_code}: {url}")
        raise FetchError(f"重试 {config.FETCH_MAX_RETRIES} 次后仍失败: {url} ({last_err})")


def fetch_registered_pages(
    force: bool = False, mode: str = "all", only: list[str] | None = None
) -> None:
    """按注册表抓取页面：已有快照默认跳过（断点续抓），--force 强制全量重抓。"""
    from .registry import load_registry
    from .snapshot import Manifest, page_filename, save_snapshot

    config.ensure_dirs()
    entries = load_registry()
    if mode != "all":
        entries = [e for e in entries if e.get("mode") == mode]
    if only:
        wanted = set(only)
        entries = [e for e in entries if e["name"] in wanted]
    if not entries:
        log.warning("注册表为空，请先运行 discover")
        return

    manifest = Manifest()
    ok = skipped = failed = 0
    with PoliteFetcher() as f:
        for i, e in enumerate(entries, 1):
            name = e["name"]
            path = config.RAW_DIR / page_filename(name)
            if path.exists() and not force:
                skipped += 1
                continue
            url = page_url(name)
            try:
                resp = f.get(url)
            except FetchError as err:
                failed += 1
                log.error("[%d/%d] 抓取失败 %s：%s", i, len(entries), name, err)
                manifest.record_page(name, url, b"", status="error", error=str(err))
                manifest.save()
                continue
            content = resp.content
            text = content.decode(resp.encoding or "utf-8", errors="replace")
            if is_challenge_page(text):
                failed += 1
                log.warning("[%d/%d] 触发海外验证，跳过 %s（需人工在浏览器完成一次验证）", i, len(entries), name)
                manifest.record_page(name, url, b"", status="challenged")
                manifest.save()
                continue
            save_snapshot(name, content)
            status = "ok"
            if is_missing_page(text):
                status = "missing"
                log.warning("[%d/%d] 页面不存在 %s", i, len(entries), name)
            manifest.record_page(
                name, url, content, status=status,
                http_last_modified=resp.headers.get("last-modified"),
                wiki_last_modified=parse_wiki_lastmod(text),
            )
            ok += 1
            log.info("[%d/%d] %s（%d KB）", i, len(entries), name, len(content) // 1024)
            if ok % 20 == 0:
                manifest.save()
    manifest.save()
    log.info("抓取完成：成功 %d，跳过 %d，失败 %d", ok, skipped, failed)
