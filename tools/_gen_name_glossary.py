"""从 name_glossary_20260727.txt(JA) + 同名 _translated.txt(ZH) 配对生成 glossary/names.yaml。

配对键 = (===X=== 段标记, [N] 序号)。两文件段标记与 [N] 对齐。
生成 JA -> ZH 专有名词（名字）词表，供 i18n render_locale 做最高优先级子串替换。
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools/_todo_translate/name_glossary_20260727.txt"
TR = ROOT / "tools/_todo_translate/name_glossary_20260727 copy.txt"
OUT = ROOT / "glossary/names.yaml"

# 段头：可选前导 '#'，尾部可有注释
_SEP_RE = re.compile(r"^\s*#?\s*===\s*([A-Za-z]+)\s*===\s*(?:#.*)?$")
# 条目：[N] 文本（单行）
_ENTRY_RE = re.compile(r"^\s*\[(\d+)\]\s*(.*?)\s*$")


def parse(text: str) -> dict[str, list[str]]:
    """返回 {段标记: [按 [N] 顺序的文本列表]}。"""
    out: dict[str, list[str]] = {}
    cur = None
    for line in text.splitlines():
        m = _SEP_RE.match(line)
        if m:
            cur = m.group(1)
            out.setdefault(cur, [])
            continue
        if line.lstrip().startswith("#"):
            continue  # 指令行 / # MAP / ## 子分类注释
        if cur is None:
            continue
        e = _ENTRY_RE.match(line)
        if e:
            out[cur].append(e.group(2).strip())
    return out


def main() -> None:
    src = parse(SRC.read_text(encoding="utf-8"))
    tr = parse(TR.read_text(encoding="utf-8"))

    if set(src) != set(tr):
        print("段标记不一致: src=", sorted(src), " tr=", sorted(tr))
        return

    pairs: dict[str, tuple[str, str]] = {}  # ja -> zh（保持顺序用 list 另存）
    ordered: list[tuple[str, str]] = []
    problems: list[str] = []
    for label in src:
        ja_list = src[label]
        zh_list = tr[label]
        if len(ja_list) != len(zh_list):
            problems.append(f"段 {label}: JA {len(ja_list)} 条 vs ZH {len(zh_list)} 条，无法对齐")
            continue
        for ja, zh in zip(ja_list, zh_list):
            if not ja or not zh:
                problems.append(f"段 {label}: 空条目 ja={ja!r} zh={zh!r}")
                continue
            if ja in pairs and pairs[ja] != zh:
                problems.append(f"段 {label}: JA {ja!r} 有冲突译文 {pairs[ja]!r} vs {zh!r}")
                continue
            if ja not in pairs:
                pairs[ja] = zh
                ordered.append((ja, zh))

    if problems:
        print("对齐问题：")
        for p in problems:
            print("  ", p)
        return

    # 统计每段的条目数
    seg_counts = {k: len(v) for k, v in src.items()}
    total = len(ordered)
    print(f"配对称功：{total} 条，分段计数 {seg_counts}")

    # 写 glossary/names.yaml
    lines = [
        "# ============================================================================",
        "# 专有名词（名字）精译词表  JA → ZH   ESCH 双语镜像站",
        "# ----------------------------------------------------------------------------",
        "# 用途：角色名 / NPC / 支援者 / 道具 / 装备 / 宝箱掉落物 / BOSS 等专有名词的",
        "#      规范中文译名。来源：tools/_todo_translate/name_glossary_20260727.txt",
        "#      （JA 原文）与其精译 _translated.txt（ZH）。",
        "# 作用：i18n render_locale 在渲染 zh 时，对所有页面按本表做「最高优先级」",
        "#      JA 子串替换（长词优先），覆盖 LLM/机翻的不一致译名；适用于当前与",
        "#      未来所有页面（随 build/渲染自动生效，重建不丢失）。",
        "# 维护：新增/更正专有名词时，在此追加「日文原名: 中文」即可，无需改代码。",
        "# ============================================================================",
        "names:",
    ]
    for ja, zh in ordered:
        # YAML 双引号转义
        j = ja.replace("\\", "\\\\").replace('"', '\\"')
        z = zh.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'  "{j}": "{z}"')
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已写入 {OUT}（{total} 条）")


if __name__ == "__main__":
    main()
