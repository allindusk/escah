"""`probe`：**只抓一页**、只报告「拿到的是正文还是反爬等待页」。

为什么单独做这个命令（2026-10-19）：
  新分工是「CI 联网抓 raw / 本地离线镜像化」。但本机直连原站会被 Cloudflare
  无感 JS 挑战挡住（40 秒过不去，出口 IP 层面），而 **GitHub Actions 的出口同样是
  数据中心 IP** —— 能否穿过挑战是整个新分工的 go/no-go 前提，不值得等真跑一轮
  才发现。所以加一个「抓一页就完事」的探针：手工触发、30 秒内出结论、不写任何盘。

判定「拿到正文」用三个独立信号（任一不满足即视为未通过）：
  ① `is_challenge_page()` —— fetcher 的统一特征集（One moment, please / 少々お待ちください /
     request is being verified / window.location.reload）；
  ② PukiWiki 正文容器 `id="body"`；
  ③ 页面标题不含 Cloudflare 标题。

用法：
    python -m escah_pipeline.cli probe                 # HTTP 通道
    python -m escah_pipeline.cli probe --browser       # 真实浏览器（playwright+chromium）
    python -m escah_pipeline.cli probe --page キャラクター一覧 --cookie "cf_clearance=..."
"""
from __future__ import annotations

import re
import time

from . import config
from .fetcher import PoliteFetcher, is_challenge_page, page_url
from .logutil import get_logger

log = get_logger()

_BODY_RE = re.compile(r'id=["\']body["\']', re.I)
_CF_TITLE_RE = re.compile(r"<title>[^<]*(moment|just a moment|attention required|"
                          r"お待ちください)[^<]*</title>", re.I)


def _verdict(text: str, status: int | None, via: str) -> dict:
    challenge = bool(is_challenge_page(text))
    body = bool(_BODY_RE.search(text))
    cf_title = bool(_CF_TITLE_RE.search(text))
    ok = (not challenge) and body and (not cf_title) and len(text) > 5000
    return {
        "via": via,
        "status": status,
        "bytes": len(text),
        "challenge": challenge,
        "wiki_body": body,
        "cf_title": cf_title,
        "verdict": "PASS-拿到正文" if ok else "FAIL-未拿到正文（很可能是反爬/结构变化）",
        "sample": re.sub(r"\s+", " ", text[:300]),
    }


def _probe_http(page: str, cookie: "str | None" = None) -> dict:
    url = page_url(page)
    headers = {"Cookie": cookie} if cookie else None
    with PoliteFetcher() as f:
        resp = f.get(url, headers=headers)
    text = resp.content.decode(resp.encoding or "utf-8", errors="replace")
    out = _verdict(text, resp.status_code, "http")
    out["cf_ray"] = resp.headers.get("cf-ray", "")
    return out


def _probe_browser(page: str, cookie: "str | None" = None,
                   timeout: float = 45.0) -> dict:
    from changelog import _browser_get_text  # 复用同一套放行等待逻辑

    url = page_url(page)
    text = _browser_get_text(url, timeout=timeout, cookie=cookie)
    return _verdict(text, None, "browser(playwright+chromium)")


def run_probe(page: str = "キャラクター一覧", browser: bool = False,
              cookie: "str | None" = None, attempts: int = 3,
              wait: float = 6.0) -> dict:
    """抓一页并判定；失败时按 `attempts` 退避重试，仍失败且 `browser` 才起浏览器。"""
    last: dict = {}
    for i in range(max(1, attempts)):
        try:
            last = _probe_http(page, cookie=cookie)
        except Exception as err:  # noqa: BLE001 网络异常也算未通过
            last = {"via": "http", "status": None, "bytes": 0, "challenge": None,
                    "verdict": f"FAIL-请求异常：{err}", "sample": ""}
        log.info("[probe] HTTP 第 %d 次：%s（%s 字节）", i + 1, last.get("verdict"), last.get("bytes"))
        if str(last.get("verdict", "")).startswith("PASS"):
            return last
        if i < attempts - 1:
            time.sleep(wait * (i + 1))
    if browser:
        try:
            last = _probe_browser(page, cookie=cookie)
            log.info("[probe] 浏览器兜底：%s（%s 字节）", last.get("verdict"), last.get("bytes"))
            return last
        except Exception as err:  # noqa: BLE001 playwright 未装/起不来也算未通过
            last = {"via": "browser", "verdict": f"FAIL-浏览器通道异常：{err}", "bytes": 0}
            log.warning("[probe] 浏览器兜底失败：%s", err)
    log.warning("[probe] 结论：%s（源站 %s）", last.get("verdict"), config.SOURCE_BASE)
    return last


def cmd_probe(args) -> int:
    import json
    import os
    import sys

    cookie = getattr(args, "cookie", None) or os.environ.get("WIKIRU_COOKIE") or None
    out = run_probe(page=args.page, browser=args.browser, cookie=cookie,
                    attempts=getattr(args, "attempts", 3))
    print(json.dumps(out, ensure_ascii=False, indent=1))
    if str(out.get("verdict", "")).startswith("FAIL"):
        log.error("[probe] ❌ 未拿到正文 —— CI 抓取方案暂不可行："
                  "需要 WIKIRU_COOKIE（浏览器里的 cf_clearance）或更强的浏览器通道")
        return 2
    log.info("[probe] ✅ 抓到正文，这条抓取通道可用")
    return 0


if __name__ == "__main__":
    sys.exit(0)
