"""角色详情页结构化提取：六个信息区 → data/parsed/characters/<name>.json（悬浮窗数据源）。

提取为通用行结构（th/td 单元格序列），不假设各角色页面版式完全一致；
缺失的信息区直接省略。文本保持日文原文，中文由翻译流水线补写 zh 字段。
"""
from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from . import config
from .logutil import get_logger
from .parser_puki import needs_translation, safe_id
from .registry import extract_characters, load_registry
from . import i18n
from .snapshot import page_filename

log = get_logger()

SECTION_KEYS = ("プロフィール", "入手方法", "基本ステータス", "詳細ステータス", "必殺技", "固有効果")

# 私用区哨兵：用于把 <br> 先替换为占位符，get_text 后再切回换行，
# 从而在收拢空白的同时保留原始 <br> 换行（必殺技/固有効果 多为多行文本）。
_BR_SENTINEL = "\uE000"


def _cell_text(c) -> str:
    """提取单元格文本：保留 <br> 换行（切为多行），逐行收拢多余空白。

    此前用 c.get_text(" ", strip=True) 会把 <br> 也当空白吞掉，导致必殺技/
    固有効果 里本应分两行的文本被合并成一行；浮窗与详情页表现不一致。
    """
    for br in c.find_all("br"):
        br.replace_with(_BR_SENTINEL)
    raw = c.get_text(" ", strip=True)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in raw.split(_BR_SENTINEL)]
    return "\n".join(ln for ln in lines if ln)


def _section_key_of(text: str) -> str | None:
    for key in SECTION_KEYS:
        if text.startswith(key):
            return key
    return None


def extract_character(name: str, raw_html: str) -> dict | None:
    """从角色详情页提取六个信息区。返回 None 表示结构不匹配。"""
    soup = BeautifulSoup(raw_html, "lxml")
    body = soup.select_one("#body")
    if body is None:
        return None

    sections: dict[str, dict] = {}
    for th in body.find_all("th"):
        key = _section_key_of(th.get_text(strip=True))
        if key is None or key in sections:
            continue
        tr = th.find_parent("tr")
        table = th.find_parent("table")
        if tr is None or table is None:
            continue
        rows = table.find_all("tr")
        try:
            start = next(i for i, r in enumerate(rows) if r is tr)
        except StopIteration:
            continue
        out_rows: list[list[dict]] = []
        for r in rows[start + 1:]:
            # 遇到下一个信息区表头则结束
            r_ths = r.find_all("th", recursive=False)
            if any(_section_key_of(t.get_text(strip=True)) for t in r_ths):
                break
            cells: list[dict] = []
            for c in r.find_all(["th", "td"], recursive=False):
                text = _cell_text(c)
                has_img = c.find("img") is not None
                if has_img and not text:
                    continue  # 立绘单元格不进入悬浮窗（纯文本要求）
                cell = {"h": c.name == "th", "t": text}
                if c.get("colspan"):
                    cell["cs"] = int(c["colspan"])
                if c.get("rowspan"):
                    cell["rs"] = int(c["rowspan"])
                if needs_translation(text):
                    cell["tr"] = True
                cells.append(cell)
            if cells:
                out_rows.append(cells)
        sections[key] = {"label": th.get_text(strip=True), "rows": out_rows}

    if not sections:
        return None
    return {"name": name, "sections": sections}


def extract_all_characters(force: bool = False) -> None:
    """批量提取全部角色详情页 → data/parsed/characters/*.json。"""
    config.ensure_dirs()
    entries = [e for e in load_registry() if e.get("category") == "character-detail"]
    # 头像本地名（img/<sha256>）以当前命名规则从「キャラクター一覧」快照重算，
    # 修正 pages.yaml 中残留的旧命名（attach2/<hex>）导致浮窗头像 404 的问题。
    icon_map: dict[str, str] = {}
    charlist_raw = config.RAW_DIR / page_filename(config.CHARLIST_PAGE)
    if charlist_raw.exists():
        try:
            for c in extract_characters(charlist_raw.read_text(encoding="utf-8", errors="replace")):
                icon_map[c["name"]] = c["icon"]
        except Exception as err:  # noqa: BLE001
            log.warning("重算角色头像本地名失败：%s", err)
    ok = failed = skipped = 0
    for i, e in enumerate(entries, 1):
        name = e["name"]
        raw_path = config.RAW_DIR / page_filename(name)
        if not raw_path.exists():
            continue
        out_path = config.PARSED_CHAR_DIR / f"{safe_id(name)}.json"
        if out_path.exists() and not force:
            skipped += 1
            continue
        try:
            data = extract_character(name, raw_path.read_text(encoding="utf-8", errors="replace"))
        except Exception as err:  # noqa: BLE001
            failed += 1
            log.error("[%d/%d] 角色提取异常 %s：%s", i, len(entries), name, err)
            continue
        if data is None:
            failed += 1
            log.warning("[%d/%d] 角色信息区未匹配 %s", i, len(entries), name)
            continue
        data["rarity"] = e.get("rarity")
        data["icon"] = icon_map.get(name) or e.get("icon")
        data["name_zh"] = i18n.name_zh(name)
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        ok += 1
    log.info("角色提取完成：成功 %d，跳过 %d，失败 %d", ok, skipped, failed)
