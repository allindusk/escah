#!/usr/bin/env python3
"""扫描所有角色 JSON，找出「名字 / 必殺技名」尚未进入 glossary（无真正中文译名）的条目。

用途（用户要求的前瞻逻辑）：今后**新增角色页**后，跑本脚本确认新角色的名字与必殺技
是否已纳入 glossary/names.yaml 与 glossary/skills.yaml（最高优先级覆盖）。缺译的会写入
tools/_glossary_pending.txt 待译清单，译者填好后重跑：
    python tools/_gen_name_glossary.py
    python tools/_gen_skill_glossary.py
即可把新角色词汇并入 glossary。

判断口径与 i18n 渲染一致：glossary 中 ja==zh 的条目视为「未真正翻译」，按缺失处理
（与 i18n._load_name_glossary 跳过 k==v 的口径统一）。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from escah_pipeline import i18n as I  # noqa: E402

CHAR_DIR = ROOT / "data" / "parsed" / "characters"
PENDING = ROOT / "tools" / "_glossary_pending.txt"

# 假名范围：仅当技能名仍含平/片假名才算「未翻译」（已译为中文的纯汉字名不算缺失）
_KANA_RE = __import__("re").compile(
    r"[\u3040-\u309F\u30A0-\u30FF\u31F0-\u31FF\uFF65-\uFF9F]"
)


def _has_kana(s: str) -> bool:
    return bool(_KANA_RE.search(s or ""))


# 不翻译名单：代号 / 非日语 / 用户指定保持原样的名字。这些不进 glossary、
# name_zh 留空（浮窗显示原样），也不应被本工具报为「缺译」。新增此类名字在此追加。
# 判定口径：纯字母数字（无假名/无汉字）的代号类自动归入，无需手动列。
_DO_NOT_TRANSLATE = {
    "FM77",
    "女郎蜘蛛初音",
    "女郎蜘蛛奏子",
}


def _is_plain_code(s: str) -> bool:
    """纯字母/数字/符号、不含任何日文（无假名无汉字）→ 视为代号，不翻译。"""
    return bool(s) and not _KANA_RE.search(s) and not any(
        "\u4E00" <= c <= "\u9FFF" for c in s
    )


def main() -> None:
    I._load_name_glossary()
    I._load_skill_glossary()
    # 名字：用原始 k->v，再归一化比对；仅计「有真正译名」(k!=v 且在表)
    names = I._NAME_MAP or {}
    names_norm = {I._norm(k): v for k, v in names.items()}
    skills_norm = I._SKILL_NORM or {}  # 已是归一化 key

    name_missing: list[tuple[str, str]] = []    # (char_id, name)
    skill_missing: list[tuple[str, str]] = []   # (char_id, skill_name)
    name_skipped: list[tuple[str, str]] = []    # 不翻译名单 / 代号，已跳过

    for p in sorted(CHAR_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        nm = d.get("name")
        if not nm:
            continue
        if nm in _DO_NOT_TRANSLATE or _is_plain_code(nm):
            name_skipped.append((p.stem, nm))
            continue
        if I._norm(nm) not in names_norm:
            name_missing.append((p.stem, nm))
        sec = (d.get("sections") or {}).get("必殺技")
        if isinstance(sec, dict):
            for r in sec.get("rows", []):
                if not r or r[0].get("h"):   # 跳过表头
                    continue
                sk = r[0].get("t")
                # 仅当技能名仍含日文（假名）且未在 skills.yaml 命中才算缺译；
                # 已是中文纯汉字的技能名视为已翻译，跳过（避免误报）。
                if sk and _has_kana(sk) and I._norm(sk) not in skills_norm:
                    skill_missing.append((p.stem, sk))

    print(f"角色名缺译（未纳入 names.yaml 或 ja==zh）：{len(name_missing)}")
    for cid, nm in name_missing:
        print(f"  [{cid}] {nm}")
    print(f"角色名跳过（不翻译名单/代号，保持原样）：{len(name_skipped)}")
    for cid, nm in name_skipped:
        print(f"  [{cid}] {nm}")
    print(f"必殺技名缺译（未纳入 skills.yaml）：{len(skill_missing)}")
    for cid, sk in skill_missing[:60]:
        print(f"  [{cid}] {sk}")
    if len(skill_missing) > 60:
        print(f"  ... 其余 {len(skill_missing) - 60} 条省略")

    lines = ["# 待补译词汇（新增角色，由 _check_glossary_coverage.py 生成）",
             "# 译者填好中文后，重跑 _gen_name_glossary.py / _gen_skill_glossary.py",
             "=== NAMES ==="]
    for cid, nm in name_missing:
        lines.append(f"{nm}\t# char={cid}")
    lines.append("=== SKILLS ===")
    for cid, sk in skill_missing:
        lines.append(f"{sk}\t# char={cid}")
    PENDING.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已写入待译清单 {PENDING}")


if __name__ == "__main__":
    main()
