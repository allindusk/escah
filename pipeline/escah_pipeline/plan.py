"""镜像计划配置：planned / mirrored 分组有序清单；最后编辑时间解析；RSS 近期变更。

- `mirror_plan.yaml` 是面向人与自动化的"计划/清单"视图：
  - `planned`：待镜像页面（字符串页名，或 {name, group} 对象），默认空。
  - `mirrored`：已镜像页面，按原 WIKI 导航分 11 组，组内保序。
- `pages.yaml` 仍是流水线机器侧真源；本模块通过 `sync_plan()` 保持一致。
"""
from __future__ import annotations

import re

import yaml

from . import config
from .fetcher import (
    FetchError,
    PoliteFetcher,
    is_challenge_page,
    page_url,
    parse_wiki_lastmod,
)
from .logutil import get_logger
from .registry import _fallback_slug, href_to_page_name, load_registry, save_registry

log = get_logger()

# 原 WIKI 导航分组（权威顺序）
GROUP_ORDER = [
    "ゲームガイド", "キャラクター一覧", "キャラクター一覧SSR", "キャラクター一覧SR",
    "キャラクター一覧R", "キャラクター一覧サポーター", "キャラクター一覧NPC",
    "システム", "装備･アイテム", "クエスト･ミッション", "その他",
]

# 列表页 slug -> 分组（这些页在 registry 中 category 同为 "character"）
LIST_SLUG_GROUP = {
    "list-ssr": "キャラクター一覧SSR",
    "list-sr": "キャラクター一覧SR",
    "list-r": "キャラクター一覧R",
    "list-supporter": "キャラクター一覧サポーター",
    "list-npc": "キャラクター一覧NPC",
}

# 角色详情页 rarity -> 分组
RARITY_GROUP = {
    "SSR": "キャラクター一覧SSR",
    "SR": "キャラクター一覧SR",
    "R": "キャラクター一覧R",
    "サポーター": "キャラクター一覧サポーター",
    "NPC": "キャラクター一覧NPC",
}

# 其余 category -> 分组
CATEGORY_GROUP = {
    "guide": "ゲームガイド",
    "system": "システム",
    "equipment": "装備･アイテム",
    "quest": "クエスト･ミッション",
    "misc": "その他",
    "character": "キャラクター一覧",
}

_RARITY_FROM_GROUP = {
    "キャラクター一覧SSR": "SSR",
    "キャラクター一覧SR": "SR",
    "キャラクター一覧R": "R",
    "キャラクター一覧サポーター": "サポーター",
    "キャラクター一覧NPC": "NPC",
}


def page_group(entry: dict) -> str:
    """依据 registry 条目的 category / slug / rarity 映射到 11 组之一。"""
    category = entry.get("category")
    slug = entry.get("slug", "")
    if category == "character-detail":
        return RARITY_GROUP.get(entry.get("rarity"), "キャラクター一覧")
    if slug in LIST_SLUG_GROUP:
        return LIST_SLUG_GROUP[slug]
    if category == "character":
        return "キャラクター一覧"
    return CATEGORY_GROUP.get(category, "その他")


def _normalize_planned(item) -> tuple[str | None, str | None]:
    """把 planned 条目规范化为 (页名, 分组)。支持字符串或 {name, group}，并解析 URL。"""
    if isinstance(item, str):
        name = item
        group = None
    elif isinstance(item, dict):
        name = item.get("name") or item.get("page") or item.get("url")
        group = item.get("group")
    else:
        return None, None
    if not name:
        return None, None
    # 可能是 URL，提取页面名
    parsed = href_to_page_name(name)
    if parsed:
        name = parsed
    name = name.strip()
    return name, group


def _group_to_entry(name: str, group: str | None) -> dict:
    """依据目标分组生成 registry 条目（planned 处理时注册用）。"""
    entry: dict = {"name": name, "mode": "watch"}
    if group in RARITY_GROUP.values():
        entry.update({
            "category": "character-detail",
            "rarity": _RARITY_FROM_GROUP[group],
            "slug": f"characters/{name}",
        })
    elif group == "キャラクター一覧":
        entry.update({"category": "character", "slug": _fallback_slug(name)})
    elif group == "ゲームガイド":
        entry.update({"category": "guide", "slug": _fallback_slug(name)})
    elif group == "システム":
        entry.update({"category": "system", "slug": _fallback_slug(name)})
    elif group == "装備･アイテム":
        entry.update({"category": "equipment", "slug": _fallback_slug(name)})
    elif group == "クエスト･ミッション":
        entry.update({"category": "quest", "slug": _fallback_slug(name)})
    else:
        entry.update({"category": "misc", "slug": _fallback_slug(name)})
    return entry


# ---------------------------------------------------------------------------
# mirror_plan.yaml 读写
# ---------------------------------------------------------------------------

def load_mirror_plan() -> dict:
    if not config.MIRROR_PLAN_FILE.exists():
        return {"planned": [], "mirrored": {}}
    data = yaml.safe_load(config.MIRROR_PLAN_FILE.read_text(encoding="utf-8"))
    if not data:
        return {"planned": [], "mirrored": {}}
    data.setdefault("planned", [])
    data.setdefault("mirrored", {})
    return data


def save_mirror_plan(plan: dict) -> None:
    config.MIRROR_PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.MIRROR_PLAN_FILE.write_text(
        yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def build_mirror_plan(registry: list[dict], planned: list) -> dict:
    """从 registry 重建 mirrored（按 11 组分组、组内保序），保留传入的 planned。"""
    mirrored: dict[str, list[dict]] = {g: [] for g in GROUP_ORDER}
    for e in registry:
        group = page_group(e)
        mirrored.setdefault(group, []).append({
            "name": e["name"],
            "slug": e.get("slug", ""),
            "url": page_url(e["name"]),
        })
    return {"planned": planned, "mirrored": mirrored}


def sync_plan() -> dict:
    """以 registry 为权威重建 mirrored，保留现有 planned（供 discover/update 末尾调用）。"""
    registry = load_registry()
    plan = load_mirror_plan()
    built = build_mirror_plan(registry, plan.get("planned", []))
    save_mirror_plan(built)
    log.info(
        "镜像计划已同步：planned %d 项，mirrored %d 页（%d 组）",
        len(built["planned"]),
        sum(len(v) for v in built["mirrored"].values()),
        len(built["mirrored"]),
    )
    return built


# ---------------------------------------------------------------------------
# RSS 近期变更（PukiWiki ?cmd=rss，RSS 1.0）
# ---------------------------------------------------------------------------

_RSS_ITEM_RE = re.compile(
    r"<item[^>]*>.*?<title>(.*?)</title>.*?<dc:date>(.*?)</dc:date>",
    re.S | re.I,
)


def fetch_recent_changes(fetcher: PoliteFetcher, limit_days: int | None = None) -> set[str]:
    """抓取并解析 WIKI 的 RecentChanges（RSS），返回近期变更页名集合。

    用于每日增量更新：只重处理这些页，避免轮询全部 ~2400 页。
    解析失败（海外验证 / 网络错误）时返回空集，调用方退化为无变更。
    """
    url = f"{config.SOURCE_BASE}?cmd=rss"
    try:
        resp = fetcher.get(url)
    except FetchError as err:
        log.warning("抓取 RSS 失败：%s", err)
        return set()
    text = resp.content.decode(resp.encoding or "utf-8", errors="replace")
    if is_challenge_page(text):
        log.warning("RSS 触发海外验证，跳过近期变更检测")
        return set()
    names: set[str] = set()
    for m in _RSS_ITEM_RE.finditer(text):
        title = m.group(1).strip()
        # 标题可能含 HTML 实体或 URL 编码
        title = re.sub(r"<[^>]+>", "", title)
        try:
            from urllib.parse import unquote_plus
            title = unquote_plus(title)
        except Exception:  # noqa: BLE001
            pass
        if title:
            names.add(title)
    log.info("RSS 近期变更页 %d 个", len(names))
    return names
