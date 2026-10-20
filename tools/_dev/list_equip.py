# -*- coding: utf-8 -*-
"""汇总装备详情页（equip-*.html / equip-*.json）清单。

- 结构取值：data/parsed/ja/equip-*.html 顶部信息表（保留外链文本，i18n json 会丢）
- 中文：data/parsed/i18n/equip-*.json 按「整行原文→zh」逐行套用；缺则查小词典或保留日文
输出：output/equipment_by_rarity.md
"""
import sys, json, pathlib, re
from collections import Counter, OrderedDict

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
JA = ROOT / "data" / "parsed" / "ja"
I18N = ROOT / "data" / "parsed" / "i18n"
OUT = ROOT / "output" / "equipment_by_rarity.md"

CAT_ZH = {
    "逸品装備": "逸品装备",
    "逸品サブ装備": "逸品副装备",
    "通常装備": "普通装备",
    "サブ装備": "副装备",
    "D2P装備": "D2P装备",
    "D2Pサブ装備": "D2P副装备",
    "D2Pサブ": "D2P副",
    "超昂装備": "超昂装备",
    "プレイヤー": "玩家",
    "プレイヤー装備": "玩家装备",
    "装備強化用アイテム": "装备强化用道具",
}
RAR_ZH = {"虹": "虹", "金": "金", "銀": "银", "銅": "铜"}
GET_EXTRA = {
    "D2Pガチャ": "D2P扭蛋",
    "D2Pガチャ(逸品)": "D2P扭蛋（逸品）",
    "D2Pガチャ（逸品）": "D2P扭蛋（逸品）",
    "宝箱・D2Pガチャ": "宝箱·D2P扭蛋",
    "D2Pガチャ、開発ラボ（トークン交換）、ショップなど": "D2P扭蛋、开发实验室（代币交换）、商店等",
    "超昂装備入手画面からアイテムを消費して入手": "从超昂装备获取界面消耗道具获得",
    "D2Pガチャ(逸品)レイドイベント『大往嬢』(第1回)の討伐報酬LV１": "D2P扭蛋（逸品）／Raid活动『大往嬢』（第1回）讨伐奖励 LV1",
}
EVENT_RE = re.compile(r"^イベント[「『](.*)[」』]\s*(.*)$")
EVENT_TAIL = {"交換品": "兑换品", "報酬": "奖励"}
CAT_ORDER = list(CAT_ZH)
RAR_ORDER = ["虹", "金", "銀", "銅"]
TAG_RE = re.compile(r"<[^>]+>")


def text_of(html):
    s = re.sub(r"<br[^>]*>", "\n", html)
    s = re.sub(r"</(p|div|li|tr|td|th)>", "\n", s)
    s = TAG_RE.sub("", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    s = s.replace("\u3000", " ")
    return s.strip()


def info_cells(html):
    first = html.split("<h2")[0]
    cells = re.findall(r"<(th|td)\b[^>]*>(.*?)</\1>", first, re.S)
    return [text_of(v) for _, v in cells]


def squeeze(s):
    return re.sub(r"\s*\n\s*", "", s or "")


def pick(cells, label):
    for i, t in enumerate(cells):
        if t == label:
            for j in range(i + 1, min(i + 3, len(cells))):
                if cells[j]:
                    return cells[j]
    return ""


def rank1_effect(cells):
    """RANK 表头可能是 装備効果 / 効果（超昂装備），取其下第一个非数字单元格。"""
    for i, t in enumerate(cells):
        if t not in ("装備効果", "効果"):
            continue
        prev = next((cells[j] for j in range(i - 1, -1, -1) if cells[j]), "")
        if t != "装備効果" and prev not in ("RANK", "成長必要個数", "効果"):
            continue
        for j in range(i + 1, min(i + 8, len(cells))):
            v = cells[j]
            if not v or re.fullmatch(r"[\d\-\s]+", v):
                continue
            if v in ("特殊効果", "効果", "装備効果", "性能", "RANK", "累計"):
                continue
            return v
    return ""


def kv_map(obj):
    m = {}
    for _, v in obj.items():
        if not isinstance(v, dict):
            continue
        ja = (v.get("ja") or "").strip()
        zh = (v.get("zh") or "").strip()
        if ja and zh and ja not in m:
            m[ja] = zh
    return m


def tr(raw, m):
    """逐行套译：整行精确命中→中文；活动名模式→中文；其余保留日文。"""
    out = []
    for ln in (raw or "").split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        if ln in GET_EXTRA:
            out.append(GET_EXTRA[ln])
            continue
        if ln in m:
            out.append(m[ln])
            continue
        e = EVENT_RE.match(ln)
        if e:
            tail = e.group(2).strip()
            for ja, zh in EVENT_TAIL.items():
                if tail.endswith(ja):
                    tail = tail[: -len(ja)] + zh
                    break
            out.append(f"活动「{e.group(1)}」" + tail)
            continue
        out.append(ln)
    return "<br>".join(out)


def esc(s):
    return re.sub(r"\s*\n\s*", "<br>", (s or "").strip()).replace("|", "\\|")


def main():
    pages = []
    for p in sorted(JA.glob("equip-*.html")):
        slug = p.stem
        cells = info_cells(p.read_text(encoding="utf-8"))
        name = squeeze(pick(cells, "名称"))
        cat = squeeze(pick(cells, "分類"))
        rar = squeeze(pick(cells, "レア"))
        get = pick(cells, "入手方法")
        eff = rank1_effect(cells)
        m = kv_map(json.loads((I18N / (slug + ".json")).read_text(encoding="utf-8")))
        name_zh = m.get(name, "")
        pages.append({
            "slug": slug,
            "name": name,
            "name_zh": name_zh,
            "has_any_zh": bool(m.get(name) or m.get(cat) or m.get(rar)),
            "cat": cat,
            "cat_zh": CAT_ZH.get(cat, ""),
            "rar": rar,
            "get": get,
            "get_zh": tr(get, m),
            "eff": eff,
            "eff_zh": tr(eff, m),
        })

    def cat_key(x):
        c = x["cat"] or "?"
        return (CAT_ORDER.index(c) if c in CAT_ORDER else len(CAT_ORDER), x["slug"])

    buckets = OrderedDict()
    for r in RAR_ORDER:
        buckets[r] = sorted([x for x in pages if x["rar"] == r], key=cat_key)
    other = [x for x in pages if x["rar"] not in RAR_ORDER]
    if other:
        buckets["未标注"] = sorted(other, key=cat_key)

    L = ["# ESCAH 装备详情页清单（按稀有度汇总）", ""]
    L.append(f"来源：`data/parsed/i18n/equip-*.json` + `data/parsed/ja/equip-*.html`（共 {len(pages)} 页）；字段取自各页顶部信息表，效果取 Rank1。")
    L.append("")

    rar_cnt = Counter(x["rar"] for x in pages)
    L += ["| 稀有度 | 中文 | 页数 |", "| --- | --- | --- |"]
    for r in RAR_ORDER + (["未标注"] if other else []):
        L.append(f"| {r} | {RAR_ZH.get(r, '—')} | {rar_cnt.get(r, 0)} |")
    L.append(f"| 合计 | | {len(pages)} |")
    L.append("")

    cat_cnt = Counter(x["cat"] for x in pages)
    L += ["| 分類 | 中文 | 页数 |", "| --- | --- | --- |"]
    for c in sorted(cat_cnt, key=lambda c: (CAT_ORDER.index(c) if c in CAT_ORDER else 99, c)):
        L.append(f"| {c or '（空）'} | {CAT_ZH.get(c, '—')} | {cat_cnt[c]} |")
    L.append("")

    for r, rows in buckets.items():
        if not rows:
            continue
        L.append(f"## {r + f'（{len(rows)}）' if r != '未标注' else f'未标注（{len(rows)}）'}")
        L.append("")
        L += ["| # | 页面 | 名称 | 中文名 | 分類 | 入手方法 | Rank1 效果 |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
        for i, x in enumerate(rows, 1):
            cat = x["cat"] + (f"（{x['cat_zh']}）" if x["cat_zh"] and x["cat_zh"] != x["cat"] else "")
            name_zh = x["name_zh"] if (x["name_zh"] and x["name_zh"] != x["name"]) else "—"
            cells = [str(i), x["slug"], x["name"] or "—", name_zh,
                     cat or "—", x["get_zh"] or "—", x["eff_zh"] or "—"]
            L.append("| " + " | ".join(esc(c) for c in cells) + " |")
        L.append("")

    no_zh = [x for x in pages if not x["has_any_zh"]]
    name_no_zh = [x for x in pages if x["has_any_zh"] and (not x["name_zh"] or x["name_zh"] == x["name"])]
    if no_zh or name_no_zh:
        L += ["## 备注", ""]
    if no_zh:
        L.append("以下页面 i18n 译文仍全空（名称/分类/稀有度都无中文），表中只列日文原文：")
        L.append("")
        L.append("、".join(f"`{x['slug']}`（{x['name']}）" for x in no_zh))
        L.append("")
    if name_no_zh:
        L.append("以下页面其余字段已译，但装备名本身没有中文译文：")
        L.append("")
        L.append("、".join(f"`{x['slug']}`（{x['name']}）" for x in name_no_zh))
        L.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")

    print("页数:", len(pages))
    for r in RAR_ORDER:
        print(f"  {r}: {len(buckets[r])}")
    print("名称缺中文:", [x["slug"] for x in pages if not x["name_zh"]])
    print("入手方法仍含日文:", [x["slug"] for x in pages if re.search(r"[ぁ-んァ-ン]", x["get_zh"])])
    print("取不到名称:", [x["slug"] for x in pages if not x["name"]])
    print("取不到效果:", [x["slug"] for x in pages if not x["eff"]])
    print("输出:", OUT)


if __name__ == "__main__":
    main()
