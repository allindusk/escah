"""页面注册表：两阶段发现（MenuBar → 观察页；キャラクター一覧 → 角色详情页）与 pages.yaml 读写。"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import unquote_plus, urljoin, urlparse

import yaml
from bs4 import BeautifulSoup

from . import config
from .logutil import get_logger

log = get_logger()

# 用户明确的第一阶段清单（观察页），按分类
NAV_CATEGORIES: dict[str, list[str]] = {
    "guide": ["序盤の手引き", "よくある質問", "小ネタ・小ワザ集", "ガチャ"],
    "character": [
        "キャラクター一覧", "SSR", "SR", "R", "サポーター", "NPC",
        "必殺技一覧", "固有効果一覧", "特殊属性一覧", "寝室シーン一覧",
        "原画別索引", "CV一覧", "実装履歴",
    ],
    "system": [
        "戦闘",
        "レイド", "レイドおすすめキャラ", "レイドバフ・デバフ別キャラ一覧", "レイド用編成例",
        "Bユニバース（強敵戦）", "広域戦", "マップリスト", "殲滅戦",
        "限界突破", "覚醒強化", "レベル上限UP",
        "宝箱", "交換所", "キャラクター交換所", "コレクション", "ショップ（VIPランク）",
    ],
    "equipment": ["装備一覧", "超昂装備", "アイテム一覧", "[初心者用]アイテム価値早見表"],
    "quest": [
        "メインストーリー", "全シナリオ実装順", "メインクエスト",
        "デイリークエスト", "ミッション一覧", "イベント一覧",
    ],
    # ⚠️ 2026-09-27 用户约束：**左侧导航栏不允许新增镜像页**。
    #    原先这里被加进了「ゲーム外企画」「事前登録特典」，但 `sitegen._write_sidebars` 对
    #    `misc`（以及 `guide`）是**按 registry 原顺序平铺**的 —— 只要注册表里多一条，
    #    左侧栏就必然多一项 ✗。允许新增的只有**不进侧栏**的类型（character-detail /
    #    subpage，见 sitegen 里 `if e.get("category") in ("character-detail", "subpage"): continue`），
    #    也就是用户说的"角色页、装备页那种不在导航栏的"。
    #    因此本清单只保留**既有**导航页；`discover` 也据此只刷新、不新增（见 discover() 的注释）。
    "misc": ["用語集", "俗語集", "Tips一覧"],
}

# 站点路由 slug 映射（观察页用英文 slug；角色详情页用日文名）
SLUG_MAP: dict[str, str] = {
    "序盤の手引き": "getting-started",
    "よくある質問": "faq",
    "小ネタ・小ワザ集": "tips-tricks",
    "ガチャ": "gacha",
    "キャラクター一覧": "characters",
    "SSR": "list-ssr",
    "SR": "list-sr",
    "R": "list-r",
    "サポーター": "list-supporter",
    "NPC": "list-npc",
    "寝室シーン一覧": "bedroom-scenes",
    "必殺技一覧": "skills",
    "固有効果一覧": "unique-effects",
    "特殊属性一覧": "special-attributes",
    "原画別索引": "artists",
    "CV一覧": "voice-actors",
    "実装履歴": "release-history",
    "戦闘": "battle",
    "レイド": "raid",
    "レイドおすすめキャラ": "raid-recommended",
    "レイドバフ・デバフ別キャラ一覧": "raid-buff-debuff",
    "レイド用編成例": "raid-formations",
    "Bユニバース（強敵戦）": "b-universe",
    "広域戦": "wide-battle",
    "マップリスト": "map-list",
    "殲滅戦": "annihilation",
    "限界突破": "limit-break",
    "覚醒強化": "awakening",
    "レベル上限UP": "level-cap",
    "宝箱": "treasure-box",
    "交換所": "exchange",
    "キャラクター交換所": "character-exchange",
    "コレクション": "collection",
    "ショップ（VIPランク）": "shop",
    "装備一覧": "equipment",
    "超昂装備": "super-equipment",
    "アイテム一覧": "items",
    "[初心者用]アイテム価値早見表": "item-value-guide",
    "メインストーリー": "main-story",
    "全シナリオ実装順": "scenario-order",
    "メインクエスト": "main-quest",
    "デイリークエスト": "daily-quest",
    "ミッション一覧": "missions",
    "イベント一覧": "events",
    "用語集": "glossary",
    "俗語集": "slang",
    "Tips一覧": "tips",
    # 「ゲーム外企画」「事前登録特典」的 slug 于 2026-09-27 连同 NAV_CATEGORIES 里的条目一并移除：
    # 它们是**导航页**（会出现在左侧栏），属于"不允许新增"的那一类（见 NAV_CATEGORIES 注释）。
}

# 菜单名称与实际页面名的差异修正（实测 wikiru 站点结构 2026-07）
ALIAS_MAP: dict[str, str] = {
    "マップリスト": "広域戦マップ/マップリスト",
    "[初心者用]アイテム価値早見表": "SandBox/アイテム価値早見表",
    "全シナリオ実装順": "テーブル/全ストーリー実装順",
    "レイドバフ・デバフ別キャラ一覧": "バフ・デバフ能力キャラ　一覧まとめ",
    "Bユニバース（強敵戦）": "Bユニバース",
    "ショップ（VIPランク）": "ショップ",
    "広域戦": "イベント50_広域戦",
    "殲滅戦": "イベント86_殲滅戦",
    "特殊属性一覧": "絞り込めるカテゴリ一覧",
}

# 排除规则（默认不抓；可在 pages.yaml 中把对应页 include 设为 true 显式开启）
EXCLUDE_PATTERNS = [
    r"^コメント/", r"^テーブル/", r"掲示板", r"^はじめに", r"編集者",
    r"寝室シーン", r"^MenuBar$", r"^SideBar$", r"^ヘッダ", r"^フッタ",
    r"練習", r"雛形", r"^InterWiki", r"^RecentChanges", r"^最近の更新",
]
_EXCLUDE_RE = [re.compile(p) for p in EXCLUDE_PATTERNS]

RARITY_SECTIONS = ("SSR", "SR", "R")
_HEADING_RE = re.compile(r"^h[1-6]$", re.I)


def _is_excluded(name: str) -> bool:
    return any(r.search(name) for r in _EXCLUDE_RE)


def _norm(s: str) -> str:
    s = s.strip()
    for a, b in (("（", "("), ("）", ")"), ("・", ""), (" ", ""), ("　", "")):
        s = s.replace(a, b)
    return s.lower()


def _fallback_slug(name: str) -> str:
    return "p-" + hashlib.md5(name.encode("utf-8")).hexdigest()[:10]


# ============================================================================
# 自动更新排除（用户 2026-09-27 指示）
# ----------------------------------------------------------------------------
# 原站有个别页面**永远读不出「最終更新日時」**：典型是反爬挑战页 `公式ヘルプ`
# （实测 manifest 里 `status=challenged`、`wiki_last_modified=None`、sha256 是空串哈希）。
# 后果有两个，都不小：
#   ① 每轮 `sync-stale` / `sync-recent` 都会把它探测一遍 → 报成"失败" → 再进礼貌重试
#      白跑一次：报告里长期挂着假失败，真正的失败被淹没 ✗；
#   ② 它的内容**早已镜像完成**（raw 172 KB、i18n 562 KB，站点照常渲染、也在左侧栏里），
#      我们并不需要它的"更新" —— 继续探测只是徒增请求与噪声。
# 用 `no_auto_update: true` 标记这类页：**站点上照常渲染**，但不进入任何自动抓取/探测流程。
# 与 `update` 里"跳过 status=challenged"的区别：那是**隐式**的、依赖当轮抓取结果；
# 本标记是**显式**的站点配置，且同时挡住 `fetch --force`（否则一次强制重抓会把
# 已经镜像好的快照换成挑战页提示，虽然有 is_challenge_page 兜底，但没必要冒险）。
# ============================================================================
AUTO_UPDATE_FLAG = "no_auto_update"


def is_auto_update(entry: dict) -> bool:
    """该镜像页是否参与自动更新（抓取 / 变更探测）。"""
    return not entry.get(AUTO_UPDATE_FLAG)


def auto_update_entries(pages: "list[dict] | None" = None) -> list[dict]:
    """过滤出参与自动更新的注册表条目（默认取整张注册表）。"""
    src = load_registry() if pages is None else pages
    return [e for e in src if is_auto_update(e)]


def load_registry() -> list[dict]:
    if not config.REGISTRY_FILE.exists():
        return []
    data = yaml.safe_load(config.REGISTRY_FILE.read_text(encoding="utf-8"))
    return data.get("pages", []) if data else []


def save_registry(pages: list[dict]) -> None:
    config.REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "pages": pages}
    config.REGISTRY_FILE.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def href_to_page_name(href: str) -> str | None:
    """把 PukiWiki 链接（?ページ名 / ./?ページ名 / 绝对 URL）解析为页面名，非页面链接返回 None。"""
    href = href.strip()
    name: str | None = None
    if href.startswith("./?"):
        name = unquote_plus(href[3:])
    elif href.startswith("?"):
        name = unquote_plus(href[1:])
    else:
        u = urlparse(href)
        base = urlparse(config.SOURCE_BASE)
        if u.netloc == base.netloc and u.path == base.path and u.query and "=" not in u.query:
            name = unquote_plus(u.query)
    if not name:
        return None
    name = name.split("#")[0].strip()
    if not name or "&" in name or "=" in name:
        return None
    return name


def extract_wiki_links(html: str) -> dict[str, str]:
    """从 HTML 抽取 PukiWiki 站内页面链接：{页面名: 链接文本}（排除 ?cmd= 类参数链接）。"""
    soup = BeautifulSoup(html, "lxml")
    links: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        name = href_to_page_name(a["href"])
        if name is not None:
            links.setdefault(name, a.get_text(strip=True))
    return links


def _resolve_name(want: str, norm_to_actual: dict[str, str]) -> str | None:
    """仅做归一化精确匹配；命名差异一律走 ALIAS_MAP（避免前缀误合并）。"""
    return norm_to_actual.get(_norm(want))


def _img_local_name(src: str) -> str:
    """把 wiki 原始图片 src 转成本地存储名（与 sitegen._img_local_name 完全一致）：img/<sha256[:16]>.<ext>。

    角色头像图经 assets 管线以该名下载到 data/assets/img（构建进 dist/img）。
    浮窗组件据此路径 withBase('img/'+icon) 显示头像。
    """
    abs_url = urljoin(config.SOURCE_BASE, src)
    digest = hashlib.sha256(abs_url.encode()).hexdigest()[:16]
    m = re.search(r"\.([a-zA-Z0-9]+)$", src.rsplit("/", 1)[-1])
    ext = (m.group(1).lower() if m else "png")
    ext = re.sub(r"[^a-z0-9]", "", ext)[:5] or "png"
    return f"img/{digest}.{ext}"


def extract_characters(html: str) -> list[dict]:
    """从キャラクター一覧抽取 SSR/SR/R 分区内的角色：[{name, rarity, icon}]。

    角色页 = 分区内 <tr> 中含 <img> 的链接（头像链接），同行为名字链接与头像地址。
    """
    soup = BeautifulSoup(html, "lxml")
    content = soup.select_one("#body") or soup.body or soup
    characters: list[dict] = []
    seen: set[str] = set()
    rarity: str | None = None
    for el in content.descendants:
        tag = getattr(el, "name", None)
        if tag and _HEADING_RE.match(tag):
            text = re.sub(r"[^A-Za-z]", "", el.get_text(strip=True)).replace("edit", "")
            rarity = text if text in RARITY_SECTIONS else None
        elif tag == "tr" and rarity:
            img_link = el.find("a", href=True, attrs={"title": True})
            if img_link is None or img_link.find("img") is None:
                continue
            name = href_to_page_name(img_link["href"])
            if name is None or name in seen or _is_excluded(name):
                continue
            img = img_link.find("img")
            seen.add(name)
            characters.append({
                "name": name,
                "rarity": rarity,
                "icon": _img_local_name(img.get("src", "")),
            })
    return characters


def discover() -> None:
    """两阶段发现：抓取 MenuBar 解析导航 → 观察页；抓取キャラクター一覧 → 角色详情页。"""
    from .fetcher import PoliteFetcher, page_url
    from .snapshot import save_snapshot

    config.ensure_dirs()
    pages_by_name: dict[str, dict] = {p["name"]: p for p in load_registry()}

    with PoliteFetcher() as f:
        # ---- Phase 1: MenuBar → 观察页 ----
        log.info("Phase 1: 抓取 MenuBar 解析左侧导航…")
        resp = f.get(page_url(config.MENUBAR_PAGE))
        save_snapshot(config.MENUBAR_PAGE, resp.content)
        menubar_text = resp.content.decode(resp.encoding or "utf-8", errors="replace")
        links = extract_wiki_links(menubar_text)

        norm_to_actual: dict[str, str] = {}
        for name in links:
            norm_to_actual.setdefault(_norm(name), name)

        watch_count = 0
        skipped_new: list[str] = []
        for category, names in NAV_CATEGORIES.items():
            for want in names:
                want_resolved = ALIAS_MAP.get(want, want)
                actual = _resolve_name(want_resolved, norm_to_actual)
                if actual is None:
                    if want_resolved != want:
                        actual = want_resolved
                        log.info("「%s」按别名登记为「%s」", want, actual)
                    else:
                        actual = want
                # ⚠️ 2026-09-27 用户约束：**只刷新已登记的导航页，绝不新增**。
                #    上一版此处是 `entry = pages_by_name.get(actual, {})` —— 对未登记的
                #    MenuBar 页也会凭空建条目；而 `sitegen._write_sidebars` 对 `guide`/`misc`
                #    是"按 registry 原顺序平铺"，于是**注册表多一条 = 左侧导航栏多一项** ✗
                #    （实测就是这样混进了「ゲーム外企画」「事前登録特典」）。
                #    导航栏属于站点骨架，新增必须经人工确认（写进 pages.yaml）后才会被刷新；
                #    需要自动增长的只有不进侧栏的类型（character-detail / subpage，见 Phase 2）。
                if actual not in pages_by_name:
                    skipped_new.append(actual)
                    continue
                slug = SLUG_MAP.get(want) or SLUG_MAP.get(actual) or _fallback_slug(actual)
                entry = pages_by_name[actual]
                entry.update({
                    "name": actual,
                    "slug": slug,
                    "category": category,
                    "mode": "watch",
                })
                watch_count += 1
        log.info("Phase 1 完成：刷新观察页 %d 个", watch_count)
        if skipped_new:
            log.warning(
                "Phase 1 跳过 %d 个未登记的导航页（**不会**自动加入，避免左侧栏新增）——"
                "如确需镜像请人工确认后写入 %s：%s",
                len(skipped_new), config.REGISTRY_FILE.name, "、".join(skipped_new[:10]),
            )

        # ---- Phase 2: キャラクター一覧 → 角色详情页 ----
        log.info("Phase 2: 抓取「%s」解析 SSR/SR/R 角色链接…", config.CHARLIST_PAGE)
        resp2 = f.get(page_url(config.CHARLIST_PAGE))
        save_snapshot(config.CHARLIST_PAGE, resp2.content)
        charlist_text = resp2.content.decode(resp2.encoding or "utf-8", errors="replace")
        characters = extract_characters(charlist_text)
        char_count = 0
        for c in characters:
            name = c["name"]
            entry = pages_by_name.get(name, {})
            entry.update({
                "name": name,
                "slug": f"characters/{name}",
                "category": "character-detail",
                "mode": "static",
                "rarity": c["rarity"],
                "icon": c["icon"],
            })
            if name not in pages_by_name:
                char_count += 1
            pages_by_name[name] = entry
        log.info("Phase 2 完成：登记角色详情页 %d 个（累计 %d）", char_count, len(characters))

    save_registry(list(pages_by_name.values()))
    log.info("注册表已写入 %s（共 %d 页）", config.REGISTRY_FILE, len(pages_by_name))
