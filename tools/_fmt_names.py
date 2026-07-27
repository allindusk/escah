#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 name_glossary_20260727 copy.txt（用户手工整理的名字大全，混合格式）
整理成标准 [N] 日文 格式（沿用 name_glossary_20260727.txt 的 # MAP / ===X=== 结构）。"""
from pathlib import Path
import re
import shutil

ROOT = Path(r"d:/D11_DeveloperProject/150_HTML_Project/escalation_heroines/escah")
SRC = ROOT / "tools/_todo_translate/name_glossary_20260727 copy.txt"
OLD = ROOT / "tools/_todo_translate/name_glossary_20260727.txt"
BAK = ROOT / "recycle_bin/tools/name_glossary_20260727.old.txt"

HEADER = (
    "【专有名词精译清单 / 専有名詞 厳密翻訳リスト】\n"
    "以下按类别汇集本站的专有名词。请将每条 [N] 后的日文专有名词翻译为中文，\n"
    "保持译名前后一致；不要翻译括号内的版本号/期数等说明文字；\n"
    "游戏通用术语（如 スタミナ、必殺技、アイテム）无需在此翻译。\n"
    "翻译后把 [N] 中文 写入同名 *_translated.txt（沿用 ===X=== 分段）。\n"
    "# MAP A=list-ssr B=list-sr C=list-r D=list-npc E=list-supporter F=items G=equipment H=treasure-box I=raid\n"
)

SECTION_HEADERS = {
    "D": "=== D ===  # NPC（源页面 list-npc）",
    "E": "=== E ===  # サポーター（支援者）（源页面 list-supporter）",
    "F": "=== F ===  # 道具（物品）（源页面 items）",
    "G": "=== G ===  # 装备（源页面 equipment）",
    "H": "=== H ===  # 宝箱掉落物（源页面 treasure-box）",
    "I": "=== I ===  # BOSS（レイドボス）（源页面 raid）",
}

# 分类哨兵：命中则切换当前分类（不输出该行本身，避免与 ===X=== 头重复）
SENTINELS = {
    "全部装备原名": "G",
    "道具名称": "F",
    "全部宝箱道具": "H",
    "レイドボス": "I",
    "全部サポーター": "E",
}

NOTE_KW = ["备注", "需要", "如果你", "文中", "补充", "？", "！", "对照表", "译名",
            "：", "；", "，", "／"]

raw = SRC.read_text(encoding="utf-8").split("\n")

sections = {c: [] for c in "DEFGHI"}      # letter -> 输出行列表
seen = {c: set() for c in "DEFGHI"}        # 分类内去重
char_blocks = {}                           # A/B/C -> 原始行（原样保留）
cur_cat = None
counter = 0
in_char = False
char_label = None


def is_note(s: str) -> bool:
    return any(k in s for k in NOTE_KW)


for line in raw:
    s = line.strip()
    if s == "":
        if in_char:
            char_blocks[char_label].append("")
        continue

    # 角色块标记 === A/B/C ===
    m = re.match(r"^===\s*([A-C])\s*===\s*(.*)$", s)
    if m:
        in_char = True
        char_label = m.group(1)
        char_blocks[char_label] = [line.rstrip()]
        cur_cat = None
        continue
    if in_char:
        char_blocks[char_label].append(line.rstrip())
        continue

    # 注释行（# 开头）
    if s.startswith("#"):
        handled = False
        for key, cat in SENTINELS.items():
            if key in s:
                cur_cat = cat
                counter = 0
                handled = True
                break
        if handled:
            continue  # 顶层哨兵头：跳过（===X=== 头已涵盖）
        # 子分类头（## ...）作为注释保留
        if cur_cat:
            sections[cur_cat].append(s)
        continue

    # 普通中文描述头（下面整理...）
    handled = False
    for key, cat in SENTINELS.items():
        if key in s:
            cur_cat = cat
            counter = 0
            sections[cat].append(f"# {s}")
            handled = True
            break
    if handled:
        continue

    # 备注/说明行
    if is_note(s):
        if cur_cat:
            sections[cur_cat].append(f"# {s}")
        continue

    # NPC 块检测：在 E（サポーター，均带编号）之后出现不带编号的名称 -> 进入 D
    if cur_cat == "E" and not re.match(r"^(\d+)[.．]\s|^\[\d+\]", s):
        cur_cat = "D"
        counter = 0

    if cur_cat is None:
        continue

    # 提取名称
    mm = re.match(r"^\[(\d+)\]\s*(.*)$", s)
    if mm:
        name = mm.group(2).strip()
    else:
        mm = re.match(r"^(\d+)[.．]\s*(.*)$", s)
        name = mm.group(2).strip() if mm else s

    # 特殊处理：資金 正式名称为 ビビビッとコイン
    if name == "資金":
        sections[cur_cat].append("# （文中表记为「資金」）")
        name = "ビビビッとコイン"

    if name in seen[cur_cat]:
        sections[cur_cat].append(f"# 重复跳过: {name}")
        continue
    seen[cur_cat].add(name)
    counter += 1
    sections[cur_cat].append(f"[{counter}] {name}")

# 备份旧文件
if OLD.exists():
    BAK.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OLD, BAK)

out = [HEADER.rstrip("\n"), ""]
# 角色块原样输出（A/B/C 顺序）
for lbl in ["A", "B", "C"]:
    if lbl in char_blocks:
        out.extend(char_blocks[lbl])
        out.append("")
# 其余分类按 MAP 顺序
for lbl in ["D", "E", "F", "G", "H", "I"]:
    out.append(SECTION_HEADERS[lbl])
    out.extend(sections[lbl])
    out.append("")

OUT_TEXT = "\n".join(out).rstrip("\n") + "\n"
OLD.write_text(OUT_TEXT, encoding="utf-8")

# 统计
print("=== 分类计数 ===")
for lbl in ["A", "B", "C"]:
    if lbl in char_blocks:
        n = sum(1 for x in char_blocks[lbl] if re.match(r"^\[\d+\]", x.strip()))
        print(f"{lbl} (角色): {n}")
for lbl in ["D", "E", "F", "G", "H", "I"]:
    n = sum(1 for x in sections[lbl] if re.match(r"^\[\d+\]", x.strip()))
    print(f"{lbl}: {n}")
print("备份 ->", BAK)
