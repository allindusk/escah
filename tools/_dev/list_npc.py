# -*- coding: utf-8 -*-
"""导出 NPC 详情页清单。

归属判定：`data/parsed/characters/<名>.json` 顶层 `rarity == "NPC"`。
该字段由 registry 从原站「NPC」目录页收录时写入（见 registry.CHAR_DIR_SECTIONS），
与「サポーター」同属全站不弹角色浮窗的两类。

数据源：
  - 资料：同文件 プロフィール 表（名前/本名/所属勢力/CV/イラスト/レアリティ）
  - 中文名：顶层 name_zh，缺失时回退 glossary/characters_generated.yaml
输出：output/npc_characters.md
"""
import json
import pathlib
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
PARSED = ROOT / "data" / "parsed" / "characters"
GEN = ROOT / "glossary" / "characters_generated.yaml"
OUT = ROOT / "output" / "npc_characters.md"

BLOCKS = [("必殺技", "必杀技"), ("固有効果", "固有效果"),
          ("基本ステータス", "基本属性"), ("詳細ステータス", "详细属性"),
          ("入手方法", "入手方法")]


def load_generated_names():
    m = {}
    if not GEN.exists():
        return m
    for line in GEN.read_text(encoding="utf-8").splitlines():
        if not line.startswith(" "):
            continue
        mm = re.match(r"^  (.+?):\s*(.*)$", line)
        if mm and mm.group(2).strip():
            m[mm.group(1).strip()] = mm.group(2).strip()
    return m


def clean(s):
    """单元格文本：多行合并、去首尾空白。"""
    return re.sub(r"\s*\n\s*", "\n", (s or "").strip()).strip()


def read_page(name):
    d = json.loads((PARSED / (name + ".json")).read_text(encoding="utf-8"))
    prof = {}
    for k, sec in (d.get("sections") or {}).items():
        if "プロフィール" not in k:
            continue
        for row in sec.get("rows", []):
            if len(row) < 2:
                continue
            head = clean(row[0].get("t"))
            prof.setdefault(head, clean(row[1].get("t")))
        break
    blocks = [zh for ja, zh in BLOCKS if (d.get("sections") or {}).get(ja)]
    return {"rarity": d.get("rarity"), "name_zh": d.get("name_zh") or "",
            "icon": d.get("icon") or "", "prof": prof, "blocks": blocks}


def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", "／")


def main():
    gen = load_generated_names()
    names = [p.stem for p in sorted(PARSED.glob("*.json"))]
    recs = []
    for n in names:
        pg = read_page(n)
        if pg["rarity"] != "NPC":
            continue
        recs.append({
            "ja": n,
            "zh": gen.get(n) or pg["name_zh"],
            "honmei": pg["prof"].get("本名", ""),
            "cv": pg["prof"].get("CV", ""),
            "force": pg["prof"].get("所属勢力", ""),
            "ill": pg["prof"].get("イラスト", ""),
            "table_rarity": pg["prof"].get("レアリティ", ""),
            "blocks": pg["blocks"],
            "icon": pg["icon"].split("/")[-1],
        })

    # 头像哈希共用检测（同 hash 多页 → 只有 1 个 NPX 时不算问题，仅提示核对）
    icon_count = Counter(r["icon"] for r in recs if r["icon"])
    for r in recs:
        shared = [x["ja"] for x in recs if x["icon"] and x["icon"] == r["icon"]]
        r["shared_icon"] = shared if len(shared) > 1 else []
        # NPC 目录页收录的页，自身レアリティ 行通常留空；非空即与原站归类不一致
        r["mismatch"] = bool(r["table_rarity"])

    lack_zh = [r["ja"] for r in recs if not r["zh"]]
    lack_honmei = [r["ja"] for r in recs if not r["honmei"]]
    lack_force = [r["ja"] for r in recs if not r["force"]]
    lack_cv = [r["ja"] for r in recs if not r["cv"]]
    mis = [r for r in recs if r["mismatch"]]
    shared = {h: c for h, c in icon_count.items() if c > 1}

    lines = ["# ESCAH NPC 详情页清单", ""]
    lines.append(
        f"归属判定：`data/parsed/characters/<名>.json` 顶层 `rarity == \"NPC\"`"
        f"（由原站「NPC」目录页收录时写入）。共 **{len(recs)}** 个 NPC 详情页；"
        "NPC 与サポーター一样全站不弹角色浮窗（`charRefs.json` 的 `noPopup`）。"
    )
    lines.append("")
    lines.append("详情页路径：中文站 `/zh/characters/<名>.html`，日文站 `/ja/characters/<名>.html`；"
                 "一览页 `list-npc`。")
    lines.append("")

    lines.append("## 汇总")
    lines.append("")
    lines.append("| 项 | 数量 |")
    lines.append("| --- | --- |")
    lines.append(f"| NPC 详情页 | {len(recs)} |")
    for ja, zh in BLOCKS:
        c = sum(1 for r in recs if zh in r["blocks"])
        lines.append(f"| 含{zh}段落 | {c} |")
    lines.append(f"| 缺中文名 | {len(lack_zh)} |")
    lines.append(f"| 本名留空 | {len(lack_honmei)} |")
    lines.append(f"| 所属勢力留空 | {len(lack_force)} |")
    lines.append(f"| CV 留空 | {len(lack_cv)} |")
    lines.append(f"| 表内レアリティ与 NPC 归类不一致 | {len(mis)} |")
    lines.append(f"| 头像哈希被多页共用 | {len(shared)} 组 |")
    lines.append("")

    lines.append("## 清单")
    lines.append("")
    lines.append("| # | 日文名 | 中文名 | 本名 | CV | 所属勢力 | 内容块 | 详情页 | 备注 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for i, r in enumerate(recs, 1):
        notes = []
        if not r["zh"]:
            notes.append("缺中文名")
        if r["mismatch"]:
            notes.append("表内レアリティ＝" + r["table_rarity"].replace("\n", " "))
        if r["shared_icon"]:
            others = [x for x in r["shared_icon"] if x != r["ja"]]
            if others:
                notes.append("头像与 " + "／".join(others) + " 共用")
        cells = [
            str(i), r["ja"], r["zh"] or "—", r["honmei"] or "—", r["cv"] or "—",
            r["force"] or "—", "／".join(r["blocks"]) or "—",
            f"`characters/{r['ja']}.html`", "；".join(notes),
        ]
        lines.append("| " + " | ".join(esc(c) for c in cells) + " |")
    lines.append("")

    if mis:
        lines.append("## 归类不一致明细（原站资料问题，非镜像错误）")
        lines.append("")
        for r in mis:
            lines.append(f"- **{r['ja']}**：在「NPC」目录页被收录，但自身 プロフィール 表写的是「{r['table_rarity'].replace(chr(10), ' ')}」")
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")

    print("NPC 详情页:", len(recs))
    print("缺中文名:", lack_zh)
    print("本名留空:", lack_honmei)
    print("所属勢力留空:", lack_force)
    print("CV 留空:", lack_cv)
    print("表内レアリティ不一致:", [(r["ja"], r["table_rarity"].replace("\n", " ")) for r in mis])
    print("共用头像:", shared)
    print("输出:", OUT)


if __name__ == "__main__":
    main()
