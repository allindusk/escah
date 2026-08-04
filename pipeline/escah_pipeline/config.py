"""全局配置：路径常量、源站信息、抓取与翻译参数。"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PARSED_JA_DIR = DATA_DIR / "parsed" / "ja"
PARSED_CHAR_DIR = DATA_DIR / "parsed" / "characters"
ASSETS_IMG_DIR = DATA_DIR / "assets" / "img"
LOG_DIR = DATA_DIR / "logs"
REGISTRY_FILE = DATA_DIR / "registry" / "pages.yaml"
MIRROR_PLAN_FILE = DATA_DIR / "registry" / "mirror_plan.yaml"
MANIFEST_FILE = DATA_DIR / "manifest.json"

SITE_DIR = ROOT / "site"
SITE_JA_DIR = SITE_DIR / "ja"
SITE_ZH_DIR = SITE_DIR / "zh"
SITE_PUBLIC_DIR = SITE_DIR / "public"

# 站点词汇表（日→中）：仅含 UI 文案（页面标题 / 侧栏 / 角色悬浮窗分段标题），由 AI 维护。
GLOSSARY_FILE = ROOT / "glossary" / "terms.yaml"

SOURCE_BASE = "https://escalationheroines.wikiru.jp/"

# 站点 base，必须和 site/.vitepress/config.ts 的 base 保持一致。
# VitePress 侧用 process.env.BASE（node）；此处用 ESCAH_BASE（python），未设置时默认 /escah/。
# 正文内由 pipeline 生成的绝对链接（/zh/xxx.html）必须带此前缀，否则在 base 下解析为 404。
_SITE_BASE = (os.environ.get("ESCAH_BASE") or "/escah/").strip()
if not _SITE_BASE.startswith("/"):
    _SITE_BASE = "/" + _SITE_BASE
if not _SITE_BASE.endswith("/"):
    _SITE_BASE += "/"
SITE_BASE = _SITE_BASE

MENUBAR_PAGE = "MenuBar"
CHARLIST_PAGE = "キャラクター一覧"
RECENT_CHANGES_PAGE = "RecentChanges"

# ---- 礼貌抓取参数 ----
FETCH_MIN_INTERVAL = float(os.getenv("FETCH_MIN_INTERVAL", "2.0"))
FETCH_MAX_INTERVAL = float(os.getenv("FETCH_MAX_INTERVAL", "4.0"))
FETCH_BACKOFF_SECONDS = (10, 20, 40)  # 429/5xx 指数退避
FETCH_MAX_RETRIES = 3
FETCH_TIMEOUT = 30.0
USER_AGENT = os.getenv(
    "FETCH_UA",
    "escah-bilingual-mirror/0.1 (personal fan mirror; polite crawl)",
)

def ensure_dirs() -> None:
    for d in (
        RAW_DIR,
        PARSED_JA_DIR,
        PARSED_CHAR_DIR,
        ASSETS_IMG_DIR,
        LOG_DIR,
        REGISTRY_FILE.parent,
    ):
        d.mkdir(parents=True, exist_ok=True)
