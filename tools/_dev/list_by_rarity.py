# -*- coding: utf-8 -*-
"""按稀有度汇总角色清单。

数据源：
  - 名册：data/parsed/i18n/characters/*.json（450 个角色页）
  - 稀有度/本名：data/parsed/characters/<name>.json 的 プロフィール 表
  - 中文名：glossary/characters_generated.yaml 的 names（缺失则回退 characters.json 的 名前 行 zh）
输出：output/characters_by_rarity.md
"""
import sys, json, pathlib, re
from collections import Counter, OrderedDict

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]
I18N = ROOT / "data" / "parsed" / "i18n" / "characters"
PARSED = ROOT / "data" / "parsed" / "characters"
GEN = ROOT / "glossary" / "characters_generated.yaml"
OUT = ROOT / "output" / "characters_by_rarity.md"

RAR_RE = re.compile(r"^(SSR|SR|R)(（サポーター）)?$")


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


def parse_rarity_cell(text):
    """把「SSR\\n（サポーター）」这类单元格解析成 [(rarity, supporter, ver), ...]"""
    items = []
    pending_ver = None
    for raw in (text or "").split("\n"):
        tok = raw.strip().replace(" ", "").replace("\u3000", "")
        if not tok:
            continue
        m = RAR_RE.match(tok)
        if m:
            items.append({"rarity": m.group(1), "sup": bool(m.group(2)), "ver": pending_ver})
            pending_ver = None
            continue
        if "サポーター" in tok or "サポータ" in tok:
            if items:
                items[-1]["sup"] = True
            continue
        vm = re.match(r"^【(.+?)】$", tok)
        if vm:
            label = vm.group(1)
            if items:
                items[-1]["ver"] = items[-1]["ver"] or label
            else:
                pending_ver = label
            continue
        # 其它杂项（如 NPC 说明）忽略
    return items


def read_profile(name):
    p = PARSED / (name + ".json")
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    info = {"items": [], "honmei": "", "name_zh": "", "raw": ""}
    for k, sec in (data.get("sections") or {}).items():
        if "プロフィール" not in k:
            continue
        for row in sec.get("rows", []):
            if len(row) < 2:
                continue
            head = (row[0].get("t") or "").strip()
            if head == "レアリティ":
                info["raw"] = (row[1].get("t") or "").strip()
                info["items"] = parse_rarity_cell(info["raw"])
            elif head == "本名":
                info["honmei"] = (row[1].get("t") or "").strip()
            elif head == "名前":
                info["name_zh"] = (row[1].get("zh") or "").strip()
        break
    return info


def esc(s):
    return re.sub(r"\s*\n\s*", "／", s or "").replace("|", "\\|")


def main():
    gen = load_generated_names()
    roster = sorted(p.stem for p in I18N.glob("*.json"))
    buckets = OrderedDict((k, []) for k in ["SSR", "SR", "R", "未标注"])
    for ja in roster:
        info = read_profile(ja) or {}
        items = info.get("items") or []
        rec = {
            "ja": ja,
            "zh": gen.get(ja) or info.get("name_zh") or "",
            "honmei": info.get("honmei") or "",
            "items": items,
        }
        if not items:
            buckets["未标注"].append(rec)
            continue
        rec["primary"] = items[0]["rarity"]
        rec["sup"] = items[0]["sup"]
        buckets[items[0]["rarity"]].append(rec)

    def note(rec):
        bits = []
        if rec.get("sup"):
            bits.append("支援者")
        others = rec["items"][1:]
        if others:
            bits.append(
                "兼：" + "／".join(
                    (("【" + o["ver"] + "】") if o["ver"] else "") + o["rarity"] + ("（支援者）" if o["sup"] else "")
                    for o in others
                )
            )
        return "；".join(bits)

    lines = ["# ESCAH 角色清单（按稀有度汇总）", ""]
    lines.append(f"名册来源：`data/parsed/i18n/characters`（共 {len(roster)} 个角色页）；稀有度取自各页「基本情報」表的レアリティ行。")
    lines.append("")
    lines.append("| 稀有度 | 人数 | 其中支援者 |")
    lines.append("| --- | --- | --- |")
    total = 0
    for k, v in buckets.items():
        total += len(v)
        sup = sum(1 for r in v if r.get("sup")) if k != "未标注" else 0
        lines.append(f"| {k} | {len(v)} | {sup} |" if k != "未标注" else f"| {k} | {len(v)} | — |")
    lines.append(f"| 合计 | {total} | |")
    lines.append("")

    for k, v in buckets.items():
        if not v:
            continue
        if k == "未标注":
            lines.append(f"## {k}（{len(v)}，原站该行留空，非可抽卡角色或资料未填）")
        else:
            lines.append(f"## {k}（{len(v)}）")
        lines.append("")
        lines.append("| # | 日文名 | 中文名 | 本名 | 备注 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for i, r in enumerate(v, 1):
            cells = [str(i), r["ja"], r["zh"] or "—", r["honmei"] or "—", note(r) or ""]
            lines.append("| " + " | ".join(esc(c) for c in cells) + " |")
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")

    print("名册总数:", len(roster))
    for k, v in buckets.items():
        sup = sum(1 for r in v if r.get("sup"))
        print(f"  {k}: {len(v)}" + (f"（支援者 {sup}）" if k != "未标注" else ""))
    print("缺中文名:", sum(1 for v in buckets.values() for r in v if not r["zh"]))
    print("多形态稀有度页:", [r["ja"] for v in buckets.values() for r in v if len(r["items"]) > 1])
    print("输出:", OUT)


if __name__ == "__main__":
    main()
