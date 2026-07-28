#!/usr/bin/env python3
"""由 必殺技/固有効果 精翻清单生成 glossary/skills.yaml（JA→ZH）。

源：tools/_translated_texts/skill_unique_effects_20260727.txt   （# MAP + ===X=== + [N] 日文）
译文：tools/_translated_texts/skill_unique_effects_20260729_translated.txt （同结构，[N] 中文）
按 (label, [N]) 对齐配对，跳过 zh==ja（未译/英文/同形）条目，写入 glossary/skills.yaml。
渲染期由 i18n.render_locale 以归一化 ja 精确匹配做最高优先级覆盖（防被其他翻译覆盖）。
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from escah_pipeline import i18n as I  # noqa: E402

SRC = ROOT / "tools" / "_translated_texts" / "skill_unique_effects_20260727.txt"
TRG = ROOT / "tools" / "_translated_texts" / "skill_unique_effects_20260729_translated.txt"
OUT = ROOT / "glossary" / "skills.yaml"

_MAP_RE = re.compile(r"^#\s*MAP\s+([A-Za-z0-9_-]+)\s*=\s*(.+?)\s*$")
_SEP_RE = re.compile(r"^===\s*([A-Za-z0-9_-]+)\s*===\s*$")
_NUM_RE = re.compile(r"^\[(\d+)\]\s*(.*)$")


def parse(path: Path):
    labels: dict[str, str] = {}
    cur = None
    out: dict[tuple[str, int], str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.rstrip("\n")
        m = _MAP_RE.match(s)
        if m:
            labels[m.group(1).strip()] = m.group(2).strip()
            continue
        m = _SEP_RE.match(s)
        if m:
            cur = m.group(1).strip()
            continue
        m = _NUM_RE.match(s)
        if m and cur is not None:
            out[(cur, int(m.group(1)))] = m.group(2).strip()
    return labels, out


def main() -> None:
    src_labels, src = parse(SRC)
    trg_labels, trg = parse(TRG)
    # label 一致性（仅告警）
    for lab in set(src_labels) | set(trg_labels):
        if src_labels.get(lab) != trg_labels.get(lab):
            print(f"[warn] label 不一致 {lab}: src={src_labels.get(lab)} trg={trg_labels.get(lab)}")
    skills: dict[str, str] = {}
    conflicts = 0
    matched = 0
    skipped = 0
    missing = 0
    per_label: "defaultdict[str, int]" = defaultdict(int)
    for (label, n), ja in src.items():
        if not ja:
            continue
        zh = trg.get((label, n))
        if zh is None:
            missing += 1
            continue
        if zh == ja:  # 未译/英文/同形，无需替换
            skipped += 1
            continue
        nkey = I._norm(ja)
        if nkey in skills and skills[nkey] != zh:
            conflicts += 1
        skills[nkey] = zh  # 归一化 ja 作键，渲染期 _norm 命中；last-wins
        matched += 1
        per_label[src_labels.get(label, label)] += 1
    OUT.write_text(
        "# 必殺技/固有効果 精翻词表（JA→ZH，2026-07-29 精炼版）\n"
        "# 来源：tools/_translated_texts/skill_unique_effects_20260727.txt (JA) + skill_unique_effects_20260729_translated.txt (ZH) 配对\n"
        "# 用途：i18n.render_locale 最高优先级覆盖（仅 zh，按归一化 ja 精确匹配），防被其他翻译覆盖。\n"
        "# 键=归一化 ja，值=规范中文译文。\n",
        encoding="utf-8",
    )
    import yaml

    with OUT.open("a", encoding="utf-8") as f:
        yaml.safe_dump({"skills": skills}, f, allow_unicode=True, sort_keys=False)
    print(f"写入 {OUT}")
    print(f"  匹配条目={matched}  跳过(=ja)={skipped}  缺译文={missing}  冲突(last-wins)={conflicts}")
    print(f"  覆盖角色/页段数={len(per_label)}")


if __name__ == "__main__":
    main()
